<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import AppLayout from '@/layouts/AppLayout.vue';
import {
    Users, ShieldAlert, BarChart3, Clock, AlertTriangle, PackageCheck, Truck, ListCollapse, Plus, ArrowUpRight, ArrowDownRight, RefreshCw, Layers
} from 'lucide-vue-next';
import { formatCurrency } from '@/composables/useFormatCurrency';
import type { Product, StockTransaction, User as UserType, Warehouse } from '@/types';
import { api } from '@/lib/api';

const authStore = useAuthStore();

const currentRole = computed(() => authStore.currentUser?.role || 'employee');
const userName    = computed(() => authStore.currentUser?.name || 'User');

const products     = ref<Product[]>([]);
const transactions = ref<StockTransaction[]>([]);
const users        = ref<UserType[]>([]);
const warehouses   = ref<Warehouse[]>([]);
const isLoading    = ref(false);

// Computed stats from API data
const totalProducts      = computed(() => products.value.length);
const lowStockProducts   = computed(() => products.value.filter(p => p.quantity > 0 && p.quantity <= p.minStockLevel));
const outOfStockProducts = computed(() => products.value.filter(p => p.quantity === 0));
const totalValuation     = computed(() => products.value.reduce((acc, p) => acc + (p.costPrice * p.quantity), 0));

async function loadDashboardData() {
    isLoading.value = true;
    try {
        const fetches: Promise<any>[] = [
            api.get<Product[]>('/products'),
            api.get<StockTransaction[]>('/transactions'),
        ];
        
        if (currentRole.value === 'super_admin') {
            fetches.push(api.get<UserType[]>('/users'));
            fetches.push(api.get<Warehouse[]>('/warehouses'));
        }
        
        const results = await Promise.all(fetches);
        products.value = results[0];
        transactions.value = results[1];
        if (currentRole.value === 'super_admin') {
            users.value = results[2];
            warehouses.value = results[3];
        }
    } catch (err) {
        console.error('Error loading dashboard data:', err);
    } finally {
        isLoading.value = false;
    }
}

onMounted(loadDashboardData);

// ── Employee barcode scanner (calls the transactions API) ──────────────────
const scanBarcode      = ref('');
const scannedProduct   = ref<Product | null>(null);
const scanQty          = ref<number>(10);
const scanNotes        = ref('');
const scannerFeedback  = ref('');
const isScanning       = ref(false);

function simulateScan() {
    scannerFeedback.value = '';
    const match = products.value.find(p => p.barcode === scanBarcode.value || p.sku === scanBarcode.value.toUpperCase());
    if (match) {
        scannedProduct.value = { ...match };
    } else {
        scannedProduct.value = null;
        scannerFeedback.value = 'No matching product found.';
    }
}

async function processScanAction(type: 'stock-in' | 'stock-out') {
    if (!scannedProduct.value) return;
    isScanning.value = true;
    try {
        await api.post('/transactions', {
            product_id: scannedProduct.value.id,
            type,
            quantity: scanQty.value,
            notes: scanNotes.value || 'Barcode scan action',
            reference_number: 'SCAN-' + Math.floor(Math.random() * 10000),
        });
        scannerFeedback.value = `✅ Registered ${scanQty.value} units ${type === 'stock-in' ? 'INTO' : 'OUT OF'} stock.`;
        scanBarcode.value = '';
        scanNotes.value = '';
        scannedProduct.value = null;
        await loadDashboardData();
    } catch (e: unknown) {
        scannerFeedback.value = e instanceof Error ? e.message : 'Error processing action';
    } finally {
        isScanning.value = false;
    }
}
</script>

<template>
    <AppLayout>
        <div class="space-y-6">
            <!-- Greeting -->
            <div>
                <h2 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">Hello, {{ userName }}</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400">Welcome to your role-tailored IMS portal. Action panels loaded.</p>
            </div>

            <!-- ========================================== -->
            <!-- 1. SUPER ADMIN VIEW                        -->
            <!-- ========================================== -->
            <div v-if="currentRole === 'super_admin'" class="space-y-6">
                <!-- Stat Grid -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Total Active Users</p>
                            <p class="text-2xl font-extrabold mt-2">{{ users.length }}</p>
                        </div>
                        <div class="h-12 w-12 bg-blue-50 dark:bg-blue-950/20 text-blue-600 rounded-xl flex items-center justify-center">
                            <Users :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Audit logs generated</p>
                            <p class="text-2xl font-extrabold mt-2">{{ transactions.length }}</p>
                        </div>
                        <div class="h-12 w-12 bg-indigo-50 dark:bg-indigo-950/20 text-indigo-600 rounded-xl flex items-center justify-center">
                            <Clock :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Critical alerts</p>
                            <p class="text-2xl font-extrabold mt-2 text-amber-500">{{ lowStockProducts.length + outOfStockProducts.length }}</p>
                        </div>
                        <div class="h-12 w-12 bg-amber-50 dark:bg-amber-950/20 text-amber-500 rounded-xl flex items-center justify-center">
                            <ShieldAlert :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Storage Nodes</p>
                            <p class="text-2xl font-extrabold mt-2">{{ warehouses.length }}</p>
                        </div>
                        <div class="h-12 w-12 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 rounded-xl flex items-center justify-center">
                            <Layers :size="22" />
                        </div>
                    </div>
                </div>

                <!-- Users and logs layouts -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Users -->
                    <div class="admin-card p-6 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="font-bold text-lg">System Users Directory</h3>
                            <router-link to="/users" class="text-emerald-600 hover:underline text-xs flex items-center gap-1">
                                Manage Users <ArrowUpRight :size="14" />
                            </router-link>
                        </div>
                        <div class="space-y-3">
                            <div v-for="u in users" :key="u.id" class="flex items-center justify-between p-3 rounded-xl border border-gray-50 dark:border-gray-850 hover:bg-gray-50 dark:hover:bg-gray-800 transition">
                                <div class="flex items-center gap-3">
                                    <div class="h-8 w-8 rounded-full bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center font-bold text-xs uppercase text-emerald-600 dark:text-emerald-300">
                                        {{ u.name.charAt(0) }}
                                    </div>
                                    <div>
                                        <p class="text-xs font-bold">{{ u.name }}</p>
                                        <p class="text-[10px] text-gray-400">{{ u.email }}</p>
                                    </div>
                                </div>
                                <span class="px-2.5 py-1 text-[10px] rounded-full font-bold uppercase tracking-wider" 
                                    :class="u.role === 'super_admin' ? 'bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400' : u.role === 'admin' ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/20 dark:text-blue-400' : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'">
                                    {{ u.role.replace('_', ' ') }}
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Logs -->
                    <div class="admin-card p-6 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="font-bold text-lg">Recent Stock Audits</h3>
                            <router-link to="/transactions" class="text-emerald-600 hover:underline text-xs flex items-center gap-1">
                                Full Audit Logs <ArrowUpRight :size="14" />
                            </router-link>
                        </div>
                        <div class="space-y-3">
                            <div v-for="t in transactions.slice(0, 4)" :key="t.id" class="flex items-center justify-between p-3 rounded-xl border border-gray-50 dark:border-gray-850 text-xs">
                                <div>
                                    <p class="font-bold text-gray-800 dark:text-gray-200">{{ t.productName }}</p>
                                    <p class="text-[10px] text-gray-400 mt-1">Logged by {{ t.userName }} • {{ t.createdAt }}</p>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                                        :class="t.type === 'stock-in' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20' : t.type === 'stock-out' ? 'bg-red-50 text-red-700 dark:bg-red-950/20' : 'bg-gray-100 text-gray-700 dark:bg-gray-800'">
                                        {{ t.type }}
                                    </span>
                                    <span class="font-bold text-sm" :class="t.type === 'stock-in' ? 'text-emerald-600' : t.type === 'stock-out' ? 'text-red-500' : 'text-gray-500'">
                                        {{ t.type === 'stock-in' ? '+' : '-' }}{{ t.quantity }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ========================================== -->
            <!-- 2. ADMIN VIEW                              -->
            <!-- ========================================== -->
            <div v-if="currentRole === 'admin'" class="space-y-6">
                <!-- Stat Grid -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Inventory Value</p>
                            <p class="text-2xl font-extrabold mt-2 text-emerald-600">{{ formatCurrency(totalValuation) }}</p>
                        </div>
                        <div class="h-12 w-12 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 rounded-xl flex items-center justify-center">
                            <BarChart3 :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Total SKUs Cataloged</p>
                            <p class="text-2xl font-extrabold mt-2">{{ totalProducts }}</p>
                        </div>
                        <div class="h-12 w-12 bg-blue-50 dark:bg-blue-950/20 text-blue-600 rounded-xl flex items-center justify-center">
                            <PackageCheck :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Low Stock SKUs</p>
                            <p class="text-2xl font-extrabold mt-2" :class="lowStockProducts.length > 0 ? 'text-amber-500' : ''">{{ lowStockProducts.length }}</p>
                        </div>
                        <div class="h-12 w-12 bg-amber-50 dark:bg-amber-950/20 text-amber-500 rounded-xl flex items-center justify-center">
                            <AlertTriangle :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Out of Stock</p>
                            <p class="text-2xl font-extrabold mt-2" :class="outOfStockProducts.length > 0 ? 'text-red-500' : ''">{{ outOfStockProducts.length }}</p>
                        </div>
                        <div class="h-12 w-12 bg-red-50 dark:bg-red-950/20 text-red-500 rounded-xl flex items-center justify-center">
                            <ShieldAlert :size="22" />
                        </div>
                    </div>
                </div>

                <!-- Admin sections -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Low Stock Widget -->
                    <div class="admin-card p-6 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl lg:col-span-2">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="font-bold text-lg">Stock Reorder Monitor</h3>
                            <router-link to="/inventory" class="text-emerald-600 hover:underline text-xs flex items-center gap-1">
                                Full Catalog <ArrowUpRight :size="14" />
                            </router-link>
                        </div>
                        <div v-if="lowStockProducts.length === 0 && outOfStockProducts.length === 0" class="py-8 text-center text-gray-400">
                            All inventories are within optimal levels.
                        </div>
                        <div v-else class="overflow-x-auto">
                            <table class="w-full text-left border-collapse text-sm">
                                <thead>
                                    <tr class="border-b border-gray-100 dark:border-gray-800 text-gray-400">
                                        <th class="pb-3 font-semibold">SKU / Item</th>
                                        <th class="pb-3 font-semibold">Available</th>
                                        <th class="pb-3 font-semibold">Alert Level</th>
                                        <th class="pb-3 font-semibold text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-gray-50 dark:divide-gray-800/50">
                                    <tr v-for="p in [...outOfStockProducts, ...lowStockProducts]" :key="p.id" class="hover:bg-gray-50/50 dark:hover:bg-gray-850">
                                        <td class="py-3 pr-2">
                                            <p class="font-bold text-gray-800 dark:text-gray-200">{{ p.name }}</p>
                                            <p class="text-[10px] text-gray-400 mt-0.5">{{ p.sku }}</p>
                                        </td>
                                        <td class="py-3">
                                            <span class="font-bold" :class="p.quantity === 0 ? 'text-red-500' : 'text-amber-500'">
                                                {{ p.quantity }}
                                            </span>
                                            <span class="text-xs text-gray-400 ml-1">{{ p.unitOfMeasure }}</span>
                                        </td>
                                        <td class="py-3 text-xs text-gray-500">
                                            Reorder below {{ p.minStockLevel }}
                                        </td>
                                        <td class="py-3 text-right">
                                            <router-link to="/transactions" class="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 rounded-lg text-xs font-semibold transition">
                                                Restock
                                            </router-link>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Side Tools Quick Links -->
                    <div class="admin-card p-6 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl flex flex-col justify-between">
                        <div class="space-y-4">
                            <h3 class="font-bold text-lg">Quick Operations</h3>
                            <p class="text-xs text-gray-400">Shortcuts to create transactions, catalogs, or registries.</p>
                            
                            <div class="space-y-2 pt-2">
                                <router-link to="/inventory" class="w-full flex items-center justify-between p-3 rounded-xl border border-gray-100 dark:border-gray-800 hover:bg-emerald-50/20 hover:border-emerald-200/30 transition text-sm">
                                    <span class="flex items-center gap-2">
                                        <Plus :size="16" class="text-emerald-600" />
                                        Add New SKU Catalog
                                    </span>
                                    <ChevronRight :size="14" class="text-gray-300" />
                                </router-link>
                                <router-link to="/transactions" class="w-full flex items-center justify-between p-3 rounded-xl border border-gray-100 dark:border-gray-800 hover:bg-emerald-50/20 hover:border-emerald-200/30 transition text-sm">
                                    <span class="flex items-center gap-2">
                                        <Plus :size="16" class="text-emerald-600" />
                                        Log Receipt/Dispatch
                                    </span>
                                    <ChevronRight :size="14" class="text-gray-300" />
                                </router-link>
                                <router-link to="/suppliers" class="w-full flex items-center justify-between p-3 rounded-xl border border-gray-100 dark:border-gray-800 hover:bg-emerald-50/20 hover:border-emerald-200/30 transition text-sm">
                                    <span class="flex items-center gap-2">
                                        <Plus :size="16" class="text-emerald-600" />
                                        Register Supplier Profile
                                    </span>
                                    <ChevronRight :size="14" class="text-gray-300" />
                                </router-link>
                            </div>
                        </div>

                        <div class="mt-8 p-4 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-100/50 dark:border-emerald-900/30 rounded-2xl text-xs text-emerald-800 dark:text-emerald-400">
                            <p class="font-bold flex items-center gap-1.5"><Truck :size="14" /> Supply Chain Notice</p>
                            <p class="mt-1 leading-relaxed opacity-90">Verify shipping receipts and seal barcodes before signing warehouse adjustments.</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ========================================== -->
            <!-- 3. EMPLOYEE / OPERATOR VIEW                -->
            <!-- ========================================== -->
            <div v-if="currentRole === 'employee'" class="space-y-6">
                <!-- Employee widgets -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Scanner Simulator Panel -->
                    <div class="admin-card p-6 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl lg:col-span-2">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="font-bold text-lg">Logistics Scanner Simulator</h3>
                            <span class="px-2 py-0.5 bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 rounded text-[10px] font-bold uppercase tracking-wider animate-pulse">
                                Handheld Online
                            </span>
                        </div>
                        <p class="text-xs text-gray-500 mb-6">
                            Simulate warehouse barcode scanning by entering a product SKU (e.g. <span class="font-bold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">RM-FLOUR-001</span>) or Barcode (<span class="font-bold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">4801234567011</span>).
                        </p>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <!-- Scanning input -->
                            <div class="space-y-4">
                                <div class="space-y-1">
                                    <label class="text-xs font-semibold text-gray-500">Scan Barcode / SKU</label>
                                    <div class="flex gap-2">
                                        <input 
                                            v-model="scanBarcode" 
                                            type="text" 
                                            class="flex-1 px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                            placeholder="Enter barcode or SKU"
                                            @keyup.enter="simulateScan"
                                        />
                                        <button 
                                            @click="simulateScan" 
                                            class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5"
                                        >
                                            <RefreshCw :size="14" />
                                            Lookup
                                        </button>
                                    </div>
                                </div>

                                <div v-if="scannedProduct" class="p-4 bg-gray-50 dark:bg-gray-850 rounded-2xl space-y-3 text-xs border border-gray-100 dark:border-gray-800">
                                    <div class="flex justify-between items-start">
                                        <div>
                                            <p class="font-bold text-sm text-gray-900 dark:text-white">{{ scannedProduct.name }}</p>
                                            <p class="text-[10px] text-gray-400 mt-0.5">{{ scannedProduct.sku }}</p>
                                        </div>
                                        <span class="px-2 py-0.5 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 rounded font-bold uppercase tracking-wider text-[9px]">
                                            {{ scannedProduct.categoryName }}
                                        </span>
                                    </div>
                                    <div class="flex justify-between pt-2 border-t border-gray-200/50">
                                        <span class="text-gray-500">Current Warehouse Qty:</span>
                                        <span class="font-bold">{{ scannedProduct.quantity }} {{ scannedProduct.unitOfMeasure }}</span>
                                    </div>
                                </div>

                                <div v-if="scannerFeedback" 
                                    class="p-3 rounded-xl text-xs font-medium border"
                                    :class="scannerFeedback.startsWith('Success') 
                                        ? 'bg-emerald-50 text-emerald-800 border-emerald-100 dark:bg-emerald-950/10' 
                                        : 'bg-amber-50 text-amber-800 border-amber-100 dark:bg-amber-950/10'"
                                >
                                    {{ scannerFeedback }}
                                </div>
                            </div>

                            <!-- Adjustment controls -->
                            <div class="space-y-4 flex flex-col justify-between" :class="!scannedProduct ? 'opacity-40 pointer-events-none' : ''">
                                <div class="space-y-3">
                                    <div class="space-y-1">
                                        <label class="text-xs font-semibold text-gray-500">Adjustment Quantity</label>
                                        <input 
                                            v-model.number="scanQty" 
                                            type="number" 
                                            min="1" 
                                            class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                        />
                                    </div>
                                    <div class="space-y-1">
                                        <label class="text-xs font-semibold text-gray-500">Adjustment Notes</label>
                                        <input 
                                            v-model="scanNotes" 
                                            type="text" 
                                            class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                            placeholder="Reason for change..."
                                        />
                                    </div>
                                </div>

                                <div class="grid grid-cols-2 gap-3 pt-4">
                                    <button 
                                        @click="processScanAction('stock-in')" 
                                        class="py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold text-xs flex items-center justify-center gap-1.5"
                                    >
                                        <ArrowUpRight :size="16" />
                                        Stock-In
                                    </button>
                                    <button 
                                        @click="processScanAction('stock-out')" 
                                        class="py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl font-bold text-xs flex items-center justify-center gap-1.5"
                                    >
                                        <ArrowDownRight :size="16" />
                                        Stock-Out
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Operator Guide -->
                    <div class="admin-card p-6 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl flex flex-col justify-between">
                        <div class="space-y-4">
                            <h3 class="font-bold text-lg">Barcode Cheat Sheet</h3>
                            <p class="text-xs text-gray-500 leading-relaxed">
                                Use these quick values in the simulator to test real-time stock-in / stock-out transactions:
                            </p>
                            
                            <div class="space-y-2 pt-2 text-xs">
                                <div v-for="p in products.slice(0, 3)" :key="p.id" class="p-2.5 bg-gray-50 dark:bg-gray-850 rounded-lg flex flex-col gap-0.5 border border-gray-100 dark:border-gray-800/80">
                                    <p class="font-bold truncate">{{ p.name }}</p>
                                    <div class="flex justify-between text-[10px] text-gray-400 mt-1">
                                        <span>SKU: <span class="text-gray-700 dark:text-gray-300 font-semibold">{{ p.sku }}</span></span>
                                        <span>Barcode: <span class="text-gray-700 dark:text-gray-300 font-semibold">{{ p.barcode }}</span></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
