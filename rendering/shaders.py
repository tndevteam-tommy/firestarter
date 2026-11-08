"""
Firestarter - ModernGL GLSL Shaders
Implements Section 8 & Section 1.4:
3D Scene shading with directional sun lighting, fire point light flicker,
emissive glowing coals, billboarding particle system, and 2D UI screen rendering.
"""

SCENE_VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 in_position;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in vec2 in_uv;
layout (location = 3) in vec4 in_color;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;

out vec3 v_world_pos;
out vec3 v_normal;
out vec2 v_uv;
out vec4 v_color;

void main() {
    vec4 world_pos = m_model * vec4(in_position, 1.0);
    v_world_pos = world_pos.xyz;
    v_normal = normalize(mat3(transpose(inverse(m_model))) * in_normal);
    v_uv = in_uv;
    v_color = in_color;
    gl_Position = m_proj * m_view * world_pos;
}
"""

SCENE_FRAGMENT_SHADER = """
#version 330 core
in vec3 v_world_pos;
in vec3 v_normal;
in vec2 v_uv;
in vec4 v_color;

uniform vec3 u_light_dir;
uniform vec3 u_light_color;
uniform vec3 u_ambient_color;
uniform vec3 u_camera_pos;

uniform vec3 u_fire_pos;
uniform vec3 u_fire_color;
uniform float u_fire_intensity;
uniform float u_fire_radius;

uniform vec4 u_base_color;
uniform float u_glow_intensity;
uniform float u_roughness;

out vec4 fragColor;

void main() {
    vec3 N = normalize(v_normal);
    vec3 L = normalize(u_light_dir);
    vec3 V = normalize(u_camera_pos - v_world_pos);

    // Directional sun illumination
    float diff = max(dot(N, L), 0.0);
    vec3 diffuse = diff * u_light_color;

    // Specular highlight
    vec3 H = normalize(L + V);
    float spec = pow(max(dot(N, H), 0.0), max(1.0, 32.0 * (1.0 - u_roughness)));
    vec3 specular = spec * u_light_color * 0.15;

    // Fire point light with quadratic falloff
    vec3 fire_dir = u_fire_pos - v_world_pos;
    float dist = length(fire_dir);
    vec3 fire_contrib = vec3(0.0);
    if (dist < u_fire_radius && dist > 0.001) {
        vec3 fire_L = normalize(fire_dir);
        float fire_diff = max(dot(N, fire_L), 0.0);
        float atten = clamp(1.0 - dist / u_fire_radius, 0.0, 1.0);
        atten = atten * atten;
        fire_contrib = fire_diff * u_fire_color * u_fire_intensity * atten;
    }

    vec4 color = u_base_color * v_color;
    vec3 lighting = u_ambient_color + diffuse + fire_contrib;
    vec3 final_rgb = color.rgb * lighting + specular;

    // Emissive self-glow (hot coals, burning flame)
    final_rgb += color.rgb * u_glow_intensity;

    fragColor = vec4(final_rgb, color.a);
}
"""

PARTICLE_VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 in_position;
layout (location = 1) in vec2 in_uv;
layout (location = 2) in vec4 in_color;

uniform mat4 m_proj;
uniform mat4 m_view;

out vec2 v_uv;
out vec4 v_color;

void main() {
    v_uv = in_uv;
    v_color = in_color;
    gl_Position = m_proj * m_view * vec4(in_position, 1.0);
}
"""

PARTICLE_FRAGMENT_SHADER = """
#version 330 core
in vec2 v_uv;
in vec4 v_color;

out vec4 fragColor;

void main() {
    // Soft circular radial falloff
    vec2 center = v_uv - vec2(0.5);
    float dist = length(center) * 2.0;
    if (dist > 1.0) {
        discard;
    }
    float alpha = smoothstep(1.0, 0.0, dist) * v_color.a;
    fragColor = vec4(v_color.rgb, alpha);
}
"""

UI_VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec2 in_position;
layout (location = 1) in vec2 in_uv;
layout (location = 2) in vec4 in_color;

uniform mat4 m_ortho;

out vec2 v_uv;
out vec4 v_color;

void main() {
    v_uv = in_uv;
    v_color = in_color;
    gl_Position = m_ortho * vec4(in_position, 0.0, 1.0);
}
"""

UI_FRAGMENT_SHADER = """
#version 330 core
in vec2 v_uv;
in vec4 v_color;

uniform sampler2D u_texture;
uniform int u_use_texture;

out vec4 fragColor;

void main() {
    if (u_use_texture != 0) {
        vec4 tex_color = texture(u_texture, v_uv);
        fragColor = tex_color * v_color;
    } else {
        fragColor = v_color;
    }
}
"""
