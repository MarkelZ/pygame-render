import pygame
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable, Optional


@dataclass(frozen=True)
class Glyph:
    """Geometry data for a single glyph inside the atlas."""
    size_px: Tuple[int, int]        # (w, h) in pixels of the rendered glyph surface
    uv: Tuple[float, float, float, float]  # (u1, v1, u2, v2) in [0,1]


class FontAtlas:
    """
    Builds a texture atlas for a font and generates a textured-quad vertex buffer
    for strings with wrapping and alignment.

    Coordinates:
        - NDC: x in [-1,1] left to right, y in [-1,1] bottom to top (OpenGL-style).
        - Position is given in pixel coordinates, relative to the top-left of the layer.
    """

    # Characters included in the atlas by default (printable ASCII).
    CHAR_START = 32   # space
    CHAR_END   = 126  # '~'
    ATLAS_COLS = 16
    PADDING_PX = 4        # padding around each glyph to reduce bleeding
    UV_SHRINK  = 0.5      # sub-pixel shrink (in pixel units) for UVs to reduce bleeding

    def __init__(self, engine, font_path: str, font_size: int):
        if not pygame.font.get_init():
            pygame.font.init()

        self.font_size = int(font_size)
        self.font = pygame.font.Font(font_path, self.font_size)

        # Metrics useful for packing & layout
        self.ascent = self.font.get_ascent()
        self.descent = self.font.get_descent()
        self.linesize = self.font.get_linesize()
        self.space_advance_px = self.font.size(" ")[0]

        # Precompute glyphs & build atlas texture
        self.glyphs: Dict[str, Glyph] = {}
        atlas_surface = self._build_atlas_surface()
        self.font_texture = engine.surface_to_texture(atlas_surface)  # keeps API the same

    def build_vertices(
        self,
        layer_width: int,
        layer_height: int,
        text: str,
        scale: float = 1.0,
        position: Tuple[float, float] = (0.0, 0.0),
        width: Optional[float] = None,
        alignment: str = "left",
        letter_frame: Optional[int] = None,
    ) -> np.ndarray:
        """
        Create a vertex buffer (x, y, u, v) for the given text as a numpy float32 array.

        Args:
            layer_width, layer_height: Target surface size in pixels.
            text: The string to render. Supports '\n'.
            scale: Multiplier for glyph size (1.0 = font size).
            position: (x,y) in pixels, offset from the top-left of the layer.
            width: Optional wrap width in pixels. If None, wraps to the right edge.
            alignment: 'left' | 'center' | 'right' (applied within the wrapping box).
            letter_frame: If provided, only the first (letter_frame+1) characters are laid out.

        Returns:
            np.ndarray with shape (N, ) of interleaved [x, y, u, v] for 6 verts per glyph (two triangles).
        """
        if not text:
            return np.zeros((0,), dtype=np.float32)

        # Convert layout quantities to NDC
        left_ndc, top_ndc = self._pixels_to_ndc(position[0], position[1], layer_width, layer_height)
        box_width_ndc = (
            2.0 * (width / layer_width) if width is not None
            else 1.0 - left_ndc  # from left edge of box to NDC right edge (+1)
        )

        # Precompute per-char NDC advances
        def px_w_to_ndc(px: float) -> float:
            return 2.0 * (px / layer_width) * scale

        def px_h_to_ndc(px: float) -> float:
            return 2.0 * (px / layer_height) * scale

        # STEP 1: Layout the FULL text to determine where each character should be positioned
        # This ensures words don't jump around during animation
        lines: List[List[Tuple[str, float, float]]] = []  # list of lines, each as [(char, w_ndc, h_ndc)]
        current: List[Tuple[str, float, float]] = []
        line_w = 0.0
        line_h = 0.0

        def commit_line():
            nonlocal current, line_w, line_h
            if current:
                lines.append(current)
                current = []
            line_w = 0.0
            line_h = 0.0

        tokens = FontAtlas._tokenize(text)  # words + spaces + newlines

        for tok in tokens:
            if tok == "\n":
                commit_line()
                continue

            # Measure token in NDC
            tok_quads: List[Tuple[str, float, float]] = []
            tok_w = 0.0
            tok_h = 0.0
            for ch in tok:
                g = self.glyphs.get(ch)
                if not g:
                    # Unknown char: approximate using space width
                    w_ndc = px_w_to_ndc(self.space_advance_px)
                    h_ndc = px_h_to_ndc(self.linesize)
                else:
                    w_ndc = px_w_to_ndc(g.size_px[0])
                    h_ndc = px_h_to_ndc(g.size_px[1])
                tok_quads.append((ch, w_ndc, h_ndc))
                tok_w += w_ndc
                tok_h = max(tok_h, h_ndc)

            # Check if this is a word (not just spaces)
            is_word = not tok.isspace()
            
            # For words: check if word fits on current line
            if is_word and line_w > 0.0:
                # If this word doesn't fit, wrap to new line BEFORE adding it
                if (line_w + tok_w) > box_width_ndc:
                    # Remove trailing spaces before wrapping
                    while current and current[-1][0].isspace():
                        removed_ch, removed_w, removed_h = current.pop()
                        line_w -= removed_w
                    commit_line()

            # Append the entire token as one unit (never break words)
            for ch, w_ndc, h_ndc in tok_quads:
                current.append((ch, w_ndc, h_ndc))
            line_w += tok_w
            line_h = max(line_h, tok_h)

        commit_line()
        
        # STEP 2: Now apply letter_frame by only rendering characters up to that index
        # But they keep their pre-calculated positions from the full layout
        if letter_frame is not None:
            if letter_frame < 0:
                return np.zeros((0,), dtype=np.float32)
            
            # Flatten lines to count characters and truncate
            char_index = 0
            truncated_lines = []
            for line in lines:
                truncated_line = []
                for char_data in line:
                    if char_index <= letter_frame:
                        truncated_line.append(char_data)
                        char_index += 1
                    else:
                        break
                if truncated_line:
                    truncated_lines.append(truncated_line)
                if char_index > letter_frame:
                    break
            lines = truncated_lines

        # Build vertices with alignment applied within the box [left_ndc, left_ndc + box_width_ndc]
        verts: List[float] = []
        y = top_ndc
        for line in lines:
            lw = sum(w for _, w, _ in line)
            lh = max((h for _, _, h in line), default=0.0)

            x = self._aligned_start_x(left_ndc, box_width_ndc, lw, alignment)

            for ch, w, h in line:
                g = self.glyphs.get(ch)
                if not g:
                    x += w  # skip unknown characters but advance
                    continue

                u1, v1, u2, v2 = g.uv

                # two triangles (x,y is top-left in NDC)
                verts.extend([
                    x,     y - h, u1, v2,  # bottom-left
                    x + w, y - h, u2, v2,  # bottom-right
                    x,     y,     u1, v1,  # top-left

                    x,     y,     u1, v1,  # top-left
                    x + w, y - h, u2, v2,  # bottom-right
                    x + w, y,     u2, v1,  # top-right
                ])

                x += w

            y -= lh  # next baseline downwards

        return np.asarray(verts, dtype=np.float32)

    def _build_atlas_surface(self) -> pygame.Surface:
        """Rasterize glyphs, pack them in a grid, compute UVs & sizes."""
        # Determine a reasonable cell size
        widest = max(self.font.size("M")[0], self.font.size("W")[0], self.font.size("@")[0])
        max_height = self.ascent + abs(self.descent)
        cell_w = widest + 2 * self.PADDING_PX
        cell_h = max_height + 2 * self.PADDING_PX

        cols = self.ATLAS_COLS
        num_chars = self.CHAR_END - self.CHAR_START + 1
        rows = (num_chars + cols - 1) // cols

        atlas_w = cols * cell_w
        atlas_h = rows * cell_h

        surf = pygame.Surface((atlas_w, atlas_h), pygame.SRCALPHA, 32).convert_alpha()
        surf.fill((0, 0, 0, 0))

        for i, code in enumerate(range(self.CHAR_START, self.CHAR_END + 1)):
            ch = chr(code)
            glyph_surface = self.font.render(ch, True, (255, 255, 255))
            gw, gh = glyph_surface.get_size()

            col = i % cols
            row = i // cols
            x_px = col * cell_w + self.PADDING_PX
            y_px = row * cell_h + self.PADDING_PX

            # Blit at padding offset; pygame already gives a tight glyph surface
            surf.blit(glyph_surface, (x_px, y_px))

            # UVs with a small inward offset to prevent sampling bleeding
            u1 = (x_px + self.UV_SHRINK) / atlas_w
            v1 = 1.0 - (y_px + self.UV_SHRINK) / atlas_h
            u2 = (x_px + gw - self.UV_SHRINK) / atlas_w
            v2 = 1.0 - (y_px + gh - self.UV_SHRINK) / atlas_h

            self.glyphs[ch] = Glyph(size_px=(gw, gh), uv=(u1, v1, u2, v2))

        return surf

    # ================================
    # Helpers
    # ================================

    @staticmethod
    def _pixels_to_ndc(x_px: float, y_px: float, layer_w: int, layer_h: int) -> Tuple[float, float]:
        """
        Convert top-left pixel position to NDC coordinates (OpenGL-style).
        """
        x_ndc = -1.0 + 2.0 * (x_px / layer_w)
        y_ndc =  1.0 - 2.0 * (y_px / layer_h)
        return x_ndc, y_ndc

    @staticmethod
    def _aligned_start_x(left: float, box_w: float, line_w: float, alignment: str) -> float:
        """
        Compute the starting x for a given line width within a box anchored at `left` with width `box_w`.
        """
        a = alignment.lower()
        if a == "center":
            return left + max(0.0, (box_w - line_w) * 0.5)
        if a == "right":
            return left + max(0.0, (box_w - line_w))
        # default 'left'
        return left

    def _tokenize(s: str) -> Iterable[str]:
        """
        Split into words, spaces, and newlines so we can wrap word-wise but preserve spacing.
        Example: "Hello  world\n!" -> ["Hello", "  ", "world", "\n", "!"]
        """
        if not s:
            return []

        tokens: List[str] = []
        buf: List[str] = []
        mode: Optional[str] = None  # 'word' | 'space'

        def flush():
            nonlocal buf, mode
            if buf:
                tokens.append("".join(buf))
                buf = []
                mode = None

        for ch in s:
            if ch == "\n":
                flush()
                tokens.append("\n")
                continue
            if ch.isspace():
                if mode != "space":
                    flush()
                    mode = "space"
                buf.append(ch)
            else:
                if mode != "word":
                    flush()
                    mode = "word"
                buf.append(ch)

        flush()
        return tokens
