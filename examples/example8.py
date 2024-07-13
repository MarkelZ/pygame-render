import random
from time import time
import moderngl
import pygame
from pygame_render import RenderEngine


# Initialize pygame
pygame.init()

# Create a render engine
engine = RenderEngine(900, 600)

# Clock
clock = pygame.time.Clock()

# Main game loop
running = True
while running:
    # Tick the clock at 60 frames per second
    clock.tick(60)
    t0 = time()

    # Clear the screen
    engine.clear(0, 0, 0)

    # Render primitives to screen
    engine.render_circle(engine.screen, (255, 0, 0), (100, 150), 50)

    engine.render_triangles(engine.screen, (0, 255, 0),
                            vertices=[(200, 200), (300, 200), (250, 100)])

    engine.render_rectangle(engine.screen, (0, 0, 255), (400, 100), 200, 100)

    engine.render_circle_arc(
        engine.screen, (255, 0, 255), (100, 300), 50, 120, 190)

    engine.render_thick_line(engine.screen, (0, 255, 255),
                             (200, 250), (300, 400), 10, capped=True)

    engine.render_lines(engine.screen, (255, 255, 0),
                        vertices=[(350, 300), (400, 400), (500, 250), (550, 350), (575, 275)], strip=True)

    # Update the display
    pygame.display.flip()

    # Display mspt
    t = time()
    mspt = (t-t0)*1000
    pygame.display.set_caption(f'{mspt:.3f} ms per tick')

    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
