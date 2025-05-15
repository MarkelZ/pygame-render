import pygame
import numpy as np


class FontAtlas:
    def __init__(self, engine, font_path: str, font_size: int):
        # Initialize pygame.font
        if not pygame.font.get_init():
            pygame.font.init()

        self.font_size = font_size
        self.font = pygame.font.Font(font_path, self.font_size)  # Preload font

        self.char_uvs = {}  # Dictionary to store character textures
        self.char_sizes = {}

        padding = 4  # Padding to avoid "bleeding"

        # Font metrics
        ascent = self.font.get_ascent()
        descent = self.font.get_descent()
        max_height = ascent + abs(descent)
        max_width = self.font.size("M")[0]  # Widest likely char

        cell_w = max_width + padding * 2
        cell_h = max_height + padding * 2

        cols = 16
        rows = ((127 - 32) + cols - 1) // cols

        atlas_width = cols * cell_w
        atlas_height = rows * cell_h

        atlas_surface = pygame.Surface(
            (atlas_width, atlas_height), pygame.SRCALPHA, 32
        ).convert_alpha()
        atlas_surface.fill((0, 0, 0, 0))

        for i, char_code in enumerate(range(32, 127)):
            char = chr(char_code)
            rendered_char = self.font.render(char, True, (255, 255, 255))
            char_w, char_h = rendered_char.get_size()

            col = i % cols
            row = i // cols

            # Blit with proper vertical offset using ascent to preserve tops
            x = col * cell_w + padding
            y = row * cell_h + padding + (ascent - self.font.get_ascent())

            atlas_surface.blit(rendered_char, (x, y))

            # Shrink UVs slightly to avoid bleeding
            u1 = (col * cell_w + padding + 0.5) / atlas_width
            v1 = 1 - (row * cell_h + padding + 0.5) / atlas_height
            u2 = (col * cell_w + padding + char_w - 0.5) / atlas_width
            v2 = 1 - (row * cell_h + padding + char_h - 0.5) / atlas_height

            self.char_uvs[char] = (u1, v1, u2, v2)
            self.char_sizes[char] = (char_w, char_h)

        self.font_texture = engine.surface_to_texture(atlas_surface)

    def get_char_batch(
        self,
        layer_width: int,
        layer_height: int,
        text: str,
        letter_frame: int,
        scale: float,
    ) -> np.ndarray:
        """
        Get the batch of characters of a string of text.

        Parameters:
        - layer_width: The width of the layer to draw on.
        - layer_height: The height of the layer to draw on.
        - text: The text to render.
        - letter_frame: The number of letters to render (useful for animations).
        - scale: Multiplier for glyph size (1.0 = original size).
        """
        text = text[: letter_frame + 1]

        x, y = -1.0, 1.0  # Start at the top-left corner
        line_width = 0  # Track width of the current line
        line_height = 0  # Track the maximum height of the current line

        vertices = []

        for char in text:
            if char in self.char_uvs and char in self.char_sizes:
                uv = self.char_uvs[char]
                char_w, char_h = self.char_sizes[
                    char
                ]  # Use true width from font rendering

                # Convert pixel size to OpenGL normalized space (-1 to 1)
                w = (char_w / layer_width) * 2 * scale
                h = (char_h / layer_height) * 2 * scale

                # Check if adding this character would exceed the width of the layer
                if line_width + w > 2.0:  # If line exceeds the width
                    # Move to the next line
                    x = -1.0  # Reset x to the start of the line
                    y -= line_height  # Move y down by the height of the current line
                    line_width = 0  # Reset line width
                    line_height = 0  # Reset line height
                    w = 0  # Skip space if new row

                # Define quad vertices (adjusted for OpenGL top-left origin)
                vertices.extend([
                    x, y - h, uv[0], uv[3],  
                    x + w, y - h, uv[2], uv[3],  
                    x, y, uv[0], uv[1],  

                    x, y, uv[0], uv[1],  
                    x + w, y - h, uv[2], uv[3],  
                    x + w, y, uv[2], uv[1]  
                ])

                # Update the current line's width and height
                line_width += w
                line_height = max(line_height, h)

                x += w  # Move x to the next character's position

        vertices = np.array(vertices, dtype=np.float32)

        return vertices

    def get_char_batch_aligned(
        self,
        layer_width: int,
        layer_height: int,
        text: str,
        letter_frame: int,
        scale: float,
        alignment: str = "left",
    ) -> np.ndarray:
        """
        Get the aligned batch of characters of a string of text.

        Parameters:
        - layer_width: The width of the layer to draw on.
        - layer_height: The height of the layer to draw on.
        - text: The text to render.
        - letter_frame: The number of letters to render (useful for animations).
        - scale: Multiplier for glyph size (1.0 = original size).
        - alignment: The alignment of the text, accepts 'left', 'center' and 'right'
        """
        text = text[: letter_frame + 1]

        max_width = 2.0  # Normalized OpenGL width (-1 to 1)
        lines = []
        current_line = []
        line_width = 0.0
        line_height = 0.0
        max_line_height = 0.0

        # --- Step 1: Break text into lines
        for char in text:
            if char in self.char_sizes:
                char_w, char_h = self.char_sizes[char]
                w = (char_w / layer_width) * 2 * scale
                h = (char_h / layer_height) * 2 * scale

                if line_width + w > max_width:
                    # Start new line
                    lines.append((current_line, line_width, max_line_height))
                    current_line = []
                    line_width = 0
                    max_line_height = 0

                current_line.append((char, w, h))
                line_width += w
                max_line_height = max(max_line_height, h)

        if current_line:
            lines.append((current_line, line_width, max_line_height))

        # --- Step 2: Render lines with alignment
        vertices = []

        y = 1.0  # Start from top of screen

        for line_chars, line_width, line_height in lines:
            # Determine starting x based on alignment
            if alignment == "center":
                x = -line_width / 2
            elif alignment == "right":
                x = 1.0 - line_width
            else:  # left
                x = -1.0

            for char, w, h in line_chars:
                uv = self.char_uvs[char]

                vertices.extend([
                    x, y - h, uv[0], uv[3],  
                    x + w, y - h, uv[2], uv[3],  
                    x, y, uv[0], uv[1],  

                    x, y, uv[0], uv[1],  
                    x + w, y - h, uv[2], uv[3],  
                    x + w, y, uv[2], uv[1]  
                ])

                x += w  # Move to next char

            y -= line_height  # Move down for next line

        vertices = np.array(vertices, dtype=np.float32)

        return vertices
