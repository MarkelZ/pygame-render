#version 330 core

in vec2 fragmentTexCoord;
uniform sampler2D imageTexture;

uniform valuesUBO{
    float values[8];
};

out vec4 color;

void main()
{
    color=texture(imageTexture,fragmentTexCoord);
    if(values[4]!=0)color.r+=values[0];
    if(values[5]!=0)color.g+=values[1];
    if(values[6]!=0)color.b+=values[2];
    if(values[7]!=0)color.a+=values[3];
}
