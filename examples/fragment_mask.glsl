#version 330 core

in vec2 fragmentTexCoord;
uniform sampler2D imageTexture;

// Additional texture
uniform sampler2D fontTexture;

uniform vec4 fontColor;

out vec4 color;

void main()
{
    vec4 texture_color=texture(imageTexture,fragmentTexCoord);
    vec4 font_value=texture(fontTexture,fragmentTexCoord);
    color=font_value.r*fontColor+(1-font_value.r)*texture_color;
}
