#version 300 es
// ROTAS Layer — motion dust particle vertex shader

precision highp float;

in vec2 a_position;     // Particle world position
in float a_speed;       // Movement speed (affects dust size)
in float a_age;         // Particle age 0.0=new, 1.0=expired
in float a_team;        // 0.0=attack, 1.0=defense

uniform mat3 u_transform;
uniform float u_time;

out float v_alpha;
out vec3 v_color;

void main() {
    // Shrink particles as they age
    float size = mix(4.0, 0.5, a_age) * (0.5 + a_speed * 0.5);
    v_alpha = 1.0 - a_age;

    // Team colors
    v_color = mix(
        vec3(0.29, 0.565, 0.847),  // Attack: #4A90D9
        vec3(0.91, 0.365, 0.365),  // Defense: #E85D5D
        a_team
    );

    vec3 world_pos = u_transform * vec3(a_position, 1.0);
    gl_Position = vec4(world_pos.xy, 0.0, 1.0);
    gl_PointSize = size;
}
