from importlib import resources
import warnings
import numbers
from math import sin, cos, radians

import moderngl
from moderngl import Texture, Context, NEAREST
import numpy as np
from OpenGL.GL import glGetUniformBlockIndex, glUniformBlockBinding
import pygame

from pygame_render.font_atlas import FontAtlas
from pygame_render.layer import Layer
from pygame_render.shader import Shader
from pygame_render.util import (
    normalize_color_arguments,
    create_rotated_rect,
    to_dest_coords,
    to_source_coords,
)


class RenderEngine:
    """
    A rendering engine for 2D graphics using Pygame and ModernGL.

    This class initializes a rendering environment, including setting up Pygame for window creation,
    configuring OpenGL with ModernGL, and loading shaders for drawing. It provides a simple interface
    for creating and managing rendering layers, as well as drawing operations using shaders.
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        fullscreen: int | bool = 0,
        resizable: int | bool = 0,
        noframe: int | bool = 0,
        scaled: int | bool = 0,
        depth: int = 0,
        display: int = 0,
        vsync: int = 0,
    ) -> None:
        """
        Initialize a rendering engine using Pygame and ModernGL.

        Parameters:
        - screen_width (int): The width of the rendering window.
        - screen_height (int): The height of the rendering window.
        - fullscreen (int or bool, optional): Set to 1 or True to enable fullscreen mode, 0 or False to disable. Default is 0.
        - resizable (int or bool, optional): Set to 1 or True to enable window resizing, 0 or False to disable. Default is 0.
        - noframe (int or bool, optional): Set to 1 or True to remove window frame, 0 or False to keep the frame. Default is 0.
        - scaled (int or bool, optional): Set to 1 or True to enable display scaling, 0 or False to disable. Default is 0.
        - depth (int, optional): Depth of the rendering window. Default is 0.
        - display (int, optional): The display index to use. Default is 0.
        - vsync (int, optional): Set to 1 to enable vertical synchronization, 0 to disable. Default is 0.

        Raises:
        - AssertionError: If Pygame is not initialized. Call pygame.init() before using the rendering engine.

        Note: Make sure to call pygame.init() before creating an instance of RenderEngine.
        """

        # Check that pygame has been initialized
        assert (
            pygame.get_init()
        ), "Error: Pygame is not initialized. Please ensure you call pygame.init() before using the lighting engine."

        # Set OpenGL version to 3.3 core
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
        )

        # Set multi-sample buffer for MSAA
        # pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)

        # Configure pygame display
        self._screen_res = (screen_width, screen_height)
        flags = pygame.OPENGL | pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN
        if resizable:
            flags |= pygame.RESIZABLE
        if noframe:
            flags |= pygame.NOFRAME
        if scaled:
            flags |= pygame.SCALED
        pygame.display.set_mode(
            self._screen_res, flags, depth=depth, display=display, vsync=vsync
        )

        # Create an OpenGL context
        self._ctx = moderngl.create_context()

        # Configure alpha blending
        self._ctx.enable(moderngl.BLEND)
        self._ctx.blend_func = (
            moderngl.SRC_ALPHA,
            moderngl.ONE_MINUS_SRC_ALPHA,
            moderngl.ONE,
            moderngl.ONE_MINUS_SRC_ALPHA,
        )
        self._ctx.blend_equation = moderngl.FUNC_ADD

        # Create screen layer
        self._screen = Layer(None, self._ctx.screen)
        self._ctx.screen

        # Read draw shader source files
        vertex_src = resources.read_text("pygame_render", "vertex.glsl")
        fragment_src_draw = resources.read_text("pygame_render", "fragment_draw.glsl")

        # Create draw shader program
        prog_draw = self._ctx.program(
            vertex_shader=vertex_src, fragment_shader=fragment_src_draw
        )
        self._shader_draw = Shader(prog_draw)

        # Read the tone mapping shader
        fragment_src_tonemap = resources.read_text(
            "pygame_render", "fragment_tone.glsl"
        )

        # Create draw shader program
        prog_tonemap = self._ctx.program(
            vertex_shader=vertex_src, fragment_shader=fragment_src_tonemap
        )
        self._shader_tonemap = Shader(prog_tonemap)
        self._exposure: float
        self.HDR_exposure = 0.1

        # Create a shader program for drawing primitives
        self.prog_prim = self.ctx.program(
            vertex_shader="""
            #version 330
            in vec2 vert;
            void main() {
            gl_Position = vec4(vert.x, vert.y, 0.0, 1.0);
            }""",
            fragment_shader="""
            #version 330
            uniform vec4 primColor;
            out vec4 color;
            void main() {
            color = primColor;
            }""",
        )

        # Read the text shader
        fragment_src_text = resources.read_text("pygame_render", "fragment_text.glsl")

        # Create text shader program
        prog_text = self._ctx.program(
            vertex_shader=vertex_src, fragment_shader=fragment_src_text
        )
        self._shader_text = Shader(prog_text)

    @property
    def screen(self) -> Layer:
        """Get the screen layer."""
        return self._screen

    @property
    def ctx(self) -> Context:
        """Get the ModernGL rendering context."""
        return self._ctx

    @property
    def display_size(self) -> tuple[int, int]:
        return pygame.display.get_window_size()

    @property
    def HDR_exposure(self) -> float:
        return self._exposure

    @HDR_exposure.setter
    def HDR_exposure(self, value: float) -> None:
        self._exposure = value
        self._shader_tonemap["exposure"] = value

    def use_alpha_blending(self, enabled: bool) -> None:
        """
        Enable or disable alpha blending.

        Args:
            enabled (bool): True to enable, False to disable premultiplied alpha blending.
        """
        if enabled:
            self._ctx.enable(moderngl.BLEND)
        else:
            self._ctx.disable(moderngl.BLEND)

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

    def make_layer(
        self,
        size: tuple[int, int],
        components: int = 4,
        data: bytes | None = None,
        samples: int = 0,
        alignment: int = 1,
        dtype: str = "f1",
        internal_format: int | None = None,
    ) -> Layer:
        """
        Create a rendering layer with optional parameters. A layer consists of a texture and a framebuffer.

        Parameters:
        - size (tuple[int, int]): The dimensions (width, height) of the texture.
        - components (int): The number of components per texel (e.g., 1 for red, 3 for RGB, 4 for RGBA).
        - data (bytes | None): Optional initial data for the texture. If None, the texture data is uninitialized.
        - samples (int): The number of samples. Value 0 means no multisample format.
        - alignment (int): The byte alignment 1, 2, 4 or 8.
        - dtype (str): Data type ('f4' for HDR textures).
        - internal_format (int): Override the internal format of the texture (IF needed).

        Returns:
        - Layer
        """
        tex = self.ctx.texture(
            size,
            components,
            data,
            samples=samples,
            alignment=alignment,
            dtype=dtype,
            internal_format=internal_format,
        )
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
        prog = self.ctx.program(vertex_shader=vertex_src, fragment_shader=fragment_src)
        shader = Shader(prog)
        return shader

    def make_font_atlas(self, font_path: str = None, font_size: int = 64) -> FontAtlas:
        return FontAtlas(self, font_path, font_size)

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

    def clear(self, R: int | tuple[int] = 0, G: int = 0, B: int = 0, A: int = 255):
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

    def render(
        self,
        tex: Texture,
        layer: Layer,
        position: tuple[float, float] = (0, 0),
        scale: tuple[float, float] | float = (1.0, 1.0),
        angle: float = 0.0,
        flip: tuple[bool, bool] | bool = (False, False),
        section: pygame.Rect | None = None,
        shader: Shader = None,
        hdr_render: bool = False,
    ) -> None:
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
        - hdr_render (bool): Whether to apply HDR tonemapping.

        Returns:
        None

        Note:
        - If scale is a scalar, it will be applied uniformly to both x and y.
        - If flip is a boolean, it will only affect the x axis.
        - If section is None, the entire texture is used.
        - If section is larger than the texture, the texture is repeated to fill the section.
        - If shader is None, a default shader (_prog_draw) is used.
        - If hdr_render is True, it uses an HDR texture with tone mapping applied.
        """

        self.render_batch(
            tex,
            layer,
            transforms=[
                {
                    "position": position,
                    "scale": scale,
                    "angle": angle,
                    "flip": flip,
                    "section": section,
                }
            ],
            shader=shader,
            hdr_render=hdr_render,
        )

    def render_from_vertices(
        self,
        tex: Texture,
        layer: Layer,
        dest_vertices: list[(float, float)],
        section_vertices: list[(float, float)],
        shader: Shader = None,
        hdr_render: bool = False,
    ) -> None:
        """
        Render a texture onto a layer given lists of vertices.

        Parameters:
        - tex (Texture): The texture to render.
        - layer (Layer): The layer to render onto.
        - dest_vertices (list[(float, float)]): The destination coordinates on the target layer.
        - section_vertices (list[(float, float)]): The section of the texture to render.
        - shader (Shader): The shader program to use for rendering. If None, a default shader is used. Default is None.
        - hdr_render (bool): Whether to apply HDR tonemapping.

        Returns:
        None
        """

        self.render_batch_from_vertices(
            tex,
            layer,
            dest_vertices_list=[dest_vertices],
            section_vertices_list=[section_vertices],
            shader=shader,
            hdr_render=hdr_render,
        )

    def render_batch(
        self,
        tex: Texture,
        layer: Layer,
        transforms: list[dict],
        shader: Shader = None,
        hdr_render: bool = False,
    ) -> None:
        """
        Efficiently render multiple instances of a texture using batched vertex data.

        Parameters:
        - tex (Texture): The texture to render.
        - layer (Layer): The layer to render onto.
        - transforms (list[dict]): Each dict should contain:
            - position
            - scale
            - angle
            - flip
            - section
        - shader (Shader): Optional shader. If None, uses internal.
        - hdr_render (bool): Whether to apply HDR tonemapping.

        Returns:
        None
        """

        dest_vertices_list = []
        section_vertices_list = []

        for tf in transforms:
            position = tf.get("position", (0, 0))
            scale = tf.get("scale", (1.0, 1.0))
            angle = tf.get("angle", 0.0)
            flip = tf.get("flip", (False, False))
            section = tf.get("section")

            if isinstance(scale, numbers.Number):
                scale = (scale, scale)
            if isinstance(flip, bool):
                flip = (flip, False)
            if section is None:
                section = pygame.Rect(0, 0, tex.width, tex.height)

            dest_vertices = create_rotated_rect(
                position, section.width, section.height, scale, angle, flip
            )
            section_vertices = [
                (section.x, section.y),
                (section.x + section.width, section.y),
                (section.x, section.y + section.height),
                (section.x + section.width, section.y + section.height),
            ]

            dest_vertices_list.append(dest_vertices)
            section_vertices_list.append(section_vertices)

        self.render_batch_from_vertices(
            tex, layer, dest_vertices_list, section_vertices_list, shader, hdr_render
        )

    def render_batch_from_vertices(
        self,
        tex: Texture,
        layer: Layer,
        dest_vertices_list: list[list[tuple[float, float]]],
        section_vertices_list: list[list[tuple[float, float]]],
        shader: Shader = None,
        hdr_render: bool = False,
    ) -> None:
        """
        Render multiple quads from raw vertex and texture coordinates.

        Parameters:
        - tex (Texture): The texture to render.
        - layer (Layer): The target framebuffer.
        - dest_vertices_list (list[tuple[float, float]]): List of destination vertices for all quads (6 per quad).
        - section_vertices_list (list[tuple[float, float]]): List of texture coordinates for all quads (6 per quad).
        - shader (Shader): Shader to use. Defaults to _shader_draw.
        - hdr_render (bool): Whether to apply HDR tonemapping.

        Returns:
        None
        """

        if hdr_render:
            shader = self._shader_tonemap
        elif shader is None:
            shader = self._shader_draw

        all_dest_coords = []
        all_section_coords = []

        for dest_vertices, section_vertices in zip(
            dest_vertices_list, section_vertices_list
        ):
            # Convert screen coordinates to texture space
            vertex_coords = [
                to_dest_coords(p, layer.width, layer.height) for p in dest_vertices
            ]
            section_coords = [
                to_source_coords(p, tex.width, tex.height) for p in section_vertices
            ]

            # Triangle order: p3, p4, p2, p2, p4, p1
            p1, p2, p3, p4 = vertex_coords
            all_dest_coords.extend([p3, p4, p2, p2, p4, p1])

            p1, p2, p3, p4 = section_coords
            all_section_coords.extend([p3, p4, p1, p1, p4, p2])

        # Interleave and upload
        vertex_data = np.array(all_dest_coords, dtype=np.float32)
        section_data = np.array(all_section_coords, dtype=np.float32)
        buffer_data = np.hstack([vertex_data, section_data])

        vbo = self._ctx.buffer(buffer_data)
        vao = self._ctx.vertex_array(
            shader.program,
            [(vbo, "2f 2f", "vertexPos", "vertexTexCoord")],
        )

        tex.use()
        shader.bind_sampler2D_uniforms()
        layer.framebuffer.use()

        vao.render(moderngl.TRIANGLES)

        shader.clear_sampler2D_uniforms()
        vbo.release()
        vao.release()

    def render_batch_unique(
        self,
        tex: Texture,
        layer: Layer,
        transforms: list[dict],
        shader: Shader = None,
        hdr_render: bool = False,
        instance_uniforms: dict[str, list] = None,
    ) -> None:
    
        if hdr_render:
            shader = self._shader_tonemap
        elif shader is None:
            shader = self._shader_draw

        # Static base quad (normalized to [-0.5, 0.5])
        base_quad = np.array([
            [-0.5, -0.5], [0.0, 1.0],
            [ 0.5, -0.5], [1.0, 1.0],
            [-0.5,  0.5], [0.0, 0.0],
            [-0.5,  0.5], [0.0, 0.0],
            [ 0.5, -0.5], [1.0, 1.0],
            [ 0.5,  0.5], [1.0, 0.0],
        ], dtype=np.float32)

        base_vbo = self._ctx.buffer(base_quad.tobytes())
        vao_bindings = [(base_vbo, "2f 2f", "vertexPos", "vertexTexCoord")]

        # Per-instance VBOs
        instance_vbos = []

        positions = []
        scales = []
        angles = []

        for tf in transforms:
            positions.append(tf.get("position", (0, 0)))
            base_scale = tf.get("scale", 1.0)
            if isinstance(base_scale, (float, int)):
                base_scale = (base_scale, base_scale)

            section = tf.get("section", pygame.Rect(0, 0, tex.width, tex.height))
            pixel_scale = (section.width * base_scale[0] * 1, section.height * base_scale[1]*1)
            scales.append(pixel_scale)
            angle_in_radians = radians(tf.get('angle', 0.0))
            angles.append(angle_in_radians)

        def add_instance_attr(name, data, fmt):
            arr = np.array(data, dtype=np.float32)
            buf = self._ctx.buffer(arr)
            vao_bindings.append((buf, f"{fmt}/i", name))
            instance_vbos.append(buf)

        add_instance_attr("position", positions, "2f")
        add_instance_attr("scale", scales, "2f")
        add_instance_attr("angle", angles, "1f")

        if instance_uniforms:
            for name, values in instance_uniforms.items():
                first = values[0]
                if isinstance(first, (float, int)):
                    fmt = "1f"
                    data = np.array(values, dtype=np.float32).reshape(-1, 1)
                elif isinstance(first, (tuple, list)):
                    fmt = f"{len(first)}f"
                    data = np.array(values, dtype=np.float32)
                else:
                    raise TypeError(f"Unsupported type for '{name}'")
                add_instance_attr(name, data, fmt)

        vao = self._ctx.vertex_array(shader.program, vao_bindings)

        tex.use()
        shader.bind_sampler2D_uniforms()
        layer.framebuffer.use()

        shader["screenSize"] = (layer.width, layer.height)

        vao.render(moderngl.TRIANGLES, instances=len(positions))

        shader.clear_sampler2D_uniforms()
        vao.release()
        base_vbo.release()
        for buf in instance_vbos:
            buf.release()

    def render_batch_a_bit_faster(
        self,
        tex: Texture,
        layer: Layer,
        transforms: list[dict],
        shader: Shader = None,
        hdr_render: bool = False,
    ) -> None:
        """
        Efficiently render multiple instances of a texture with various transforms in a single GPU call.

        Parameters:
        - tex (Texture): The texture to render.
        - layer (Layer): The layer to render onto.
        - transforms (list[dict]): Each dict should have:
            - position (tuple[float, float])
            - scale (tuple[float, float] | float)
            - angle (float)
            - flip (tuple[bool, bool] | bool)
            - section (pygame.Rect | None)
        - shader (Shader): The shader to use. Defaults to internal shader.
        - hdr_render (bool): Whether to render using HDR tone mapping.

        Returns:
        None
        """

        if shader is None:
            shader = self._shader_tonemap if hdr_render else self._shader_draw

        all_vertex_data = []
        all_section_data = []

        for tf in transforms:
            position = tf.get("position", (0, 0))
            scale = tf.get("scale", (1.0, 1.0))
            angle = tf.get("angle", 0.0)
            flip = tf.get("flip", (False, False))
            section = tf.get("section")

            if isinstance(scale, numbers.Number):
                scale = (scale, scale)
            if isinstance(flip, bool):
                flip = (flip, False)
            if section is None:
                section = pygame.Rect(0, 0, tex.width, tex.height)

            dest_vertices = create_rotated_rect(
                position, section.width, section.height, scale, angle, flip
            )
            section_vertices = [
                (section.x, section.y),
                (section.x + section.width, section.y),
                (section.x, section.y + section.height),
                (section.x + section.width, section.y + section.height),
            ]

            # Convert to screen and texture coordinates
            vertex_coords = [to_dest_coords(p, layer.width, layer.height) for p in dest_vertices]
            section_coords = [to_source_coords(p, tex.width, tex.height) for p in section_vertices]

            # Order as triangles: [p3, p4, p2], [p2, p4, p1]
            p1, p2, p3, p4 = vertex_coords
            all_vertex_data.extend([p3, p4, p2, p2, p4, p1])

            p1, p2, p3, p4 = section_coords
            all_section_data.extend([p3, p4, p1, p1, p4, p2])

        # Combine and upload
        vertex_data = np.array(all_vertex_data, dtype=np.float32)
        section_data = np.array(all_section_data, dtype=np.float32)

        buffer_data = np.hstack([vertex_data, section_data])

        vbo = self._ctx.buffer(buffer_data)
        vao = self._ctx.vertex_array(
            shader.program,
            [(vbo, "2f 2f", "vertexPos", "vertexTexCoord")],
        )

        tex.use()
        shader.bind_sampler2D_uniforms()
        layer.framebuffer.use()
        vao.render(moderngl.TRIANGLES)
        shader.clear_sampler2D_uniforms()

        vbo.release()
        vao.release()


    def render_primitive(
        self,
        layer: Layer,
        color: tuple,
        vertices: list[tuple[float, float]],
        antialias: bool = False,
        mode: int = moderngl.LINES,
    ):
        """
        Render a primitive shape (e.g., lines, triangles) on the specified layer.

        :param layer: The rendering layer.
        :param color: The color of the primitive in (R, G, B) or (R, G, B, A) format.
        :param vertices: A list of vertex coordinates as (x, y) tuples.
        :param antialias: Enables antialiasing if True.
        :param mode: The rendering mode (e.g., LINES, TRIANGLES).
        """
        if len(color) == 3:
            color = (color[0], color[1], color[2], 255)

        # Enable MSAA
        if antialias:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)

        # Convert to destination coordinates
        dest_width, dest_height = layer.size
        dest_vertices = np.array(
            [to_dest_coords(v, dest_width, dest_height) for v in vertices]
        )

        # VBO and VAO
        vbo = self.ctx.buffer(dest_vertices.astype("f4").tobytes())
        vao = self.ctx.simple_vertex_array(self.prog_prim, vbo, "vert")

        # Send color uniform
        self.prog_prim["primColor"] = color

        # Set layer as target
        layer.framebuffer.use()

        # Render
        vao.render(mode)

        # Disable MSAA
        if antialias:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 1)

        # Free vertex data
        vbo.release()
        vao.release()

    def render_triangles(
        self,
        layer: Layer,
        color: tuple,
        vertices: list[tuple[float, float]],
        antialias: bool = False,
        strip: bool = False,
        fan: bool = False,
    ):
        """
        Render triangles on the specified layer.

        :param layer: The rendering layer.
        :param color: The color of the triangles in (R, G, B) or (R, G, B, A) format.
        :param vertices: A list of vertex coordinates as (x, y) tuples.
        :param antialias: Enables antialiasing if True.
        :param strip: If True, uses TRIANGLE_STRIP mode.
        :param fan: If True, uses TRIANGLE_FAN mode.
        """
        # Warn if both strip and fan flags are enabled simultaneously
        if strip and fan:
            warnings.warn(
                "Both strip and fan flags enabled. Overriding with strip flag."
            )

        # Pick the flag for the render mode
        if strip:
            flag = moderngl.TRIANGLE_STRIP
        elif fan:
            flag = moderngl.TRIANGLE_FAN
        else:
            flag = moderngl.TRIANGLES

        self.render_primitive(layer, color, vertices, antialias, flag)

    def render_lines(
        self,
        layer: Layer,
        color: tuple[float, float, float],
        vertices: list[tuple[float, float]],
        antialias: bool = False,
        strip: bool = False,
    ):
        """
        Render lines on the specified layer.

        :param layer: The rendering layer.
        :param color: The color of the lines in (R, G, B) or (R, G, B, A) format.
        :param vertices: A list of vertex coordinates as (x, y) tuples.
        :param antialias: Enables antialiasing if True.
        :param strip: If True, uses LINE_STRIP mode.
        """
        # Pick the flag for the render mode
        if strip:
            flag = moderngl.LINE_STRIP
        else:
            flag = moderngl.LINES

        self.render_primitive(layer, color, vertices, antialias, flag)

    def render_circle_arc(
        self,
        layer: Layer,
        color: tuple,
        center: tuple[float, float],
        radius: float,
        angle1: float,
        angle2: float,
        antialias: bool = False,
        num_segments: None | int = None,
    ):
        """
        Render a circular arc on the specified layer.

        :param layer: The rendering layer.
        :param color: The color of the arc in (R, G, B) or (R, G, B, A) format.
        :param center: The center of the arc as (x, y) tuple.
        :param radius: The radius of the arc.
        :param angle1: The starting angle of the arc in degrees.
        :param angle2: The ending angle of the arc in degrees.
        :param antialias: Enables antialiasing if True.
        :param num_segments: The number of segments to use for the arc. If None, defaults to a smooth arc.
        """
        # Ensure the arc always goes the shortest route
        if angle2 < angle1:
            angle2 += 360

        # If the number of segments is not provided, fix it to 32 segments per
        # 360 degrees, to get a smooth looking arc
        if num_segments == None:
            num_segments = max(4, int(32 * abs(angle2 - angle1) / 360))

        # Convert angles from degrees to radians
        angle1 = np.radians(angle1)
        angle2 = np.radians(angle2)

        # Include the center as the first vertex to render with TRIANGLE_FAN
        vertices = [center]

        # Generate the vertices
        for angle in np.linspace(angle1, angle2, num_segments + 1):

            # Calculate the x and y coordinates for each vertex
            x = center[0] + radius * cos(angle)
            y = center[1] + radius * sin(angle)

            vertices.append((x, y))

        # Render a triangle fan with the vertices
        self.render_primitive(layer, color, vertices, antialias, moderngl.TRIANGLE_FAN)

    def render_circle(
        self,
        layer: Layer,
        color: tuple,
        center: tuple[float, float],
        radius: float,
        antialias: bool = False,
        num_segments: int = None,
    ):
        """
        Render a full circle on the specified layer.

        :param layer: The rendering layer.
        :param color: The color of the circle in (R, G, B) or (R, G, B, A) format.
        :param center: The center of the circle as (x, y) tuple.
        :param radius: The radius of the circle.
        :param antialias: Enables antialiasing if True.
        :param num_segments: The number of segments to use for the circle. If None, defaults to a smooth circle.
        """
        self.render_circle_arc(
            layer, color, center, radius, 0, 360, antialias, num_segments
        )

    def render_rectangle(
        self,
        layer: Layer,
        color: tuple,
        position: tuple[float, float],
        width: float,
        height: float,
        angle: float = 0,
        antialias: bool = False,
    ):
        """
        Render a rectangle on the specified layer.

        :param layer: The rendering layer.
        :param color: The color of the rectangle in (R, G, B) or (R, G, B, A) format.
        :param position: The position of the rectangle's center as (x, y) tuple.
        :param width: The width of the rectangle.
        :param height: The height of the rectangle.
        :param angle: The rotation angle of the rectangle in degrees.
        :param antialias: Enables antialiasing if True.
        """
        vertices = create_rotated_rect(
            position, width, height, [1, 1], angle, [False, False]
        )
        v1, v2, v3, v4 = vertices
        self.render_primitive(
            layer, color, [v2, v3, v1, v4], antialias, moderngl.TRIANGLE_STRIP
        )

    def render_thick_line(
        self,
        layer: Layer,
        color: tuple,
        p1: tuple[float, float],
        p2: tuple[float, float],
        thickness: float,
        capped: bool = False,
        antialias: bool = False,
    ):
        """
        Render a thick line on the specified layer.

        :param layer: The rendering layer.
        :param color: The color of the line in (R, G, B) or (R, G, B, A) format.
        :param p1: The starting point of the line as (x, y) tuple.
        :param p2: The ending point of the line as (x, y) tuple.
        :param thickness: The thickness of the line.
        :param capped: If True, adds caps at the ends of the line.
        :param antialias: Enables antialiasing if True.
        """
        # Calculate direction vector and normalize it
        direction = (p2[0] - p1[0], p2[1] - p1[1])
        direction_norm = np.linalg.norm(direction)
        direction = direction / direction_norm

        # Calculate the perpendicular vector
        h_thickness = thickness / 2
        perpendicular = np.array([-direction[1], direction[0]]) * h_thickness

        # Calculate the four corners of the rectangle
        vertices = np.array(
            [
                p1 + perpendicular,
                p1 - perpendicular,
                p2 + perpendicular,
                p2 - perpendicular,
            ]
        )

        # Draw line segment as a rectangle
        self.render_primitive(
            layer, color, vertices, antialias, moderngl.TRIANGLE_STRIP
        )

        # Draw caps at both ends of the line segment
        if capped:
            angle = np.rad2deg(np.arctan2(direction[1], direction[0]))
            self.render_circle_arc(
                layer, color, p1, h_thickness, angle + 90, angle + 270, antialias
            )
            self.render_circle_arc(
                layer, color, p2, h_thickness, angle - 90, angle + 90
            )

    def render_text(
        self,
        font_atlas: FontAtlas,
        layer: Layer,
        text: str,
        letter_frame: int,
        color: tuple = (1.0, 1.0, 1.0, 1.0),
        scale: float = 1.0,
        alignment: str = None,
    ):
        """
        Render the text on the specified layer with an optional color.

        Parameters:
        - font_atlas: The font atlas.
        - layer: The rendering layer to draw on.
        - text: The text to render.
        - letter_frame: The number of letters to render (useful for animations).
        - color: The color of the text as an RGBA tuple. Default is white (1.0, 1.0, 1.0, 1.0).
        - scale: Multiplier for glyph size (1.0 = original size).
        - alignment: The alignment of the text, accepts None, 'left', 'center' and 'right'.
        """
        if len(color) == 3:
            color = (color[0], color[1], color[2], 1.0)

        if alignment == None:
            vertices = font_atlas.get_char_batch(
                layer.width, layer.height, text, letter_frame, scale
            )
        else:
            vertices = font_atlas.get_char_batch_aligned(
                layer.width, layer.height, text, letter_frame, scale, alignment
            )

        font_atlas.font_texture.use(location=0)  # Bind the font texture at location 0

        vbo = self._ctx.buffer(vertices.tobytes())
        vao = self._ctx.vertex_array(
            self._shader_text.program,
            [
                (vbo, "2f 2f", "vertexPos", "vertexTexCoord"),
            ],
        )

        self._shader_text.program["textColor"].value = (
            color  # Pass the color to the shader
        )

        layer.framebuffer.use()  # Bind the framebuffer

        vao.render(mode=self._ctx.TRIANGLES)

        # Cleanup after rendering
        vbo.release()
        vao.release()

    def release_opengl_resources(self):
        """
        Manually release OpenGL resources managed by the RenderEngine.

        Note:
        - Once this method is called, the engine is no longer usable.
        - This method is automatically called by the garbage collector,
          so there is no need to do it manually.
        """
        self._shader_draw.release()
        self._screen.framebuffer.release()
        self._ctx.release()

        self._shader_draw = None
        self._screen = None
        self._ctx = None

    def __del__(self):
        # Check if ctx is None to avoid double-freeing
        if self._ctx != None:
            self.release_opengl_resources()
