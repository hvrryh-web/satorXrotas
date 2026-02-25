/**
 * ROTAS Layer — Layer 5: Rotation trails, LR balance wheel, motion dust.
 * WebGL (Canvas) rendering for particle system performance.
 *
 * Rendering strategy:
 *   1. Attempt WebGL2 — uses the dust particle vertex shader pipeline (mirrors
 *      shaders/dust.vert) for GPU-accelerated gl.POINTS particles.
 *   2. Fall back to Canvas2D — stroked polylines + head dot for environments
 *      (JSDOM in tests, older browsers) that cannot provide a WebGL2 context.
 */
import React, { useEffect, useRef } from 'react';

export interface RotasTrail {
  playerId: string;
  team: 'attack' | 'defense';
  positions: Array<{ x: number; y: number; tick: number }>;
  directionLR: -1 | 0 | 1; // -1 left flank, 0 mid, 1 right flank
}

interface RotasLayerProps {
  trails: RotasTrail[];
  width: number;
  height: number;
  currentTick: number;
  trailLength: number; // Number of positions to render
}

const TEAM_TRAIL_COLORS = {
  attack: 'rgba(74, 144, 217, 0.6)',
  defense: 'rgba(232, 93, 93, 0.6)',
};

export const RotasLayer: React.FC<RotasLayerProps> = ({
  trails,
  width,
  height,
  currentTick,
  trailLength = 10,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Prefer WebGL2 for GPU-accelerated dust particles; degrade gracefully
    const gl = canvas.getContext('webgl2');
    if (gl) {
      renderWebGLTrails(gl, trails, currentTick, trailLength, width, height);
    } else {
      renderCanvas2D(canvas, trails, currentTick, trailLength, width, height);
    }
  }, [trails, currentTick, trailLength, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
      data-testid="rotas-layer"
    />
  );
};

// =============================================================================
// Canvas2D fallback — stroked polylines + head dot per trail
// =============================================================================
function renderCanvas2D(
  canvas: HTMLCanvasElement,
  trails: RotasTrail[],
  currentTick: number,
  trailLength: number,
  width: number,
  height: number,
): void {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.clearRect(0, 0, width, height);

  for (const trail of trails) {
    const recent = trail.positions
      .filter((p) => p.tick <= currentTick && p.tick >= currentTick - trailLength)
      .sort((a, b) => a.tick - b.tick);

    if (recent.length < 2) continue;

    ctx.beginPath();
    ctx.moveTo(recent[0].x, recent[0].y);
    for (let i = 1; i < recent.length; i++) {
      ctx.lineTo(recent[i].x, recent[i].y);
    }
    ctx.strokeStyle = TEAM_TRAIL_COLORS[trail.team];
    ctx.lineWidth = 2;
    ctx.stroke();

    // Dust particle at trail head
    const head = recent[recent.length - 1];
    ctx.beginPath();
    ctx.arc(head.x, head.y, 3, 0, Math.PI * 2);
    ctx.fillStyle = TEAM_TRAIL_COLORS[trail.team].replace('0.6', '1.0');
    ctx.fill();
  }
}

// =============================================================================
// WebGL2 path — dust particle system using inline GLSL that mirrors dust.vert.
//
// Each trail position becomes a gl.POINTS particle. Attributes fed per vertex:
//   a_position  — NDC xy converted from screen coords
//   a_speed     — normalised speed (affects gl_PointSize)
//   a_age       — 0.0 = trail head (newest), 1.0 = tail (oldest)
//   a_team      — 0.0 = attack, 1.0 = defense (drives color mix)
//
// The fragment shader renders a soft circular disc and discards outside r > 1
// so particles look like dust puffs rather than squares.
// =============================================================================
function renderWebGLTrails(
  gl: WebGL2RenderingContext,
  trails: RotasTrail[],
  currentTick: number,
  trailLength: number,
  width: number,
  height: number,
): void {
  // ---------------------------------------------------------------------------
  // Inline GLSL — mirrors shaders/dust.vert exactly (logic & uniforms match)
  // ---------------------------------------------------------------------------
  const vsSource = `#version 300 es
    precision highp float;
    in vec2 a_position;
    in float a_speed;
    in float a_age;
    in float a_team;
    uniform mat3 u_transform;
    uniform float u_time;
    out float v_alpha;
    out vec3 v_color;
    void main() {
      // Particles shrink as they age; speed boosts size slightly
      float size = mix(4.0, 0.5, a_age) * (0.5 + a_speed * 0.5);
      v_alpha = 1.0 - a_age;
      // Attack: #4A90D9 ≈ vec3(0.29, 0.565, 0.847)
      // Defense: #E85D5D ≈ vec3(0.91, 0.365, 0.365)
      v_color = mix(
        vec3(0.29, 0.565, 0.847),
        vec3(0.91, 0.365, 0.365),
        a_team
      );
      vec3 world_pos = u_transform * vec3(a_position, 1.0);
      gl_Position = vec4(world_pos.xy, 0.0, 1.0);
      gl_PointSize = size;
    }
  `;

  // Fragment shader — soft circular disc via gl_PointCoord distance
  const fsSource = `#version 300 es
    precision highp float;
    in float v_alpha;
    in vec3 v_color;
    out vec4 fragColor;
    void main() {
      vec2 coord = gl_PointCoord - vec2(0.5);
      float r = length(coord) * 2.0;
      if (r > 1.0) discard;
      // Radial fade: fully opaque at centre, transparent at edge
      fragColor = vec4(v_color, v_alpha * (1.0 - r));
    }
  `;

  // ---------------------------------------------------------------------------
  // Shader compilation helper
  // ---------------------------------------------------------------------------
  function compileShader(type: number, src: string): WebGLShader | null {
    const shader = gl.createShader(type);
    if (!shader) return null;
    gl.shaderSource(shader, src);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error('RotasLayer shader compile error:', gl.getShaderInfoLog(shader));
      gl.deleteShader(shader);
      return null;
    }
    return shader;
  }

  const vs = compileShader(gl.VERTEX_SHADER, vsSource);
  const fs = compileShader(gl.FRAGMENT_SHADER, fsSource);
  if (!vs || !fs) return;

  const program = gl.createProgram();
  if (!program) return;
  gl.attachShader(program, vs);
  gl.attachShader(program, fs);
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error('RotasLayer program link error:', gl.getProgramInfoLog(program));
    gl.deleteProgram(program);
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    return;
  }

  // ---------------------------------------------------------------------------
  // Build particle data from trail positions
  // Each trail position → one particle; age encodes its position in the trail
  // (0 = head / newest, 1 = tail / oldest) so the shader fades it correctly.
  // ---------------------------------------------------------------------------
  const particles: Array<{
    x: number; y: number; speed: number; age: number; team: number;
  }> = [];

  for (const trail of trails) {
    const recent = trail.positions
      .filter((p) => p.tick <= currentTick && p.tick >= currentTick - trailLength)
      .sort((a, b) => a.tick - b.tick);

    const teamVal = trail.team === 'attack' ? 0.0 : 1.0;

    recent.forEach((pos, i) => {
      // age: oldest position in the window (i=0) → 1.0, newest (i=last) → 0.0
      const age = recent.length > 1 ? 1.0 - i / (recent.length - 1) : 0.0;

      // Instantaneous speed estimated from consecutive position delta, clamped [0,1]
      let speed = 0.5;
      if (i > 0) {
        const dx = pos.x - recent[i - 1].x;
        const dy = pos.y - recent[i - 1].y;
        speed = Math.min(1.0, Math.sqrt(dx * dx + dy * dy) / 10.0);
      }

      particles.push({ x: pos.x, y: pos.y, speed, age, team: teamVal });
    });
  }

  // Clear regardless of particle count so stale frames are not shown
  gl.viewport(0, 0, width, height);
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  gl.clearColor(0, 0, 0, 0);
  gl.clear(gl.COLOR_BUFFER_BIT);

  if (particles.length === 0) {
    gl.deleteProgram(program);
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    return;
  }

  // ---------------------------------------------------------------------------
  // Interleaved vertex buffer layout (stride = 5 × 4 bytes = 20 bytes):
  //   offset  0: a_position.x  (float)
  //   offset  4: a_position.y  (float)
  //   offset  8: a_speed       (float)
  //   offset 12: a_age         (float)
  //   offset 16: a_team        (float)
  //
  // Screen coordinates are converted to NDC here on the CPU so we can use an
  // identity mat3 for u_transform (positions are already in clip space).
  // ---------------------------------------------------------------------------
  const STRIDE = 5;
  const data = new Float32Array(particles.length * STRIDE);
  particles.forEach((p, i) => {
    data[i * STRIDE]     = (p.x / width) * 2.0 - 1.0;          // NDC x
    data[i * STRIDE + 1] = 1.0 - (p.y / height) * 2.0;         // NDC y (flip Y)
    data[i * STRIDE + 2] = p.speed;
    data[i * STRIDE + 3] = p.age;
    data[i * STRIDE + 4] = p.team;
  });

  // Identity mat3 — positions already in NDC, no further transform needed
  const transform = new Float32Array([1, 0, 0, 0, 1, 0, 0, 0, 1]);

  gl.useProgram(program);

  const vao = gl.createVertexArray();
  gl.bindVertexArray(vao);
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);

  const strideBytes = STRIDE * 4; // 5 floats × 4 bytes

  const posLoc   = gl.getAttribLocation(program, 'a_position');
  const speedLoc = gl.getAttribLocation(program, 'a_speed');
  const ageLoc   = gl.getAttribLocation(program, 'a_age');
  const teamLoc  = gl.getAttribLocation(program, 'a_team');

  gl.enableVertexAttribArray(posLoc);
  gl.vertexAttribPointer(posLoc,   2, gl.FLOAT, false, strideBytes, 0);   // xy
  gl.enableVertexAttribArray(speedLoc);
  gl.vertexAttribPointer(speedLoc, 1, gl.FLOAT, false, strideBytes, 8);   // speed
  gl.enableVertexAttribArray(ageLoc);
  gl.vertexAttribPointer(ageLoc,   1, gl.FLOAT, false, strideBytes, 12);  // age
  gl.enableVertexAttribArray(teamLoc);
  gl.vertexAttribPointer(teamLoc,  1, gl.FLOAT, false, strideBytes, 16);  // team

  gl.uniformMatrix3fv(gl.getUniformLocation(program, 'u_transform'), false, transform);
  gl.uniform1f(gl.getUniformLocation(program, 'u_time'), performance.now() / 1000.0);

  gl.drawArrays(gl.POINTS, 0, particles.length);

  // ---------------------------------------------------------------------------
  // Cleanup — all GPU objects released; this component re-renders on every tick
  // ---------------------------------------------------------------------------
  gl.deleteBuffer(buf);
  gl.deleteVertexArray(vao);
  gl.deleteProgram(program);
  gl.deleteShader(vs);
  gl.deleteShader(fs);
}

export default RotasLayer;
