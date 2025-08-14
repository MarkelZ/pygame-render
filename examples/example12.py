from random import randint, uniform
from time import time
import pygame
from pygame_render import RenderEngine
import math

# Initialize pygame
pygame.init()

# Create a render engine
width, height = 1280, 720
engine = RenderEngine(width, height)

# Load texture
tex = engine.load_texture("sprite.png")

# Clock
clock = pygame.time.Clock()

# Positions
num_sprites = 1000
positions = [(randint(0, width), randint(0, height)) for _ in range(num_sprites)]

# Load shader
shader_glow = engine.load_shader_from_path("vertex_batch.glsl", "fragment_glow_batch.glsl")

# Main game loop
running = True
total_time = 0

while running:
    # Tick the clock at 60 frames per second
    clock.tick()
    t0 = time()

    # Clear the screen
    engine.clear(64, 128, 64)

    # Update the time
    total_time += clock.get_time()

    # Send time uniform to glow shader
    shader_glow["time"] = total_time

    # Render texture to screen
    angle = total_time * 0.05

    #clear
    transforms = []
    tints = []
    glow_strengths = []
    for i in range(num_sprites):
        transforms.append({
            "position": positions[i],
            "scale": 16 * math.sin(i*0.1),
            "angle": total_time * math.sin(i*0.001),
        })
        tints.append((math.sin(i*0.1),math.sin(i*0.1),math.sin(i*0.1),math.sin(i*0.1)))
        glow_strengths.append(math.sin(0.4 * i + i * 0.001))
    
    engine.render_batch_unique(
        tex,
        engine.screen,
        transforms=transforms,
        shader=shader_glow,
        instance_uniforms={
                "tint": tints,
                "glow": glow_strengths,
            }     
    )

    # Update the display
    pygame.display.flip()

    # Display mspt
    t = time()
    mspt = (t - t0) * 1000
    pygame.display.set_caption(
        f"Rendering {num_sprites} sprites at {mspt:.3f} ms per tick!"
    )

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
