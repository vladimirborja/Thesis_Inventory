<script setup lang="ts">
/**
 * Vue recreation of shadcn.io Light Waves background.
 * WebGL2 layered translucent hills of light under hero copy.
 */
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { cn } from '@/lib/utils'

const props = withDefaults(
  defineProps<{
    class?: string
    className?: string
    colors?: string[]
    amplitude?: number
    angle?: number
    depth?: number
    fill?: number
    frequency?: number
    height?: number
    intensity?: number
    layers?: number
    opacity?: number
    placement?: 'bottom' | 'top'
    reach?: number
    softness?: number
    speed?: number
    interactive?: boolean
    paused?: boolean
    quality?: number
    grain?: number
    seed?: number
  }>(),
  {
    colors: () => ['#67e8f9', '#22d3ee', '#3b82f6', '#4f46e5'],
    amplitude: 1,
    angle: 0,
    depth: 0.7,
    fill: 0.15,
    frequency: 1,
    height: 0.5,
    intensity: 1,
    layers: 5,
    opacity: 1,
    placement: 'bottom',
    reach: 0.6,
    softness: 0.1,
    speed: 1,
    interactive: true,
    paused: false,
    quality: 1,
    grain: 0,
    seed: 0,
  },
)

const rootEl = ref<HTMLElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)

const rootClass = computed(() => cn('relative isolate overflow-hidden bg-background', props.class, props.className))

const VERT = `#version 300 es
in vec2 a_pos;
void main(){ gl_Position = vec4(a_pos, 0.0, 1.0); }`

const FRAG = `#version 300 es
precision highp float;
out vec4 fragColor;

uniform vec2 u_res;
uniform float u_time;
uniform vec2 u_mouse;
uniform float u_amp;
uniform float u_angle;
uniform float u_depth;
uniform float u_fill;
uniform float u_freq;
uniform float u_height;
uniform float u_intensity;
uniform float u_layers;
uniform float u_opacity;
uniform float u_reach;
uniform float u_soft;
uniform float u_speed;
uniform float u_placement;
uniform float u_grain;
uniform float u_seed;
uniform vec3 u_c0;
uniform vec3 u_c1;
uniform vec3 u_c2;
uniform vec3 u_c3;
uniform float u_colorCount;

float hash(vec2 p){
  return fract(sin(dot(p, vec2(127.1, 311.7)) + u_seed) * 43758.5453);
}

vec3 samplePalette(float t){
  t = clamp(t, 0.0, 1.0);
  float n = max(u_colorCount - 1.0, 1.0);
  float x = t * n;
  float i = floor(x);
  float f = fract(x);
  vec3 a = u_c0;
  vec3 b = u_c1;
  if(i < 0.5){ a = u_c0; b = u_c1; }
  else if(i < 1.5){ a = u_c1; b = u_c2; }
  else if(i < 2.5){ a = u_c2; b = u_c3; }
  else { a = u_c3; b = u_c3; }
  return mix(a, b, smoothstep(0.0, 1.0, f));
}

float hillY(float x, float layer, float t){
  float lf = 1.0 - layer * 0.08 * u_depth;
  float phase = t * u_speed * (0.35 + (1.0 - layer * 0.12 * u_depth)) + layer * 1.7 + u_seed;
  float f = u_freq * (0.85 + layer * 0.08);
  float a = u_amp * (0.55 + layer * 0.12) * lf;
  float w =
      sin(x * 2.1 * f + phase) * 0.55
    + sin(x * 3.7 * f - phase * 1.3 + layer) * 0.28
    + cos(x * 1.3 * f + phase * 0.7) * 0.17;
  float base = mix(0.08, u_height, layer / max(u_layers - 1.0, 1.0));
  return base + w * a * 0.22;
}

void main(){
  vec2 uv = gl_FragCoord.xy / u_res;
  float aspect = u_res.x / max(u_res.y, 1.0);

  // placement: 0 = bottom, 1 = top
  float y = mix(uv.y, 1.0 - uv.y, u_placement);
  float x = (uv.x - 0.5) * aspect;
  float ang = radians(clamp(u_angle, -30.0, 30.0));
  x = x * cos(ang) - (y - 0.5) * sin(ang);

  // pointer parallax
  x += (u_mouse.x - 0.5) * 0.18;
  y += (u_mouse.y - 0.5) * 0.04 * (1.0 - u_placement * 2.0);

  float t = u_time;
  vec3 col = vec3(0.0);
  float alpha = 0.0;

  float nLayers = clamp(u_layers, 2.0, 8.0);
  for(float i = 0.0; i < 8.0; i++){
    if(i >= nLayers) break;
    float layer = i;
    float far = layer / max(nLayers - 1.0, 1.0);
    float crest = hillY(x, far, t);
    float below = crest - y;

    if(below < -0.02) continue;

    float edge = max(u_soft * 0.08, 0.004);
    float mask = smoothstep(-edge, edge * 2.0, below);

    // hairline crest
    float hair = exp(-pow(below / 0.01, 2.0)) * (1.0 - far * 0.35);

    // glow under crest
    float glowLen = max(u_reach * crest, 0.04);
    float glow = exp(-max(below, 0.0) / glowLen) * (0.55 + u_fill * 0.45);

    float body = smoothstep(crest, 0.0, y) * u_fill * (0.35 + 0.65 * (1.0 - far * u_depth));

    float strength = (hair * 1.35 + glow * 0.9 + body) * mask;
    strength *= mix(1.0, 0.45, far * u_depth);
    strength *= u_intensity;

    // color: crest (light/first) -> depth (last)
    float shade = clamp(below / max(crest, 0.001), 0.0, 1.0);
    vec3 hillCol = samplePalette(shade);

    col += hillCol * strength * (0.55 + 0.45 * (1.0 - far));
    alpha = max(alpha, strength * 0.85);
  }

  if(u_grain > 0.001){
    float g = hash(gl_FragCoord.xy + t) - 0.5;
    col += g * u_grain * 0.15;
  }

  fragColor = vec4(col, clamp(alpha * u_opacity, 0.0, 1.0));
}`

function parseColor(hex: string): [number, number, number] {
  const raw = hex.trim()
  if (raw.startsWith('#') && (raw.length === 7 || raw.length === 4)) {
    const h = raw.length === 4
      ? `#${raw[1]}${raw[1]}${raw[2]}${raw[2]}${raw[3]}${raw[3]}`
      : raw
    return [
      parseInt(h.slice(1, 3), 16) / 255,
      parseInt(h.slice(3, 5), 16) / 255,
      parseInt(h.slice(5, 7), 16) / 255,
    ]
  }
  return [1, 1, 1]
}

let gl: WebGL2RenderingContext | null = null
let program: WebGLProgram | null = null
let raf = 0
let start = 0
let mouse = { x: 0.5, y: 0.5 }
let reducedMotion = false
let visible = true
let ro: ResizeObserver | null = null
let io: IntersectionObserver | null = null

function compile(ctx: WebGL2RenderingContext, type: number, src: string) {
  const s = ctx.createShader(type)!
  ctx.shaderSource(s, src)
  ctx.compileShader(s)
  if (!ctx.getShaderParameter(s, ctx.COMPILE_STATUS)) {
    console.error(ctx.getShaderInfoLog(s))
    ctx.deleteShader(s)
    return null
  }
  return s
}

function loc(name: string) {
  return gl!.getUniformLocation(program!, name)
}

function setUniforms(time: number) {
  if (!gl || !program) return
  const canvas = canvasEl.value!
  const q = Math.min(Math.max(props.quality, 0.25), 1)
  const w = Math.max(1, Math.floor(canvas.clientWidth * devicePixelRatio * q))
  const h = Math.max(1, Math.floor(canvas.clientHeight * devicePixelRatio * q))
  if (canvas.width !== w || canvas.height !== h) {
    canvas.width = w
    canvas.height = h
    gl.viewport(0, 0, w, h)
  }

  const colors = props.colors.slice(0, 4)
  while (colors.length < 4) colors.push(colors[colors.length - 1] ?? '#ffffff')
  const c0 = parseColor(colors[0] ?? '#ffffff')
  const c1 = parseColor(colors[1] ?? '#ffffff')
  const c2 = parseColor(colors[2] ?? '#ffffff')
  const c3 = parseColor(colors[3] ?? '#ffffff')

  gl.uniform2f(loc('u_res'), w, h)
  gl.uniform1f(loc('u_time'), time)
  gl.uniform2f(loc('u_mouse'), mouse.x, mouse.y)
  gl.uniform1f(loc('u_amp'), props.amplitude)
  gl.uniform1f(loc('u_angle'), props.angle)
  gl.uniform1f(loc('u_depth'), props.depth)
  gl.uniform1f(loc('u_fill'), props.fill)
  gl.uniform1f(loc('u_freq'), props.frequency)
  gl.uniform1f(loc('u_height'), props.height)
  gl.uniform1f(loc('u_intensity'), props.intensity)
  gl.uniform1f(loc('u_layers'), props.layers)
  gl.uniform1f(loc('u_opacity'), props.opacity)
  gl.uniform1f(loc('u_reach'), props.reach)
  gl.uniform1f(loc('u_soft'), props.softness)
  gl.uniform1f(loc('u_speed'), props.speed)
  gl.uniform1f(loc('u_placement'), props.placement === 'top' ? 1 : 0)
  gl.uniform1f(loc('u_grain'), props.grain)
  gl.uniform1f(loc('u_seed'), props.seed)
  gl.uniform3f(loc('u_c0'), c0[0], c0[1], c0[2])
  gl.uniform3f(loc('u_c1'), c1[0], c1[1], c1[2])
  gl.uniform3f(loc('u_c2'), c2[0], c2[1], c2[2])
  gl.uniform3f(loc('u_c3'), c3[0], c3[1], c3[2])
  gl.uniform1f(loc('u_colorCount'), Math.min(props.colors.length, 4))
}

function frame(now: number) {
  raf = 0
  if (!gl || !program) return
  if (!visible) return
  if (!start) start = now
  const t = props.paused || reducedMotion ? 0 : (now - start) * 0.001
  gl.clearColor(0, 0, 0, 0)
  gl.clear(gl.COLOR_BUFFER_BIT)
  setUniforms(t)
  gl.drawArrays(gl.TRIANGLES, 0, 6)
  if (!props.paused && !reducedMotion) raf = requestAnimationFrame(frame)
}

function onPointer(e: PointerEvent) {
  if (!props.interactive || reducedMotion || !rootEl.value) return
  const r = rootEl.value.getBoundingClientRect()
  mouse.x = (e.clientX - r.left) / Math.max(r.width, 1)
  mouse.y = 1 - (e.clientY - r.top) / Math.max(r.height, 1)
}

function init() {
  const canvas = canvasEl.value
  if (!canvas) return
  gl = canvas.getContext('webgl2', {
    alpha: true,
    antialias: false,
    premultipliedAlpha: true,
  })
  if (!gl) return

  const vs = compile(gl, gl.VERTEX_SHADER, VERT)
  const fs = compile(gl, gl.FRAGMENT_SHADER, FRAG)
  if (!vs || !fs) return

  program = gl.createProgram()!
  gl.attachShader(program, vs)
  gl.attachShader(program, fs)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error(gl.getProgramInfoLog(program))
    return
  }
  gl.useProgram(program)

  const buf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(
    gl.ARRAY_BUFFER,
    new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
    gl.STATIC_DRAW,
  )
  const a = gl.getAttribLocation(program, 'a_pos')
  gl.enableVertexAttribArray(a)
  gl.vertexAttribPointer(a, 2, gl.FLOAT, false, 0, 0)
  gl.enable(gl.BLEND)
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)

  reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  raf = requestAnimationFrame(frame)
}

onMounted(() => {
  init()
  rootEl.value?.addEventListener('pointermove', onPointer, { passive: true })
  ro = new ResizeObserver(() => {
    if (props.paused || reducedMotion) {
      setUniforms(0)
      gl?.drawArrays(gl.TRIANGLES, 0, 6)
    }
  })
  if (rootEl.value) ro.observe(rootEl.value)

  io = new IntersectionObserver(([entry]) => {
    const was = visible
    visible = entry?.isIntersecting ?? true
    if (visible && !was && !props.paused && !reducedMotion && !raf) {
      raf = requestAnimationFrame(frame)
    }
  })
  if (rootEl.value) io.observe(rootEl.value)

  document.addEventListener('visibilitychange', onVis)
})

function onVis() {
  visible = document.visibilityState === 'visible'
}

onUnmounted(() => {
  cancelAnimationFrame(raf)
  rootEl.value?.removeEventListener('pointermove', onPointer)
  document.removeEventListener('visibilitychange', onVis)
  ro?.disconnect()
  io?.disconnect()
  if (gl && program) gl.deleteProgram(program)
  gl = null
  program = null
})

watch(
  () => props.paused,
  (p) => {
    if (!p && !reducedMotion) raf = requestAnimationFrame(frame)
  },
)
</script>

<template>
  <div
    ref="rootEl"
    data-slot="light-waves"
    :class="rootClass"
  >
    <canvas
      ref="canvasEl"
      aria-hidden="true"
      class="pointer-events-none absolute inset-0 z-0 h-full w-full"
    />
    <div class="relative z-10">
      <slot />
    </div>
  </div>
</template>
