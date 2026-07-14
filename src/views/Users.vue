<script setup lang="ts">
import { computed, ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import AppLayout from '@/layouts/AppLayout.vue';
import { 
    Search, Plus, Edit, Trash2, X, Shield, User, Briefcase
} from 'lucide-vue-next';
import type { User as UserType, UserRole } from '@/types';

const authStore = useAuthStore();

const searchQuery = ref('');

// Modal state
const isModalOpen = ref(false);
const isEditMode = ref(false);
const currentEditId = ref<number | null>(null);

// Form state
const formName = ref('');
const formEmail = ref('');
const formRole = ref<UserRole>('employee');
const formCompany = ref('Apex Food Processing Corp');

const filteredUsers = computed(() => {
    return authStore.users.filter(u => {
        return u.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
               u.email.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
               u.role.toLowerCase().includes(searchQuery.value.toLowerCase());
    });
});

function openAddModal() {
    isEditMode.value = false;
    currentEditId.value = null;
    formName.value = '';
    formEmail.value = '';
    formRole.value = 'employee';
    formCompany.value = 'Apex Food Processing Corp';
    isModalOpen.value = true;
}

function openEditModal(user: UserType) {
    isEditMode.value = true;
    currentEditId.value = user.id;
    formName.value = user.name;
    formEmail.value = user.email;
    formRole.value = user.role;
    formCompany.value = user.companyName || 'Apex Food Processing Corp';
    isModalOpen.value = true;
}

function handleSave() {
    if (!formName.value || !formEmail.value) return;

    if (isEditMode.value && currentEditId.value !== null) {
        const idx = authStore.users.findIndex(u => u.id === currentEditId.value);
        if (idx !== -1) {
            const existing = authStore.users[idx]!;
            authStore.users[idx] = {
                id: existing.id,
                name: formName.value,
                email: formEmail.value,
                role: formRole.value,
                companyName: formCompany.value
            };
        }
    } else {
        const newUser: UserType = {
            id: Date.now(),
            name: formName.value,
            email: formEmail.value,
            role: formRole.value,
            companyName: formCompany.value
        };
        authStore.users.unshift(newUser);
    }
    isModalOpen.value = false;
}

function handleDelete(id: number) {
    if (authStore.currentUser?.id === id) {
        alert('You cannot delete your own session!');
        return;
    }
    if (confirm('Are you sure you want to remove this user from the directory?')) {
        authStore.users = authStore.users.filter(u => u.id !== id);
    }
}
</script>

<template>
    <AppLayout>
        <div class="space-y-6">
            <!-- Header section -->
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h2 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">User Directory</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400">Manage internal operator accounts, administrator roles, and permissions catalog.</p>
                </div>
                <button 
                    @click="openAddModal"
                    class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-600/10 transition shrink-0"
                >
                    <Plus :size="16" />
                    Provision User
                </button>
            </div>

            <!-- Toolbar -->
            <div class="p-4 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
                <!-- Search bar -->
                <div class="relative flex-1 max-w-md">
                    <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
                        <Search :size="16" />
                    </span>
                    <input 
                        v-model="searchQuery"
                        type="text"
                        class="w-full pl-9 pr-4 py-2 rounded-xl border border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                        placeholder="Search users name, email, role..."
                    />
                </div>
            </div>

            <!-- Table -->
            <div class="admin-table-wrap overflow-x-auto bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
                <table class="w-full text-left border-collapse text-xs md:text-sm">
                    <thead class="bg-gray-50 dark:bg-gray-800/80 text-gray-400 dark:text-gray-300 border-b border-gray-100 dark:border-gray-800 uppercase text-[10px] tracking-wider font-bold">
                        <tr>
                            <th class="px-6 py-4">Identity Details</th>
                            <th class="px-6 py-4">Corporate Email</th>
                            <th class="px-6 py-4">Security Role</th>
                            <th class="px-6 py-4">Associated Company</th>
                            <th class="px-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-50 dark:divide-gray-800/50">
                        <tr v-if="filteredUsers.length === 0">
                            <td colspan="5" class="px-6 py-12 text-center text-gray-400">
                                No user profiles match the active directories.
                            </td>
                        </tr>
                        <tr v-for="u in filteredUsers" :key="u.id" class="hover:bg-gray-50/50 dark:hover:bg-gray-850 transition">
                            <td class="px-6 py-4">
                                <div class="flex items-center gap-3">
                                    <div class="h-8 w-8 rounded-full bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center font-bold text-emerald-700 dark:text-emerald-300 uppercase">
                                        {{ u.name.charAt(0) }}
                                    </div>
                                    <div>
                                        <p class="font-bold text-gray-900 dark:text-white text-xs md:text-sm">{{ u.name }}</p>
                                        <p class="text-[10px] text-gray-400 mt-0.5">UID: {{ u.id }}</p>
                                    </div>
                                </div>
                            </td>
                            <td class="px-6 py-4 text-xs font-semibold text-gray-600 dark:text-gray-400">
                                {{ u.email }}
                            </td>
                            <td class="px-6 py-4">
                                <span class="px-2.5 py-1 text-[9px] font-bold rounded-full uppercase tracking-wider inline-flex items-center gap-1"
                                    :class="u.role === 'super_admin' ? 'bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400' : u.role === 'admin' ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/20 dark:text-blue-400' : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'">
                                    <Shield v-if="u.role === 'super_admin'" :size="10" />
                                    <Briefcase v-else-if="u.role === 'admin'" :size="10" />
                                    <User v-else :size="10" />
                                    {{ u.role.replace('_', ' ') }}
                                </span>
                            </td>
                            <td class="px-6 py-4 text-xs text-gray-500">
                                {{ u.companyName || 'Apex Food Processing Corp' }}
                            </td>
                            <td class="px-6 py-4 text-right">
                                <div class="flex items-center justify-end gap-2">
                                    <button 
                                        @click="openEditModal(u)"
                                        class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition text-gray-500 hover:text-emerald-600"
                                        title="Edit User Role"
                                    >
                                        <Edit :size="15" />
                                    </button>
                                    <button 
                                        @click="handleDelete(u.id)"
                                        class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition text-gray-500 hover:text-red-500"
                                        title="Revoke Access"
                                    >
                                        <Trash2 :size="15" />
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- MODAL FORM DIALOG -->
            <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center px-4">
                <!-- Backdrop -->
                <div @click="isModalOpen = false" class="fixed inset-0 bg-black/40 backdrop-blur-xs"></div>

                <!-- Modal box -->
                <div class="relative bg-white dark:bg-gray-900 rounded-3xl w-full max-w-md p-6 md:p-8 shadow-2xl border border-gray-100 dark:border-gray-800 space-y-6">
                    <button @click="isModalOpen = false" class="absolute top-4 right-4 p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-400">
                        <X :size="18" />
                    </button>

                    <div>
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white">{{ isEditMode ? 'Edit User Credentials' : 'Provision New System User' }}</h3>
                        <p class="text-xs text-gray-400 mt-1">Specify role clearance level and associate organization.</p>
                    </div>

                    <form @submit.prevent="handleSave" class="space-y-4">
                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Full Name</label>
                            <input 
                                v-model="formName" 
                                type="text"
                                class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none"
                                placeholder="Enter full name"
                                required
                            />
                        </div>

                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Email Address</label>
                            <input 
                                v-model="formEmail" 
                                type="email"
                                class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none"
                                placeholder="name@company.com"
                                required
                            />
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">System Role Clearance</label>
                                <select 
                                    v-model="formRole"
                                    class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-950 text-sm focus:outline-none"
                                    required
                                >
                                    <option value="employee">Employee</option>
                                    <option value="admin">Admin</option>
                                    <option value="super_admin">Super Admin</option>
                                </select>
                            </div>
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Associated Company</label>
                                <input 
                                    v-model="formCompany" 
                                    type="text"
                                    class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none"
                                    required
                                />
                            </div>
                        </div>

                        <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-100 dark:border-gray-800">
                            <button 
                                type="button" 
                                @click="isModalOpen = false" 
                                class="px-4 py-2.5 border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 text-xs font-semibold rounded-xl hover:bg-gray-50"
                            >
                                Cancel
                            </button>
                            <button 
                                type="submit" 
                                class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl"
                            >
                                Save User
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
