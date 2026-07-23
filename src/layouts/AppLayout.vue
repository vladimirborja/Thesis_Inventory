<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { 
    LayoutDashboard, Users, Package, Store, History, LogOut, Menu, X, Sun, Moon, User, ChevronRight, Package2, ChefHat, Receipt
} from 'lucide-vue-next';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const isMobileOpen = ref(false);
const isDark = ref(false);

const currentUser = computed(() => authStore.currentUser);
const currentRole = computed(() => currentUser.value?.role || 'employee');
const userName = computed(() => currentUser.value?.name || 'User');
const userEmail = computed(() => currentUser.value?.email || 'user@company.com');
const userCompany = computed(() => currentUser.value?.companyName || 'Apex Food Processing Corp');

// Computed list of paths for Breadcrumbs
const breadcrumbs = computed(() => {
    const path = route.path;
    if (path === '/dashboard') return [{ title: 'Dashboard' }];
    if (path === '/inventory') return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Inventory' }];
    if (path === '/ingredients') return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Ingredients' }];
    if (path === '/sales') return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Sales Ledger' }];
    if (path === '/suppliers') return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Suppliers' }];
    if (path === '/transactions') return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Stock Transactions' }];
    if (path === '/users') return [{ title: 'Dashboard', href: '/dashboard' }, { title: 'User Management' }];
    return [{ title: 'System' }];
});

const navItems = computed(() => {
    const items = [
        { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    ];

    if (currentRole.value === 'super_admin') {
        items.push(
            { title: 'User Management', href: '/users', icon: Users },
            { title: 'System Audit Logs', href: '/transactions', icon: History }
        );
    } else {
        items.push(
            { title: 'Inventory Catalog', href: '/inventory', icon: Package },
            { title: 'Ingredients Inventory', href: '/ingredients', icon: ChefHat },
            { title: 'Sales & POS', href: '/sales', icon: Receipt },
            { title: 'Supplier Registry', href: '/suppliers', icon: Store },
            { title: 'Stock Transactions', href: '/transactions', icon: History }
        );
    }

    return items;
});

function handleLogout() {
    authStore.logout();
    router.push('/');
}

function toggleDarkMode() {
    isDark.value = !isDark.value;
    if (isDark.value) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
}

onMounted(() => {
    // Initial check
    if (document.documentElement.classList.contains('dark')) {
        isDark.value = true;
    }
});
</script>

<template>
    <div class="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 flex font-sans">
        <!-- Desktop Sidebar (Fixed) -->
        <aside class="hidden lg:flex flex-col w-64 border-r border-gray-200 dark:border-gray-800 bg-emerald-900 text-white shrink-0">
            <!-- Sidebar Header -->
            <div class="h-16 flex items-center gap-3 border-b border-emerald-800 px-6">
                <div class="h-9 w-9 bg-emerald-700 rounded-lg flex items-center justify-center">
                    <Package2 :size="20" />
                </div>
                <div>
                    <h2 class="text-sm font-bold leading-tight truncate w-40">{{ userCompany }}</h2>
                    <p class="text-[10px] text-emerald-300 font-medium">IMS Core Control</p>
                </div>
            </div>

            <!-- Navigation Links -->
            <nav class="flex-1 space-y-1.5 p-4 overflow-y-auto">
                <router-link 
                    v-for="item in navItems" 
                    :key="item.href"
                    :to="item.href"
                    class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition"
                    :class="route.path === item.href 
                        ? 'bg-emerald-800 text-white font-bold' 
                        : 'text-emerald-100/80 hover:bg-emerald-800/40 hover:text-white'"
                >
                    <component :is="item.icon" :size="18" class="shrink-0" />
                    <span>{{ item.title }}</span>
                </router-link>
            </nav>

            <!-- Sidebar Footer User Panel -->
            <div class="p-4 border-t border-emerald-800 space-y-3">
                <div class="flex items-center gap-3">
                    <div class="h-9 w-9 rounded-full bg-emerald-800 border border-emerald-700/50 flex items-center justify-center font-bold text-sm text-emerald-200 uppercase">
                        {{ userName.charAt(0) }}
                    </div>
                    <div class="overflow-hidden">
                        <p class="text-xs font-bold leading-none truncate text-white">{{ userName }}</p>
                        <p class="text-[10px] text-emerald-300 capitalize mt-1">{{ currentRole.replace('_', ' ') }}</p>
                    </div>
                </div>
                
                <!-- Extra Tools -->
                <div class="flex items-center justify-between gap-2 border-t border-emerald-800/50 pt-3">
                    <button 
                        @click="toggleDarkMode" 
                        class="p-2 hover:bg-emerald-800 rounded-lg transition text-emerald-200"
                        title="Toggle dark mode"
                    >
                        <Sun v-if="isDark" :size="16" />
                        <Moon v-else :size="16" />
                    </button>
                    <button 
                        @click="handleLogout"
                        class="flex items-center gap-1.5 px-2.5 py-1.5 hover:bg-red-800 text-red-100 hover:text-white rounded-lg transition text-xs font-semibold"
                    >
                        <LogOut :size="14" />
                        Sign Out
                    </button>
                </div>
            </div>
        </aside>

        <!-- Main Workspace (Varying on sidebar size) -->
        <div class="flex-1 flex flex-col min-w-0">
            <!-- Topbar Header -->
            <header class="h-16 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 px-4 md:px-6 flex items-center justify-between z-30">
                <!-- Left: Sidebar trigger & Breadcrumbs -->
                <div class="flex items-center gap-4">
                    <button 
                        @click="isMobileOpen = true"
                        class="lg:hidden p-2 text-gray-500 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
                    >
                        <Menu :size="20" />
                    </button>

                    <!-- Breadcrumbs -->
                    <nav class="flex items-center gap-2 text-xs md:text-sm text-gray-400 font-medium">
                        <div class="flex items-center gap-1.5">
                            <span class="hover:text-gray-600 dark:hover:text-gray-300">Apex System</span>
                        </div>
                        <template v-for="(crumb, idx) in breadcrumbs" :key="idx">
                            <ChevronRight :size="12" class="text-gray-300 shrink-0" />
                            <router-link 
                                v-if="crumb.href" 
                                :to="crumb.href" 
                                class="hover:text-gray-600 dark:hover:text-gray-300"
                            >
                                {{ crumb.title }}
                            </router-link>
                            <span v-else class="text-gray-950 dark:text-gray-100 font-semibold">{{ crumb.title }}</span>
                        </template>
                    </nav>
                </div>

                <!-- Right Menu: Company context label -->
                <div class="flex items-center gap-3">
                    <div class="hidden sm:block text-right">
                        <p class="text-xs font-bold">{{ userName }}</p>
                        <p class="text-[10px] text-gray-400 capitalize mt-0.5">{{ currentRole.replace('_', ' ') }}</p>
                    </div>
                    <div class="h-8 w-8 rounded-full bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center font-bold text-sm text-emerald-700 dark:text-emerald-300 uppercase">
                        {{ userName.charAt(0) }}
                    </div>
                </div>
            </header>

            <!-- Internal Viewport Area -->
            <main class="flex-1 overflow-auto p-4 md:p-6 lg:p-8">
                <slot />
            </main>
        </div>

        <!-- Mobile Sidebar Drawer (Overlay) -->
        <div v-if="isMobileOpen" class="fixed inset-0 z-50 flex lg:hidden">
            <!-- Backdrop -->
            <div @click="isMobileOpen = false" class="fixed inset-0 bg-black/40 backdrop-blur-xs"></div>

            <!-- Drawer Container -->
            <aside class="relative flex flex-col w-64 bg-emerald-900 text-white h-full z-10 transition-transform">
                <!-- Close Button -->
                <button 
                    @click="isMobileOpen = false" 
                    class="absolute top-4 right-4 p-2 hover:bg-emerald-800 rounded-lg text-emerald-200"
                >
                    <X :size="18" />
                </button>

                <!-- Header -->
                <div class="h-16 flex items-center gap-3 border-b border-emerald-800 px-6">
                    <div class="h-8 w-8 bg-emerald-700 rounded-lg flex items-center justify-center">
                        <Package2 :size="18" />
                    </div>
                    <span class="font-bold text-sm truncate w-36">{{ userCompany }}</span>
                </div>

                <!-- Nav Links -->
                <nav class="flex-1 space-y-1.5 p-4 overflow-y-auto" @click="isMobileOpen = false">
                    <router-link 
                        v-for="item in navItems" 
                        :key="item.href"
                        :to="item.href"
                        class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition"
                        :class="route.path === item.href 
                            ? 'bg-emerald-800 text-white font-bold' 
                            : 'text-emerald-100/80 hover:bg-emerald-800/40 hover:text-white'"
                    >
                        <component :is="item.icon" :size="18" class="shrink-0" />
                        <span>{{ item.title }}</span>
                    </router-link>
                </nav>

                <!-- Footer panel -->
                <div class="p-4 border-t border-emerald-800 space-y-4">
                    <div class="flex items-center gap-3">
                        <div class="h-9 w-9 rounded-full bg-emerald-800 flex items-center justify-center font-bold text-emerald-200">
                            {{ userName.charAt(0) }}
                        </div>
                        <div>
                            <p class="text-xs font-bold leading-none text-white truncate w-36">{{ userName }}</p>
                            <p class="text-[10px] text-emerald-300 capitalize mt-1">{{ currentRole.replace('_', ' ') }}</p>
                        </div>
                    </div>
                    
                    <div class="flex items-center justify-between gap-2 pt-2 border-t border-emerald-800/50">
                        <button 
                            @click="toggleDarkMode" 
                            class="p-2 hover:bg-emerald-800 rounded-lg transition"
                        >
                            <Sun v-if="isDark" :size="16" />
                            <Moon v-else :size="16" />
                        </button>
                        <button 
                            @click="handleLogout"
                            class="flex items-center gap-1.5 px-3 py-1.5 hover:bg-red-800 text-red-100 hover:text-white rounded-lg transition text-xs font-bold"
                        >
                            <LogOut :size="14" />
                            Sign Out
                        </button>
                    </div>
                </div>
            </aside>
        </div>
    </div>
</template>
