<script setup lang="ts">
import { computed, ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import AppLayout from '@/layouts/AppLayout.vue';
import { 
    Search, Plus, Filter, X, ArrowUpRight, ArrowDownRight, RefreshCw, ClipboardList, Info
} from 'lucide-vue-next';
import type { StockTransaction } from '@/types';

const authStore = useAuthStore();

// Filters state
const searchQuery = ref('');
const selectedType = ref('');

// Modal state
const isModalOpen = ref(false);

// Form state
const formProductId = ref<number>(authStore.products[0]?.id || 0);
const formWarehouseId = ref<number>(1);
const formType = ref<'stock-in' | 'stock-out' | 'adjustment' | 'transfer'>('stock-in');
const formQty = ref(10);
const formRef = ref('');
const formNotes = ref('');

const filteredTransactions = computed(() => {
    return authStore.transactions.filter(t => {
        const matchesSearch = t.productName.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                             (t.referenceNumber && t.referenceNumber.toLowerCase().includes(searchQuery.value.toLowerCase())) ||
                             t.userName.toLowerCase().includes(searchQuery.value.toLowerCase());
        
        const matchesType = !selectedType.value || t.type === selectedType.value;
        
        return matchesSearch && matchesType;
    });
});

function openAddModal() {
    formProductId.value = authStore.products[0]?.id || 0;
    formWarehouseId.value = 1;
    formType.value = 'stock-in';
    formQty.value = 10;
    formRef.value = 'PO-' + Math.floor(1000 + Math.random() * 9000);
    formNotes.value = '';
    isModalOpen.value = true;
}

function handleSave() {
    const product = authStore.products.find(p => p.id === formProductId.value);
    const warehouse = authStore.warehouses.find(w => w.id === formWarehouseId.value);
    
    if (!product || !warehouse) return;

    // Apply stock quantity calculations to core store
    const qtyChange = formType.value === 'stock-in' ? formQty.value : -formQty.value;
    
    // Check if operator exceeds inventory for stock-out
    if (formType.value === 'stock-out' && product.quantity < formQty.value) {
        alert('Action aborted: Insufficient available warehouse quantity.');
        return;
    }

    product.quantity += qtyChange;

    const newTx: StockTransaction = {
        id: Date.now(),
        productId: product.id,
        productName: product.name,
        warehouseId: warehouse.id,
        warehouseName: warehouse.name,
        userId: authStore.currentUser?.id || 3,
        userName: authStore.currentUser?.name || 'Operator',
        type: formType.value,
        quantity: formQty.value,
        referenceNumber: formRef.value,
        notes: formNotes.value,
        createdAt: new Date().toISOString().replace('T', ' ').substring(0, 19)
    };

    authStore.transactions.unshift(newTx);
    isModalOpen.value = false;
}
</script>

<template>
    <AppLayout>
        <div class="space-y-6">
            <!-- Header section -->
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h2 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">Stock Transactions</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400">Complete audit trail of stock acquisitions, production outputs, and adjustments.</p>
                </div>
                <button 
                    @click="openAddModal"
                    class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-600/10 transition shrink-0"
                >
                    <Plus :size="16" />
                    Log Stock Voucher
                </button>
            </div>

            <!-- Filters -->
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
                        placeholder="Search product, vouchers, operator..."
                    />
                </div>

                <!-- Select Filters -->
                <div class="flex items-center gap-3">
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-gray-400 font-medium">Tx Type:</span>
                        <select 
                            v-model="selectedType" 
                            class="px-3 py-2 border border-gray-100 dark:border-gray-800 rounded-xl bg-gray-50 dark:bg-gray-950 text-xs text-gray-700 dark:text-gray-300 focus:outline-none"
                        >
                            <option value="">All Transactions</option>
                            <option value="stock-in">Stock-In (Receipt)</option>
                            <option value="stock-out">Stock-Out (Release)</option>
                            <option value="adjustment">Stock Adjustment</option>
                            <option value="transfer">Stock Transfer</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Table View -->
            <div class="admin-table-wrap overflow-x-auto bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
                <table class="w-full text-left border-collapse text-xs md:text-sm">
                    <thead class="bg-gray-50 dark:bg-gray-800/80 text-gray-400 dark:text-gray-300 border-b border-gray-100 dark:border-gray-800 uppercase text-[10px] tracking-wider font-bold">
                        <tr>
                            <th class="px-6 py-4">Transaction Details</th>
                            <th class="px-6 py-4">Voucher Ref</th>
                            <th class="px-6 py-4">Quantity Altered</th>
                            <th class="px-6 py-4">Operator / Time</th>
                            <th class="px-6 py-4">Remarks</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-50 dark:divide-gray-800/50">
                        <tr v-if="filteredTransactions.length === 0">
                            <td colspan="5" class="px-6 py-12 text-center text-gray-400">
                                No stock vouchers registered.
                            </td>
                        </tr>
                        <tr v-for="t in filteredTransactions" :key="t.id" class="hover:bg-gray-50/50 dark:hover:bg-gray-850 transition">
                            <td class="px-6 py-4">
                                <div class="flex items-center gap-3">
                                    <div class="h-8 w-8 rounded-lg flex items-center justify-center font-bold"
                                        :class="t.type === 'stock-in' ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600' : t.type === 'stock-out' ? 'bg-red-50 dark:bg-red-950/20 text-red-600' : 'bg-gray-100 dark:bg-gray-800 text-gray-500'">
                                        <ArrowUpRight v-if="t.type === 'stock-in'" :size="16" />
                                        <ArrowDownRight v-else-if="t.type === 'stock-out'" :size="16" />
                                        <RefreshCw v-else :size="16" />
                                    </div>
                                    <div>
                                        <p class="font-bold text-gray-900 dark:text-white text-xs md:text-sm">{{ t.productName }}</p>
                                        <p class="text-[10px] text-gray-400 mt-0.5">Warehouse: {{ t.warehouseName }}</p>
                                    </div>
                                </div>
                            </td>
                            <td class="px-6 py-4 font-mono text-xs font-semibold text-gray-600 dark:text-gray-400">
                                {{ t.referenceNumber || 'N/A' }}
                            </td>
                            <td class="px-6 py-4">
                                <div class="flex items-center gap-1.5">
                                    <span class="font-extrabold text-sm" 
                                        :class="t.type === 'stock-in' ? 'text-emerald-600' : t.type === 'stock-out' ? 'text-red-500' : 'text-gray-600 dark:text-gray-300'">
                                        {{ t.type === 'stock-in' ? '+' : '-' }}{{ t.quantity }}
                                    </span>
                                </div>
                                <span class="text-[9px] font-bold uppercase mt-1 inline-block px-2 py-0.5 rounded"
                                    :class="t.type === 'stock-in' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20' : t.type === 'stock-out' ? 'bg-red-50 text-red-700 dark:bg-red-950/20' : 'bg-gray-100 text-gray-700 dark:bg-gray-800'">
                                    {{ t.type.replace('-', ' ') }}
                                </span>
                            </td>
                            <td class="px-6 py-4 text-xs">
                                <p class="font-bold text-gray-800 dark:text-gray-200">{{ t.userName }}</p>
                                <p class="text-[10px] text-gray-400 mt-0.5">{{ t.createdAt }}</p>
                            </td>
                            <td class="px-6 py-4 text-xs text-gray-500 dark:text-gray-400 max-w-xs truncate">
                                <div class="flex items-center gap-1">
                                    <Info :size="12" class="text-gray-400 shrink-0" />
                                    <span>{{ t.notes || 'No remarks recorded.' }}</span>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- VOUCHER MODAL DIALOG -->
            <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center px-4">
                <!-- Backdrop -->
                <div @click="isModalOpen = false" class="fixed inset-0 bg-black/40 backdrop-blur-xs"></div>

                <!-- Modal box -->
                <div class="relative bg-white dark:bg-gray-900 rounded-3xl w-full max-w-md p-6 md:p-8 shadow-2xl border border-gray-100 dark:border-gray-800 space-y-6">
                    <button @click="isModalOpen = false" class="absolute top-4 right-4 p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-400">
                        <X :size="18" />
                    </button>

                    <div>
                        <h3 class="text-xl font-bold text-gray-900 dark:text-white">Log Stock Voucher</h3>
                        <p class="text-xs text-gray-400 mt-1">Manual adjustment or warehouse receiving audit.</p>
                    </div>

                    <form @submit.prevent="handleSave" class="space-y-4">
                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Target Catalog Product</label>
                            <select 
                                v-model="formProductId"
                                class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-950 text-sm focus:outline-none"
                                required
                            >
                                <option v-for="p in authStore.products" :key="p.id" :value="p.id">
                                    {{ p.name }} (SKU: {{ p.sku }})
                                </option>
                            </select>
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Adjustment Type</label>
                                <select 
                                    v-model="formType"
                                    class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-950 text-sm focus:outline-none"
                                    required
                                >
                                    <option value="stock-in">Stock-In (Receipt)</option>
                                    <option value="stock-out">Stock-Out (Dispatch)</option>
                                    <option value="adjustment">Inventory Reconciliation</option>
                                </select>
                            </div>
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Warehouse Node</label>
                                <select 
                                    v-model="formWarehouseId"
                                    class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-950 text-sm focus:outline-none"
                                    required
                                >
                                    <option v-for="w in authStore.warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
                                </select>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Quantity Adjusted</label>
                                <input 
                                    v-model.number="formQty" 
                                    type="number"
                                    min="1"
                                    class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none"
                                    required
                                />
                            </div>
                            <div class="space-y-1">
                                <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Voucher Reference</label>
                                <input 
                                    v-model="formRef" 
                                    type="text"
                                    class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none"
                                    placeholder="PO-2026-000"
                                />
                            </div>
                        </div>

                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Voucher Notes</label>
                            <textarea 
                                v-model="formNotes" 
                                class="w-full px-4 py-2 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none h-16"
                                placeholder="Explain reason for stock movement..."
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
                                Submit Voucher
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
