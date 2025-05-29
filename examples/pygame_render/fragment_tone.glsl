#version 330 core

in vec2 fragmentTexCoord;// top-left is [0, 1] and bottom-right is [1, 0]
uniform sampler2D imageTexture;// texture in location 0

out vec4 FragColor;
uniform float exposure = 0.1;

vec3 toneMapping(vec3 color) {
    return vec3(1) - exp(-color*exposure);
}

void main() {    
    vec3 hdrColor = texture(imageTexture, fragmentTexCoord).rgb;    
    vec3 ldrColor = toneMapping(hdrColor);    
    FragColor = vec4(ldrColor, 1.0);
}