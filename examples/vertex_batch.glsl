#version 330 core

in vec2 vertexPos;
in vec2 vertexTexCoord;

in vec2 position;
in vec2 scale;
in float angle;

in vec4 tint;
in float glow;

out vec2 fragmentTexCoord;
out vec4 instanceTint;
out float instanceGlow;

uniform vec2 screenSize;

void main() {
    // 1. Scale first
    vec2 local = vertexPos * scale;

    // 2. Rotate
    float s = sin(angle);
    float c = cos(angle);
    vec2 rotated = vec2(
        local.x * c - local.y * s,
        local.x * s + local.y * c
    );

    // 3. Translate
    vec2 worldPos = rotated + position;

    // 4. Convert to clip space
    vec2 ndc = (worldPos / screenSize) * 2.0 - 1.0;
    ndc.y *= -1.0;

    gl_Position = vec4(ndc, 0.0, 1.0);
    fragmentTexCoord = vertexTexCoord;
    instanceTint = tint;
    instanceGlow = glow;
}
