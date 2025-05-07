#version 330
in vec2 vertexPos;         // Vertex positions (screen space)
in vec2 vertexTexCoord;    // Texture coordinates (UVs)

out vec2 fragTexCoord;     // Pass the texture coordinates to the fragment shader

void main() {
    gl_Position = vec4(vertexPos.x, vertexPos.y, 0.0, 1.0); // Set the position
    fragTexCoord = vertexTexCoord; // Pass the texture coordinate
}
