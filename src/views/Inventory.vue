<script setup lang="ts">
import { computed, ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import AppLayout from '@/layouts/AppLayout.vue';
import { 
    Search, Plus, Filter, Edit, Trash2, PackageCheck, AlertTriangle, ShieldX, X, Tag
} from 'lucide-vue-next';
import { formatCurrency } from '@/composables/useFormatCurrency';
import type { Product } from '@/types';

const authStore = useAuthStore();

const currentRole = computed(() => authStore.currentUser?.role || 'employee');
const isAdmin = computed(() => currentRole.value === 'admin' || currentRole.value === 'super_admin');

// Search & Filter state
const searchQuery = ref('');
const selectedCategory = ref('');
const selectedStockStatus = ref('all'); // all, low, out, instock

// Modal Dialog state
const isModalOpen = ref(false);
const isEditMode = ref(false);
const currentEditId = ref<number | null>(null);

// Form state
const formName = ref('');
const formSku = ref('');
const formBarcode = ref('');
const formCategory = ref('');
const formCost = ref(0);
const formPrice = ref(0);
const formMinStock = ref(5);
const formQty = ref(0);
const formUom = ref('pcs');
const formDesc = ref('');

// Computed filtered products
const filteredProducts = computed(() => {
    return authStore.products.filter(p => {
        const matchesSearch = p.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
                             p.sku.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                             (p.barcode && p.barcode.includes(searchQuery.value));
        
        const matchesCategory = !selectedCategory.value || p.categoryName === selectedCategory.value;
        
        let matchesStatus = true;
        if (selectedStockStatus.value === 'low') {
            matchesStatus = p.quantity > 0 && p.quantity <= p.minStockLevel;
        } else if (selectedStockStatus.value === 'out') {
            matchesStatus = p.quantity === 0;
        } else if (selectedStockStatus.value === 'instock') {
            matchesStatus = p.quantity > p.minStockLevel;
        }

        return matchesSearch && matchesCategory && matchesStatus;
    });
});

function openAddModal() {
    isEditMode.value = false;
    currentEditId.value = null;
    formName.value = '';
    formSku.value = 'RM-' + Math.floor(1000 + Math.random() * 9000);
    formBarcode.value = '480' + Math.floor(100000000 + Math.random() * 900000000);
    formCategory.value = authStore.categories[0]?.name || '';
    formCost.value = 10;
    formPrice.value = 15;
    formMinStock.value = 10;
    formQty.value = 100;
    formUom.value = 'pcs';
    formDesc.value = '';
    
    isModalOpen.value = true;
}

function openEditModal(product: Product) {
    isEditMode.value = true;
    currentEditId.value = product.id;
    formName.value = product.name;
    formSku.value = product.sku;
    formBarcode.value = product.barcode || '';
    formCategory.value = product.categoryName || '';
    formCost.value = product.costPrice;
    formPrice.value = product.sellingPrice;
    formMinStock.value = product.minStockLevel;
    formQty.value = product.quantity;
    formUom.value = product.unitOfMeasure;
    formDesc.value = product.description || '';

    isModalOpen.value = true;
}

function handleSave() {
    if (!formName.value || !formSku.value) return;

    if (isEditMode.value && currentEditId.value !== null) {
        // Edit mode
        const idx = authStore.products.findIndex(p => p.id === currentEditId.value);
        if (idx !== -1) {
            const existing = authStore.products[idx]!;
            authStore.products[idx] = {
                id: existing.id,
                name: formName.value,
                sku: formSku.value,
                barcode: formBarcode.value,
                categoryId: existing.categoryId,
                categoryName: formCategory.value,
                costPrice: formCost.value,
                sellingPrice: formPrice.value,
                minStockLevel: formMinStock.value,
                quantity: existing.quantity,
                unitOfMeasure: formUom.value,
                description: formDesc.value
            };
        }
    } else {
        // Add mode
        const newProduct: Product = {
            id: Date.now(),
            name: formName.value,
            sku: formSku.value,
            barcode: formBarcode.value,
            categoryId: authStore.categories.find(c => c.name === formCategory.value)?.id || 1,
            categoryName: formCategory.value,
            costPrice: formCost.value,
            sellingPrice: formPrice.value,
            minStockLevel: formMinStock.value,
            quantity: formQty.value,
            unitOfMeasure: formUom.value,
            description: formDesc.value
        };
        authStore.products.unshift(newProduct);
    }
    isModalOpen.value = false;
}

function handleDelete(id: number) {
    if (confirm('Are you sure you want to remove this SKU?')) {
        authStore.products = authStore.products.filter(p => p.id !== id);
    }
}
</script>

<template>
    <AppLayout>
        <div class="space-y-6">
            <!-- Header section -->
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h2 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">Inventory Catalog</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400">Manage raw ingredients, additives, and finished packaging reserves.</p>
                </div>
                <button 
                    v-if="isAdmin"
                    @click="openAddModal"
                    class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-600/10 transition shrink-0"
                >
                    <Plus :size="16" />
                    Register SKU Catalog
                </button>
            </div>

            <!-- Filters Toolbar -->
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
                        placeholder="Search SKU, barcode, name..."
                    />
                </div>

                <!-- Select Filters -->
                <div class="flex flex-wrap items-center gap-3">
                    <!-- Category -->
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-gray-400 font-medium">Category:</span>
                        <select 
                            v-model="selectedCategory" 
                            class="px-3 py-2 border border-gray-100 dark:border-gray-800 rounded-xl bg-gray-50 dark:bg-gray-950 text-xs text-gray-700 dark:text-gray-300 focus:outline-none"
                        >
                            <option value="">All Categories</option>
                            <option v-for="c in authStore.categories" :key="c.id" :value="c.name">{{ c.name }}</option>
                        </select>
                    </div>

                    <!-- Stock Status -->
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-gray-400 font-medium">Stock Status:</span>
                        <select 
                            v-model="selectedStockStatus" 
                            class="px-3 py-2 border border-gray-100 dark:border-gray-800 rounded-xl bg-gray-50 dark:bg-gray-950 text-xs text-gray-700 dark:text-gray-300 focus:outline-none"
                        >
                            <option value="all">All Levels</option>
                            <option value="instock">Optimal (In Stock)</option>
                            <option value="low">Reorder Alert (Low)</option>
                            <option value="out">Out of Stock</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Table Card -->
            <div class="admin-table-wrap overflow-x-auto bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
                <table class="w-full text-left border-collapse text-xs md:text-sm">
                    <thead class="bg-gray-50 dark:bg-gray-800/80 text-gray-400 dark:text-gray-300 border-b border-gray-100 dark:border-gray-800 uppercase text-[10px] tracking-wider font-bold">
                        <tr>
                            <th class="px-6 py-4">Item Details</th>
                            <th class="px-6 py-4">SKU / Barcode</th>
                            <th class="px-6 py-4">Quantity Available</th>
                            <th class="px-6 py-4">Valuation (Cost)</th>
                            <th class="px-6 py-4">Threshold</th>
                            <th v-if="isAdmin" class="px-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-50 dark:divide-gray-800/50">
                        <tr v-if="filteredProducts.length === 0">
                            <td colspan="6" class="px-6 py-12 text-center text-gray-400">
                                No items match the active catalog filters.
                            </td>
                        </tr>
                        <tr v-for="p in filteredProducts" :key="p.id" class="hover:bg-gray-50/50 dark:hover:bg-gray-850 transition">
                            <td class="px-6 py-4">
                                <div class="flex items-center gap-3">
                                    <div class="h-8 w-8 rounded-lg bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300 flex items-center justify-center font-bold">
                                        <Tag :size="16" />
                                    </div>
                                    <div>
                                        <p class="font-bold text-gray-900 dark:text-white text-xs md:text-sm">{{ p.name }}</p>
                                        <p class="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold uppercase mt-0.5">{{ p.categoryName }}</p>
                                    </div>
                                </div>
                            </td>
                            <td class="px-6 py-4 font-mono text-[10px] text-gray-500">
                                <p>SKU: {{ p.sku }}</p>
                                <p class="mt-0.5 text-gray-400" v-if="p.barcode">UPC: {{ p.barcode }}</p>
                            </td>
                            <td class="px-6 py-4">
                                <div class="flex items-center gap-2">
                                    <span class="font-bold text-sm" 
                                        :class="p.quantity === 0 ? 'text-red-500' : p.quantity <= p.minStockLevel ? 'text-amber-500' : 'text-gray-900 dark:text-white'">
                                        {{ p.quantity }}
                                    </span>
                                    <span class="text-gray-400 text-xs">{{ p.unitOfMeasure }}</span>
                                </div>
                                <span v-if="p.quantity === 0" class="inline-flex items-center gap-1 mt-1 text-[9px] font-bold text-red-500 bg-red-50 dark:bg-red-950/20 px-2 py-0.5 rounded-full uppercase">
                                    <ShieldX :size="10" /> Out of stock
                                </span>
                                <span v-else-if="p.quantity <= p.minStockLevel" class="inline-flex items-center gap-1 mt-1 text-[9px] font-bold text-amber-500 bg-amber-50 dark:bg-amber-950/20 px-2 py-0.5 rounded-full uppercase">
                                    <AlertTriangle :size="10" /> Low Stock Warning
                                </span>
                                <span v-else class="inline-flex items-center gap-1 mt-1 text-[9px] font-bold text-emerald-500 bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded-full uppercase">
                                    <PackageCheck :size="10" /> Optimal Level
                                </span>
                            </td>
                            <td class="px-6 py-4">
                                <p class="font-semibold text-gray-900 dark:text-white">{{ formatCurrency(p.costPrice * p.quantity) }}</p>
                                <p class="text-[10px] text-gray-400 mt-0.5">Unit cost: {{ formatCurrency(p.costPrice) }}</p>
                            </td>
                            <td class="px-6 py-4 text-xs text-gray-500">
                                Warn below {{ p.minStockLevel }} {{ p.unitOfMeasure }}
                            </td>
                            <td v-if="isAdmin" class="px-6 py-4 text-right">
                                <div class="flex items-center justify-end gap-2">
                                    <button 
                                        @click="openEditModal(p)"
                                        class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition text-gray-500 hover:text-emerald-600"
                                        title="Edit SKU details"
                                    >
                                        <Edit :size="15" />
                                    </button>
                                    <button 
                                        @click="handleDelete(p.id)"
                                        class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition text-gray-500 hover:text-red-500"
                                        title="Delete SKU"
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
                <div class="relative bg-white dark:bg-gray-900 rounded-3xl w-full max-w-lg p-6 md:p-8 shadow-2xl border border-gray-100 dark:border-gray-800 space-y-6">
                    <button @click="isModalOpen = false" class="absolute top-4 right-4 p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-400">
                        <X :size="18" />
                    </button>

                    <div>
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white">{{ isEditMode ? 'Edit SKU Catalog Details' : 'Register New SKU Catalog' }}</h3>
                        <p class="text-xs text-gray-400 mt-1">Provide unique identifiers and storage metadata.</p>
                    </div>

                    <form @submit.prevent="handleSave" class="space-y-4">
                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Item Name</label>
                            <input 
                                v-model="formName" 
                                type="text"
                                class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                placeholder="e.g. Refined Sugar"
                                required
                            />
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">SKU Code</label>
                                <input 
                                    v-model="formSku" 
                                    type="text"
                                    class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                    required
                                />
                            </div>
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Barcode (UPC)</label>
                                <input 
                                    v-model="formBarcode" 
                                    type="text"
                                    class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                />
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Category</label>
                                <select 
                                    v-model="formCategory"
                                    class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-950 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                >
                                    <option v-for="c in authStore.categories" :key="c.id" :value="c.name">{{ c.name }}</option>
                                </select>
                            </div>
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Unit of Measure (UoM)</label>
                                <input 
                                    v-model="formUom" 
                                    type="text"
                                    class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                    placeholder="e.g. bags (50kg)"
                                    required
                                />
                            </div>
                        </div>

                        <div class="grid grid-cols-3 gap-3">
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Cost Price (₱)</label>
                                <input 
                                    v-model.number="formCost" 
                                    type="number"
                                    step="0.01"
                                    class="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                    required
                                />
                            </div>
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Selling Price (₱)</label>
                                <input 
                                    v-model.number="formPrice" 
                                    type="number"
                                    step="0.01"
                                    class="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                    required
                                />
                            </div>
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Stock Alert Level</label>
                                <input 
                                    v-model.number="formMinStock" 
                                    type="number"
                                    class="w-full px-3 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                    required
                                />
                            </div>
                        </div>

                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Initial Warehouse Quantity</label>
                            <input 
                                v-model.number="formQty" 
                                type="number"
                                class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                :disabled="isEditMode"
                                required
                            />
                            <p v-if="isEditMode" class="text-[10px] text-gray-400">To adjust stock, please log a transaction voucher.</p>
                        </div>

                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Product Description</label>
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
                                class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl"
                            >
                                Save Catalog
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
