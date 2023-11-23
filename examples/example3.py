from time import time
import pygame
from pygame_render.engine import RenderEngine


# Initialize pygame
pygame.init()

# Create a render engine
engine = RenderEngine((900, 600))

# Load texture
tex = engine.load_texture('sprite_sheet.png')

# Clock
clock = pygame.time.Clock()

# Main game loop
running = True
total_time = 0
anim_ind = 0
anim_frames = 4
frame_width = 15
frame_height = 22
while running:
    # Tick the clock at 60 frames per second
    clock.tick(60)
    t0 = time()

    # Clear the screen
    engine.clear(255, 0, 255)

    # Update the time and angle
    total_time += clock.get_time()

    # Render texture to screen
    selection = pygame.Rect(frame_width * int(anim_ind),
                            0, frame_width, frame_height)
    engine.render(tex, engine.screen, position=(200, 200), scale=16.,
                  section=selection)

    # Update anim
    anim_ind = anim_ind + 0.1
    while anim_ind >= anim_frames:
        anim_ind -= anim_frames

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
