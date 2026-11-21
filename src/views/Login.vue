<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  Lock,
  Mail,
  User,
  Building2,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Eye,
  EyeOff,
} from 'lucide-vue-next'
import { LightWaves } from '@/components/ui/light-waves'
import { useDarkMode } from '@/composables/useDarkMode'

const router = useRouter()
const authStore = useAuthStore()
const { isDark } = useDarkMode()

const isRegister = ref(false)

const alertMsg = ref('')
const alertType = ref<'success' | 'error'>('success')
const alertVisible = ref(false)
const isSubmitting = ref(false)

const loginEmail = ref('')
const loginPassword = ref('')
const showLoginPass = ref(false)

const regName = ref('')
const regEmail = ref('')
const regCompany = ref('Duque Food Products')
const regPassword = ref('')
const showRegPass = ref(false)

const mounted = ref(false)
onMounted(() =>
  requestAnimationFrame(() => {
    mounted.value = true
  }),
)

const alertClass = {
  success:
    'bg-[var(--brand-green)]/10 text-[var(--brand-green-deep)] border-[var(--brand-green)]/20',
  error: 'bg-[var(--brand-red)]/10 text-[var(--brand-red)] border-[var(--brand-red)]/20',
}

function toggleMode() {
  isRegister.value = !isRegister.value
  alertVisible.value = false
  authStore.error = null
}

function triggerAlert(msg: string, type: 'success' | 'error') {
  alertMsg.value = msg
  alertType.value = type
  alertVisible.value = true
  if (type !== 'success') setTimeout(() => { alertVisible.value = false }, 5000)
}

async function handleLogin() {
  if (!loginEmail.value.trim() || !loginPassword.value) {
    triggerAlert('Please enter your email and password.', 'error')
    return
  }
  isSubmitting.value = true
  alertVisible.value = false
  try {
    await authStore.login(loginEmail.value.trim(), loginPassword.value)
    triggerAlert('Signed in! Redirecting…', 'success')
    setTimeout(() => router.push({ name: 'dashboard' }), 800)
  } catch (e: unknown) {
    triggerAlert(e instanceof Error ? e.message : 'Login failed. Check your credentials.', 'error')
  } finally {
    isSubmitting.value = false
  }
}

async function handleRegister() {
  if (!regName.value || !regEmail.value || !regPassword.value || !regCompany.value.trim()) {
    triggerAlert('All fields are required.', 'error')
    return
  }
  if (regPassword.value.length < 8) {
    triggerAlert('Password must be at least 8 characters.', 'error')
    return
  }
  isSubmitting.value = true
  alertVisible.value = false
  try {
    await authStore.register(
      regName.value,
      regEmail.value,
      regPassword.value,
      'employee',
      regCompany.value.trim(),
    )
    triggerAlert('Account created! Please sign in.', 'success')
    regName.value = regEmail.value = regPassword.value = ''
    regCompany.value = 'Duque Food Products'
    setTimeout(() => {
      isRegister.value = false
      alertVisible.value = false
    }, 2000)
  } catch (e: unknown) {
    triggerAlert(e instanceof Error ? e.message : 'Registration failed.', 'error')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div
    class="auth-page relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-4 py-10 font-sans text-gray-900"
    :class="{ 'is-mounted': mounted }"
  >
    <LightWaves
      class="pointer-events-none fixed inset-0 -z-10 min-h-screen bg-white dark:bg-[#050a08]"
      :colors="
        isDark
          ? ['#FF5A55', '#FFB020', '#3DDC84', '#86EFAC']
          : ['#D42D2A', '#F39C12', '#1B7C3D', '#FFFFFF']
      "
      placement="bottom"
      :amplitude="1"
      :angle="0"
      :depth="0.7"
      :fill="isDark ? 0.28 : 0.15"
      :height="0.55"
      :layers="6"
      :intensity="isDark ? 1.45 : 1"
    />

    <button
      type="button"
      class="back-btn liquid-glass liquid-glass--light fixed top-5 left-5 z-30 inline-flex items-center gap-2 rounded-xl px-3.5 py-2.5 text-sm font-medium text-gray-700 transition hover:text-[var(--brand-green)] sm:top-6 sm:left-6"
      :class="{ 'back-btn--in': mounted }"
      @click="router.push('/')"
    >
      <ArrowLeft :size="16" /> Back to Home
    </button>

    <div
      class="auth-card liquid-glass liquid-glass--light relative z-10 mt-14 w-full max-w-[940px] overflow-hidden rounded-[1.75rem] sm:mt-10"
      :class="{ 'auth-card--in': mounted }"
    >
      <!-- Mobile -->
      <div class="md:hidden">
        <div class="brand-panel flex flex-col items-center gap-5 p-8 text-center text-white">
          <img
            src="/images/brand/logo.png"
            alt="Duque Food Products"
            class="h-16 w-16 rounded-full border-2 border-white/80 object-cover shadow-lg"
          />
          <div>
            <h2 class="text-2xl font-extrabold tracking-tight">
              {{ isRegister ? 'Join the System' : 'Welcome Back' }}
            </h2>
            <p class="mt-1 text-sm text-white/80">
              {{ isRegister ? 'Create your IMS profile.' : 'Sign in to manage inventory.' }}
            </p>
          </div>
          <button
            type="button"
            class="toggle-btn rounded-full border-2 border-white/70 px-7 py-2.5 text-sm font-semibold text-white transition-all hover:bg-white hover:text-[var(--brand-green-deep)]"
            @click="toggleMode"
          >
            {{ isRegister ? 'Sign In Instead' : 'Create an Account' }}
          </button>
        </div>

        <div class="p-8">
          <Transition name="alert-drop">
            <div
              v-if="alertVisible"
              :class="alertType === 'success' ? alertClass.success : alertClass.error"
              class="alert-box mb-5"
            >
              <CheckCircle2 v-if="alertType === 'success'" :size="16" class="shrink-0" />
              <XCircle v-else :size="16" class="shrink-0" />
              {{ alertMsg }}
            </div>
          </Transition>
          <Transition name="form-slide" mode="out-in">
            <form
              v-if="!isRegister"
              key="mob-login"
              class="space-y-4"
              @submit.prevent="handleLogin"
            >
              <h3 class="mb-4 text-xl font-bold text-gray-900">Sign In</h3>
              <div class="field-wrap">
                <span class="fi"><Mail :size="16" /></span>
                <input
                  v-model="loginEmail"
                  type="email"
                  class="fi-input"
                  placeholder="name@company.com"
                  required
                />
              </div>
              <div class="field-wrap">
                <span class="fi"><Lock :size="16" /></span>
                <input
                  v-model="loginPassword"
                  :type="showLoginPass ? 'text' : 'password'"
                  class="fi-input pr-10"
                  placeholder="Password"
                  required
                />
                <button type="button" class="field-eye" @click="showLoginPass = !showLoginPass">
                  <EyeOff v-if="showLoginPass" :size="15" /><Eye v-else :size="15" />
                </button>
              </div>
              <button type="submit" :disabled="isSubmitting" class="submit-btn">
                {{ isSubmitting ? 'Signing in…' : 'Sign In' }}
              </button>
            </form>
            <form
              v-else
              key="mob-register"
              class="space-y-4"
              @submit.prevent="handleRegister"
            >
              <h3 class="mb-4 text-xl font-bold text-gray-900">Create Account</h3>
              <div class="field-wrap">
                <span class="fi"><User :size="16" /></span>
                <input
                  v-model="regName"
                  type="text"
                  class="fi-input"
                  placeholder="Full name"
                  required
                />
              </div>
              <div class="field-wrap">
                <span class="fi"><Mail :size="16" /></span>
                <input
                  v-model="regEmail"
                  type="email"
                  class="fi-input"
                  placeholder="email@company.com"
                  required
                />
              </div>
              <div class="field-wrap">
                <span class="fi"><Building2 :size="16" /></span>
                <input
                  v-model="regCompany"
                  type="text"
                  class="fi-input"
                  placeholder="Company name"
                  required
                />
              </div>
              <p class="rounded-xl border border-[var(--brand-green)]/20 bg-[var(--brand-green)]/5 px-3 py-2 text-[11px] text-gray-600">
                New accounts register as <strong>Employee</strong>. Admins are created by a Super Admin.
              </p>
              <div class="field-wrap">
                <span class="fi"><Lock :size="16" /></span>
                <input
                  v-model="regPassword"
                  :type="showRegPass ? 'text' : 'password'"
                  class="fi-input pr-10"
                  placeholder="Min. 8 characters"
                  required
                />
                <button type="button" class="field-eye" @click="showRegPass = !showRegPass">
                  <EyeOff v-if="showRegPass" :size="15" /><Eye v-else :size="15" />
                </button>
              </div>
              <button type="submit" :disabled="isSubmitting" class="submit-btn">
                {{ isSubmitting ? 'Creating…' : 'Create Account' }}
              </button>
            </form>
          </Transition>
        </div>
      </div>

      <!-- Desktop -->
      <div class="relative hidden md:block" style="height: 680px">
        <div
          class="desk-panel right-0 flex flex-col justify-center px-12 py-10"
          :style="{
            opacity: isRegister ? 0 : 1,
            pointerEvents: isRegister ? 'none' : 'auto',
            transition: 'opacity 0.35s ease 0.15s',
          }"
        >
          <Transition name="alert-drop">
            <div
              v-if="alertVisible && !isRegister"
              :class="alertType === 'success' ? alertClass.success : alertClass.error"
              class="alert-box mb-5"
            >
              <CheckCircle2 v-if="alertType === 'success'" :size="16" class="shrink-0" />
              <XCircle v-else :size="16" class="shrink-0" />
              {{ alertMsg }}
            </div>
          </Transition>

          <p class="eyebrow">IMS Portal</p>
          <h3 class="mb-1 text-2xl font-bold text-gray-900">Sign In to Your Account</h3>
          <p class="mb-6 text-sm text-gray-500">Enter your credentials to access the system</p>

          <form class="space-y-4" @submit.prevent="handleLogin">
            <div>
              <label class="field-label">Email Address</label>
              <div class="field-wrap">
                <span class="fi"><Mail :size="16" /></span>
                <input
                  v-model="loginEmail"
                  type="email"
                  class="fi-input"
                  placeholder="name@company.com"
                  autocomplete="email"
                  required
                />
              </div>
            </div>
            <div>
              <label class="field-label">Password</label>
              <div class="field-wrap">
                <span class="fi"><Lock :size="16" /></span>
                <input
                  v-model="loginPassword"
                  :type="showLoginPass ? 'text' : 'password'"
                  class="fi-input pr-10"
                  placeholder="Your password"
                  autocomplete="current-password"
                  required
                />
                <button type="button" class="field-eye" @click="showLoginPass = !showLoginPass">
                  <EyeOff v-if="showLoginPass" :size="15" /><Eye v-else :size="15" />
                </button>
              </div>
            </div>
            <button type="submit" :disabled="isSubmitting" class="submit-btn mt-2">
              {{ isSubmitting ? 'Signing in…' : 'Sign In' }}
            </button>
            <p class="mt-1 text-center text-[11px] text-gray-400">
              Demo: <strong>admin@duquefood.com</strong> / <strong>admin123</strong>
            </p>
          </form>
        </div>

        <div
          class="desk-panel left-0 flex flex-col justify-center px-12 py-10"
          :style="{
            opacity: isRegister ? 1 : 0,
            pointerEvents: isRegister ? 'auto' : 'none',
            transition: 'opacity 0.35s ease 0.15s',
          }"
        >
          <Transition name="alert-drop">
            <div
              v-if="alertVisible && isRegister"
              :class="alertType === 'success' ? alertClass.success : alertClass.error"
              class="alert-box mb-5"
            >
              <CheckCircle2 v-if="alertType === 'success'" :size="16" class="shrink-0" />
              <XCircle v-else :size="16" class="shrink-0" />
              {{ alertMsg }}
            </div>
          </Transition>

          <p class="eyebrow">New Account</p>
          <h3 class="mb-1 text-2xl font-bold text-gray-900">Create Your Profile</h3>
          <p class="mb-5 text-sm text-gray-500">Register as a floor operator (employee). Elevated roles are assigned by admins.</p>

          <form class="space-y-4" @submit.prevent="handleRegister">
            <div>
              <label class="field-label">Full Name</label>
              <div class="field-wrap">
                <span class="fi"><User :size="16" /></span>
                <input
                  v-model="regName"
                  type="text"
                  class="fi-input"
                  placeholder="Your full name"
                  required
                />
              </div>
            </div>
            <div>
              <label class="field-label">Email Address</label>
              <div class="field-wrap">
                <span class="fi"><Mail :size="16" /></span>
                <input
                  v-model="regEmail"
                  type="email"
                  class="fi-input"
                  placeholder="email@company.com"
                  required
                />
              </div>
            </div>
            <div>
              <label class="field-label">Company Name</label>
              <div class="field-wrap">
                <span class="fi"><Building2 :size="16" /></span>
                <input
                  v-model="regCompany"
                  type="text"
                  class="fi-input"
                  placeholder="Duque Food Products"
                  required
                />
              </div>
            </div>
            <div>
              <label class="field-label">
                Password
                <span class="font-normal normal-case text-gray-400">(min. 8 characters)</span>
              </label>
              <div class="field-wrap">
                <span class="fi"><Lock :size="16" /></span>
                <input
                  v-model="regPassword"
                  :type="showRegPass ? 'text' : 'password'"
                  class="fi-input pr-10"
                  placeholder="Create a password"
                  required
                />
                <button type="button" class="field-eye" @click="showRegPass = !showRegPass">
                  <EyeOff v-if="showRegPass" :size="15" /><Eye v-else :size="15" />
                </button>
              </div>
            </div>
            <button type="submit" :disabled="isSubmitting" class="submit-btn mt-2">
              {{ isSubmitting ? 'Creating Account…' : 'Create Account' }}
            </button>
          </form>
        </div>

        <div class="green-panel" :class="isRegister ? 'green-panel--right' : 'green-panel--left'">
          <div class="flex h-full flex-col items-center justify-center gap-7 px-10 text-center text-white">
            <img
              src="/images/brand/logo.png"
              alt="Duque Food Products"
              class="h-20 w-20 rounded-full border-2 border-white/80 object-cover shadow-lg"
            />
            <Transition name="panel-text" mode="out-in">
              <div v-if="!isRegister" key="t-login" class="max-w-xs space-y-2">
                <h2 class="text-3xl font-extrabold tracking-tight">Welcome Back</h2>
                <p class="text-sm leading-relaxed text-white/85">
                  Sign in to access real-time stock thresholds,<br />
                  record receipts, or monitor audits.
                </p>
              </div>
              <div v-else key="t-reg" class="max-w-xs space-y-2">
                <h2 class="text-3xl font-extrabold tracking-tight">Join the System</h2>
                <p class="text-sm leading-relaxed text-white/85">
                  Register as an employee to file daily reports with error-proof totals.
                </p>
              </div>
            </Transition>
            <button
              type="button"
              class="toggle-btn rounded-full border-2 border-white/70 px-8 py-3 text-sm font-semibold text-white transition-all duration-300 hover:bg-white hover:text-[var(--brand-green-deep)] active:scale-95"
              @click="toggleMode"
            >
              {{ isRegister ? 'Sign In Instead' : 'Create an Account' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <p
      class="footer-note liquid-glass liquid-glass--light mt-6 rounded-2xl px-5 py-3 text-center text-xs text-gray-500"
      :class="{ 'footer-note--in': mounted }"
    >
      Duque Food Products · DIMS Portal
    </p>
  </div>
</template>

<style scoped>
.auth-card {
  opacity: 0;
  transform: translateY(24px) scale(0.985);
  transition:
    opacity 0.55s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.55s cubic-bezier(0.22, 1, 0.36, 1);
}
.auth-card--in {
  opacity: 1;
  transform: translateY(0) scale(1);
}
.back-btn {
  opacity: 0;
  transform: translateX(-8px);
  transition:
    opacity 0.4s ease 0.2s,
    transform 0.4s ease 0.2s,
    color 0.2s;
}
.back-btn--in {
  opacity: 1;
  transform: translateX(0);
}
.footer-note {
  opacity: 0;
  transition: opacity 0.6s ease 0.5s;
}
.footer-note--in {
  opacity: 1;
}

.auth-card.liquid-glass {
  border: 2px solid var(--brand-green);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 -10px 24px rgba(0, 0, 0, 0.04) inset,
    0 14px 40px rgba(0, 48, 28, 0.12),
    0 0 0 1px color-mix(in srgb, var(--brand-green) 20%, transparent);
}

.auth-card.liquid-glass::after {
  display: none;
}

.liquid-glass {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.55);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 -10px 24px rgba(0, 0, 0, 0.04) inset,
    0 14px 40px rgba(0, 48, 28, 0.1),
    0 2px 10px rgba(0, 0, 0, 0.04);
}

@supports ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .liquid-glass,
  .liquid-glass--light {
    background: linear-gradient(
      155deg,
      rgba(255, 255, 255, 0.78) 0%,
      rgba(255, 255, 255, 0.42) 48%,
      rgba(255, 255, 255, 0.28) 100%
    );
    -webkit-backdrop-filter: blur(24px) saturate(170%);
    backdrop-filter: blur(24px) saturate(170%);
  }
}

.liquid-glass--light {
  background: rgba(255, 255, 255, 0.55);
}

.liquid-glass::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 1;
  border-radius: inherit;
  pointer-events: none;
  background: linear-gradient(
    125deg,
    rgba(255, 255, 255, 0.75) 0%,
    rgba(255, 255, 255, 0.18) 24%,
    transparent 48%,
    transparent 62%,
    rgba(255, 255, 255, 0.12) 100%
  );
  opacity: 0.9;
  mix-blend-mode: soft-light;
}

.liquid-glass::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 2;
  border-radius: inherit;
  pointer-events: none;
  padding: 1.5px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    rgba(255, 255, 255, 0.55) 18%,
    rgba(27, 124, 61, 0.28) 42%,
    rgba(240, 144, 32, 0.4) 68%,
    rgba(212, 45, 42, 0.35) 85%,
    rgba(255, 255, 255, 0.7) 100%
  );
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  mask-composite: exclude;
}

.liquid-glass > * {
  position: relative;
  z-index: 3;
}

.desk-panel {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 50%;
}

.brand-panel,
.green-panel {
  background: var(--brand-green);
}

.green-panel {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 50%;
  z-index: 10;
  box-shadow:
    6px 0 40px rgba(0, 0, 0, 0.15),
    -6px 0 40px rgba(0, 0, 0, 0.08);
  transition: transform 0.65s cubic-bezier(0.76, 0, 0.24, 1);
  will-change: transform;
}
.green-panel--left {
  transform: translateX(0%);
}
.green-panel--right {
  transform: translateX(100%);
}

.panel-text-enter-active,
.panel-text-leave-active {
  transition: all 0.2s ease;
}
.panel-text-enter-from {
  opacity: 0;
  transform: translateY(14px);
}
.panel-text-leave-to {
  opacity: 0;
  transform: translateY(-14px);
}
.form-slide-enter-active,
.form-slide-leave-active {
  transition: all 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}
.form-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.form-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.alert-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  border-width: 1px;
}
.alert-drop-enter-active {
  transition: all 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}
.alert-drop-leave-active {
  transition: all 0.18s ease;
}
.alert-drop-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}
.alert-drop-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

.eyebrow {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--brand-green);
  margin-bottom: 4px;
}
.field-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #9ca3af;
  margin-bottom: 4px;
}
.field-wrap {
  position: relative;
}
.fi {
  position: absolute;
  inset-block: 0;
  left: 0;
  display: flex;
  align-items: center;
  padding-left: 12px;
  color: #9ca3af;
  pointer-events: none;
}
.field-eye {
  position: absolute;
  inset-block: 0;
  right: 0;
  display: flex;
  align-items: center;
  padding-right: 12px;
  color: #9ca3af;
  background: none;
  border: none;
  cursor: pointer;
}
.fi-input {
  width: 100%;
  padding: 11px 14px 11px 38px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.55);
  background: rgba(255, 255, 255, 0.45);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  font-size: 14px;
  outline: none;
  transition:
    border-color 0.2s,
    box-shadow 0.2s,
    background 0.2s;
  color: #111827;
}
.fi-input:focus {
  border-color: color-mix(in srgb, var(--brand-green) 45%, white);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand-green) 18%, transparent);
}
.fi-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.submit-btn {
  width: 100%;
  padding: 13px;
  margin-top: 4px;
  background: linear-gradient(135deg, var(--brand-green), var(--brand-green-deep));
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  border-radius: 14px;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 20px color-mix(in srgb, var(--brand-green) 28%, transparent);
  transition:
    transform 0.15s ease,
    box-shadow 0.2s ease,
    opacity 0.2s;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 28px color-mix(in srgb, var(--brand-green) 34%, transparent);
}
.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}
.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.toggle-btn:active {
  transform: scale(0.97);
}
</style>
