/**
 * OPERA Layer — Layer 2: Fog of war with audio ripples, uncertainty visualization.
 * WebGL (Canvas) rendering for performance.
 */
import React, { useEffect, useRef } from 'react';

interface OperaLayerProps {
  width: number;
  height: number;
  visibilityMask: Float32Array; // 0.0 = fully fogged, 1.0 = clear
  uncertaintyPoints: Array<{ x: number; y: number; uncertainty: number }>;
}

export const OperaLayer: React.FC<OperaLayerProps> = ({
  width,
  height,
  visibilityMask,
  uncertaintyPoints,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext('webgl2');
    if (!gl) {
      console.warn('WebGL2 not available — OPERA layer degraded to 2D canvas');
      renderFallback(canvas, visibilityMask, width, height);
      return;
    }

    renderWebGL(gl, visibilityMask, uncertaintyPoints, width, height);
  }, [visibilityMask, uncertaintyPoints, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{
        position: 'absolute', top: 0, left: 0,
        opacity: 0.75, pointerEvents: 'none',
      }}
      data-testid="opera-layer"
    />
  );
};

function renderFallback(
  canvas: HTMLCanvasElement,
  mask: Float32Array,
  width: number,
  height: number,
): void {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  ctx.fillStyle = 'rgba(0,0,0,0.6)';
  ctx.fillRect(0, 0, width, height);
}

function renderWebGL(
  gl: WebGL2RenderingContext,
  mask: Float32Array,
  points: Array<{ x: number; y: number; uncertainty: number }>,
  width: number,
  height: number,
): void {
  // ---------------------------------------------------------------------------
  // Inline GLSL sources — mirrors shaders/fog.frag and a companion vertex shader.
  // We inline rather than fetch() so the WebGL context compiles synchronously
  // inside the React useEffect without needing an async loader.
  // ---------------------------------------------------------------------------
  const vsSource = `#version 300 es
    in vec2 a_position;
    out vec2 v_texcoord;
    void main() {
      // Convert clip-space NDC position [-1,1] → UV [0,1]
      v_texcoord = a_position * 0.5 + 0.5;
      gl_Position = vec4(a_position, 0.0, 1.0);
    }
  `;

  // Fragment shader logic is 1-to-1 with shaders/fog.frag:
  //   • Samples the Float32 visibility mask texture (R channel)
  //   • Adds value-noise animated fog density
  //   • Overlays uncertainty ripples (concentric sine waves)
  //   • Outputs dark-navy fog with alpha proportional to fog density
  const fsSource = `#version 300 es
    precision highp float;
    uniform sampler2D u_visibility_mask;
    uniform float u_time;
    uniform float u_uncertainty_scale;
    in vec2 v_texcoord;
    out vec4 fragColor;
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
      float n = noise(v_texcoord * 8.0 + vec2(u_time * 0.1, u_time * 0.07));
      float animated_fog = fog_density * (0.85 + 0.15 * n);
      float dist = length(v_texcoord - vec2(0.5, 0.5));
      float ripple = sin(dist * 20.0 - u_time * 3.0) * 0.05 * u_uncertainty_scale;
      animated_fog = clamp(animated_fog + ripple, 0.0, 1.0);
      vec3 fog_color = vec3(0.05, 0.05, 0.12);
      fragColor = vec4(fog_color, animated_fog * 0.85);
    }
  `;

  // ---------------------------------------------------------------------------
  // Shader compilation helper — logs info log on failure, returns null
  // ---------------------------------------------------------------------------
  function compileShader(type: number, src: string): WebGLShader | null {
    const shader = gl.createShader(type);
    if (!shader) return null;
    gl.shaderSource(shader, src);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error('Shader compile error:', gl.getShaderInfoLog(shader));
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
    console.error('Program link error:', gl.getProgramInfoLog(program));
    gl.deleteProgram(program);
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    return;
  }

  // ---------------------------------------------------------------------------
  // Fullscreen triangle-strip quad — covers the entire viewport in NDC space.
  // Two triangles: (-1,-1)→(1,-1)→(-1,1)→(1,1) using TRIANGLE_STRIP
  // ---------------------------------------------------------------------------
  const positions = new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]);
  const vao = gl.createVertexArray();
  gl.bindVertexArray(vao);
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);
  const posLoc = gl.getAttribLocation(program, 'a_position');
  gl.enableVertexAttribArray(posLoc);
  gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

  // ---------------------------------------------------------------------------
  // Visibility mask → R32F texture.
  // The mask is a flat Float32Array of arbitrary length; we square-pad it to
  // the nearest texel grid so texImage2D receives a complete rectangle.
  // LINEAR filtering ensures smooth fog gradients across coarse mask grids.
  // ---------------------------------------------------------------------------
  const maskSize = Math.ceil(Math.sqrt(mask.length || 1));
  const padded = new Float32Array(maskSize * maskSize);
  padded.set(mask);
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(
    gl.TEXTURE_2D, 0, gl.R32F,       // internal format: single-channel 32-bit float
    maskSize, maskSize, 0,
    gl.RED, gl.FLOAT, padded,
  );
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

  // ---------------------------------------------------------------------------
  // Draw — alpha-blended so the fog layer composites over the layers beneath it
  // ---------------------------------------------------------------------------
  gl.viewport(0, 0, width, height);
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  gl.clearColor(0, 0, 0, 0);   // transparent clear — not opaque black
  gl.clear(gl.COLOR_BUFFER_BIT);

  gl.useProgram(program);

  // Texture unit 0 → u_visibility_mask sampler
  gl.uniform1i(gl.getUniformLocation(program, 'u_visibility_mask'), 0);

  // u_time drives fog animation; performance.now() / 1000 gives seconds-since-load
  gl.uniform1f(gl.getUniformLocation(program, 'u_time'), performance.now() / 1000.0);

  // u_uncertainty_scale — average uncertainty across all provided points, clamped to [0, 1]
  const uncertaintyScale =
    points.length > 0
      ? Math.min(1.0, points.reduce((sum, p) => sum + p.uncertainty, 0) / points.length)
      : 0.5;
  gl.uniform1f(gl.getUniformLocation(program, 'u_uncertainty_scale'), uncertaintyScale);

  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.bindVertexArray(vao);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

  // ---------------------------------------------------------------------------
  // Cleanup — release all GPU objects immediately after draw.
  // This layer re-renders on every prop change, so we never cache GPU state.
  // ---------------------------------------------------------------------------
  gl.deleteTexture(tex);
  gl.deleteBuffer(buf);
  gl.deleteVertexArray(vao);
  gl.deleteProgram(program);
  gl.deleteShader(vs);
  gl.deleteShader(fs);
}

export default OperaLayer;
