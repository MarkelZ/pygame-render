#version 330 core

in vec2 fragmentTexCoord;// top-left is [0, 1] and bottom-right is [1, 0]
uniform sampler2D imageTexture;// texture in location 0

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
