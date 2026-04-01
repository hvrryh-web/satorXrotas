#version 300 es
// OPERA Layer — fog of war fragment shader

precision highp float;

uniform sampler2D u_visibility_mask;  // 0.0=fog, 1.0=clear
uniform float u_time;
uniform float u_uncertainty_scale;

in vec2 v_texcoord;
out vec4 fragColor;

// Animated noise for fog texture
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
        mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x),
        mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
        f.y
    );
}

void main() {
    float visibility = texture(u_visibility_mask, v_texcoord).r;
    float fog_density = 1.0 - visibility;

    // Animated fog noise
    float n = noise(v_texcoord * 8.0 + vec2(u_time * 0.1, u_time * 0.07));
    float animated_fog = fog_density * (0.85 + 0.15 * n);

    // Uncertainty ripples (audio-like concentric waves)
    float dist = length(v_texcoord - vec2(0.5, 0.5));
    float ripple = sin(dist * 20.0 - u_time * 3.0) * 0.05 * u_uncertainty_scale;
    animated_fog = clamp(animated_fog + ripple, 0.0, 1.0);

    vec3 fog_color = vec3(0.05, 0.05, 0.12);  // Dark navy fog
    fragColor = vec4(fog_color, animated_fog * 0.85);
}
