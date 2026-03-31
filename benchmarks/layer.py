from time import time
import pygame
from pygame_render import RenderEngine
import random


# Shared constants
WIDTH = 900
HEIGHT = 600
RNG_SEED = 123
MAX_FPS = 120

# Test 1 constants
NUM_SURFACES = 100
WARMUP_ITERS = 100
TEST1_ITERS = 200


# Fix RNG seed for reprodicibility
random.seed(RNG_SEED)

# Initialize pygame
pygame.init()

# Create a render engine
engine = RenderEngine(WIDTH, HEIGHT)

# Initialize the clock
clock = pygame.time.Clock()

# List of surfaces to convert to textures
surfaces = [
    pygame.Surface(size=(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
    for _ in range(NUM_SURFACES)
]

# Benchmarks a test
# Note that we still update the screen, to simulate real usage
def benchmark(test, after, iters: int, warmup_iters: int, name: str):
    avg_mspt = 0
    total_iters = iters + warmup_iters
    for i in range(total_iters):
        pygame.display.set_caption(f"{name} iter.: {i+1}/{total_iters}")

        # Tick clock
        clock.tick(120)

        # Clear the screen
        engine.clear(0, 0, 0)

        t0 = time()

        res = test()

        t = time()
        mspt = (t - t0) * 1000

        if i >= warmup_iters:
            avg_mspt += mspt

        after(res)

        # Update the display
        pygame.display.flip()

    avg_mspt /= TEST1_ITERS
    print(f"{name}")
    print(f"Average MSPT: {avg_mspt}")

    return avg_mspt


# Test1: surface_to_texture

def test1():
    # Convert pygame surfaces to OpenGL textures
    return [engine.surface_to_texture(s) for s in surfaces]

def test1_after(textures):
    # Release texture data
    for tex in textures:
        tex.release()

# Run the benchmarks
benchmark(test1, test1_after, TEST1_ITERS, WARMUP_ITERS, "surface_to_texture")
