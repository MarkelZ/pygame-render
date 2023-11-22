from random import randint
from time import time
import pygame
from pygame_render.engine import RenderEngine


# Initialize pygame
pygame.init()

# Create a render engine
res = (1280, 720)
engine = RenderEngine(res)

# Load texture
tex = engine.load_texture('sprite.png')

# Clock
clock = pygame.time.Clock()

# Positions
num_sprites = 1000
w, h = res
positions = [(randint(0, w), randint(0, h)) for _ in range(num_sprites)]

# Load shader
shader_glow = engine.load_shader_from_path('vertex.glsl', 'fragment_glow.glsl')

# Main game loop
running = True
total_time = 0
while running:
    # Tick the clock at 60 frames per second
    clock.tick(60)
    t0 = time()

    # Clear the screen
    engine.clear(64, 128, 64)

    # Update the time and angle
    total_time += clock.get_time()
    angle = total_time * 0.05

    # Send time uniform to glow shader
    shader_glow['time'] = total_time

    # Render texture to screen
    for p in positions:
        engine.render(tex, engine.screen,
                      position=p, scale=16., angle=angle, shader=shader_glow)

    # Update the display
    pygame.display.flip()

    # Display mspt
    t = time()
    mspt = (t-t0)*1000
    pygame.display.set_caption(
        f'Rendering {num_sprites} sprites at {mspt:.3f} ms per tick!')
    t0 = t

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
