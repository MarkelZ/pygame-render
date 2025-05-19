from time import time
import pygame
from pygame_render import RenderEngine


# Initialize pygame
pygame.init()

# Create a render engine
width, height = 1280, 720
engine = RenderEngine(width, height)

# Load texture
tex = engine.load_texture("sprite.png")

# Perinstance transforms
hmargin, vmargin = 30, 30
transforms = [
    {
        "position": ((hmargin * i) % width, vmargin * (hmargin * i // width)),
        "scale": 1.5,
        "angle": 10 * i,
        "flip": False,
        "section": None,
    }
    for i in range(1000)
]

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

    # Update the time and angle
    total_time += clock.get_time()

    # Render texture to screen
    engine.render_batch(tex, engine.screen, transforms)

    # Update the display
    pygame.display.flip()

    # Display mspt
    t = time()
    mspt = (t - t0) * 1000
    pygame.display.set_caption(f"{mspt:.3f} ms per tick")
    print(mspt)

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
