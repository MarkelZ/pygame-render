from time import time
import numpy as np
import pygame
from pygame_render import RenderEngine


# Initialize pygame
pygame.init()

# Create a render engine
engine = RenderEngine(900, 600)

# Load texture
tex = engine.load_texture('sprite.png')

# Load background texture
tex_bg = engine.load_texture('clouds.png')

# Make shader
ubo_shader = engine.load_shader_from_path('vertex.glsl', 'fragment_ubo.glsl')

# Array of values
values = np.array([0.5, 0.5, 0.5, -0.5, 0, 0, 0, 0], dtype=np.float32)

# Uniform buffer
engine.reserve_uniform_block(ubo_shader, 'valuesUBO', values.nbytes)

# Clock
clock = pygame.time.Clock()

# Main game loop
running = True
total_time = 0
while running:
    # Tick the clock at 60 frames per second
    clock.tick(60)
    t0 = time()

    # Clear the screen
    engine.clear(255, 0, 255)

    # Render background texture
    engine.render(tex_bg, engine.screen, position=(0, 0),
                  section=pygame.Rect(0, 0, tex_bg.width, tex_bg.height))

    # Enable colors acording to keys
    keys = pygame.key.get_pressed()
    values[4] = 1 if keys[pygame.K_r] else 0
    values[5] = 1 if keys[pygame.K_g] else 0
    values[6] = 1 if keys[pygame.K_b] else 0
    values[7] = 1 if keys[pygame.K_a] else 0

    # Send uniform block data
    ubo_shader['valuesUBO'] = values.tobytes()

    # Render texture to screen
    engine.render(tex, engine.screen,
                  position=(200, 200), scale=16., shader=ubo_shader)

    # Update the display
    pygame.display.flip()

    # Display mspt
    t = time()
    mspt = (t-t0)*1000
    pygame.display.set_caption(f'{mspt:.3f} ms per tick')
    t0 = t

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
