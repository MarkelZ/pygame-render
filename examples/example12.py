import pygame
from pygame_render import RenderEngine
import numpy as np

# Initialize pygame
pygame.init()

# Create a render engine
width, height = 1280, 720
engine = RenderEngine(width, height)

legacy_shader = engine.load_shader_from_path(None, "fragment_alpha.glsl")
instanced_shader = engine.load_instanced_shader_from_path("fragment_alpha.glsl", {"alpha": "float"})

# Load texture
tex = engine.load_texture("sprite.png")

clock = pygame.time.Clock()

# Generate the same data for both render paths.
num_sprites = 200000
rng = np.random.default_rng(12)
positions = np.column_stack((rng.uniform(-15, width, num_sprites), rng.uniform(-22, height, num_sprites))).astype("f4")
scales = rng.uniform(0.6, 1.8, (num_sprites, 2)).astype("f4")
rotations = rng.uniform(0.0, 360.0, num_sprites).astype("f4")
rotation_speeds = rng.uniform(-90.0, 90.0, num_sprites).astype("f4")
flips = rng.integers(0, 2, (num_sprites, 2)).astype("f4")
alpha_phases = rng.uniform(0.0, np.pi * 2.0, num_sprites).astype("f4")
alphas = np.empty(num_sprites, dtype="f4")

running = True
use_instancing = True
elapsed = 0.0

while running:
    delta_time = clock.tick() / 1000.0
    elapsed += delta_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            use_instancing = not use_instancing

    rotations += rotation_speeds * delta_time
    np.remainder(rotations, 360.0, out=rotations)
    np.add(alpha_phases, elapsed * 2.0, out=alphas)
    np.sin(alphas, out=alphas)
    alphas *= 0.425
    alphas += 0.575

    engine.clear(18, 20, 28)

    if use_instancing:
        engine.render_instanced(
            tex,
            engine.screen,
            positions = positions,
            scales=scales,
            angles=rotations,
            flips=flips,
            shader=instanced_shader,
            instance_data={"alpha": alphas},
        )
    else:
        for index in range(num_sprites):
            legacy_shader["alpha"] = float(alphas[index])
            engine.render(
                tex,
                engine.screen,
                position=positions[index],
                scale=scales[index],
                angle=float(rotations[index]),
                flip=flips[index],
                shader=legacy_shader,
                mode="transform",
            )

    pygame.display.flip()

    mode = "1 instanced draw" if use_instancing else f"{num_sprites} render() calls"
    pygame.display.set_caption(
        f"{num_sprites} sprites | {mode} | {clock.get_fps():.1f} FPS | SPACE toggles"
    )

pygame.quit()
