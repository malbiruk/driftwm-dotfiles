// Parallax variant of boho_dawn — two FBM layers at different camera rates.
// Near layer carries the original cut-paper Memphis palette and drifts at
// 0.45x camera; far layer drifts at 0.12x and shows through the cream
// negative space as a soft depth wash. Pan the WM camera to see parallax.
precision highp float;

varying vec2 v_coords;
uniform vec2 size;
uniform float alpha;
uniform vec2 u_camera;

float hash1(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash1(i);
    float b = hash1(i + vec2(1.0, 0.0));
    float c = hash1(i + vec2(0.0, 1.0));
    float d = hash1(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    mat2 rot = mat2(0.8, 0.6, -0.6, 0.8);
    for (int i = 0; i < 4; i++) {
        v += a * noise(p);
        p = rot * p * 2.0;
        a *= 0.5;
    }
    return v;
}

const vec3 CREAM = vec3(0.980, 0.957, 0.929); // #faf4ed
const vec3 ROSE = vec3(0.843, 0.510, 0.494); // #d7827e
const vec3 LOVE = vec3(0.706, 0.388, 0.478); // #b4637a
const vec3 FOAM = vec3(0.337, 0.580, 0.624); // #56949f
const vec3 IRIS = vec3(0.565, 0.478, 0.663); // #907aa9
const vec3 GOLD = vec3(0.918, 0.616, 0.204); // #ea9d34

vec3 wash(vec3 c, float amount) {
    return mix(c, CREAM, amount);
}

vec3 paletteColor(float t) {
    vec3 col = CREAM;
    col = mix(col, wash(ROSE, 0.55), step(0.390, t));
    col = mix(col, wash(FOAM, 0.55), step(0.525, t));
    col = mix(col, wash(IRIS, 0.65), step(0.620, t));
    col = mix(col, wash(LOVE, 0.45), step(0.695, t));
    col = mix(col, wash(GOLD, 0.70), step(0.770, t));
    return col;
}

void main() {
    // Near layer — original cut-paper palette, drifts at 0.45x camera.
    vec2 near = (v_coords * size + u_camera * 0.45) * 0.0022;
    float fn = fbm(near);
    vec3 col = paletteColor(fn);

    // Far layer — slower drift (0.12x), larger scale, offset domain so it
    // doesn't echo the near layer. Heavily washed toward cream so it reads
    // as ambient depth rather than a competing pattern.
    vec2 far = (v_coords * size + u_camera * 0.12) * 0.0016 + vec2(137.0, 89.0);
    float ff = fbm(far);
    vec3 far_col = mix(CREAM, wash(IRIS, 0.88), smoothstep(0.45, 0.62, ff));

    // Far layer only leaks through the near layer's cream negative space,
    // preserving the hard Memphis edges on the blobs.
    float cream_mask = 1.0 - step(0.390, fn);
    col = mix(col, far_col, cream_mask * 0.55);

    gl_FragColor = vec4(col, 1.0) * alpha;
}
