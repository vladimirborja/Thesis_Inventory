import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import Landing from '@/views/Landing.vue';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        { path: '/',            name: 'landing',      component: Landing },
        { path: '/company',     name: 'company',      component: () => import('@/views/CompanyInfo.vue') },
        { path: '/auth',        name: 'auth',         component: () => import('@/views/Login.vue') },
        { path: '/dashboard',   name: 'dashboard',    component: () => import('@/views/Dashboard.vue'),    meta: { requiresAuth: true } },
        { path: '/analytics',   name: 'analytics',    component: () => import('@/views/Analytics.vue'),    meta: { requiresAuth: true, roles: ['admin', 'super_admin'] } },
        { path: '/inventory',   name: 'inventory',    component: () => import('@/views/Inventory.vue'),    meta: { requiresAuth: true } },
        { path: '/ingredients', name: 'ingredients',  component: () => import('@/views/Ingredients.vue'),  meta: { requiresAuth: true } },
        { path: '/sales',       name: 'sales',        component: () => import('@/views/Sales.vue'),        meta: { requiresAuth: true } },
        { path: '/suppliers',   name: 'suppliers',    component: () => import('@/views/Suppliers.vue'),    meta: { requiresAuth: true } },
        { path: '/transactions',   name: 'transactions',   component: () => import('@/views/Transactions.vue'),  meta: { requiresAuth: true } },
        { path: '/users',       name: 'users',        component: () => import('@/views/Users.vue'),        meta: { requiresAuth: true, roles: ['admin', 'super_admin'] } },
        // 404 — must be last
        { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFound.vue') },
    ],
});

// Route guard — validates auth and role access on every navigation
router.beforeEach(async (to) => {
    const authStore = useAuthStore();

    // Hydrate session from stored token once per page lifecycle
    if (!authStore.currentUser) {
        await authStore.initSession();
    }

    const isAuthenticated = authStore.isAuthenticated;

    // Logged-in users bounced away from login page
    if (to.name === 'auth' && isAuthenticated) {
        return { name: 'dashboard' };
    }

    // Unauthenticated users blocked from protected routes
    if (to.meta.requiresAuth && !isAuthenticated) {
        return { name: 'auth' };
    }

    // Role-restricted routes — redirect to dashboard if not allowed
    if (to.meta.roles && isAuthenticated) {
        const allowed = to.meta.roles as string[];
        if (!allowed.includes(authStore.currentUser!.role)) {
            return { name: 'dashboard' };
        }
    }

    // Allow navigation
    return true;
});

export default router;
