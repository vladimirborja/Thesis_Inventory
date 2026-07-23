<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import {
    Lock, Mail, User, ShieldCheck, UserCheck,
    Briefcase, ArrowLeft, CheckCircle2, XCircle, Eye, EyeOff
} from 'lucide-vue-next';
import type { UserRole } from '@/types';

const router    = useRouter();
const authStore = useAuthStore();

const isRegister = ref(false);

const alertMsg     = ref('');
const alertType    = ref<'success' | 'error'>('success');
const alertVisible = ref(false);
const isSubmitting = ref(false);

// Login
const loginEmail    = ref('');
const loginPassword = ref('');
const showLoginPass = ref(false);

// Register
const regName        = ref('');
const regEmail       = ref('');
const regPassword    = ref('');
const regCompany     = ref('');
const regRole        = ref<UserRole>('employee');
const showRegPass    = ref(false);

const mounted = ref(false);
onMounted(() => requestAnimationFrame(() => { mounted.value = true; }));

const roles = [
    { value: 'super_admin' as UserRole, label: 'Super Admin', icon: UserCheck },
    { value: 'admin'       as UserRole, label: 'Admin',       icon: ShieldCheck },
    { value: 'employee'    as UserRole, label: 'Employee',    icon: User },
];

const alertClass = (() => {
    const success = 'bg-emerald-50 text-emerald-800 border-emerald-100 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-900';
    const error   = 'bg-red-50 text-red-800 border-red-100 dark:bg-red-950/30 dark:text-red-300 dark:border-red-900';
    return { success, error };
})();

function toggleMode() {
    isRegister.value   = !isRegister.value;
    alertVisible.value = false;
    authStore.error    = null;
}

function triggerAlert(msg: string, type: 'success' | 'error') {
    alertMsg.value     = msg;
    alertType.value    = type;
    alertVisible.value = true;
    if (type !== 'success') setTimeout(() => { alertVisible.value = false; }, 5000);
}

async function handleLogin() {
    if (!loginEmail.value.trim() || !loginPassword.value) {
        triggerAlert('Please enter your email and password.', 'error');
        return;
    }
    isSubmitting.value = true;
    alertVisible.value = false;
    try {
        await authStore.login(loginEmail.value.trim(), loginPassword.value);
        triggerAlert('Signed in! Redirecting…', 'success');
        setTimeout(() => router.push({ name: 'dashboard' }), 800);
    } catch (e: unknown) {
        triggerAlert(e instanceof Error ? e.message : 'Login failed. Check your credentials.', 'error');
    } finally {
        isSubmitting.value = false;
    }
}

async function handleRegister() {
    if (!regName.value || !regEmail.value || !regPassword.value || !regCompany.value) {
        triggerAlert('All fields are required.', 'error');
        return;
    }
    if (regPassword.value.length < 8) {
        triggerAlert('Password must be at least 8 characters.', 'error');
        return;
    }
    isSubmitting.value = true;
    alertVisible.value = false;
    try {
        await authStore.register(regName.value, regEmail.value, regPassword.value, regRole.value, regCompany.value);
        triggerAlert('Account created! Please sign in.', 'success');
        // Clear form and switch to login (no auto-login)
        regName.value = regEmail.value = regPassword.value = regCompany.value = '';
        setTimeout(() => { isRegister.value = false; alertVisible.value = false; }, 2000);
    } catch (e: unknown) {
        triggerAlert(e instanceof Error ? e.message : 'Registration failed.', 'error');
    } finally {
        isSubmitting.value = false;
    }
}
</script>

<template>
    <div
        class="auth-page min-h-screen flex flex-col items-center justify-center px-4 py-10 relative overflow-hidden bg-gradient-to-br from-gray-50 via-white to-emerald-50 dark:from-gray-950 dark:via-gray-900 dark:to-emerald-950"
        :class="{ 'is-mounted': mounted }"
    >
        <div class="blob blob-1" aria-hidden="true" />
        <div class="blob blob-2" aria-hidden="true" />

        <button
            @click="router.push('/')"
            class="back-btn absolute top-6 left-6 z-20 flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-emerald-700 dark:hover:text-emerald-400 transition-colors"
            :class="{ 'back-btn--in': mounted }"
        >
            <ArrowLeft :size="16" /> Back to Home
        </button>

        <div
            class="auth-card w-full max-w-[940px] rounded-3xl shadow-2xl shadow-black/10 border border-gray-100 dark:border-gray-800 overflow-hidden"
            :class="{ 'auth-card--in': mounted }"
        >
            <!-- ── MOBILE layout ─────────────────────────────────── -->
            <div class="md:hidden">
                <div class="bg-gradient-to-br from-emerald-600 to-emerald-800 text-white p-8 flex flex-col items-center text-center gap-5">
                    <div class="h-16 w-16 rounded-2xl bg-white/10 border border-white/20 flex items-center justify-center">
                        <Briefcase :size="30" />
                    </div>
                    <div>
                        <h2 class="text-2xl font-extrabold tracking-tight">{{ isRegister ? 'Join the System' : 'Welcome Back' }}</h2>
                        <p class="text-emerald-100 text-sm mt-1">{{ isRegister ? 'Create your IMS profile.' : 'Sign in to manage inventory.' }}</p>
                    </div>
                    <button @click="toggleMode" class="toggle-btn px-7 py-2.5 border-2 border-white/60 rounded-full text-sm font-semibold hover:bg-white hover:text-emerald-700 transition-all">
                        {{ isRegister ? 'Sign In Instead' : 'Create an Account' }}
                    </button>
                </div>

                <div class="bg-white dark:bg-gray-900 p-8">
                    <Transition name="alert-drop">
                        <div v-if="alertVisible" :class="alertType === 'success' ? alertClass.success : alertClass.error" class="alert-box mb-5">
                            <CheckCircle2 v-if="alertType === 'success'" :size="16" class="shrink-0" />
                            <XCircle      v-else                          :size="16" class="shrink-0" />
                            {{ alertMsg }}
                        </div>
                    </Transition>
                    <Transition name="form-slide" mode="out-in">
                        <form v-if="!isRegister" key="mob-login" @submit.prevent="handleLogin" class="space-y-4">
                            <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-4">Sign In</h3>
                            <div class="field-wrap"><span class="fi"><Mail :size="16"/></span><input v-model="loginEmail" type="email" class="fi-input" placeholder="name@company.com" required /></div>
                            <div class="field-wrap">
                                <span class="fi"><Lock :size="16"/></span>
                                <input v-model="loginPassword" :type="showLoginPass ? 'text' : 'password'" class="fi-input pr-10" placeholder="Password" required />
                                <button type="button" @click="showLoginPass = !showLoginPass" class="field-eye"><EyeOff v-if="showLoginPass" :size="15" /><Eye v-else :size="15" /></button>
                            </div>
                            <button type="submit" :disabled="isSubmitting" class="submit-btn">{{ isSubmitting ? 'Signing in…' : 'Sign In' }}</button>
                        </form>
                        <form v-else key="mob-register" @submit.prevent="handleRegister" class="space-y-4">
                            <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-4">Create Account</h3>
                            <div class="field-wrap"><span class="fi"><User :size="16"/></span><input v-model="regName" type="text" class="fi-input" placeholder="Full name" required /></div>
                            <div class="field-wrap"><span class="fi"><Mail :size="16"/></span><input v-model="regEmail" type="email" class="fi-input" placeholder="email@company.com" required /></div>
                            <div class="grid grid-cols-2 gap-3">
                                <input v-model="regCompany" type="text" class="fi-input px-3" placeholder="Company" required />
                                <select v-model="regRole" class="fi-input px-3 bg-white dark:bg-gray-900">
                                    <option value="employee">Employee</option>
                                    <option value="admin">Admin</option>
                                    <option value="super_admin">Super Admin</option>
                                </select>
                            </div>
                            <div class="field-wrap">
                                <span class="fi"><Lock :size="16"/></span>
                                <input v-model="regPassword" :type="showRegPass ? 'text' : 'password'" class="fi-input pr-10" placeholder="Min. 8 characters" required />
                                <button type="button" @click="showRegPass = !showRegPass" class="field-eye"><EyeOff v-if="showRegPass" :size="15" /><Eye v-else :size="15" /></button>
                            </div>
                            <button type="submit" :disabled="isSubmitting" class="submit-btn">{{ isSubmitting ? 'Creating…' : 'Create Account' }}</button>
                        </form>
                    </Transition>
                </div>
            </div>

            <!-- ── DESKTOP sliding panel layout ─────────────────── -->
            <div class="hidden md:block relative" style="height: 620px;">

                <!-- Login form — pinned RIGHT half -->
                <div
                    class="desk-panel right-0 flex flex-col justify-center px-12 py-10 bg-white dark:bg-gray-900"
                    :style="{ opacity: isRegister ? 0 : 1, pointerEvents: isRegister ? 'none' : 'auto', transition: 'opacity 0.35s ease 0.15s' }"
                >
                    <Transition name="alert-drop">
                        <div v-if="alertVisible && !isRegister" :class="alertType === 'success' ? alertClass.success : alertClass.error" class="alert-box mb-5">
                            <CheckCircle2 v-if="alertType === 'success'" :size="16" class="shrink-0" />
                            <XCircle      v-else                          :size="16" class="shrink-0" />
                            {{ alertMsg }}
                        </div>
                    </Transition>

                    <p class="eyebrow">IMS Portal</p>
                    <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-1">Sign In to Your Account</h3>
                    <p class="text-sm text-gray-400 mb-6">Enter your credentials to access the system</p>

                    <form @submit.prevent="handleLogin" class="space-y-4">
                        <div>
                            <label class="field-label">Email Address</label>
                            <div class="field-wrap"><span class="fi"><Mail :size="16"/></span>
                                <input v-model="loginEmail" type="email" class="fi-input" placeholder="name@company.com" autocomplete="email" required />
                            </div>
                        </div>
                        <div>
                            <label class="field-label">Password</label>
                            <div class="field-wrap">
                                <span class="fi"><Lock :size="16"/></span>
                                <input v-model="loginPassword" :type="showLoginPass ? 'text' : 'password'" class="fi-input pr-10" placeholder="Your password" autocomplete="current-password" required />
                                <button type="button" @click="showLoginPass = !showLoginPass" class="field-eye">
                                    <EyeOff v-if="showLoginPass" :size="15" /><Eye v-else :size="15" />
                                </button>
                            </div>
                        </div>
                        <button type="submit" :disabled="isSubmitting" class="submit-btn mt-2">
                            {{ isSubmitting ? 'Signing in…' : 'Sign In' }}
                        </button>
                        <p class="text-[11px] text-center text-gray-400 mt-1">
                            Demo: <strong>admin@foodprocessing.com</strong> / <strong>admin123</strong>
                        </p>
                    </form>
                </div>

                <!-- Register form — pinned LEFT half -->
                <div
                    class="desk-panel left-0 flex flex-col justify-center px-12 py-10 bg-white dark:bg-gray-900"
                    :style="{ opacity: isRegister ? 1 : 0, pointerEvents: isRegister ? 'auto' : 'none', transition: 'opacity 0.35s ease 0.15s' }"
                >
                    <Transition name="alert-drop">
                        <div v-if="alertVisible && isRegister" :class="alertType === 'success' ? alertClass.success : alertClass.error" class="alert-box mb-5">
                            <CheckCircle2 v-if="alertType === 'success'" :size="16" class="shrink-0" />
                            <XCircle      v-else                          :size="16" class="shrink-0" />
                            {{ alertMsg }}
                        </div>
                    </Transition>

                    <p class="eyebrow">New Account</p>
                    <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-1">Create Your Profile</h3>
                    <p class="text-sm text-gray-400 mb-5">Register as an admin or floor operator</p>

                    <form @submit.prevent="handleRegister" class="space-y-4">
                        <div>
                            <label class="field-label">Full Name</label>
                            <div class="field-wrap"><span class="fi"><User :size="16"/></span>
                                <input v-model="regName" type="text" class="fi-input" placeholder="Your full name" required />
                            </div>
                        </div>
                        <div>
                            <label class="field-label">Email Address</label>
                            <div class="field-wrap"><span class="fi"><Mail :size="16"/></span>
                                <input v-model="regEmail" type="email" class="fi-input" placeholder="email@company.com" required />
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <label class="field-label">Company</label>
                                <input v-model="regCompany" type="text" class="fi-input px-3" placeholder="Company name" required />
                            </div>
                            <div>
                                <label class="field-label">Role</label>
                                <select v-model="regRole" class="fi-input px-3 bg-white dark:bg-gray-900" required>
                                    <option value="employee">Employee</option>
                                    <option value="admin">Admin</option>
                                    <option value="super_admin">Super Admin</option>
                                </select>
                            </div>
                        </div>
                        <div>
                            <label class="field-label">Password <span class="text-gray-400 font-normal normal-case">(min. 8 characters)</span></label>
                            <div class="field-wrap">
                                <span class="fi"><Lock :size="16"/></span>
                                <input v-model="regPassword" :type="showRegPass ? 'text' : 'password'" class="fi-input pr-10" placeholder="Create a password" required />
                                <button type="button" @click="showRegPass = !showRegPass" class="field-eye">
                                    <EyeOff v-if="showRegPass" :size="15" /><Eye v-else :size="15" />
                                </button>
                            </div>
                        </div>
                        <button type="submit" :disabled="isSubmitting" class="submit-btn mt-2">
                            {{ isSubmitting ? 'Creating Account…' : 'Create Account' }}
                        </button>
                    </form>
                </div>

                <!-- Sliding green panel -->
                <div class="green-panel" :class="isRegister ? 'green-panel--right' : 'green-panel--left'">
                    <div class="flex flex-col items-center justify-center h-full text-white text-center px-10 gap-7">
                        <div class="h-20 w-20 rounded-2xl bg-white/10 border border-white/20 flex items-center justify-center shadow-lg">
                            <Briefcase :size="36" />
                        </div>
                        <Transition name="panel-text" mode="out-in">
                            <div v-if="!isRegister" key="t-login" class="space-y-2 max-w-xs">
                                <h2 class="text-3xl font-extrabold tracking-tight">Welcome Back</h2>
                                <p class="text-emerald-100 text-sm leading-relaxed">
                                    Sign in to access real-time stock thresholds,<br>record receipts, or monitor audits.
                                </p>
                            </div>
                            <div v-else key="t-reg" class="space-y-2 max-w-xs">
                                <h2 class="text-3xl font-extrabold tracking-tight">Join the System</h2>
                                <p class="text-emerald-100 text-sm leading-relaxed">
                                    Create an Employee or Admin profile to coordinate warehouse logistics.
                                </p>
                            </div>
                        </Transition>
                        <button @click="toggleMode" class="toggle-btn px-8 py-3 border-2 border-white/60 rounded-full text-sm font-semibold hover:bg-white hover:text-emerald-700 transition-all duration-300 active:scale-95">
                            {{ isRegister ? 'Sign In Instead' : 'Create an Account' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <p class="footer-note mt-6 text-xs text-gray-400 dark:text-gray-600" :class="{ 'footer-note--in': mounted }">
            Apex Food Processing Corp · IMS v1.0
        </p>
    </div>
</template>

<style scoped>
.auth-card { opacity:0; transform:translateY(24px) scale(0.985); transition:opacity .55s cubic-bezier(0.22,1,0.36,1), transform .55s cubic-bezier(0.22,1,0.36,1); }
.auth-card--in { opacity:1; transform:translateY(0) scale(1); }
.back-btn { opacity:0; transform:translateX(-8px); transition:opacity .4s ease .2s,transform .4s ease .2s,color .2s; }
.back-btn--in { opacity:1; transform:translateX(0); }
.footer-note { opacity:0; transition:opacity .6s ease .5s; }
.footer-note--in { opacity:1; }
.blob { position:absolute; border-radius:50%; filter:blur(90px); pointer-events:none; z-index:0; }
.blob-1 { width:500px; height:500px; background:radial-gradient(circle,rgba(16,185,129,.1),transparent 70%); top:-160px; right:-100px; animation:float 9s ease-in-out infinite; }
.blob-2 { width:360px; height:360px; background:radial-gradient(circle,rgba(16,185,129,.07),transparent 70%); bottom:-100px; left:-80px; animation:float 11s ease-in-out infinite reverse; }
@keyframes float { 0%,100%{transform:translateY(0) rotate(0deg)} 40%{transform:translateY(-20px) rotate(2deg)} 70%{transform:translateY(10px) rotate(-1deg)} }
.desk-panel { position:absolute; top:0; bottom:0; width:50%; }
.green-panel { position:absolute; top:0; bottom:0; left:0; width:50%; z-index:10; background:linear-gradient(145deg,#059669 0%,#065f46 100%); box-shadow:6px 0 40px rgba(0,0,0,0.2),-6px 0 40px rgba(0,0,0,0.1); transition:transform 0.65s cubic-bezier(0.76,0,0.24,1); will-change:transform; }
.green-panel--left  { transform:translateX(0%); }
.green-panel--right { transform:translateX(100%); }
.panel-text-enter-active,.panel-text-leave-active { transition:all .2s ease; }
.panel-text-enter-from  { opacity:0; transform:translateY(14px); }
.panel-text-leave-to    { opacity:0; transform:translateY(-14px); }
.form-slide-enter-active,.form-slide-leave-active { transition:all .28s cubic-bezier(0.22,1,0.36,1); }
.form-slide-enter-from { opacity:0; transform:translateX(20px); }
.form-slide-leave-to   { opacity:0; transform:translateX(-20px); }
.alert-box { display:flex; align-items:center; gap:8px; padding:12px 14px; border-radius:12px; font-size:13px; font-weight:500; border-width:1px; }
.alert-drop-enter-active { transition:all .28s cubic-bezier(0.22,1,0.36,1); }
.alert-drop-leave-active { transition:all .18s ease; }
.alert-drop-enter-from   { opacity:0; transform:translateY(-10px); }
.alert-drop-leave-to     { opacity:0; transform:translateY(-5px); }
.eyebrow { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.08em; color:#059669; margin-bottom:4px; }
.field-label { display:block; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:#9ca3af; margin-bottom:4px; }
.field-wrap { position:relative; }
.fi { position:absolute; inset-block:0; left:0; display:flex; align-items:center; padding-left:12px; color:#9ca3af; pointer-events:none; }
.field-eye { position:absolute; inset-block:0; right:0; display:flex; align-items:center; padding-right:12px; color:#9ca3af; background:none; border:none; cursor:pointer; }
.fi-input { width:100%; padding:11px 14px 11px 38px; border-radius:12px; border:1px solid #e5e7eb; background:transparent; font-size:14px; outline:none; transition:border-color .2s,box-shadow .2s; color:#111827; }
.fi-input:focus { border-color:#059669; box-shadow:0 0 0 3px rgba(5,150,105,.14); }
.fi-input:disabled { opacity:.5; cursor:not-allowed; }
.submit-btn { width:100%; padding:13px; margin-top:4px; background:linear-gradient(135deg,#059669,#047857); color:#fff; font-weight:700; font-size:14px; border-radius:14px; border:none; cursor:pointer; box-shadow:0 4px 20px rgba(5,150,105,.28); transition:transform .15s ease,box-shadow .2s ease,opacity .2s; }
.submit-btn:hover:not(:disabled)  { transform:translateY(-1px); box-shadow:0 8px 28px rgba(5,150,105,.34); }
.submit-btn:active:not(:disabled) { transform:translateY(0); }
.submit-btn:disabled { opacity:.6; cursor:not-allowed; }
.toggle-btn:active { transform:scale(0.97); }
</style>
