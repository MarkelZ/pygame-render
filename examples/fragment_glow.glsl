#version 330 core

in vec2 fragmentTexCoord;
uniform sampler2D imageTexture;

uniform float time;

out vec4 color;

const float SCALE_GLOW=.2f;
const float SCALE_TIME=.005f;

void main()
{
    color=texture(imageTexture,fragmentTexCoord);
    float intensity=(sin(time*SCALE_TIME)+1)*SCALE_GLOW;
    color+=intensity*vec4(1,1,0,0);
}
