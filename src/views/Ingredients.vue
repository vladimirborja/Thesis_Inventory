<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import AppLayout from '@/layouts/AppLayout.vue';
import { 
    Search, Plus, Edit, Trash2, X, AlertTriangle, Scale, ClipboardList
} from 'lucide-vue-next';
import type { Ingredient } from '@/types';
import { api } from '@/lib/api';

const authStore = useAuthStore();
const currentRole = computed(() => authStore.currentUser?.role || 'employee');
const isAdmin = computed(() => currentRole.value === 'admin' || currentRole.value === 'super_admin');

const ingredients = ref<Ingredient[]>([]);
const isLoading = ref(false);
const isSaving = ref(false);
const searchQuery = ref('');

// Modal Dialog state
const isModalOpen = ref(false);
const isEditMode = ref(false);
const currentEditId = ref<number | null>(null);

// Form state
const formName = ref('');
const formQuantity = ref(0);
const formUnit = ref('kg');
const formMinStock = ref(10);
const formDesc = ref('');

const filteredIngredients = computed(() => {
    const q = searchQuery.value.toLowerCase();
    if (!q) return ingredients.value;
    return ingredients.value.filter(i => 
        i.name.toLowerCase().includes(q) || 
        (i.description && i.description.toLowerCase().includes(q))
    );
});

async function loadIngredients() {
    isLoading.value = true;
    try {
        ingredients.value = await api.get<Ingredient[]>('/ingredients');
    } finally {
        isLoading.value = false;
    }
}

onMounted(loadIngredients);

function openAddModal() {
    isEditMode.value = false;
    currentEditId.value = null;
    formName.value = '';
    formQuantity.value = 0;
    formUnit.value = 'kg';
    formMinStock.value = 10;
    formDesc.value = '';
    isModalOpen.value = true;
}

function openEditModal(ingredient: Ingredient) {
    isEditMode.value = true;
    currentEditId.value = ingredient.id;
    formName.value = ingredient.name;
    formQuantity.value = ingredient.quantity;
    formUnit.value = ingredient.unit || 'kg';
    formMinStock.value = ingredient.minStockLevel;
    formDesc.value = ingredient.description || '';
    isModalOpen.value = true;
}

async function handleSave() {
    if (!formName.value) return;
    isSaving.value = true;
    const payload = {
        name: formName.value,
        quantity: formQuantity.value,
        unit: formUnit.value,
        min_stock_level: formMinStock.value,
        description: formDesc.value
    };
    try {
        if (isEditMode.value && currentEditId.value !== null) {
            await api.put(`/ingredients/${currentEditId.value}`, payload);
        } else {
            await api.post('/ingredients', payload);
        }
        await loadIngredients();
        isModalOpen.value = false;
    } catch (e: unknown) {
        alert(e instanceof Error ? e.message : 'Error saving ingredient');
    } finally {
        isSaving.value = false;
    }
}

async function handleDelete(id: number) {
    if (!confirm('Are you sure you want to delete this ingredient?')) return;
    try {
        await api.delete(`/ingredients/${id}`);
        await loadIngredients();
    } catch (e: unknown) {
        alert(e instanceof Error ? e.message : 'Error deleting ingredient');
    }
}
</script>

<template>
    <AppLayout>
        <div class="space-y-6">
            <!-- Header section -->
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h2 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">Ingredients Inventory</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400">Track and monitor raw ingredients, stock levels, and units used in recipe items.</p>
                </div>
                <button 
                    @click="openAddModal"
                    class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-600/10 transition shrink-0"
                >
                    <Plus :size="16" />
                    Add Ingredient
                </button>
            </div>

            <!-- Toolbar -->
            <div class="p-4 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
                <div class="relative flex-1 max-w-md">
                    <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
                        <Search :size="16" />
                    </span>
                    <input 
                        v-model="searchQuery"
                        type="text"
                        class="w-full pl-9 pr-4 py-2 rounded-xl border border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                        placeholder="Search ingredients..."
                    />
                </div>
            </div>

            <!-- Table -->
            <div class="admin-table-wrap overflow-x-auto bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
                <table class="w-full text-left border-collapse text-xs md:text-sm">
                    <thead class="bg-gray-50 dark:bg-gray-800/80 text-gray-400 dark:text-gray-300 border-b border-gray-100 dark:border-gray-800 uppercase text-[10px] tracking-wider font-bold">
                        <tr>
                            <th class="px-6 py-4">Ingredient Name</th>
                            <th class="px-6 py-4">Available Quantity</th>
                            <th class="px-6 py-4">Alert Threshold</th>
                            <th class="px-6 py-4">Status</th>
                            <th class="px-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-50 dark:divide-gray-800/50">
                        <tr v-if="filteredIngredients.length === 0">
                            <td colspan="5" class="px-6 py-12 text-center text-gray-400">
                                No ingredients found matching the filter.
                            </td>
                        </tr>
                        <tr v-for="i in filteredIngredients" :key="i.id" class="hover:bg-gray-50/50 dark:hover:bg-gray-850 transition">
                            <td class="px-6 py-4">
                                <div class="flex items-center gap-3">
                                    <div class="h-8 w-8 rounded-full bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center font-bold text-emerald-700 dark:text-emerald-300 uppercase">
                                        <Scale :size="14" />
                                    </div>
                                    <div>
                                        <p class="font-bold text-gray-900 dark:text-white text-xs md:text-sm">{{ i.name }}</p>
                                        <p class="text-[10px] text-gray-400 mt-0.5" v-if="i.description">{{ i.description }}</p>
                                    </div>
                                </div>
                            </td>
                            <td class="px-6 py-4 text-xs font-semibold text-gray-700 dark:text-gray-300">
                                {{ i.quantity }} {{ i.unit || 'kg' }}
                            </td>
                            <td class="px-6 py-4 text-xs text-gray-500">
                                {{ i.minStockLevel }} {{ i.unit || 'kg' }}
                            </td>
                            <td class="px-6 py-4">
                                <span class="px-2.5 py-1 text-[9px] font-bold rounded-full uppercase tracking-wider inline-flex items-center gap-1"
                                    :class="i.quantity <= i.minStockLevel ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-400' : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400'">
                                    <AlertTriangle v-if="i.quantity <= i.minStockLevel" :size="10" />
                                    {{ i.quantity <= i.minStockLevel ? 'Low Stock' : 'Good' }}
                                </span>
                            </td>
                            <td class="px-6 py-4 text-right">
                                <div class="flex items-center justify-end gap-2">
                                    <button 
                                        @click="openEditModal(i)"
                                        class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition text-gray-500 hover:text-emerald-600"
                                        title="Edit Ingredient"
                                    >
                                        <Edit :size="15" />
                                    </button>
                                    <button 
                                        v-if="isAdmin"
                                        @click="handleDelete(i.id)"
                                        class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition text-gray-500 hover:text-red-500"
                                        title="Delete Ingredient"
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
                <div @click="isModalOpen = false" class="fixed inset-0 bg-black/40 backdrop-blur-xs"></div>

                <div class="relative bg-white dark:bg-gray-900 rounded-3xl w-full max-w-md p-6 md:p-8 shadow-2xl border border-gray-100 dark:border-gray-800 space-y-6">
                    <button @click="isModalOpen = false" class="absolute top-4 right-4 p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-400">
                        <X :size="18" />
                    </button>

                    <div>
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white">{{ isEditMode ? 'Edit Ingredient' : 'Add New Ingredient' }}</h3>
                        <p class="text-xs text-gray-400 mt-1">Specify name, quantities and unit descriptors.</p>
                    </div>

                    <form @submit.prevent="handleSave" class="space-y-4">
                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Ingredient Name</label>
                            <input 
                                v-model="formName" 
                                type="text"
                                class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                placeholder="e.g. Chilli Powder"
                                required
                            />
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Initial Quantity</label>
                                <input 
                                    v-model.number="formQuantity" 
                                    type="number"
                                    step="0.001"
                                    class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                    required
                                />
                            </div>
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Unit (e.g. kg, L)</label>
                                <input 
                                    v-model="formUnit" 
                                    type="text"
                                    class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                    required
                                />
                            </div>
                        </div>

                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Safety Alert Threshold</label>
                            <input 
                                v-model.number="formMinStock" 
                                type="number"
                                step="0.001"
                                class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                required
                            />
                        </div>

                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Description</label>
                            <textarea 
                                v-model="formDesc" 
                                class="w-full px-4 py-2 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30 h-20"
                                placeholder="Details..."
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
                                :disabled="isSaving"
                                class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl"
                            >
                                Save Ingredient
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
