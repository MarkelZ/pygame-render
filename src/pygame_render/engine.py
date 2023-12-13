from importlib import resources
import numbers

import moderngl
from moderngl import Texture, Context, NEAREST
import numpy as np
from OpenGL.GL import glGetUniformBlockIndex, glUniformBlockBinding
import pygame

from pygame_render.layer import Layer
from pygame_render.shader import Shader
from pygame_render.util import normalize_color_arguments, create_rotated_rect, to_dest_coords


class RenderEngine:
    """
    A rendering engine for 2D graphics using Pygame and ModernGL.

    This class initializes a rendering environment, including setting up Pygame for window creation,
    configuring OpenGL with ModernGL, and loading shaders for drawing. It provides a simple interface
    for creating and managing rendering layers, as well as drawing operations using shaders.
    """

    def __init__(self, screen_width: int, screen_height: int) -> None:
        """
        Initialize a rendering engine using Pygame and ModernGL.

        Parameters:
        - screen_width (int): The width of the rendering window.
        - screen_height (int): The height of the rendering window.

        Raises:
        - AssertionError: If Pygame is not initialized. Call pygame.init() before using the rendering engine.

        Note: Make sure to call pygame.init() before creating an instance of RenderEngine.
        """
        self._screen_res = (screen_width, screen_height)

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
        prog_draw = self._ctx.program(vertex_shader=vertex_src,
                                      fragment_shader=fragment_src_draw)
        self._shader_draw = Shader(prog_draw)

    @property
    def screen(self) -> Layer:
        """Get the screen layer."""
        return self._screen

    @property
    def ctx(self) -> Context:
        """Get the ModernGL rendering context."""
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
                   components: int = 4,
                   data: bytes | None = None,
                   samples: int = 0,
                   alignment: int = 1,
                   dtype: str = 'f1',
                   internal_format: int | None = None) -> Layer:
        """
        Create a rendering layer with optional parameters. A layer consists of a texture and a framebuffer.

        Parameters:
        - size (tuple[int, int]): The dimensions (width, height) of the texture.
        - components (int): The number of components per texel (e.g., 1 for red, 3 for RGB, 4 for RGBA).
        - data (bytes | None): Optional initial data for the texture. If None, the texture data is uninitialized.
        - samples (int): The number of samples. Value 0 means no multisample format.
        - alignment (int): The byte alignment 1, 2, 4 or 8.
        - dtype (str): Data type.
        - internal_format (int): Override the internal format of the texture (IF needed).

        Returns:
        - Layer
        """
        tex = self.ctx.texture(size, components, data, samples=samples,
                               alignment=alignment, dtype=dtype,
                               internal_format=internal_format)
        tex.filter = (NEAREST, NEAREST)
        fbo = self.ctx.framebuffer([tex])
        return Layer(tex, fbo)

    def make_shader(self, vertex_src: str, fragment_src: str) -> Shader:
        """
        Creates a shader program using the provided vertex and fragment shader source code.

        Parameters:
        - vertex_src (str): A string containing the source code for the vertex shader.
        - fragment_src (str): A string containing the source code for the fragment shader.

        Returns:
        - A Shader object representing the compiled shader program.

        Note: If you want to load the shader source code from a file path, consider using the
        'load_shader_from_path' method instead.
        """
        prog = self.ctx.program(vertex_shader=vertex_src,
                                fragment_shader=fragment_src)
        shader = Shader(prog)
        return shader

    def load_shader_from_path(self, vertex_path: str, fragment_path: str) -> Shader:
        """
        Loads shader source code from specified file paths and creates a shader program.

        Parameters:
        - vertex_path (str): File path to the vertex shader source code.
        - fragment_path (str): File path to the fragment shader source code.

        Returns:
        - A Shader object representing the compiled shader program.
        """
        with open(vertex_path) as f:
            vertex_src = f.read()
        with open(fragment_path) as f:
            fragment_src = f.read()

        return self.make_shader(vertex_src, fragment_src)

    def reserve_uniform_block(self, shader: Shader, ubo_name: str, nbytes: int) -> None:
        """
        Allocate the memory for a uniform block in a given shader.

        Parameters:
        - shader (Shader): The shader program for which the uniform block will be reserved.
        - ubo_name (str): The name of the uniform block in the shader program.
        - nbytes (int): The size, in bytes, to reserve for the uniform block in the buffer.
        """
        # Program's GL object
        prog_glo = shader.program.glo

        # Bind uniform block to given binding
        binding = shader.sample_ubo_binding()
        block_index = glGetUniformBlockIndex(prog_glo, ubo_name)
        glUniformBlockBinding(prog_glo, block_index, binding)

        # Create the uniform block
        ubo = self.ctx.buffer(reserve=nbytes)
        ubo.bind_to_uniform_block(binding)
        shader.add_ubo(ubo, ubo_name)

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
               flip: tuple[bool, bool] | bool = (False, False),
               section: pygame.Rect | None = None,
               shader: Shader = None) -> None:
        """
        Render a texture onto a layer with optional transformations.

        Parameters:
        - tex (Texture): The texture to render.
        - layer (Layer): The layer to render onto.
        - position (tuple[float, float]): The position (x, y) where the texture will be rendered. Default is (0, 0).
        - scale (tuple[float, float] | float): The scaling factor for the texture. Can be a tuple (x, y) or a scalar. Default is (1.0, 1.0).
        - angle (float): The rotation angle in degrees. Default is 0.0.
        - flip (tuple[bool, bool] | bool): Whether to flip the texture. Can be a tuple (flip x axis, flip y axis) or a boolean (flip x axis). Default is (False, False).
        - section (pygame.Rect | None): The section of the texture to render. If None, the entire texture is rendered. Default is None.
        - shader (Shader): The shader program to use for rendering. If None, a default shader is used. Default is None.

        Returns:
        None

        Note:
        - If scale is a scalar, it will be applied uniformly to both x and y.
        - If flip is a boolean, it will only affect the x axis.
        - If section is None, the entire texture is used.
        - If section is larger than the texture, the texture is repeated to fill the section.
        - If shader is None, a default shader (_prog_draw) is used.
        """

        # Create section rect if none
        if section == None:
            section = pygame.Rect(0, 0, tex.width, tex.height)

        # Default to draw shader program if none
        if shader == None:
            shader = self._shader_draw

        # If the scale is not a tuple but a scalar, convert it into a tuple
        if isinstance(scale, numbers.Number):
            scale = (scale, scale)

        # If flip is not a tuple but a boolean, convert it into a tuple
        if isinstance(flip, bool):
            flip = (flip, False)

        # Get the vertex coordinates of a rectangle that has been rotated,
        # scaled, and translated, in world coordinates
        points = create_rotated_rect(position, section.width,
                                     section.height, scale, angle, flip)

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
        vao = self._ctx.vertex_array(shader.program, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

        # Use textures
        tex.use()
        shader.bind_sampler2D_uniforms()

        # Set layer as target
        layer.framebuffer.use()

        # Render
        vao.render()

        # Clear the sampler2D locations
        shader.clear_sampler2D_uniforms()

        # Free vertex data
        vbo.release()
        vao.release()
