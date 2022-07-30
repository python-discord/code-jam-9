#version 330

uniform vec2 resolution;
uniform sampler2D texture0;
uniform float time;
uniform bool glitch;

in vec2 uv;
out vec4 fragColor;

void main() {
    // Edit this 
    if (glitch) {
        float multiplier = fract(sin(time * 50) * 0.0000042);
        float r = texture(texture0, uv - vec2(resolution.x * multiplier, 0)).x; 
        float g = texture(texture0, uv).y;
        float b = texture(texture0, uv + vec2(resolution.x * multiplier, 0)).z;
        fragColor = vec4(r, g, b, 0.7);
    }
    else {
        fragColor = texture(texture0, uv);
    }
}  