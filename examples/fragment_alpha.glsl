#version 330 core

in vec2 fragmentTexCoord;
uniform sampler2D imageTexture;
uniform float alpha;

out vec4 color;

void main()
{
    color = texture(imageTexture, fragmentTexCoord);
    color.a *= alpha;
}
