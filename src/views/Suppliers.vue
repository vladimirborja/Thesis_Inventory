<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import AppLayout from '@/layouts/AppLayout.vue';
import { 
    Search, Plus, Edit, Trash2, X, Store, Mail, Phone, MapPin, RefreshCw
} from 'lucide-vue-next';
import type { Supplier } from '@/types';
import { api } from '@/lib/api';

const authStore = useAuthStore();

const currentRole = computed(() => authStore.currentUser?.role || 'employee');
const isAdmin = computed(() => currentRole.value === 'admin' || currentRole.value === 'super_admin');

const suppliers    = ref<Supplier[]>([]);
const isLoading    = ref(false);
const isSaving     = ref(false);
const searchQuery  = ref('');

// Modal state
const isModalOpen   = ref(false);
const isEditMode    = ref(false);
const currentEditId = ref<number | null>(null);

// Form state
const formName    = ref('');
const formContact = ref('');
const formEmail   = ref('');
const formPhone   = ref('');
const formAddress = ref('');

const filteredSuppliers = computed(() => {
    const q = searchQuery.value.toLowerCase();
    if (!q) return suppliers.value;
    return suppliers.value.filter(s =>
        s.name.toLowerCase().includes(q) ||
        (s.contactName && s.contactName.toLowerCase().includes(q)) ||
        (s.email && s.email.toLowerCase().includes(q))
    );
});

async function loadSuppliers() {
    isLoading.value = true;
    try {
        suppliers.value = await api.get<Supplier[]>('/suppliers');
    } finally {
        isLoading.value = false;
    }
}

onMounted(loadSuppliers);

function openAddModal() {
    isEditMode.value = false;
    currentEditId.value = null;
    formName.value = formContact.value = formEmail.value = formPhone.value = formAddress.value = '';
    isModalOpen.value = true;
}

function openEditModal(supplier: Supplier) {
    isEditMode.value    = true;
    currentEditId.value = supplier.id;
    formName.value      = supplier.name;
    formContact.value   = supplier.contactName || '';
    formEmail.value     = supplier.email || '';
    formPhone.value     = supplier.phone || '';
    formAddress.value   = supplier.address || '';
    isModalOpen.value   = true;
}

async function handleSave() {
    if (!formName.value) return;
    isSaving.value = true;
    const payload = {
        name: formName.value, contact_name: formContact.value,
        email: formEmail.value, phone: formPhone.value, address: formAddress.value,
    };
    try {
        if (isEditMode.value && currentEditId.value !== null) {
            await api.put(`/suppliers/${currentEditId.value}`, payload);
        } else {
            await api.post('/suppliers', payload);
        }
        await loadSuppliers();
        isModalOpen.value = false;
    } finally {
        isSaving.value = false;
    }
}

async function handleDelete(id: number) {
    if (!confirm('Are you sure you want to delete this supplier?')) return;
    await api.delete(`/suppliers/${id}`);
    await loadSuppliers();
}
</script>

<template>
    <AppLayout>
        <div class="space-y-6">
            <!-- Header section -->
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h2 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">Supplier Registry</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400">Maintain directory of accredited food ingredient and packaging supply partners.</p>
                </div>
                <button 
                    v-if="isAdmin"
                    @click="openAddModal"
                    class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-600/10 transition shrink-0"
                >
                    <Plus :size="16" />
                    Register Supplier
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
                        placeholder="Search supplier name, representative, email..."
                    />
                </div>
            </div>

            <!-- Grid Display -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div v-if="filteredSuppliers.length === 0" class="col-span-full py-12 text-center text-gray-400">
                    No suppliers match the active search queries.
                </div>
                <div 
                    v-for="s in filteredSuppliers" 
                    :key="s.id" 
                    class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex flex-col justify-between gap-4 group hover:border-emerald-250 transition"
                >
                    <div class="space-y-3">
                        <div class="flex items-center justify-between">
                            <div class="h-10 w-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-300 flex items-center justify-center">
                                <Store :size="20" />
                            </div>
                            <div v-if="isAdmin" class="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition duration-300">
                                <button 
                                    @click="openEditModal(s)"
                                    class="p-1.5 bg-gray-50 hover:bg-emerald-50 dark:bg-gray-800 dark:hover:bg-emerald-950/30 rounded text-gray-500 hover:text-emerald-600 transition"
                                >
                                    <Edit :size="13" />
                                </button>
                                <button 
                                    @click="handleDelete(s.id)"
                                    class="p-1.5 bg-gray-50 hover:bg-red-50 dark:bg-gray-800 dark:hover:bg-red-950/30 rounded text-gray-500 hover:text-red-500 transition"
                                >
                                    <Trash2 :size="13" />
                                </button>
                            </div>
                        </div>

                        <div>
                            <h4 class="font-bold text-gray-900 dark:text-white">{{ s.name }}</h4>
                            <p class="text-[10px] text-gray-400 dark:text-gray-500 mt-1" v-if="s.contactName">Rep: {{ s.contactName }}</p>
                        </div>

                        <div class="space-y-1.5 pt-2 border-t border-gray-50 dark:border-gray-800/80 text-xs text-gray-500 dark:text-gray-400">
                            <p class="flex items-center gap-2 truncate" v-if="s.email">
                                <Mail :size="14" class="text-gray-400 shrink-0" />
                                <span>{{ s.email }}</span>
                            </p>
                            <p class="flex items-center gap-2" v-if="s.phone">
                                <Phone :size="14" class="text-gray-400 shrink-0" />
                                <span>{{ s.phone }}</span>
                            </p>
                            <p class="flex items-start gap-2" v-if="s.address">
                                <MapPin :size="14" class="text-gray-400 shrink-0 mt-0.5" />
                                <span class="line-clamp-2 leading-relaxed">{{ s.address }}</span>
                            </p>
                        </div>
                    </div>
                </div>
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
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white">{{ isEditMode ? 'Edit Supplier Profile' : 'Register New Supplier' }}</h3>
                        <p class="text-xs text-gray-400 mt-1">Acquaint logistics team with supplier contact details.</p>
                    </div>

                    <form @submit.prevent="handleSave" class="space-y-4">
                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Supplier Name</label>
                            <input 
                                v-model="formName" 
                                type="text"
                                class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                placeholder="e.g. Agri-Grow Farms Inc."
                                required
                            />
                        </div>

                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Representative Name</label>
                            <input 
                                v-model="formContact" 
                                type="text"
                                class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                placeholder="e.g. Robert Vance"
                            />
                        </div>

                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Email Address</label>
                            <input 
                                v-model="formEmail" 
                                type="email"
                                class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                placeholder="e.g. vance@agrigrow.com"
                            />
                        </div>

                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Contact Number</label>
                            <input 
                                v-model="formPhone" 
                                type="text"
                                class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                placeholder="e.g. +63 905 123 4567"
                            />
                        </div>

                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">HQ Address</label>
                            <textarea 
                                v-model="formAddress" 
                                class="w-full px-4 py-2 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30 h-16"
                                placeholder="HQ location..."
                            ></textarea>
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
                                Save Profile
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
