from moderngl import Texture, Framebuffer
from pygame_render.util import normalize_color_arguments


class Layer:

    def __init__(self, tex: Texture, fbo: Framebuffer) -> None:
        self._tex = tex
        self._fbo = fbo

    @property
    def texture(self) -> Texture:
        return self._tex

    @property
    def framebuffer(self) -> Framebuffer:
        return self._fbo

    @property
    def size(self) -> tuple[int, int]:
        return self._fbo.size

    def clear(self, R: (int | tuple[int]) = 0, G: int = 0, B: int = 0, A: int = 255):
        """
        Clear the layer with a color.

        Args:
            R (int or tuple[int]): Red component value or tuple containing RGB or RGBA values (0-255).
            G (int): Green component value (0-255).
            B (int): Blue component value (0-255).
            A (int): Alpha component value (0-255).
        """
        R, G, B, A = normalize_color_arguments(R, G, B, A)
        self._fbo.clear(R, G, B, A)
