from importlib import resources
import moderngl
from moderngl import Texture, Framebuffer, Context, Program
import numpy as np
import pygame
import numbers
from pygame_render.layer import Layer

from pygame_render.util import normalize_color_arguments, create_rotated_rect, to_dest_coords


class RenderEngine:
    def __init__(self, screen_res: tuple[int, int]) -> None:
        self._screen_res = screen_res

        # Check that pygame has been initialized
        assert pygame.get_init(), 'Error: Pygame is not initialized. Please ensure you call pygame.init() before using the lighting engine.'

        # Set OpenGL version to 3.3 core
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        # Configure pygame display
        pygame.display.set_mode(
            self._screen_res, pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF)

        # Create an OpenGL context
        self._ctx = moderngl.create_context()
        self._ctx.enable(moderngl.BLEND)
        self._ctx.blend_func = self._ctx.SRC_ALPHA, self._ctx.ONE_MINUS_SRC_ALPHA

        # Create screen layer
        self._screen = Layer(None, self._ctx.screen)
        self._ctx.screen

        # Read draw shader source files
        vertex_src = resources.read_text(
            'pygame_render', 'vertex.glsl')
        fragment_src_draw = resources.read_text(
            'pygame_render', 'fragment_draw.glsl')

        # Create draw shader program
        self._prog_draw = self._ctx.program(vertex_shader=vertex_src,
                                            fragment_shader=fragment_src_draw)

    @property
    def screen(self) -> Layer:
        return self._screen

    @property
    def ctx(self) -> Context:
        return self._ctx

    def surface_to_texture(self, sfc: pygame.Surface) -> moderngl.Texture:
        """
        Convert a pygame.Surface to a moderngl.Texture.

        Args:
            sfc (pygame.Surface): Surface to convert.

        Returns:
            moderngl.Texture: Converted texture.
        """

        img_flip = pygame.transform.flip(sfc, False, True)
        img_data = pygame.image.tostring(img_flip, "RGBA")

        tex = self._ctx.texture(sfc.get_size(), components=4, data=img_data)
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        return tex

    def load_texture(self, path: str) -> moderngl.Texture:
        """
        Load a texture from a file.

        Args:
            path (str): Path to the texture file.

        Returns:
            moderngl.Texture: Loaded texture.
        """

        img = pygame.image.load(path).convert_alpha()
        return self.surface_to_texture(img)

    def make_layer(self,
                   size: tuple[int, int],
                   components: int,
                   data: bytes | None = None,
                   samples: int = 0,
                   alignment: int = 1,
                   dtype: str = 'f1',
                   internal_format: int | None = None) -> None:
        tex = self.ctx.texture(size, components, data, samples=samples,
                               alignment=alignment, dtype=dtype,
                               internal_format=internal_format)
        fbo = self.ctx.framebuffer([tex])
        return Layer(tex, fbo)

    def make_shader(self, vertex_src: str, fragment_src: str) -> Program:
        """
        Creates a shader program using the provided vertex and fragment shader source code.

        Parameters:
        - vertex_src (str): A string containing the source code for the vertex shader.
        - fragment_src (str): A string containing the source code for the fragment shader.

        Returns:
        - A ModernGL Program object representing the compiled shader program.

        Note: If you want to load the shader source code from a file path, consider using the
        'load_shader_from_path' method instead.
        """
        prog = self.ctx.program(vertex_shader=vertex_src,
                                fragment_shader=fragment_src)
        return prog

    def load_shader_from_path(self, vertex_path: str, fragment_path: str) -> Program:
        """
        Loads shader source code from specified file paths and creates a shader program.

        Parameters:
        - vertex_path (str): File path to the vertex shader source code.
        - fragment_path (str): File path to the fragment shader source code.

        Returns:
        - A ModernGL Program object representing the compiled shader program.
        """
        with open(vertex_path) as f:
            vertex_src = f.read()
        with open(fragment_path) as f:
            fragment_src = f.read()

        return self.make_shader(vertex_src, fragment_src)

    def clear(self, R: (int | tuple[int]) = 0, G: int = 0, B: int = 0, A: int = 255):
        """
        Clear the screen with a color.

        Args:
            R (int or tuple[int]): Red component value or tuple containing RGB or RGBA values (0-255).
            G (int): Green component value (0-255).
            B (int): Blue component value (0-255).
            A (int): Alpha component value (0-255).
        """
        R, G, B, A = normalize_color_arguments(R, G, B, A)
        self._ctx.screen.clear(R, G, B, A)

    def render(self,
               tex: Texture,
               layer: Layer,
               position: tuple[float, float] = (0, 0),
               scale: tuple[float, float] | float = (1.0, 1.0),
               angle: float = 0.0,
               section: pygame.Rect | None = None,
               shader: Program = None) -> None:
        """
        Render a texture onto a framebuffer with optional transformations.

        Parameters:
        - tex (Texture): The texture to render.
        - layer (Layer): The layer to render onto.
        - position (tuple[float, float]): The position (x, y) where the texture will be rendered. Default is (0, 0).
        - scale (tuple[float, float] | float): The scaling factor for the texture. Can be a tuple (x, y) or a scalar. Default is (1.0, 1.0).
        - angle (float): The rotation angle in degrees. Default is 0.0.
        - section (pygame.Rect | None): The section of the texture to render. If None, the entire texture is rendered. Default is None.
        - shader (Program): The shader program to use for rendering. If None, a default shader is used. Default is None.

        Returns:
        None

        Note:
        - If scale is a scalar, it will be applied uniformly to both x and y.
        - If section is None, the entire texture is used.
        - If section is larger than the texture, the texture is repeated to fill the section.
        - If shader is None, a default shader (_prog_draw) is used.
        """

        # Create section rect if none
        if section == None:
            section = pygame.Rect(0, 0, tex.width, tex.height)

        # Default to draw shader program if none
        if shader == None:
            shader = self._prog_draw

        # If the scale is not a tuple but a scalar, convert it into a tuple
        if isinstance(scale, numbers.Number):
            scale = (scale, scale)

        # Get the vertex coordinates of a rectangle that has been rotated,
        # scaled, and translated, in world coordinates
        points = create_rotated_rect(position, section.width,
                                     section.height, scale, angle)

        # Convert to destination coordinates
        dest_width, dest_height = layer.size
        points = [to_dest_coords(p, dest_width, dest_height) for p in points]

        # Mesh for destination rect on screen
        p1, p2, p3, p4 = points
        vertex_coords = np.array([p3, p4, p2,
                                  p2, p4, p1], dtype=np.float32)

        # Calculate the texture coordinates
        x = section.x / tex.width
        y = section.y / tex.height
        w = section.width / tex.width
        h = section.height / tex.height

        # Mesh for the section within the texture
        tex_coords = np.array([(x, y + h), (x + w, y + h), (x, y),
                               (x, y), (x + w, y + h), (x + w, y)], dtype=np.float32)

        # Create VBO and VAO
        buffer_data = np.hstack([vertex_coords, tex_coords])

        vbo = self._ctx.buffer(buffer_data)
        vao = self._ctx.vertex_array(shader, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

        # Use buffers and render
        tex.use()
        layer.framebuffer.use()
        vao.render()

        # Free vertex data
        vbo.release()
        vao.release()
