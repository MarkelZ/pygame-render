#version 330 core

uniform sampler2D fontTexture;
uniform vec4 textColor;  // The color for the text

in vec2 fragmentTexCoord;
out vec4 color;

void main() {
    vec4 texColor = texture(fontTexture, fragmentTexCoord);
    color = texColor * textColor;  // Apply the color to the texture
}