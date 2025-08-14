#version 330 core

in vec2 fragmentTexCoord;
in vec4 instanceTint;
in float instanceGlow;

uniform sampler2D imageTexture;
uniform float time;

out vec4 color;

const float SCALE_GLOW = .2f;
const float SCALE_TIME = .005f;

void main()
{
    color = texture(imageTexture, fragmentTexCoord) * instanceTint;
    float timeGlow = (sin(time * SCALE_TIME) + 1.0) * instanceGlow;
    color += timeGlow * instanceGlow * vec4(1, 1, 0, 0);
}
