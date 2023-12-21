#version 330 core

in vec2 fragmentTexCoord;
uniform sampler2D imageTexture;

out vec4 color;

void main()
{
    color=texture2D(imageTexture,fragmentTexCoord);
}
