<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { Home, LayoutDashboard, AlertTriangle } from 'lucide-vue-next';

const router    = useRouter();
const authStore = useAuthStore();
</script>

<template>
    <div class="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col items-center justify-center px-4 text-center">
        <!-- Floating card -->
        <div class="max-w-md w-full bg-white dark:bg-gray-900 rounded-3xl shadow-2xl border border-gray-100 dark:border-gray-800 p-12 flex flex-col items-center gap-6">
            <!-- Icon -->
            <div class="h-20 w-20 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-100 dark:border-amber-900/50 flex items-center justify-center">
                <AlertTriangle :size="36" class="text-amber-500" />
            </div>

            <!-- Status code -->
            <p class="text-8xl font-black text-gray-100 dark:text-gray-800 leading-none select-none">404</p>

            <!-- Message -->
            <div class="-mt-4">
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Page not found</h1>
                <p class="text-sm text-gray-400 dark:text-gray-500 mt-2 leading-relaxed">
                    The page you're looking for doesn't exist or has been moved.
                </p>
            </div>

            <!-- Actions -->
            <div class="flex flex-col sm:flex-row gap-3 w-full">
                <button
                    @click="router.push('/')"
                    class="flex-1 flex items-center justify-center gap-2 py-3 px-5 rounded-xl bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm font-semibold hover:bg-gray-200 dark:hover:bg-gray-700 transition"
                >
                    <Home :size="16" /> Home
                </button>
                <button
                    v-if="authStore.isAuthenticated"
                    @click="router.push('/dashboard')"
                    class="flex-1 flex items-center justify-center gap-2 py-3 px-5 rounded-xl bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 transition shadow-lg shadow-emerald-900/20"
                >
                    <LayoutDashboard :size="16" /> Dashboard
                </button>
                <button
                    v-else
                    @click="router.push('/auth')"
                    class="flex-1 flex items-center justify-center gap-2 py-3 px-5 rounded-xl bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 transition shadow-lg shadow-emerald-900/20"
                >
                    Sign In
                </button>
            </div>
        </div>

        <p class="mt-6 text-xs text-gray-400 dark:text-gray-600">Apex Food Processing Corp · IMS v1.0</p>
    </div>
</template>
