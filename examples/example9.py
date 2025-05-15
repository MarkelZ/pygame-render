import pygame
from pygame_render import RenderEngine
import math

pygame.init()
display_size = (800, 600)

engine = RenderEngine(display_size[0], display_size[1])
screen = engine.make_layer(display_size)

hdr_texture = engine.make_layer(display_size, dtype = 'f4')
hdr_layer = engine.make_layer(display_size, dtype = 'f4')
engine.HDR_exposure = 0.1

pygame.font.init()
font = pygame.font.SysFont("Arial", 30)

# Clock
clock = pygame.time.Clock()

running = True
time = 0
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    time += 0.005
    value = 5 * math.sin(time) + 5#0 - 10

    screen.clear(0, 0, 0, 255)
    hdr_texture.clear(255 * value, 255, 255, 255)

    engine.render(hdr_texture.texture, hdr_layer)
    engine.render(hdr_layer.texture, screen, hdr_render=True)

    value_text = f"R value: {255 * value:.2f}"  # Format the value to 2 decimal places
    text_surface = font.render(value_text, True, (255, 255, 255))  # White text
    texture = engine.surface_to_texture(text_surface)
    
    engine.render(texture, screen)
    texture.release()

    engine.render(screen.texture, engine.screen)

    pygame.display.flip()

pygame.quit()
