#version 330 core

layout(location=0) in vec2 quadPos;  // Unit quad coordinates in [0,1]

// The engine rewrites these uniforms into attributes for instanced rendering.
uniform vec2 spritePosition;  // Destination top-left in pixels
uniform vec2 spriteScale;     // Scale factor for destination size
uniform float spriteAngleDeg; // Rotation angle in degrees
uniform vec2 spriteFlip;      // X/Y flip flags: 0.0 or 1.0
uniform vec4 spriteSection;   // Source x, y, width, height in pixels

/*__INSTANCE_INPUTS__*/

uniform vec2 uTextureSize;
uniform vec2 uLayerSize;

out vec3 fragmentColor;
out vec2 fragmentTexCoord;
/*__INSTANCE_OUTPUTS__*/

void main() {
    vec2 sizePx = spriteSection.zw * spriteScale;
    vec2 centerOffset = sizePx * 0.5;

    // Local pixel-space point around center
    vec2 local = (quadPos - vec2(0.5, 0.5)) * sizePx;

    float angleRad = radians(spriteAngleDeg);
    float c = cos(angleRad);
    float s = sin(angleRad);
    vec2 rotated = vec2(
        local.x * c - local.y * s,
        local.x * s + local.y * c
    );

    vec2 worldPx = spritePosition + centerOffset + rotated;
    vec2 ndc = vec2(
        2.0 * worldPx.x / uLayerSize.x - 1.0,
        1.0 - 2.0 * worldPx.y / uLayerSize.y
    );
    gl_Position = vec4(ndc, 0.0, 1.0);

    vec2 uvLocal = vec2(quadPos.x, 1.0 - quadPos.y);
    uvLocal.x = mix(uvLocal.x, 1.0 - uvLocal.x, spriteFlip.x);
    uvLocal.y = mix(uvLocal.y, 1.0 - uvLocal.y, spriteFlip.y);

    fragmentTexCoord = (
        spriteSection.xy + uvLocal * spriteSection.zw
    ) / uTextureSize;
    fragmentColor = vec3(1.0, 1.0, 1.0);

/*__INSTANCE_ASSIGNMENTS__*/
}
