from time import time
import pygame
from pygame_render import RenderEngine


# Initialize pygame
pygame.init()

# Create a render engine
engine = RenderEngine(900, 600)

# Load texture
tex_clouds = engine.load_texture('clouds.png')

# Load mask shader
shader_mask = engine.load_shader_from_path('vertex.glsl', 'fragment_mask.glsl')

# Font
font = pygame.font.SysFont(pygame.font.get_default_font(), 64)

# Clock
clock = pygame.time.Clock()

# Main game loop
running = True
start_time = time()
while running:
    # Tick the clock at 60 frames per second
    clock.tick(60)

    # Clear the screen
    engine.clear(255, 0, 255)

    # Render texture with uptime
    t = time() - start_time
    font_sfc = font.render(f'{t:.2f}', True,
                           (255, 255, 255), (0, 0, 0))
    font_texture = engine.surface_to_texture(font_sfc)

    # Send font_texture to the shader
    shader_mask['fontTexture'] = font_texture

    # Send fontColor uniform to the shader
    shader_mask['fontColor'] = [0.0, 0.0, 0.0, 1]

    # Render both textures to screen using the mask shader
    engine.render(tex_clouds, engine.screen, shader=shader_mask)

    # Update the display
    pygame.display.flip()

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
