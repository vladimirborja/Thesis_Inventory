/**
 * src/stores/auth.ts
 * Real API-backed auth store. All data (products, suppliers, etc.)
 * is now fetched individually by each view — this store only manages
 * the authenticated user and their JWT token.
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api, setToken, clearToken, getToken } from '@/lib/api';
import type { User, LoginResponse } from '@/types';

export const useAuthStore = defineStore('auth', () => {
    const currentUser = ref<User | null>(null);
    const isLoading   = ref(false);
    const error       = ref<string | null>(null);

    const isAuthenticated = computed(() => !!currentUser.value);

    // ── Session restore ────────────────────────────────────────────────────────
    async function initSession(): Promise<void> {
        const token = getToken();
        if (!token) return;
        try {
            const user = await api.get<User>('/auth/me');
            currentUser.value = user;
        } catch {
            // Token invalid / expired
            clearToken();
            currentUser.value = null;
        }
    }

    // ── Login ──────────────────────────────────────────────────────────────────
    async function login(email: string, password: string): Promise<void> {
        isLoading.value = true;
        error.value = null;
        try {
            const res = await api.post<LoginResponse>('/auth/login', { email, password });
            setToken(res.access_token);
            currentUser.value = res.user;
        } catch (e: unknown) {
            error.value = e instanceof Error ? e.message : 'Login failed';
            throw e;
        } finally {
            isLoading.value = false;
        }
    }

    // ── Register ───────────────────────────────────────────────────────────────
    async function register(
        name: string,
        email: string,
        password: string,
        role: string,
        companyName: string,
    ): Promise<void> {
        isLoading.value = true;
        error.value = null;
        try {
            // Register but do NOT log in automatically — redirect to login
            await api.post<LoginResponse>('/auth/register', {
                name,
                email,
                password,
                role,
                company_name: companyName,
            });
            // No setToken — user must log in manually
        } catch (e: unknown) {
            error.value = e instanceof Error ? e.message : 'Registration failed';
            throw e;
        } finally {
            isLoading.value = false;
        }
    }

    // ── Logout ─────────────────────────────────────────────────────────────────
    function logout(): void {
        clearToken();
        currentUser.value = null;
    }

    return {
        currentUser,
        isLoading,
        error,
        isAuthenticated,
        initSession,
        login,
        register,
        logout,
    };
});
