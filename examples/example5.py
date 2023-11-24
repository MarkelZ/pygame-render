from time import time
import pygame
from pygame_render import RenderEngine, Layer, NEAREST


# Initialize pygame
pygame.init()

# Create a render engine
engine = RenderEngine(900, 600)

# Load texture
tex = engine.load_texture('sprite.png')

# Main layer
layer: Layer = engine.make_layer(size=(90, 60), components=4)
scale = engine.screen.size[0] // layer.size[0]

# This is for pixelated scaling, otherwise it looks blurry
layer.texture.filter = (NEAREST, NEAREST)

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
    layer.clear(0, 0, 0)

    # Update the time and angle
    total_time += clock.get_time()
    angle = total_time * 0.1

    # Render texture to the layer
    engine.render(tex, layer, position=(10, 10), angle=angle)

    # Upscale the texture to fit the screen
    engine.render(layer.texture, engine.screen, scale=scale)

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
