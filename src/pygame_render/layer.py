from moderngl import Texture, Framebuffer
from pygame_render.util import normalize_color_arguments


class Layer:
    """
    A rendering layer consisting of a texture and a framebuffer.

    Note: A Layer object cannot be instantiated directly. 
    Use RenderEngine.make_layer to create one.
    """

    def __init__(self, tex: Texture, fbo: Framebuffer) -> None:
        """
        Initialize a Layer with a given texture and framebuffer.

        Note: A Layer object cannot be instantiated directly. 
        Use RenderEngine.make_layer to create one.
        """

        self._tex = tex
        self._fbo = fbo

    @property
    def texture(self) -> Texture:
        """Get the texture associated with the layer."""
        return self._tex

    @property
    def framebuffer(self) -> Framebuffer:
        """Get the framebuffer associated with the layer."""
        return self._fbo

    @property
    def size(self) -> tuple[int, int]:
        """Get the size (width, height) of the layer."""
        return self._fbo.size

    @property
    def width(self) -> tuple[int, int]:
        """Get the width of the layer."""
        return self._fbo.width

    @property
    def height(self) -> tuple[int, int]:
        """Get the height of the layer."""
        return self._fbo.height

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

    def release(self):
        """
        Release the ModernGL object associated with the layer.
        """
        self._tex.release()
        self._fbo.release()
