import sys
sys.path.insert(0, '/Users/olakenjiforslund/OKF/Leisure/Programming/Python/projects/pygame-render/src/') 

import pygame
from pygame_render import RenderEngine

pygame.init()
display_size = (800, 600)

engine = RenderEngine(display_size[0], display_size[1], font_path = None, font_size = 20)

screen = engine.make_layer(display_size)
text_layer = engine.make_layer((300, 300))

running = True
time = 0
while running:
    screen.clear(0,0,0,255)
    text_layer.clear(0,0,0,255)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    time += 0.01

    layer = engine.render_text_alignment(text_layer, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ, abcdefghijklmnopqrstuvwxyz', letter_frame = int(time), colour = (0, 1, 0,1 ), scale = 1)
    engine.render(layer.texture, screen)
    engine.render(screen.texture, engine.screen) 
    pygame.display.flip()

pygame.quit()