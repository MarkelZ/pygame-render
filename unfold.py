import moderngl
from moderngl import Texture, Framebuffer, Context, Program
import numpy as np
import pygame
from importlib import resources


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


def render(ctx: Context, tex: Texture, fbo: Framebuffer,
           position=(0, 0), section=None, scale=1.0, rotation=0.0, shader: Program = None):
    # Create section rect if none
    if section == None:
        section = pygame.Rect(0, 0, tex.width, tex.height)

    # Default to draw shader program if none
    if shader == None:
        shader = prog_draw

    # Rotation not implemented yet
    if rotation != 0.0:
        raise NotImplementedError('Rotation has not been implemented yet!')

    # Mesh for destination rect on screen
    x = 2. * position[0] / fbo.width - 1.
    y = 1. - 2. * position[1] / fbo.height
    w = 2. * section.width * scale / fbo.width
    h = 2. * section.height * scale / fbo.height
    vertices = np.array([(x, y), (x + w, y), (x, y - h),
                         (x, y - h), (x + w, y), (x + w, y - h)], dtype=np.float32)

    # Mesh for source within the texture
    x = section.x / tex.width
    y = section.y / tex.height
    w = section.width / tex.width
    h = section.height / tex.height
    tex_coords = np.array([(x, y + h), (x + w, y + h), (x, y),
                           (x, y), (x + w, y + h), (x + w, y)], dtype=np.float32)

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
    print('what')
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
    # vertex_src = resources.read_text(
    #     'pygame_render', 'vertex.glsl')
    # fragment_src_draw = resources.read_text(
    #     'pygame_render', 'fragment_draw.glsl')
    with open('vertex.glsl') as f:
        vertex_src = ''.join(f.readlines())
    with open('fragment_draw.glsl') as f:
        fragment_src = ''.join(f.readlines())

    # Create shader program
    prog_draw = ctx.program(vertex_shader=vertex_src,
                            fragment_shader=fragment_src)

    # Load a texture
    tex_path = 'sprite.png'
    img = pygame.image.load(tex_path).convert_alpha()
    tex = surface_to_texture(ctx, img)

    # Game loop
    clock = pygame.time.Clock()
    running = True
    while running:
        # Tick the clock at 60 frames per second
        clock.tick(60)

        # Render texture to screen
        render(ctx, tex, ctx.screen, position=(
            100, 100), scale=16., section=pygame.Rect(0, 0, 8, 20), shader=prog_draw)

        # Update the display
        pygame.display.flip()

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
