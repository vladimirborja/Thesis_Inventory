import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import Landing from '@/views/Landing.vue';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        { path: '/',            name: 'landing',      component: Landing },
        { path: '/auth',        name: 'auth',         component: () => import('@/views/Login.vue') },
        { path: '/dashboard',   name: 'dashboard',    component: () => import('@/views/Dashboard.vue'),    meta: { requiresAuth: true } },
        { path: '/inventory',   name: 'inventory',    component: () => import('@/views/Inventory.vue'),    meta: { requiresAuth: true } },
        { path: '/ingredients', name: 'ingredients',  component: () => import('@/views/Ingredients.vue'),  meta: { requiresAuth: true } },
        { path: '/sales',       name: 'sales',        component: () => import('@/views/Sales.vue'),        meta: { requiresAuth: true } },
        { path: '/suppliers',   name: 'suppliers',    component: () => import('@/views/Suppliers.vue'),    meta: { requiresAuth: true } },
        { path: '/transactions',name: 'transactions', component: () => import('@/views/Transactions.vue'), meta: { requiresAuth: true } },
        { path: '/users',       name: 'users',        component: () => import('@/views/Users.vue'),        meta: { requiresAuth: true, roles: ['super_admin'] } },
        // 404 — must be last
        { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFound.vue') },
    ],
});

// Async route guard — validates JWT via /api/auth/me on every navigation
router.beforeEach(async (to, _from, next) => {
    const authStore = useAuthStore();

    // Only call initSession once per page lifecycle (skip if already hydrated)
    if (!authStore.currentUser) {
        await authStore.initSession();
    }

    const isAuthenticated = authStore.isAuthenticated;

    if (to.name === 'auth' && isAuthenticated) {
        // Logged-in users can't access login page
        return next({ name: 'dashboard' });
    }

    if (to.meta.requiresAuth && !isAuthenticated) {
        // Not logged in — redirect to auth
        return next({ name: 'auth' });
    }

    if (to.meta.roles && isAuthenticated) {
        const allowed = to.meta.roles as string[];
        if (!allowed.includes(authStore.currentUser!.role)) {
            return next({ name: 'dashboard' });
        }
    }

    next();
});

export default router;
