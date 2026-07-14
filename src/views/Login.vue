<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { Eye, EyeOff, Lock, Mail, User, ShieldCheck, Briefcase, UserCheck, ArrowLeft } from 'lucide-vue-next';
import type { UserRole } from '@/types';

const router = useRouter();
const authStore = useAuthStore();

const isRegister = ref(false);
const showPassword = ref(false);
const alertMsg = ref('');
const alertType = ref<'success' | 'error'>('success');

// Form States
const loginEmail = ref('admin@foodprocessing.com');
const loginRole = ref<UserRole>('admin');

const regName = ref('');
const regEmail = ref('');
const regPassword = ref('');
const regCompany = ref('Apex Food Processing Corp');
const regRole = ref<UserRole>('employee');

function toggleMode() {
    isRegister.value = !isRegister.value;
    alertMsg.value = '';
}

function handleLogin() {
    if (!loginEmail.value) {
        triggerAlert('Please fill in your email.', 'error');
        return;
    }
    
    authStore.login(loginEmail.value, loginRole.value);
    triggerAlert('Logged in successfully! Redirecting...', 'success');
    setTimeout(() => {
        router.push({ name: 'dashboard' });
    }, 1000);
}

function handleRegister() {
    if (!regName.value || !regEmail.value || !regPassword.value || !regCompany.value) {
        triggerAlert('All fields are required.', 'error');
        return;
    }

    authStore.register(regName.value, regEmail.value, regRole.value, regCompany.value);
    triggerAlert('Account registered successfully! Redirecting...', 'success');
    setTimeout(() => {
        router.push({ name: 'dashboard' });
    }, 1000);
}

function triggerAlert(msg: string, type: 'success' | 'error') {
    alertMsg.value = msg;
    alertType.value = type;
}
</script>

<template>
    <div class="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col justify-center items-center px-4 py-8 relative">
        <!-- Back to Home -->
        <button 
            @click="router.push('/')" 
            class="absolute top-6 left-6 flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white transition"
        >
            <ArrowLeft :size="16" />
            Back to Home
        </button>

        <div class="w-full max-w-[960px] min-h-[620px] rounded-3xl overflow-hidden shadow-2xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 relative flex flex-col md:flex-row transition-all duration-500">
            <!-- Sliding brand visual on the LEFT (for log in) or RIGHT (for sign up) on desktop -->
            <div 
                class="w-full md:w-1/2 bg-emerald-700 text-white p-8 md:p-12 flex flex-col justify-between items-center text-center transition-all duration-500 z-20"
                :class="isRegister ? 'md:order-last' : ''"
            >
                <div class="my-auto space-y-6 max-w-sm">
                    <div class="h-16 w-16 bg-white/10 backdrop-blur-md rounded-2xl flex items-center justify-center mx-auto border border-white/20">
                        <Briefcase :size="32" class="text-white" />
                    </div>
                    <h2 class="text-3xl font-extrabold tracking-tight">
                        {{ isRegister ? 'Join the System' : 'Welcome Back' }}
                    </h2>
                    <p class="text-emerald-100 text-sm leading-relaxed">
                        {{ isRegister 
                            ? 'Create an Employee profile or register an Admin identity to coordinate warehouse logistics.' 
                            : 'Sign in to access real-time stock thresholds, record receipts, or monitor audits.' }}
                    </p>
                    <button 
                        @click="toggleMode"
                        class="mt-4 px-8 py-3 border-2 border-white rounded-full font-semibold hover:bg-white hover:text-emerald-700 transition duration-300 tracking-wide text-sm"
                    >
                        {{ isRegister ? 'Sign In Instead' : 'Create an Account' }}
                    </button>
                </div>
            </div>

            <!-- Form Content Panel -->
            <div class="w-full md:w-1/2 p-8 md:p-12 flex flex-col justify-center bg-white dark:bg-gray-900">
                <!-- Alert Alert -->
                <div 
                    v-if="alertMsg" 
                    class="mb-6 p-4 rounded-xl text-sm border font-medium"
                    :class="alertType === 'success' 
                        ? 'bg-emerald-50 text-emerald-800 border-emerald-100' 
                        : 'bg-red-50 text-red-800 border-red-100'"
                >
                    {{ alertMsg }}
                </div>

                <!-- LOGIN FORM -->
                <div v-if="!isRegister" class="space-y-6">
                    <div>
                        <h3 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">Sign In</h3>
                        <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">Select your role and enter email to proceed</p>
                    </div>

                    <!-- Role selector -->
                    <div class="space-y-2">
                        <label class="block text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Access Level</label>
                        <div class="grid grid-cols-3 gap-2">
                            <button 
                                @click="loginRole = 'super_admin'"
                                type="button"
                                class="py-2.5 px-2 rounded-xl text-xs font-medium border flex flex-col items-center gap-1.5 transition"
                                :class="loginRole === 'super_admin'
                                    ? 'border-emerald-600 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400'
                                    : 'border-gray-100 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400'"
                            >
                                <UserCheck :size="16" />
                                Super Admin
                            </button>
                            <button 
                                @click="loginRole = 'admin'"
                                type="button"
                                class="py-2.5 px-2 rounded-xl text-xs font-medium border flex flex-col items-center gap-1.5 transition"
                                :class="loginRole === 'admin'
                                    ? 'border-emerald-600 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400'
                                    : 'border-gray-100 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400'"
                            >
                                <ShieldCheck :size="16" />
                                Admin
                            </button>
                            <button 
                                @click="loginRole = 'employee'"
                                type="button"
                                class="py-2.5 px-2 rounded-xl text-xs font-medium border flex flex-col items-center gap-1.5 transition"
                                :class="loginRole === 'employee'
                                    ? 'border-emerald-600 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400'
                                    : 'border-gray-100 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400'"
                            >
                                <User :size="16" />
                                Employee
                            </button>
                        </div>
                    </div>

                    <form @submit.prevent="handleLogin" class="space-y-4">
                        <div class="space-y-1">
                            <label for="email" class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Email Address</label>
                            <div class="relative">
                                <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
                                    <Mail :size="18" />
                                </span>
                                <input 
                                    id="email" 
                                    v-model="loginEmail" 
                                    type="email" 
                                    class="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30 dark:text-white"
                                    placeholder="name@company.com"
                                    required
                                />
                            </div>
                        </div>

                        <div class="space-y-1">
                            <label for="password" class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Password</label>
                            <div class="relative">
                                <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
                                    <Lock :size="18" />
                                </span>
                                <input 
                                    id="password" 
                                    type="password" 
                                    class="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30 dark:text-white"
                                    value="••••••••••••"
                                    disabled
                                />
                            </div>
                            <p class="text-[10px] text-gray-400 dark:text-gray-500 mt-1">Note: Authentication is simulated for rapid testing.</p>
                        </div>

                        <button 
                            type="submit" 
                            class="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl transition shadow-lg shadow-emerald-600/10 text-sm mt-6"
                        >
                            Sign In
                        </button>
                    </form>
                </div>

                <!-- REGISTER FORM -->
                <div v-else class="space-y-6">
                    <div>
                        <h3 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">Create Account</h3>
                        <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">Register as system admin or floor operator</p>
                    </div>

                    <form @submit.prevent="handleRegister" class="space-y-4">
                        <div class="space-y-1">
                            <label for="reg-name" class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Full Name</label>
                            <div class="relative">
                                <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
                                    <User :size="18" />
                                </span>
                                <input 
                                    id="reg-name" 
                                    v-model="regName" 
                                    type="text" 
                                    class="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30 dark:text-white"
                                    placeholder="Enter your name"
                                    required
                                />
                            </div>
                        </div>

                        <div class="space-y-1">
                            <label for="reg-email" class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Email Address</label>
                            <div class="relative">
                                <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
                                    <Mail :size="18" />
                                </span>
                                <input 
                                    id="reg-email" 
                                    v-model="regEmail" 
                                    type="email" 
                                    class="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30 dark:text-white"
                                    placeholder="email@company.com"
                                    required
                                />
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div class="space-y-1">
                                <label for="reg-company" class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Company</label>
                                <input 
                                    id="reg-company" 
                                    v-model="regCompany" 
                                    type="text" 
                                    class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30 dark:text-white"
                                    required
                                />
                            </div>
                            <div class="space-y-1">
                                <label for="reg-role" class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Role Access</label>
                                <select 
                                    id="reg-role" 
                                    v-model="regRole" 
                                    class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30 dark:text-white"
                                    required
                                >
                                    <option value="employee">Employee</option>
                                    <option value="admin">Admin</option>
                                    <option value="super_admin">Super Admin</option>
                                </select>
                            </div>
                        </div>

                        <div class="space-y-1">
                            <label for="reg-pass" class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Password</label>
                            <input 
                                id="reg-pass" 
                                v-model="regPassword" 
                                type="password" 
                                class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30 dark:text-white"
                                placeholder="••••••••"
                                required
                            />
                        </div>

                        <button 
                            type="submit" 
                            class="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl transition shadow-lg shadow-emerald-600/10 text-sm mt-4"
                        >
                            Sign Up
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</template>
