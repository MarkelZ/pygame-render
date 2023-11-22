import moderngl
from moderngl import Texture, Framebuffer, Context, Program
import numpy as np
import pygame
from time import time
from math import radians, sin, cos
import numbers


def surface_to_texture(ctx: Context, sfc: pygame.Surface) -> moderngl.Texture:
    """
    Convert a pygame.Surface to a moderngl.Texture.

    Args:
        sfc (pygame.Surface): Surface to convert.

    Returns:
        moderngl.Texture: Converted texture.
    """

    img_flip = pygame.transform.flip(sfc, False, True)
    img_data = pygame.image.tostring(img_flip, "RGBA")

    tex = ctx.texture(sfc.get_size(), components=4, data=img_data)
    tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
    return tex


def load_texture(ctx: Context, path: str) -> moderngl.Texture:
    """
    Load a texture from a file.

    Args:
        path (str): Path to the texture file.

    Returns:
        moderngl.Texture: Loaded texture.
    """

    img = pygame.image.load(path).convert_alpha()
    return surface_to_texture(ctx, img)


def create_rotated_rect(position, width, height, scale, angle):
    # Scale rect
    w = scale[0] * width
    h = scale[1] * height

    # Rotate rect
    ar = radians(angle)
    cos_a, sin_a = cos(ar), sin(ar)

    half_w, half_h = w / 2, h / 2

    half_w_cos, half_w_sin = half_w * cos_a, half_w * sin_a
    half_h_cos, half_h_sin = half_h * cos_a, half_h * sin_a

    p1 = (half_w_cos - half_h_sin, half_w_sin + half_h_cos)
    p2 = (-half_w_cos - half_h_sin, -half_w_sin + half_h_cos)
    p3 = (-half_w_cos + half_h_sin, -half_w_sin - half_h_cos)
    p4 = (half_w_cos + half_h_sin, half_w_sin - half_h_cos)
    ps = [p1, p2, p3, p4]

    # Translate vertices
    x, y = position
    ps = [(px + x, py + y) for px, py in ps]

    return ps


def render(ctx: Context, tex: Texture, fbo: Framebuffer,
           position=(0, 0), scale=(1.0, 1.0), angle=0.0, section=None, shader: Program = None):
    # Create section rect if none
    if section == None:
        section = pygame.Rect(0, 0, tex.width, tex.height)

    # Default to draw shader program if none
    if shader == None:
        shader = prog_draw  # prog_draw will be built upon initialization in the actual engine

    # If the scale is not a tuple but a scalar, convert it into a tuple
    if isinstance(scale, numbers.Number):
        scale = (scale, scale)

    # ================ Create a mesh with screen vertex data ================
    def to_screen_coords(p):
        return (2. * p[0] / fbo.width - 1., 1. - 2. * p[1] / fbo.height)

    ps = create_rotated_rect(position, section.width,
                             section.height, scale, angle)

    # Convert to screen coordinates
    ps = [to_screen_coords(p) for p in ps]
    p1, p2, p3, p4 = ps

    # Mesh for destination rect on screen
    vertices = np.array([p3, p4, p2,
                         p2, p4, p1], dtype=np.float32)

    # ================ Create a mesh with texture vertex data ================
    # Convert to texture coordinates
    x = section.x / tex.width
    y = section.y / tex.height
    w = section.width / tex.width
    h = section.height / tex.height

    # Mesh for source within the texture
    tex_coords = np.array([(x, y + h), (x + w, y + h), (x, y),
                           (x, y), (x + w, y + h), (x + w, y)], dtype=np.float32)

    # ================ Create vertex buffer objects and render ================
    # Create VBO and VAO
    buffer_data = np.hstack([vertices, tex_coords])

    vbo = ctx.buffer(buffer_data)
    vao = ctx.vertex_array(shader, [
        (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
    ])

    # Use buffers and render
    tex.use()
    fbo.use()
    vao.render()

    # Free vertex data
    vbo.release()
    vao.release()


if __name__ == '__main__':
    # Initialize pygame
    pygame.init()

    # Screen resolution
    screen_res = (1280, 720)

    # Configure pygame to use opengl
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(
        pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

    pygame.display.set_mode(screen_res, pygame.HWSURFACE |
                            pygame.OPENGL | pygame.DOUBLEBUF)

    # Create opengl context
    ctx = moderngl.create_context()

    # Load shader source code
    with open('vertex.glsl') as f:
        vertex_src = ''.join(f.readlines())
    with open('fragment_draw.glsl') as f:
        fragment_src = ''.join(f.readlines())

    # Create shader program
    prog_draw = ctx.program(vertex_shader=vertex_src,
                            fragment_shader=fragment_src)

    # Create glow shader
    with open('fragment_glow.glsl') as f:
        fragment_src = ''.join(f.readlines())
    prog_glow = ctx.program(vertex_shader=vertex_src,
                            fragment_shader=fragment_src)

    # Load a texture
    tex_path = 'sprite.png'
    img = pygame.image.load(tex_path).convert_alpha()
    tex = surface_to_texture(ctx, img)

    # Game loop
    clock = pygame.time.Clock()
    running = True
    total_time = 0
    while running:
        # Tick the clock at 60 frames per second
        clock.tick(60)
        t0 = time()

        ctx.screen.clear(0, 0, 0, 1)

        total_time += clock.get_time()
        angle = total_time * 0.05
        prog_glow['time'] = total_time * 0.005

        # Render texture to screen
        render(ctx, tex, ctx.screen, position=(300, 300),
               scale=(16., 16.), angle=angle, shader=prog_glow)

        # Update the display
        pygame.display.flip()

        t = time()
        mspt = (t-t0)*1000
        pygame.display.set_caption(f'{mspt:.3f} ms per tick')
        t0 = t

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
