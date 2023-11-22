from time import time
import numpy as np
import pygame
from pygame_render.engine import RenderEngine


# Initialize pygame
pygame.init()

# Create a render engine
engine = RenderEngine((900, 600))

# Load texture
tex = engine.load_texture('sprite.png')

# Make shader
ubo_shader = engine.load_shader_from_path('vertex.glsl', 'fragment_ubo.glsl')

# Array of values
values = np.array([0.1, 0.5, 0.1, 0.0, 1, 1, 1, 1], dtype=np.float32)

# Uniform buffer
ubo = engine.make_uniform_block(ubo_shader, 'valuesUBO', values.nbytes)

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

    # Send uniform block data
    ubo.write(values.tobytes())

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
