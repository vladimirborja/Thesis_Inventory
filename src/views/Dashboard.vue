<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import AppLayout from '@/layouts/AppLayout.vue';
import {
    Users, ShieldAlert, BarChart3, Clock, AlertTriangle, PackageCheck, Truck,
    Plus, ArrowUpRight, ArrowDownRight, RefreshCw, Layers, ShoppingCart,
    TrendingUp, ChevronRight, CalendarDays, FileDown, FileSpreadsheet,
    ClipboardList,
} from 'lucide-vue-next';
import { formatCurrency } from '@/composables/useFormatCurrency';
import type {
    Product, StockTransaction, User as UserType, Warehouse,
    DashboardSummary, MonthlySalesItem, ComplianceSummary,
} from '@/types';
import { api } from '@/lib/api';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as XLSX from 'xlsx';

const authStore = useAuthStore();

const currentRole = computed(() => authStore.currentUser?.role || 'employee');
const userName    = computed(() => authStore.currentUser?.name || 'User');
const canInput    = computed(() => authStore.currentUser?.canInputTransactions ?? false);
const isAdminRole = computed(() => currentRole.value === 'admin' || currentRole.value === 'super_admin');

const products     = ref<Product[]>([]);
const transactions = ref<StockTransaction[]>([]);
const users        = ref<UserType[]>([]);
const warehouses   = ref<Warehouse[]>([]);
const isLoading    = ref(false);

const summary = ref<DashboardSummary>({ totalUsers: 0, totalBuy: 0, totalSell: 0 });
const monthlySales = ref<MonthlySalesItem[]>([]);
const salesRange = ref<6 | 12>(6);
const compliance = ref<ComplianceSummary | null>(null);

const visibleMonthlySales = computed(() =>
    monthlySales.value.slice(-salesRange.value),
);

const maxMonthlyTotal = computed(() =>
    Math.max(1, ...visibleMonthlySales.value.map((m) => m.total)),
);

const needsDailyReport = computed(() => {
    if (!canInput.value && !isAdminRole.value) return false;
    if (isAdminRole.value) return false; // admins see missing_today list instead
    return compliance.value?.todayStatus !== 'submitted';
});

// ── Calendar (wired to daily-report compliance) ──────────────────────────────
const calendarNow = new Date();
const calendarYear = calendarNow.getFullYear();
const calendarMonth = calendarNow.getMonth();
const calendarMonthLabel = calendarNow.toLocaleString('en-PH', { month: 'short', year: 'numeric' });
const calendarWeekdays = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

const complianceByDay = computed(() => {
    const map = new Map<number, string>();
    for (const d of compliance.value?.days ?? []) {
        const dt = new Date(d.date + 'T00:00:00');
        if (dt.getFullYear() === calendarYear && dt.getMonth() === calendarMonth) {
            map.set(dt.getDate(), d.status);
        }
    }
    return map;
});

const calendarCells = computed(() => {
    const firstWeekday = new Date(calendarYear, calendarMonth, 1).getDay();
    const daysInMonth = new Date(calendarYear, calendarMonth + 1, 0).getDate();
    const today = calendarNow.getDate();
    const cells: Array<{ day: number | null; isToday: boolean; status: string | null }> = [];
    for (let i = 0; i < firstWeekday; i++) cells.push({ day: null, isToday: false, status: null });
    for (let d = 1; d <= daysInMonth; d++) {
        cells.push({
            day: d,
            isToday: d === today,
            status: complianceByDay.value.get(d) ?? null,
        });
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
        const monthStart = new Date(calendarYear, calendarMonth, 1).toISOString().slice(0, 10);
        const monthEnd = new Date(calendarYear, calendarMonth + 1, 0).toISOString().slice(0, 10);

        const fetches: Promise<unknown>[] = [
            api.get<Product[]>('/products'),
            api.get<StockTransaction[]>('/transactions'),
            api.get<ComplianceSummary>(`/daily-reports/compliance?date_from=${monthStart}&date_to=${monthEnd}`),
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
        compliance.value = results[2] as ComplianceSummary;
        if (currentRole.value === 'super_admin') {
            users.value = results[3] as UserType[];
            warehouses.value = results[4] as Warehouse[];
            summary.value = results[5] as DashboardSummary;
            monthlySales.value = results[6] as MonthlySalesItem[];
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
            <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-2">
                <div>
                    <p class="text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-700/80 dark:text-emerald-400">Duque DIMS</p>
                    <h2 class="text-2xl md:text-[1.75rem] font-bold tracking-tight text-gray-900 dark:text-white mt-1">Hello, {{ userName.split(' ')[0] }}</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-xl">Daily recording with Poka-Yoke totals — then stock visibility when you need it.</p>
                </div>
            </div>

            <!-- Admin / operator compliance strip (admins only here — employees get hero below) -->
            <div
                v-if="compliance && isAdminRole"
                class="rounded-2xl border p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
                :class="compliance.missingToday.length > 0
                    ? 'bg-amber-50/90 border-amber-200 dark:bg-amber-950/20 dark:border-amber-900/40'
                    : 'bg-emerald-50/90 border-emerald-200 dark:bg-emerald-950/20 dark:border-emerald-900/40'"
            >
                <div class="space-y-1">
                    <p class="text-[10px] font-bold uppercase tracking-wider"
                        :class="compliance.missingToday.length > 0 ? 'text-amber-700 dark:text-amber-400' : 'text-emerald-700 dark:text-emerald-400'">
                        Plant compliance · today
                    </p>
                    <p class="text-sm font-semibold text-gray-900 dark:text-white">
                        <span v-if="compliance.missingToday.length === 0">All assigned operators submitted today.</span>
                        <span v-else>{{ compliance.missingToday.length }} operator(s) still open — {{ compliance.submissionRatePercent }}% submitted this month.</span>
                    </p>
                    <p class="text-[11px] text-gray-500">
                        Missing rate {{ compliance.missingRatePercent }}% · {{ compliance.submittedDays }}/{{ compliance.expectedDays }} filed
                    </p>
                </div>
                <router-link
                    to="/transactions"
                    class="shrink-0 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold text-white transition bg-emerald-700 hover:bg-emerald-800"
                >
                    <ClipboardList :size="16" />
                    Open Daily Reports
                </router-link>
            </div>

            <!-- ========================================== -->
            <!-- 1. SUPER ADMIN VIEW                        -->
            <!-- ========================================== -->
            <div v-if="currentRole === 'super_admin'" class="space-y-6">
                <!-- 1. Summary: Total Users / Total Buy / Total Sell -->
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div class="p-6 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Total Users</p>
                            <p class="text-2xl font-extrabold mt-2">{{ summary.totalUsers }}</p>
                        </div>
                        <div class="h-12 w-12 bg-blue-50 dark:bg-blue-950/20 text-blue-600 rounded-xl flex items-center justify-center">
                            <Users :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Total Buy</p>
                            <p class="text-2xl font-extrabold mt-2 text-emerald-600">{{ formatCurrency(summary.totalBuy) }}</p>
                            <p class="text-[10px] text-gray-400 mt-1">Stock-in × cost price</p>
                        </div>
                        <div class="h-12 w-12 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 rounded-xl flex items-center justify-center">
                            <ShoppingCart :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
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
                    <div class="p-5 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Audit logs</p>
                            <p class="text-xl font-extrabold mt-1">{{ transactions.length }}</p>
                        </div>
                        <Clock :size="20" class="text-indigo-500" />
                    </div>
                    <div class="p-5 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Critical alerts</p>
                            <p class="text-xl font-extrabold mt-1 text-amber-500">{{ lowStockProducts.length + outOfStockProducts.length }}</p>
                        </div>
                        <ShieldAlert :size="20" class="text-amber-500" />
                    </div>
                    <div class="p-5 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
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
                    <div class="lg:col-span-2 p-5 rounded-2xl ims-glass shadow-sm">
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

                    <!-- Mini calendar — daily report compliance colors -->
                    <div class="p-4 rounded-2xl ims-glass shadow-sm">
                        <div class="flex items-center justify-between mb-3">
                            <h3 class="font-bold text-sm flex items-center gap-1.5">
                                <CalendarDays :size="14" class="text-emerald-600" />
                                {{ calendarMonthLabel }}
                            </h3>
                            <span class="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400">
                                Daily filing
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
                                    : cell.status === 'submitted'
                                        ? 'bg-emerald-600 text-white font-bold'
                                        : cell.status === 'draft'
                                            ? 'bg-amber-400 text-white font-semibold'
                                            : cell.status === 'missing'
                                                ? 'bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400 font-semibold'
                                                : cell.isToday
                                                    ? 'ring-2 ring-emerald-600 text-gray-800 dark:text-gray-200 font-bold'
                                                    : 'text-gray-600 dark:text-gray-300'"
                                :title="cell.status ? `${cell.day}: ${cell.status}` : undefined"
                            >
                                {{ cell.day ?? '' }}
                            </div>
                        </div>
                        <div class="mt-3 flex flex-wrap gap-2 text-[9px] text-gray-500">
                            <span class="inline-flex items-center gap-1"><span class="h-2 w-2 rounded-sm bg-emerald-600" /> Submitted</span>
                            <span class="inline-flex items-center gap-1"><span class="h-2 w-2 rounded-sm bg-amber-400" /> Draft</span>
                            <span class="inline-flex items-center gap-1"><span class="h-2 w-2 rounded-sm bg-red-200" /> Missing</span>
                        </div>
                    </div>
                </div>

                <!-- Missing today operators -->
                <div v-if="compliance && compliance.missingToday.length" class="p-5 rounded-2xl ims-glass border-amber-300/60 dark:border-amber-700/40 shadow-sm">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="font-bold text-base flex items-center gap-2">
                            <AlertTriangle :size="16" class="text-amber-500" />
                            Missing today’s daily report
                        </h3>
                        <router-link to="/transactions" class="text-emerald-600 hover:underline text-xs">Review reports</router-link>
                    </div>
                    <ul class="space-y-2">
                        <li
                            v-for="row in compliance.missingToday"
                            :key="`${row.userId}-${row.date}`"
                            class="flex items-center justify-between p-3 rounded-xl bg-amber-50/80 dark:bg-amber-950/20 text-sm"
                        >
                            <span class="font-semibold text-gray-800 dark:text-gray-200">{{ row.userName || `User #${row.userId}` }}</span>
                            <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white dark:bg-gray-900 text-amber-700">{{ row.status }}</span>
                        </li>
                    </ul>
                </div>

                <!-- Users and logs layouts -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Users -->
                    <div class="admin-card p-6 ims-glass rounded-2xl">
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
                    <div class="admin-card p-6 ims-glass rounded-2xl">
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
                <!-- DIMS KPI strip -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="p-6 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Submission rate</p>
                            <p class="text-2xl font-extrabold mt-2 text-emerald-600">{{ compliance?.submissionRatePercent ?? 0 }}%</p>
                        </div>
                        <div class="h-12 w-12 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 rounded-xl flex items-center justify-center">
                            <ClipboardList :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Missing days</p>
                            <p class="text-2xl font-extrabold mt-2" :class="(compliance?.missingDays ?? 0) > 0 ? 'text-red-500' : ''">{{ compliance?.missingDays ?? 0 }}</p>
                        </div>
                        <div class="h-12 w-12 bg-red-50 dark:bg-red-950/20 text-red-500 rounded-xl flex items-center justify-center">
                            <AlertTriangle :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Low Stock SKUs</p>
                            <p class="text-2xl font-extrabold mt-2" :class="lowStockProducts.length > 0 ? 'text-amber-500' : ''">{{ lowStockProducts.length }}</p>
                        </div>
                        <div class="h-12 w-12 bg-amber-50 dark:bg-amber-950/20 text-amber-500 rounded-xl flex items-center justify-center">
                            <PackageCheck :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Out of Stock</p>
                            <p class="text-2xl font-extrabold mt-2" :class="outOfStockProducts.length > 0 ? 'text-red-500' : ''">{{ outOfStockProducts.length }}</p>
                        </div>
                        <div class="h-12 w-12 bg-red-50 dark:bg-red-950/20 text-red-500 rounded-xl flex items-center justify-center">
                            <ShieldAlert :size="22" />
                        </div>
                    </div>
                </div>

                <div v-if="compliance && compliance.missingToday.length" class="p-5 rounded-2xl ims-glass border-amber-300/60 dark:border-amber-700/40 shadow-sm">
                    <h3 class="font-bold text-base mb-3 flex items-center gap-2">
                        <AlertTriangle :size="16" class="text-amber-500" />
                        Operators missing today’s report
                    </h3>
                    <ul class="grid sm:grid-cols-2 gap-2">
                        <li
                            v-for="row in compliance.missingToday"
                            :key="`${row.userId}-${row.date}`"
                            class="flex items-center justify-between p-3 rounded-xl bg-amber-50/80 dark:bg-amber-950/20 text-sm"
                        >
                            <span class="font-semibold">{{ row.userName || `User #${row.userId}` }}</span>
                            <span class="text-[10px] font-bold uppercase text-amber-700">{{ row.status }}</span>
                        </li>
                    </ul>
                </div>

                <!-- Admin sections -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Low Stock Widget -->
                    <div class="admin-card p-6 ims-glass rounded-2xl lg:col-span-2">
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
                    <div class="admin-card p-6 ims-glass rounded-2xl flex flex-col justify-between">
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
                                <router-link to="/transactions" class="w-full flex items-center justify-between p-3 rounded-xl border border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/40 dark:bg-emerald-950/10 hover:bg-emerald-50/70 transition text-sm">
                                    <span class="flex items-center gap-2 font-semibold text-emerald-800 dark:text-emerald-300">
                                        <ClipboardList :size="16" class="text-emerald-600" />
                                        Open Daily Reports
                                    </span>
                                    <ChevronRight :size="14" class="text-emerald-400" />
                                </router-link>
                                <router-link to="/transactions" class="w-full flex items-center justify-between p-3 rounded-xl border border-gray-100 dark:border-gray-800 hover:bg-emerald-50/20 hover:border-emerald-200/30 transition text-sm">
                                    <span class="flex items-center gap-2">
                                        <Plus :size="16" class="text-emerald-600" />
                                        Log Stock Voucher
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
            <div v-if="currentRole === 'employee' && canInput" class="space-y-5">
                <!-- Single hero: daily report status + CTA -->
                <section
                    class="relative overflow-hidden rounded-3xl text-white shadow-xl shadow-emerald-900/15"
                    :class="needsDailyReport ? 'bg-[#1a4a38]' : 'bg-[#14532d]'"
                >
                    <div class="pointer-events-none absolute inset-0 opacity-50"
                        style="background: radial-gradient(ellipse 60% 80% at 100% 0%, rgba(52,211,153,0.35), transparent 55%), radial-gradient(ellipse 40% 50% at 0% 100%, rgba(0,0,0,0.25), transparent);" />
                    <div class="relative grid lg:grid-cols-[1.4fr_1fr] gap-6 p-6 md:p-8">
                        <div class="space-y-4">
                            <div class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-white/10 text-[10px] font-bold uppercase tracking-wider">
                                <span class="h-1.5 w-1.5 rounded-full" :class="needsDailyReport ? 'bg-amber-300 animate-pulse' : 'bg-emerald-300'" />
                                {{ needsDailyReport ? 'Action required' : 'Today complete' }}
                            </div>
                            <div>
                                <h3 class="text-2xl md:text-3xl font-bold tracking-tight leading-tight">
                                    <template v-if="compliance?.todayStatus === 'submitted'">Today’s sheet is locked in</template>
                                    <template v-else-if="compliance?.todayStatus === 'draft'">Finish your draft report</template>
                                    <template v-else>File today’s daily report</template>
                                </h3>
                                <p class="mt-2 text-sm text-emerald-100/85 max-w-md leading-relaxed">
                                    Auto-computed sales and balance stop manual math mistakes — the core Poka-Yoke of this DIMS.
                                </p>
                            </div>
                            <div class="flex flex-wrap gap-3 pt-1">
                                <router-link
                                    to="/transactions"
                                    class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white text-emerald-900 text-sm font-bold hover:bg-emerald-50 transition shadow-lg shadow-black/10"
                                >
                                    <ClipboardList :size="16" />
                                    {{ needsDailyReport ? 'Open daily sheet' : 'View reports' }}
                                </router-link>
                                <router-link
                                    to="/inventory"
                                    class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-white/25 text-sm font-semibold text-white/90 hover:bg-white/10 transition"
                                >
                                    Check stock
                                </router-link>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-3 content-start">
                            <div class="rounded-2xl bg-black/20 border border-white/10 p-4 backdrop-blur-sm">
                                <p class="text-[10px] font-bold uppercase tracking-wider text-emerald-200/80">Submission rate</p>
                                <p class="text-3xl font-extrabold mt-2 tabular-nums">{{ compliance?.submissionRatePercent ?? 0 }}%</p>
                                <p class="text-[11px] text-emerald-100/70 mt-1">This month</p>
                            </div>
                            <div class="rounded-2xl bg-black/20 border border-white/10 p-4 backdrop-blur-sm">
                                <p class="text-[10px] font-bold uppercase tracking-wider text-emerald-200/80">Missing days</p>
                                <p class="text-3xl font-extrabold mt-2 tabular-nums" :class="(compliance?.missingDays ?? 0) > 0 ? 'text-amber-300' : ''">{{ compliance?.missingDays ?? 0 }}</p>
                                <p class="text-[11px] text-emerald-100/70 mt-1">Of {{ compliance?.expectedDays ?? 0 }} expected</p>
                            </div>
                            <!-- Mini filing calendar -->
                            <div class="col-span-2 rounded-2xl bg-black/20 border border-white/10 p-4 backdrop-blur-sm">
                                <div class="flex items-center justify-between mb-2">
                                    <p class="text-[10px] font-bold uppercase tracking-wider text-emerald-200/80 flex items-center gap-1.5">
                                        <CalendarDays :size="12" /> {{ calendarMonthLabel }}
                                    </p>
                                    <div class="flex gap-2 text-[9px] text-emerald-100/70">
                                        <span class="inline-flex items-center gap-1"><span class="h-1.5 w-1.5 rounded-sm bg-emerald-400" /> Done</span>
                                        <span class="inline-flex items-center gap-1"><span class="h-1.5 w-1.5 rounded-sm bg-amber-400" /> Draft</span>
                                        <span class="inline-flex items-center gap-1"><span class="h-1.5 w-1.5 rounded-sm bg-red-400/80" /> Miss</span>
                                    </div>
                                </div>
                                <div class="grid grid-cols-7 gap-0.5 text-center text-[8px] font-semibold text-emerald-200/50 mb-1">
                                    <span v-for="(wd, i) in calendarWeekdays" :key="i">{{ wd }}</span>
                                </div>
                                <div class="grid grid-cols-7 gap-0.5">
                                    <div
                                        v-for="(cell, idx) in calendarCells"
                                        :key="idx"
                                        class="h-6 flex items-center justify-center rounded text-[10px]"
                                        :class="cell.day === null
                                            ? ''
                                            : cell.status === 'submitted'
                                                ? 'bg-emerald-400/90 text-[#0f3d2e] font-bold'
                                                : cell.status === 'draft'
                                                    ? 'bg-amber-400/90 text-amber-950 font-semibold'
                                                    : cell.status === 'missing'
                                                        ? 'bg-red-400/40 text-red-50 font-semibold'
                                                        : cell.isToday
                                                            ? 'ring-1 ring-white/60 font-bold'
                                                            : 'text-emerald-100/50'"
                                    >
                                        {{ cell.day ?? '' }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Compact stock tools (secondary) -->
                <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
                    <div class="lg:col-span-3 rounded-2xl ims-glass p-5 shadow-sm">
                        <div class="flex items-center justify-between mb-3">
                            <div>
                                <h3 class="font-bold text-gray-900 dark:text-white">Quick stock scan</h3>
                                <p class="text-[11px] text-gray-500 mt-0.5">Optional — for warehouse adjustments after the daily sheet.</p>
                            </div>
                            <span class="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400">Secondary</span>
                        </div>
                        <div class="flex flex-col sm:flex-row gap-3">
                            <div class="flex-1 flex gap-2">
                                <input
                                    v-model="scanBarcode"
                                    type="text"
                                    class="flex-1 px-3 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50/80 dark:bg-gray-950 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600/25"
                                    placeholder="SKU or barcode"
                                    @keyup.enter="simulateScan"
                                />
                                <button
                                    @click="simulateScan"
                                    class="px-3.5 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-semibold"
                                >
                                    Lookup
                                </button>
                            </div>
                        </div>
                        <div v-if="scannedProduct" class="mt-3 flex flex-col sm:flex-row sm:items-center gap-3 p-3 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30">
                            <div class="flex-1 min-w-0">
                                <p class="font-bold text-sm truncate">{{ scannedProduct.name }}</p>
                                <p class="text-[10px] text-gray-500">{{ scannedProduct.sku }} · {{ scannedProduct.quantity }} {{ scannedProduct.unitOfMeasure }}</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <input v-model.number="scanQty" type="number" min="1" class="w-16 px-2 py-1.5 border border-gray-200 dark:border-gray-700 rounded-lg text-xs text-center" />
                                <button @click="processScanAction('stock-in')" class="px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-[11px] font-bold">In</button>
                                <button @click="processScanAction('stock-out')" class="px-3 py-1.5 bg-red-600 text-white rounded-lg text-[11px] font-bold">Out</button>
                            </div>
                        </div>
                        <p v-if="scannerFeedback" class="mt-2 text-[11px] text-amber-700 dark:text-amber-400">{{ scannerFeedback }}</p>
                    </div>

                    <div class="lg:col-span-2 rounded-2xl ims-glass p-5 shadow-sm">
                        <h3 class="font-bold text-gray-900 dark:text-white text-sm">Sample SKUs</h3>
                        <p class="text-[11px] text-gray-500 mt-0.5 mb-3">Tap to fill the scanner</p>
                        <div class="space-y-1.5">
                            <button
                                v-for="p in products.slice(0, 4)"
                                :key="p.id"
                                type="button"
                                class="w-full text-left px-3 py-2 rounded-xl hover:bg-emerald-50 dark:hover:bg-emerald-950/30 transition border border-transparent hover:border-emerald-100 dark:hover:border-emerald-900/40"
                                @click="scanBarcode = p.barcode || p.sku; simulateScan()"
                            >
                                <p class="text-xs font-bold text-gray-800 dark:text-gray-200 truncate">{{ p.name }}</p>
                                <p class="text-[10px] text-gray-400 font-mono mt-0.5">{{ p.sku }}</p>
                            </button>
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
                    <div class="p-6 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Total Products</p>
                            <p class="text-2xl font-extrabold mt-2">{{ totalProducts }}</p>
                        </div>
                        <div class="h-12 w-12 bg-blue-50 dark:bg-blue-950/20 text-blue-600 rounded-xl flex items-center justify-center">
                            <PackageCheck :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Inventory Value</p>
                            <p class="text-2xl font-extrabold mt-2 text-emerald-600">{{ formatCurrency(totalValuation) }}</p>
                        </div>
                        <div class="h-12 w-12 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 rounded-xl flex items-center justify-center">
                            <BarChart3 :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
                        <div>
                            <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Low Stock Items</p>
                            <p class="text-2xl font-extrabold mt-2" :class="lowStockProducts.length > 0 ? 'text-amber-500' : ''">{{ lowStockProducts.length }}</p>
                        </div>
                        <div class="h-12 w-12 bg-amber-50 dark:bg-amber-950/20 text-amber-500 rounded-xl flex items-center justify-center">
                            <AlertTriangle :size="22" />
                        </div>
                    </div>

                    <div class="p-6 rounded-2xl ims-glass shadow-sm flex items-center justify-between">
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
                    <div class="p-6 ims-glass rounded-2xl lg:col-span-2">
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
                    <div class="p-6 ims-glass rounded-2xl flex flex-col justify-between">
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
