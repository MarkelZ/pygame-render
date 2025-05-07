#version 330 core

uniform sampler2D fontTexture;
uniform vec4 textColor;  // The color for the text

in vec2 fragTexCoord;
out vec4 FragColor;

void main() {
    vec4 texColor = texture(fontTexture, fragTexCoord);
    FragColor = texColor * textColor;  // Apply the color to the texture
}