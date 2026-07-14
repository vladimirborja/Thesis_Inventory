import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import Landing from '@/views/Landing.vue';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'landing',
            component: Landing,
        },
        {
            path: '/auth',
            name: 'auth',
            component: () => import('@/views/Login.vue'),
        },
        {
            path: '/dashboard',
            name: 'dashboard',
            component: () => import('@/views/Dashboard.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/inventory',
            name: 'inventory',
            component: () => import('@/views/Inventory.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/suppliers',
            name: 'suppliers',
            component: () => import('@/views/Suppliers.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/transactions',
            name: 'transactions',
            component: () => import('@/views/Transactions.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/users',
            name: 'users',
            component: () => import('@/views/Users.vue'),
            meta: { requiresAuth: true, roles: ['super_admin'] }
        }
    ],
});

// Route Guard
router.beforeEach((to, from, next) => {
    const authStore = useAuthStore();
    // Initialize session from localstorage
    authStore.initSession();

    if (to.meta.requiresAuth && !authStore.currentUser) {
        // Redirect to auth page
        next({ name: 'auth' });
    } else if (to.meta.roles && authStore.currentUser) {
        // Check if role is allowed
        const allowedRoles = to.meta.roles as string[];
        if (!allowedRoles.includes(authStore.currentUser.role)) {
            // Redirect to general dashboard
            next({ name: 'dashboard' });
        } else {
            next();
        }
    } else {
        next();
    }
});

export default router;
