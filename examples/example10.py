import pygame
from pygame_render import RenderEngine

pygame.init()
display_size = (800, 600)

engine = RenderEngine(display_size[0], display_size[1])

screen = engine.make_layer(display_size)
text_layer = engine.make_layer((800, 600))

font = engine.make_font_atlas(font_size=64)

# Clock
clock = pygame.time.Clock()

running = True
time = 0
while running:
    clock.tick(60)
    time += 0.5

    screen.clear(0, 0, 0, 255)
    text_layer.clear(0, 0, 0, 255)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    engine.render_text(
        font,
        text_layer,
        text = "Before frost found the earth, there was only song.",
        letter_frame=int(time),
        color=(255,255,255,255),
        scale=1,
        position=(10, 10),
        width = 400,
    )
    engine.render(text_layer.texture, screen)
    engine.render(screen.texture, engine.screen)
    pygame.display.flip()

pygame.quit()
