<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import AppLayout from '@/layouts/AppLayout.vue';
import {
    Users, ShieldAlert, BarChart3, Clock, AlertTriangle, PackageCheck, Truck,
    Plus, ArrowUpRight, ArrowDownRight, RefreshCw, Layers, ShoppingCart,
    TrendingUp, ChevronRight, CalendarDays, FileDown, FileSpreadsheet,
} from 'lucide-vue-next';
import { formatCurrency } from '@/composables/useFormatCurrency';
import type {
    Product, StockTransaction, User as UserType, Warehouse,
    DashboardSummary, MonthlySalesItem,
} from '@/types';
import { api } from '@/lib/api';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as XLSX from 'xlsx';

const authStore = useAuthStore();

const currentRole = computed(() => authStore.currentUser?.role || 'employee');
const userName    = computed(() => authStore.currentUser?.name || 'User');
const canInput    = computed(() => authStore.currentUser?.canInputTransactions ?? false);

const products     = ref<Product[]>([]);
const transactions = ref<StockTransaction[]>([]);
const users        = ref<UserType[]>([]);
const warehouses   = ref<Warehouse[]>([]);
const isLoading    = ref(false);

const summary = ref<DashboardSummary>({ totalUsers: 0, totalBuy: 0, totalSell: 0 });
const monthlySales = ref<MonthlySalesItem[]>([]);
const salesRange = ref<6 | 12>(6);

const visibleMonthlySales = computed(() =>
    monthlySales.value.slice(-salesRange.value),
);

const maxMonthlyTotal = computed(() =>
    Math.max(1, ...visibleMonthlySales.value.map((m) => m.total)),
);

// ── Calendar (mini current-month view) ───────────────────────────────────────
const calendarNow = new Date();
const calendarYear = calendarNow.getFullYear();
const calendarMonth = calendarNow.getMonth();
const calendarMonthLabel = calendarNow.toLocaleString('en-PH', { month: 'short', year: 'numeric' });
const calendarWeekdays = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

const calendarCells = computed(() => {
    const firstWeekday = new Date(calendarYear, calendarMonth, 1).getDay();
    const daysInMonth = new Date(calendarYear, calendarMonth + 1, 0).getDate();
    const today = calendarNow.getDate();
    const cells: Array<{ day: number | null; isToday: boolean }> = [];
    for (let i = 0; i < firstWeekday; i++) cells.push({ day: null, isToday: false });
    for (let d = 1; d <= daysInMonth; d++) {
        cells.push({ day: d, isToday: d === today });
    }
    return cells;
});

const totalProducts      = computed(() => products.value.length);
const lowStockProducts   = computed(() => products.value.filter(p => p.quantity > 0 && p.quantity <= p.minStockLevel));
const outOfStockProducts = computed(() => products.value.filter(p => p.quantity === 0));
const totalValuation     = computed(() => products.value.reduce((acc, p) => acc + (p.costPrice * p.quantity), 0));

function exportRows() {
    return visibleMonthlySales.value.map((m) => ({
        Month: m.label,
        'Sales (PHP)': m.total,
    }));
}

function exportPdf() {
    const doc = new jsPDF();
    const generated = new Date().toLocaleString('en-PH');
    doc.setFontSize(16);
    doc.text('Monthly Sales Review', 14, 18);
    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(`Generated ${generated} · Last ${salesRange.value} months`, 14, 26);
    doc.setTextColor(0);
    doc.text(`Total Users: ${summary.value.totalUsers}`, 14, 36);
    doc.text(`Total Buy: ${formatCurrency(summary.value.totalBuy)}`, 14, 42);
    doc.text(`Total Sell: ${formatCurrency(summary.value.totalSell)}`, 14, 48);

    autoTable(doc, {
        startY: 56,
        head: [['Month', 'Sales (PHP)']],
        body: visibleMonthlySales.value.map((m) => [m.label, formatCurrency(m.total)]),
        styles: { fontSize: 10 },
        headStyles: { fillColor: [5, 150, 105] },
    });
    doc.save(`monthly-sales-${salesRange.value}m.pdf`);
}

function exportExcel() {
    const sheet = XLSX.utils.json_to_sheet([
        { Metric: 'Total Users', Value: summary.value.totalUsers },
        { Metric: 'Total Buy (PHP)', Value: summary.value.totalBuy },
        { Metric: 'Total Sell (PHP)', Value: summary.value.totalSell },
        {},
        ...exportRows(),
    ]);
    const book = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(book, sheet, 'Sales Review');
    XLSX.writeFile(book, `monthly-sales-${salesRange.value}m.xlsx`);
}

async function loadDashboardData() {
    isLoading.value = true;
    try {
        const fetches: Promise<unknown>[] = [
            api.get<Product[]>('/products'),
            api.get<StockTransaction[]>('/transactions'),
        ];

        if (currentRole.value === 'super_admin') {
            fetches.push(api.get<UserType[]>('/users'));
            fetches.push(api.get<Warehouse[]>('/warehouses'));
            fetches.push(api.get<DashboardSummary>('/dashboard/summary'));
            fetches.push(api.get<MonthlySalesItem[]>('/sales/monthly-summary?months=12'));
        }

        const results = await Promise.all(fetches);
        products.value = results[0] as Product[];
        transactions.value = results[1] as StockTransaction[];
        if (currentRole.value === 'super_admin') {
            users.value = results[2] as UserType[];
            warehouses.value = results[3] as Warehouse[];
            summary.value = results[4] as DashboardSummary;
            monthlySales.value = results[5] as MonthlySalesItem[];
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
                <!-- 1. Summary: Total Users / Total Buy / Total Sell -->
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Total Users</p>
                            <p class="text-2xl font-extrabold mt-2">{{ summary.totalUsers }}</p>
                        </div>
                        <div class="h-12 w-12 bg-blue-50 dark:bg-blue-950/20 text-blue-600 rounded-xl flex items-center justify-center">
                            <Users :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Total Buy</p>
                            <p class="text-2xl font-extrabold mt-2 text-emerald-600">{{ formatCurrency(summary.totalBuy) }}</p>
                            <p class="text-[10px] text-gray-400 mt-1">Stock-in × cost price</p>
                        </div>
                        <div class="h-12 w-12 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 rounded-xl flex items-center justify-center">
                            <ShoppingCart :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Total Sell</p>
                            <p class="text-2xl font-extrabold mt-2 text-indigo-600">{{ formatCurrency(summary.totalSell) }}</p>
                            <p class="text-[10px] text-gray-400 mt-1">All recorded sales</p>
                        </div>
                        <div class="h-12 w-12 bg-indigo-50 dark:bg-indigo-950/20 text-indigo-600 rounded-xl flex items-center justify-center">
                            <TrendingUp :size="22" />
                        </div>
                    </div>
                </div>

                <!-- Secondary ops metrics -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Audit logs</p>
                            <p class="text-xl font-extrabold mt-1">{{ transactions.length }}</p>
                        </div>
                        <Clock :size="20" class="text-indigo-500" />
                    </div>
                    <div class="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Critical alerts</p>
                            <p class="text-xl font-extrabold mt-1 text-amber-500">{{ lowStockProducts.length + outOfStockProducts.length }}</p>
                        </div>
                        <ShieldAlert :size="20" class="text-amber-500" />
                    </div>
                    <div class="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Storage nodes</p>
                            <p class="text-xl font-extrabold mt-1">{{ warehouses.length }}</p>
                        </div>
                        <Layers :size="20" class="text-emerald-600" />
                    </div>
                </div>

                <!-- Sales review + mini calendar (compact side-by-side) -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    <!-- Monthly Sales Review -->
                    <div class="lg:col-span-2 p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm">
                        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                            <div>
                                <h3 class="font-bold text-base flex items-center gap-2">
                                    <BarChart3 :size="16" class="text-emerald-600" />
                                    Monthly Sales
                                </h3>
                                <p class="text-[11px] text-gray-400 mt-0.5">Amounts in ₱ · hover a bar for detail</p>
                            </div>
                            <div class="flex flex-wrap items-center gap-2">
                                <div class="inline-flex rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden text-[11px] font-semibold">
                                    <button
                                        type="button"
                                        class="px-2.5 py-1.5 transition"
                                        :class="salesRange === 6 ? 'bg-emerald-600 text-white' : 'bg-transparent text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800'"
                                        @click="salesRange = 6"
                                    >6 mo</button>
                                    <button
                                        type="button"
                                        class="px-2.5 py-1.5 transition border-l border-gray-200 dark:border-gray-700"
                                        :class="salesRange === 12 ? 'bg-emerald-600 text-white' : 'bg-transparent text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800'"
                                        @click="salesRange = 12"
                                    >12 mo</button>
                                </div>
                                <button
                                    type="button"
                                    class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-[11px] font-semibold text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                                    @click="exportPdf"
                                >
                                    <FileDown :size="13" /> PDF
                                </button>
                                <button
                                    type="button"
                                    class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-emerald-200 dark:border-emerald-900/40 text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/20 transition"
                                    @click="exportExcel"
                                >
                                    <FileSpreadsheet :size="13" /> Excel
                                </button>
                            </div>
                        </div>

                        <div class="flex items-end gap-1.5 h-28">
                            <div
                                v-for="m in visibleMonthlySales"
                                :key="m.month"
                                class="flex-1 flex flex-col items-center justify-end h-full gap-1 group relative"
                            >
                                <span class="pointer-events-none absolute -top-5 left-1/2 -translate-x-1/2 text-[9px] font-semibold text-gray-600 dark:text-gray-300 opacity-0 group-hover:opacity-100 transition whitespace-nowrap bg-white dark:bg-gray-800 px-1.5 py-0.5 rounded shadow-sm border border-gray-100 dark:border-gray-700 z-10">
                                    {{ formatCurrency(m.total) }}
                                </span>
                                <div
                                    class="w-full max-w-[36px] mx-auto rounded-t-md bg-emerald-500/80 dark:bg-emerald-500/60 group-hover:bg-emerald-600 transition"
                                    :style="{ height: `${Math.max(6, (m.total / maxMonthlyTotal) * 100)}%` }"
                                />
                                <span class="text-[9px] text-gray-400 font-medium">{{ m.label.split(' ')[0] }}</span>
                            </div>
                        </div>
                        <p v-if="visibleMonthlySales.length === 0" class="text-center text-xs text-gray-400 py-6">No sales data yet.</p>
                    </div>

                    <!-- Mini calendar -->
                    <div class="p-4 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm">
                        <div class="flex items-center justify-between mb-3">
                            <h3 class="font-bold text-sm flex items-center gap-1.5">
                                <CalendarDays :size="14" class="text-emerald-600" />
                                {{ calendarMonthLabel }}
                            </h3>
                            <span class="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400">
                                Today {{ calendarNow.getDate() }}
                            </span>
                        </div>
                        <div class="grid grid-cols-7 gap-0.5 text-center text-[9px] font-semibold text-gray-400 mb-1">
                            <span v-for="(wd, i) in calendarWeekdays" :key="i">{{ wd }}</span>
                        </div>
                        <div class="grid grid-cols-7 gap-0.5">
                            <div
                                v-for="(cell, idx) in calendarCells"
                                :key="idx"
                                class="h-7 flex items-center justify-center rounded-md text-[11px]"
                                :class="cell.day === null
                                    ? ''
                                    : cell.isToday
                                        ? 'bg-emerald-600 text-white font-bold'
                                        : 'text-gray-600 dark:text-gray-300'"
                            >
                                {{ cell.day ?? '' }}
                            </div>
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
            <!-- 3. EMPLOYEE — DATA ENTRY (canInput=true)  -->
            <!-- ========================================== -->
            <div v-if="currentRole === 'employee' && canInput" class="space-y-6">
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
                            Simulate warehouse barcode scanning by entering a product SKU (e.g. <span class="font-bold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">DFP-LONG-001</span>) or Barcode (<span class="font-bold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">4809001001001</span>).
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

            <!-- ========================================== -->
            <!-- 4. EMPLOYEE — VIEWER (canInput=false)      -->
            <!-- ========================================== -->
            <div v-if="currentRole === 'employee' && !canInput" class="space-y-6">
                <!-- Read-only stat cards -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Total Products</p>
                            <p class="text-2xl font-extrabold mt-2">{{ totalProducts }}</p>
                        </div>
                        <div class="h-12 w-12 bg-blue-50 dark:bg-blue-950/20 text-blue-600 rounded-xl flex items-center justify-center">
                            <PackageCheck :size="22" />
                        </div>
                    </div>

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
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Low Stock Items</p>
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

                <!-- Read-only panels -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Recent Transactions (read-only) -->
                    <div class="p-6 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl lg:col-span-2">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="font-bold text-lg">Recent Stock Movements</h3>
                            <router-link to="/transactions" class="text-emerald-600 hover:underline text-xs flex items-center gap-1">
                                View All <ArrowUpRight :size="14" />
                            </router-link>
                        </div>
                        <div v-if="transactions.length === 0" class="py-8 text-center text-gray-400 text-sm">
                            No transactions recorded yet.
                        </div>
                        <div v-else class="space-y-2">
                            <div v-for="t in transactions.slice(0, 8)" :key="t.id" 
                                class="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-850 border border-gray-100 dark:border-gray-800/50"
                            >
                                <div class="flex items-center gap-3">
                                    <div class="h-8 w-8 rounded-lg flex items-center justify-center"
                                        :class="t.type === 'stock-in' ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600' : t.type === 'stock-out' ? 'bg-red-50 dark:bg-red-950/20 text-red-500' : 'bg-gray-100 dark:bg-gray-800 text-gray-500'"
                                    >
                                        <ArrowUpRight v-if="t.type === 'stock-in'" :size="14" />
                                        <ArrowDownRight v-else-if="t.type === 'stock-out'" :size="14" />
                                        <RefreshCw v-else :size="14" />
                                    </div>
                                    <div>
                                        <p class="text-xs font-bold text-gray-800 dark:text-gray-200">{{ t.referenceNumber || t.type }}</p>
                                        <p class="text-[10px] text-gray-400">{{ t.notes || 'No notes' }}</p>
                                    </div>
                                </div>
                                <span class="font-bold text-sm" :class="t.type === 'stock-in' ? 'text-emerald-600' : t.type === 'stock-out' ? 'text-red-500' : 'text-gray-500'">
                                    {{ t.type === 'stock-in' ? '+' : '-' }}{{ t.quantity }}
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Inventory summary -->
                    <div class="p-6 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl flex flex-col justify-between">
                        <div class="space-y-4">
                            <h3 class="font-bold text-lg">Inventory Overview</h3>
                            <p class="text-xs text-gray-500 leading-relaxed">
                                Read-only view of current stock levels. Contact an admin if you need transaction input access.
                            </p>
                            
                            <div class="space-y-2 pt-2 text-xs">
                                <div v-for="p in products.slice(0, 5)" :key="p.id" class="p-3 bg-gray-50 dark:bg-gray-850 rounded-xl border border-gray-100 dark:border-gray-800/80">
                                    <div class="flex items-center justify-between">
                                        <p class="font-bold truncate text-gray-800 dark:text-gray-200">{{ p.name }}</p>
                                        <span class="font-bold" :class="p.quantity <= p.minStockLevel ? 'text-amber-500' : 'text-emerald-600'">
                                            {{ p.quantity }} {{ p.unitOfMeasure }}
                                        </span>
                                    </div>
                                    <div class="mt-1.5">
                                        <div class="h-1.5 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                                            <div class="h-full rounded-full transition-all"
                                                :class="p.quantity === 0 ? 'bg-red-500' : p.quantity <= p.minStockLevel ? 'bg-amber-500' : 'bg-emerald-500'"
                                                :style="{ width: `${Math.min(100, (p.quantity / Math.max(p.minStockLevel * 2, 1)) * 100)}%` }"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="mt-6 p-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-100/50 dark:border-blue-900/30 rounded-2xl text-xs text-blue-800 dark:text-blue-400">
                            <p class="font-bold flex items-center gap-1.5"><Layers :size="14" /> Viewer Mode</p>
                            <p class="mt-1 leading-relaxed opacity-90">You have read-only access. Request transaction input permissions from your admin to perform stock adjustments.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
