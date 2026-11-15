<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useDarkMode } from '@/composables/useDarkMode';
import {
    LayoutDashboard, Users, Package, Store, History, LogOut, Menu, X, Sun, Moon,
    ChevronRight, ChefHat, Receipt, LineChart, UserCircle,
} from 'lucide-vue-next';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const { isDark, toggleDarkMode } = useDarkMode();

const isMobileOpen = ref(false);

const currentUser = computed(() => authStore.currentUser);
const currentRole = computed(() => currentUser.value?.role || 'employee');
const userName = computed(() => currentUser.value?.name || 'User');
const userCompany = computed(() => currentUser.value?.companyName || 'Duque Food Products');
const avatarUrl = computed(() => currentUser.value?.avatarUrl || '');

const todayLabel = computed(() =>
    new Date().toLocaleDateString('en-PH', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
    }),
);

const roleLabel = computed(() => currentRole.value.replace('_', ' '));

const breadcrumbs = computed(() => {
    const path = route.path;
    if (path === '/dashboard')    return [{ title: 'Dashboard' }];
    if (path === '/analytics')    return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Analytics' }];
    if (path === '/inventory')    return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Inventory' }];
    if (path === '/ingredients')  return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Ingredients' }];
    if (path === '/sales')        return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Sales Ledger' }];
    if (path === '/suppliers')    return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Suppliers' }];
    if (path === '/transactions') return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Daily Reports' }];
    if (path === '/users')        return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'User Management' }];
    if (path === '/profile')      return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Profile' }];
    return [{ title: 'System' }];
});

const canInput = computed(() => currentUser.value?.canInputTransactions ?? false);

const navItems = computed(() => {
    const items = [
        { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    ];

    const isAdminRole = currentRole.value === 'admin' || currentRole.value === 'super_admin';
    if (isAdminRole) {
        items.push({ title: 'Analytics', href: '/analytics', icon: LineChart });
    }

    if (isAdminRole || canInput.value) {
        items.push({ title: 'Daily Reports', href: '/transactions', icon: History });
    }

    if (currentRole.value === 'super_admin') {
        items.push(
            { title: 'Inventory Catalog', href: '/inventory', icon: Package },
            { title: 'User Management', href: '/users', icon: Users },
        );
    } else if (currentRole.value === 'admin') {
        items.push(
            { title: 'Inventory Catalog', href: '/inventory', icon: Package },
            { title: 'Ingredients Inventory', href: '/ingredients', icon: ChefHat },
            { title: 'Sales & POS', href: '/sales', icon: Receipt },
            { title: 'Supplier Registry', href: '/suppliers', icon: Store },
            { title: 'Employee Management', href: '/users', icon: Users },
        );
    } else if (canInput.value) {
        items.push(
            { title: 'Inventory Catalog', href: '/inventory', icon: Package },
            { title: 'Ingredients Inventory', href: '/ingredients', icon: ChefHat },
        );
    } else {
        items.push(
            { title: 'Inventory Catalog', href: '/inventory', icon: Package },
            { title: 'Daily Reports', href: '/transactions', icon: History },
        );
    }

    items.push({ title: 'My Profile', href: '/profile', icon: UserCircle });

    return items;
});

function handleLogout() {
    authStore.logout();
    router.push('/');
}
</script>

<template>
    <div class="ims-app-shell min-h-screen flex font-sans text-gray-900 dark:text-gray-100 relative">
        <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
            <div class="absolute -top-24 -right-16 h-80 w-80 rounded-full bg-emerald-700/28 blur-3xl dark:bg-emerald-600/20" />
            <div class="absolute top-1/3 -left-20 h-72 w-72 rounded-full bg-amber-600/18 blur-3xl dark:bg-amber-500/12" />
            <div class="absolute bottom-0 right-1/4 h-64 w-64 rounded-full bg-emerald-800/16 blur-3xl dark:bg-emerald-700/14" />
        </div>

        <!-- Desktop Sidebar — frosted, menu only (no extra nav widgets) -->
        <aside class="ims-sidebar-glass hidden lg:flex flex-col w-[15.5rem] shrink-0 text-white relative z-10 overflow-hidden">
            <div class="relative h-[4.25rem] flex items-center gap-3 border-b border-white/15 px-5">
                <img
                    src="/images/brand/logo.jpg"
                    alt="Duque"
                    class="h-10 w-10 rounded-full object-cover ring-2 ring-white/35 shadow-lg"
                />
                <div class="min-w-0">
                    <h2 class="text-[13px] font-bold leading-tight truncate tracking-tight">{{ userCompany }}</h2>
                    <p class="text-[10px] text-emerald-200/90 font-medium tracking-wide mt-0.5">DIMS · Daily Control</p>
                </div>
            </div>

            <nav class="relative flex-1 space-y-1 p-3 overflow-y-auto">
                <p class="px-3 pt-2 pb-1.5 text-[9px] font-bold uppercase tracking-[0.14em] text-emerald-200/70">Menu</p>
                <router-link
                    v-for="item in navItems"
                    :key="item.href"
                    :to="item.href"
                    class="group flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-200"
                    :class="route.path === item.href
                        ? 'bg-white/20 text-white shadow-sm ring-1 ring-white/25 backdrop-blur-md'
                        : 'text-emerald-50/80 hover:bg-white/10 hover:text-white'"
                >
                    <span
                        class="flex h-8 w-8 items-center justify-center rounded-lg transition"
                        :class="route.path === item.href ? 'bg-emerald-400 text-[#0f3d2e]' : 'bg-white/10 text-emerald-100 group-hover:bg-white/15'"
                    >
                        <component :is="item.icon" :size="16" />
                    </span>
                    <span>{{ item.title }}</span>
                </router-link>
            </nav>

            <div class="relative p-4 border-t border-white/15 space-y-3">
                <router-link
                    to="/profile"
                    class="flex items-center gap-3 rounded-xl bg-white/10 hover:bg-white/15 ring-1 ring-white/15 px-3 py-2.5 transition backdrop-blur-md"
                >
                    <div class="h-9 w-9 rounded-full overflow-hidden bg-emerald-500/80 flex items-center justify-center font-bold text-sm text-white uppercase ring-2 ring-white/30 shrink-0">
                        <img v-if="avatarUrl" :src="avatarUrl" alt="" class="h-full w-full object-cover" />
                        <span v-else>{{ userName.charAt(0) }}</span>
                    </div>
                    <div class="overflow-hidden min-w-0">
                        <p class="text-xs font-bold leading-none truncate text-white">{{ userName }}</p>
                        <p class="text-[10px] text-emerald-100/90 capitalize mt-1.5 truncate">{{ roleLabel }}</p>
                    </div>
                </router-link>

                <div class="flex items-center gap-2">
                    <button
                        type="button"
                        @click="toggleDarkMode"
                        class="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-white/10 hover:bg-white/15 ring-1 ring-white/10 transition text-emerald-50 text-[11px] font-semibold"
                        title="Toggle dark mode"
                    >
                        <Sun v-if="isDark" :size="14" />
                        <Moon v-else :size="14" />
                        Theme
                    </button>
                    <button
                        type="button"
                        @click="handleLogout"
                        class="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-red-500/25 hover:bg-red-500/40 ring-1 ring-red-300/20 text-red-50 hover:text-white transition text-[11px] font-semibold"
                    >
                        <LogOut :size="14" />
                        Sign Out
                    </button>
                </div>
            </div>
        </aside>

        <!-- Main -->
        <div class="flex-1 flex flex-col min-w-0 relative z-10">
            <header class="ims-header-glass h-[4.25rem] px-4 md:px-7 flex items-center justify-between z-30 sticky top-0">
                <div class="flex items-center gap-3 min-w-0">
                    <button
                        type="button"
                        @click="isMobileOpen = true"
                        class="lg:hidden p-2 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-white/40 dark:hover:bg-white/10 rounded-lg transition"
                    >
                        <Menu :size="20" />
                    </button>

                    <nav class="flex items-center gap-1.5 text-xs md:text-sm text-gray-500 dark:text-gray-400 font-medium min-w-0">
                        <span class="hidden sm:inline text-emerald-800/80 dark:text-emerald-400/90 font-semibold shrink-0">Apex</span>
                        <template v-for="(crumb, idx) in breadcrumbs" :key="idx">
                            <ChevronRight :size="12" class="text-gray-300 dark:text-gray-600 shrink-0" />
                            <router-link
                                v-if="crumb.href"
                                :to="crumb.href"
                                class="hover:text-emerald-700 dark:hover:text-emerald-400 truncate"
                            >
                                {{ crumb.title }}
                            </router-link>
                            <span v-else class="text-gray-900 dark:text-gray-100 font-semibold truncate">{{ crumb.title }}</span>
                        </template>
                    </nav>
                </div>

                <div class="flex items-center gap-3 shrink-0">
                    <div class="hidden md:flex flex-col items-end">
                        <p class="text-[11px] font-semibold text-gray-700 dark:text-gray-200">{{ todayLabel }}</p>
                        <p class="text-[10px] text-emerald-700 dark:text-emerald-400 capitalize">{{ roleLabel }} session</p>
                    </div>
                    <router-link
                        to="/profile"
                        class="h-9 w-9 rounded-full overflow-hidden bg-gradient-to-br from-emerald-500 to-emerald-800 flex items-center justify-center font-bold text-sm text-white uppercase shadow-md shadow-emerald-900/20 ring-2 ring-white/50 dark:ring-white/15"
                    >
                        <img v-if="avatarUrl" :src="avatarUrl" alt="" class="h-full w-full object-cover" />
                        <span v-else>{{ userName.charAt(0) }}</span>
                    </router-link>
                </div>
            </header>

            <main class="flex-1 overflow-auto p-4 md:p-6 lg:p-8 bg-transparent">
                <slot />
            </main>
        </div>

        <!-- Mobile drawer -->
        <div v-if="isMobileOpen" class="fixed inset-0 z-50 flex lg:hidden">
            <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" @click="isMobileOpen = false" />
            <aside class="ims-sidebar-glass relative flex flex-col w-72 text-white h-full z-10 shadow-2xl">
                <button
                    type="button"
                    class="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-lg text-emerald-200"
                    @click="isMobileOpen = false"
                >
                    <X :size="18" />
                </button>

                <div class="h-16 flex items-center gap-3 border-b border-white/10 px-5">
                    <img src="/images/brand/logo.jpg" alt="Duque" class="h-9 w-9 rounded-full object-cover ring-2 ring-emerald-400/40" />
                    <span class="font-bold text-sm truncate">{{ userCompany }}</span>
                </div>

                <nav class="flex-1 space-y-1 p-3 overflow-y-auto" @click="isMobileOpen = false">
                    <router-link
                        v-for="item in navItems"
                        :key="item.href"
                        :to="item.href"
                        class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition"
                        :class="route.path === item.href
                            ? 'bg-white/15 text-white'
                            : 'text-emerald-100/80 hover:bg-white/10'"
                    >
                        <component :is="item.icon" :size="18" />
                        <span>{{ item.title }}</span>
                    </router-link>
                </nav>

                <div class="p-4 border-t border-white/10 space-y-3">
                    <router-link to="/profile" class="flex items-center gap-3" @click="isMobileOpen = false">
                        <div class="h-9 w-9 rounded-full overflow-hidden bg-emerald-600 flex items-center justify-center font-bold text-white">
                            <img v-if="avatarUrl" :src="avatarUrl" alt="" class="h-full w-full object-cover" />
                            <span v-else>{{ userName.charAt(0) }}</span>
                        </div>
                        <div>
                            <p class="text-xs font-bold text-white truncate w-40">{{ userName }}</p>
                            <p class="text-[10px] text-emerald-300 capitalize mt-1">{{ roleLabel }}</p>
                        </div>
                    </router-link>
                    <div class="flex gap-2">
                        <button type="button" class="flex-1 py-2 rounded-lg bg-white/5 text-xs font-semibold" @click="toggleDarkMode">
                            <Sun v-if="isDark" :size="14" class="inline" />
                            <Moon v-else :size="14" class="inline" />
                        </button>
                        <button type="button" class="flex-1 py-2 rounded-lg bg-red-500/20 text-red-100 text-xs font-bold flex items-center justify-center gap-1" @click="handleLogout">
                            <LogOut :size="14" /> Sign Out
                        </button>
                    </div>
                </div>
            </aside>
        </div>
    </div>
</template>

<style scoped>
.ims-app-shell {
    background:
        radial-gradient(ellipse 70% 45% at 100% -5%, rgba(4, 120, 87, 0.22), transparent 55%),
        radial-gradient(ellipse 55% 35% at 0% 100%, rgba(180, 120, 40, 0.12), transparent 50%),
        linear-gradient(180deg, #dce8e1 0%, #e4ebe7 42%, #d5e2db 100%);
}
:global(.dark) .ims-app-shell {
    background:
        radial-gradient(ellipse 70% 45% at 100% -5%, rgba(4, 120, 87, 0.2), transparent 55%),
        radial-gradient(ellipse 55% 35% at 0% 100%, rgba(180, 120, 40, 0.1), transparent 50%),
        linear-gradient(180deg, #020617 0%, #071410 50%, #04120c 100%);
}
.ims-sidebar-glass {
    background:
        linear-gradient(165deg, rgba(8, 42, 32, 0.94) 0%, rgba(4, 64, 48, 0.88) 55%, rgba(8, 42, 32, 0.96) 100%);
    backdrop-filter: blur(22px) saturate(1.4);
    -webkit-backdrop-filter: blur(22px) saturate(1.4);
    border-right: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 8px 0 32px -16px rgba(0, 0, 0, 0.35);
}
.ims-header-glass {
    border-bottom: 1px solid rgba(255, 255, 255, 0.45);
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0.48));
    backdrop-filter: blur(16px) saturate(1.3);
    -webkit-backdrop-filter: blur(16px) saturate(1.3);
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.5) inset;
}
:global(.dark) .ims-header-glass {
    border-bottom-color: rgba(255, 255, 255, 0.08);
    background:
        linear-gradient(180deg, rgba(17, 24, 39, 0.82), rgba(17, 24, 39, 0.62));
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04) inset;
}
@media (prefers-reduced-motion: reduce) {
    .ims-sidebar-glass,
    .ims-header-glass {
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
    }
}
</style>
