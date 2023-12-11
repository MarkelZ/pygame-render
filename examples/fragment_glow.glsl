#version 330 core

in vec2 fragmentTexCoord;// top-left is [0, 1] and bottom-right is [1, 0]
uniform sampler2D imageTexture;// texture in location 0

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
