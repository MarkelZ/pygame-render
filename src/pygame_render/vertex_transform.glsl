#version 330 core

layout(location=0) in vec2 quadPos;  // Unit quad coordinates in [0,1]

uniform vec2 uPosition;    // Destination top-left in pixels
uniform vec2 uSectionSize; // Source section size in pixels
uniform vec2 uScale;       // Scale factor for destination size
uniform float uAngleRad;   // Rotation angle in radians
uniform int uFlipX;
uniform int uFlipY;

uniform vec2 uSectionMin;  // UV min
uniform vec2 uSectionMax;  // UV max
uniform vec2 uLayerSize;   // Destination framebuffer size in pixels

out vec3 fragmentColor;
out vec2 fragmentTexCoord;

void main() {
    vec2 sizePx = uSectionSize * uScale;
    vec2 centerOffset = sizePx * 0.5;

    // Local pixel-space point around center
    vec2 local = (quadPos - vec2(0.5, 0.5)) * sizePx;

    float c = cos(uAngleRad);
    float s = sin(uAngleRad);
    vec2 rotated = vec2(
        local.x * c - local.y * s,
        local.x * s + local.y * c
    );

    vec2 worldPx = uPosition + centerOffset + rotated;
    vec2 ndc = vec2(
        2.0 * worldPx.x / uLayerSize.x - 1.0,
        1.0 - 2.0 * worldPx.y / uLayerSize.y
    );
    gl_Position = vec4(ndc, 0.0, 1.0);

    vec2 uvLocal = vec2(quadPos.x, 1.0 - quadPos.y);
    if (uFlipX == 1) {
        uvLocal.x = 1.0 - uvLocal.x;
    }
    if (uFlipY == 1) {
        uvLocal.y = 1.0 - uvLocal.y;
    }
    fragmentTexCoord = mix(uSectionMin, uSectionMax, uvLocal);
    fragmentColor = vec3(1.0, 1.0, 1.0);
}
