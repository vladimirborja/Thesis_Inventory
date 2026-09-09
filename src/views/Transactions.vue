<script setup lang="ts">
import { computed, ref, onMounted, nextTick, watch } from 'vue';
import { useAuthStore } from '@/stores/auth';
import AppLayout from '@/layouts/AppLayout.vue';
import DateRangeFilter from '@/components/DateRangeFilter.vue';
import {
    Search, Plus, X, ArrowUpRight, ArrowDownRight, RefreshCw, Info,
    ClipboardList, Calendar, FileText, Send, CheckCircle2,
    ChevronDown, ChevronUp, AlertCircle,
} from 'lucide-vue-next';
import type { StockTransaction, Product, Warehouse } from '@/types';
import { api } from '@/lib/api';
import { Chart, ArcElement, Tooltip, Legend, PieController } from 'chart.js';

Chart.register(ArcElement, Tooltip, Legend, PieController);

// ─── Auth ────────────────────────────────────────────────────────────────────
const authStore   = useAuthStore();
const currentRole = computed(() => authStore.currentUser?.role || 'employee');
const canInput    = computed(() => authStore.currentUser?.canInputTransactions ?? false);
const isAdminRole = computed(() => currentRole.value === 'admin' || currentRole.value === 'super_admin');

const activeTab = ref<'stock-vouchers' | 'daily-reports'>(
    canInput.value && currentRole.value === 'employee' ? 'daily-reports' : 'stock-vouchers'
);

// ─────────────────────────────────────────────────────────────────────────────
// TAB 1 — STOCK VOUCHERS
// ─────────────────────────────────────────────────────────────────────────────

const transactions = ref<StockTransaction[]>([]);
const products     = ref<Product[]>([]);
const warehouses   = ref<Warehouse[]>([]);
const isLoadingTx  = ref(false);
const isSavingTx   = ref(false);
const searchQuery  = ref('');
const selectedType = ref('');
const isVoucherModalOpen = ref(false);

const formProductId   = ref<number>(0);
const formWarehouseId = ref<number>(1);
const formType        = ref<'stock-in' | 'stock-out' | 'adjustment' | 'transfer'>('stock-in');
const formQty         = ref(10);
const formRef         = ref('');
const formNotes       = ref('');

const filteredTransactions = computed(() => {
    const q = searchQuery.value.toLowerCase();
    return transactions.value.filter(t => {
        const matchesSearch = !q ||
            t.productName.toLowerCase().includes(q) ||
            (t.referenceNumber && t.referenceNumber.toLowerCase().includes(q)) ||
            t.userName.toLowerCase().includes(q);
        const matchesType = !selectedType.value || t.type === selectedType.value;
        return matchesSearch && matchesType;
    });
});

async function loadStockData() {
    isLoadingTx.value = true;
    try {
        [transactions.value, products.value, warehouses.value] = await Promise.all([
            api.get<StockTransaction[]>('/transactions'),
            api.get<Product[]>('/products'),
            api.get<Warehouse[]>('/warehouses'),
        ]);
        if (products.value.length) formProductId.value = products.value[0]!.id;
    } finally {
        isLoadingTx.value = false;
    }
}

function openVoucherModal() {
    formProductId.value   = products.value[0]?.id || 0;
    formWarehouseId.value = warehouses.value[0]?.id || 1;
    formType.value        = 'stock-in';
    formQty.value         = 10;
    formRef.value         = 'PO-' + Math.floor(1000 + Math.random() * 9000);
    formNotes.value       = '';
    isVoucherModalOpen.value = true;
}

async function handleVoucherSave() {
    if (!formProductId.value) return;
    isSavingTx.value = true;
    try {
        await api.post('/transactions', {
            product_id:       formProductId.value,
            warehouse_id:     formWarehouseId.value,
            type:             formType.value,
            quantity:         formQty.value,
            reference_number: formRef.value,
            notes:            formNotes.value,
        });
        await loadStockData();
        isVoucherModalOpen.value = false;
    } catch (e: unknown) {
        alert(e instanceof Error ? e.message : 'Failed to save transaction');
    } finally {
        isSavingTx.value = false;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// TAB 2 — DAILY REPORTS
// ─────────────────────────────────────────────────────────────────────────────

interface LineItem {
    category: string;
    product_name: string;
    weight: string | null;
    load_in: string | null;           // text — can be "20 + 7"
    load_out_bundle: string | null;   // text — same format
    load_out_piece: number | null;
    sales_bundle: number | null;
    sales_piece: number | null;
    sales_peso_bundle: number | null;
    sales_peso_piece: number | null;
    total_sales: number;
    sort_order: number;
}

interface DenomForm {
    bill_1000: number; bill_500: number; bill_200: number;
    bill_100: number;  bill_50: number;  bill_20: number; coins: number;
}

interface DailyReport {
    id: number; userId: number; userName?: string; reportDate: string;
    clientName?: string; totalSales: number; cashCollection: number;
    checksCollection: number; creditSales: number; expenses: number;
    balance: number; status: string; notes?: string; createdAt?: string;
    items: LineItem[];
    denominations?: {
        bill1000: number; bill500: number; bill200: number;
        bill100: number;  bill50: number;  bill20: number;
        coins: number; totalAmount: number;
    };
}

const reports          = ref<DailyReport[]>([]);
const isLoadingRpt     = ref(false);
const isSavingRpt      = ref(false);
const isDailyModalOpen = ref(false);
const successReport    = ref<DailyReport | null>(null);
const expandedId       = ref<number | null>(null);
const dateFilter       = ref<{ from: string; to: string } | null>(null);
const templateRows     = ref<LineItem[]>([]);

// Form state
const formDate     = ref(new Date().toISOString().slice(0, 10));
const formClient   = ref('');
const formPrepared = ref('');
const formCash     = ref(0);
const formChecks   = ref(0);
const formCredit   = ref(0);
const formExpenses = ref(0);
const formBalance  = ref(0);
const formRptNotes = ref('');
const formStatus   = ref<'draft' | 'submitted'>('submitted');
const formItems    = ref<LineItem[]>([]);
const formDenom    = ref<DenomForm>({ bill_1000: 0, bill_500: 0, bill_200: 0, bill_100: 0, bill_50: 0, bill_20: 0, coins: 0 });

// ── Reactive totals ─────────────────────────────────────────────────────────
// Using a computed ARRAY so every cell keystroke triggers live re-render
const rowTotals = computed<number[]>(() =>
    formItems.value.map(item =>
        (item.sales_peso_bundle ?? 0) + (item.sales_peso_piece ?? 0)
    )
);
const grandTotal = computed<number>(() =>
    rowTotals.value.reduce((sum, v) => sum + v, 0)
);

// Denomination auto-total
const denomTotal = computed(() =>
    formDenom.value.bill_1000 * 1000 + formDenom.value.bill_500 * 500 +
    formDenom.value.bill_200  * 200  + formDenom.value.bill_100 * 100 +
    formDenom.value.bill_50   * 50   + formDenom.value.bill_20  * 20  +
    formDenom.value.coins
);

// Grouped items for category-header rows
const groupedItems = computed(() => {
    const groups: Record<string, Array<LineItem & { _idx: number }>> = {};
    formItems.value.forEach((item, idx) => {
        if (!groups[item.category]) groups[item.category] = [];
        groups[item.category].push({ ...item, _idx: idx });
    });
    return groups;
});

async function loadTemplate() {
    try { templateRows.value = await api.get<LineItem[]>('/daily-reports/template'); }
    catch { templateRows.value = []; }
}

async function loadReports() {
    isLoadingRpt.value = true;
    try {
        const params = new URLSearchParams();
        if (dateFilter.value?.from) params.set('report_date', dateFilter.value.from);
        const qs = params.toString() ? `?${params}` : '';
        reports.value = await api.get<DailyReport[]>(`/daily-reports${qs}`);
    } finally {
        isLoadingRpt.value = false;
    }
}
watch(dateFilter, () => loadReports());

// Validation — all numeric fields required, load_in/load_out_bundle can be any non-empty string
const validationErrors = computed(() => {
    const errs: string[] = [];
    formItems.value.forEach((item, i) => {
        const lbl = item.weight ? `${item.product_name} (${item.weight})` : item.product_name;
        if (!item.load_in && item.load_in !== '0')       errs.push(`Row ${i+1} "${lbl}": Load-in`);
        if (!item.load_out_bundle && item.load_out_bundle !== '0') errs.push(`Row ${i+1} "${lbl}": Load-out/Bdl`);
        if (item.load_out_piece   === null)              errs.push(`Row ${i+1} "${lbl}": Load-out/Pc`);
        if (item.sales_bundle     === null)              errs.push(`Row ${i+1} "${lbl}": Sales/Bdl`);
        if (item.sales_piece      === null)              errs.push(`Row ${i+1} "${lbl}": Sales/Pc`);
        if (item.sales_peso_bundle === null)             errs.push(`Row ${i+1} "${lbl}": ₱/Bdl`);
        if (item.sales_peso_piece  === null)             errs.push(`Row ${i+1} "${lbl}": ₱/Pc`);
    });
    return errs;
});
const isFormValid = computed(() => validationErrors.value.length === 0 && formDate.value.length > 0);

async function loadReportForDate(dateStr: string) {
    if (!dateStr) return;
    try {
        const existing = await api.get<DailyReport>(`/daily-reports/by-date/${dateStr}`);
        formClient.value   = existing.clientName || '';
        formPrepared.value = existing.userName || authStore.currentUser?.name || '';
        formCash.value     = existing.cashCollection;
        formChecks.value   = existing.checksCollection;
        formCredit.value   = existing.creditSales;
        formExpenses.value = existing.expenses;
        formBalance.value  = existing.balance;
        formRptNotes.value = existing.notes || '';
        formStatus.value   = existing.status as 'draft' | 'submitted';
        if (existing.denominations) {
            formDenom.value = {
                bill_1000: existing.denominations.bill1000,
                bill_500: existing.denominations.bill500,
                bill_200: existing.denominations.bill200,
                bill_100: existing.denominations.bill100,
                bill_50: existing.denominations.bill50,
                bill_20: existing.denominations.bill20,
                coins: existing.denominations.coins,
            };
        }
        if (existing.items && existing.items.length > 0) {
            formItems.value = existing.items.map(r => ({
                ...r,
                load_in: r.load_in !== undefined && r.load_in !== null ? String(r.load_in) : null,
                load_out_bundle: r.load_out_bundle !== undefined && r.load_out_bundle !== null ? String(r.load_out_bundle) : null,
            }));
        }
    } catch (e: any) {
        // If not found, fall back to blank template
        formClient.value   = '';
        formPrepared.value = authStore.currentUser?.name ?? '';
        formCash.value     = 0;
        formChecks.value   = 0;
        formCredit.value   = 0;
        formExpenses.value = 0;
        formBalance.value  = 0;
        formRptNotes.value = '';
        formStatus.value   = 'submitted';
        formDenom.value    = { bill_1000: 0, bill_500: 0, bill_200: 0, bill_100: 0, bill_50: 0, bill_20: 0, coins: 0 };
        formItems.value    = templateRows.value.map(r => ({
            ...r,
            load_in: null, load_out_bundle: null, load_out_piece: null,
            sales_bundle: null, sales_piece: null,
            sales_peso_bundle: null, sales_peso_piece: null,
            total_sales: 0,
        }));
    }
}

watch(formDate, (newDate) => {
    if (isDailyModalOpen.value && newDate) {
        loadReportForDate(newDate);
    }
});

function openDailyModal() {
    const today = new Date().toISOString().slice(0, 10);
    // If it's already today, just load it. Otherwise, setting formDate will trigger the watcher.
    if (formDate.value === today) {
        loadReportForDate(today);
    } else {
        formDate.value = today;
    }
    isDailyModalOpen.value = true;
}

async function handleDailySubmit() {
    if (!isFormValid.value) {
        alert(`${validationErrors.value.length} field(s) required — fill all rows completely.`);
        return;
    }
    isSavingRpt.value = true;
    try {
        const payload = {
            report_date:       formDate.value,
            client_name:       formClient.value || null,
            cash_collection:   formCash.value,
            checks_collection: formChecks.value,
            credit_sales:      formCredit.value,
            expenses:          formExpenses.value,
            balance:           formBalance.value,
            status:            formStatus.value,
            notes:             formRptNotes.value || null,
            items: formItems.value.map((item, idx) => ({
                ...item,
                total_sales: rowTotals.value[idx] ?? 0,
            })),
            denominations: formDenom.value,
        };
        const created = await api.post<DailyReport>('/daily-reports/upsert', payload);
        isDailyModalOpen.value = false;
        successReport.value    = created;
        await loadReports();
        await nextTick();
        renderPieChart(created);
        document.getElementById('pie-section')?.scrollIntoView({ behavior: 'smooth' });
    } catch (e: unknown) {
        alert(e instanceof Error ? e.message : 'Failed to save report');
    } finally {
        isSavingRpt.value = false;
    }
}

// ─── Pie Chart ────────────────────────────────────────────────────────────────
let pieInstance: Chart | null = null;
function renderPieChart(report: DailyReport) {
    const canvas = document.getElementById('daily-pie-chart') as HTMLCanvasElement | null;
    if (!canvas) return;
    if (pieInstance) { pieInstance.destroy(); pieInstance = null; }
    const catMap: Record<string, number> = {};
    report.items.forEach(item => {
        const val = (item.sales_peso_bundle ?? 0) + (item.sales_peso_piece ?? 0);
        catMap[item.category] = (catMap[item.category] ?? 0) + val;
    });
    const PALETTE = ['#10b981','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#ec4899','#84cc16','#f97316','#6366f1'];
    pieInstance = new Chart(canvas, {
        type: 'pie',
        data: {
            labels: Object.keys(catMap),
            datasets: [{ data: Object.values(catMap), backgroundColor: PALETTE, borderWidth: 2, borderColor: '#fff', hoverOffset: 8 }],
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { font: { size: 11 }, padding: 14, boxWidth: 12 } },
                tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ₱${Number(ctx.raw).toLocaleString('en-PH', { minimumFractionDigits: 2 })}` } },
            },
        },
    });
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function fmtPeso(n: number | null | undefined) {
    if (n === null || n === undefined) return '—';
    return `₱${Number(n).toLocaleString('en-PH', { minimumFractionDigits: 2 })}`;
}
function fmtNum(n: number) {
    return n.toLocaleString('en-PH', { minimumFractionDigits: 2 });
}
function statusBadge(s: string) {
    return s === 'submitted'
        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400'
        : 'bg-amber-50 text-amber-600 dark:bg-amber-950/20 dark:text-amber-400';
}
const CATEGORY_COLORS: Record<string, string> = {
    'TOCINO':            'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300',
    'PORK HOTDOG':       'bg-rose-100 text-rose-800 dark:bg-rose-950/30 dark:text-rose-300',
    'CHICKEN HOTDOG':    'bg-amber-100 text-amber-800 dark:bg-amber-950/30 dark:text-amber-300',
    'LONGANISA':         'bg-purple-100 text-purple-800 dark:bg-purple-950/30 dark:text-purple-300',
    'EMBOTIDO':          'bg-blue-100 text-blue-800 dark:bg-blue-950/30 dark:text-blue-300',
    'Hamburger Patties': 'bg-orange-100 text-orange-800 dark:bg-orange-950/30 dark:text-orange-300',
    'HAM':               'bg-pink-100 text-pink-800 dark:bg-pink-950/30 dark:text-pink-300',
    'SAUSAGES':          'bg-cyan-100 text-cyan-800 dark:bg-cyan-950/30 dark:text-cyan-300',
};
const catColor = (c: string) => CATEGORY_COLORS[c] ?? 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';

// ─── Mount ────────────────────────────────────────────────────────────────────
onMounted(async () => {
    await Promise.all([loadStockData(), loadTemplate(), loadReports()]);
});
</script>

<template>
    <AppLayout>
        <div class="space-y-5">

            <!-- ── Page Header ──────────────────────────────────────────── -->
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h2 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">Transactions</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Stock voucher audit trail and daily report entry.</p>
                </div>
                <div class="flex items-center gap-3">
                    <template v-if="activeTab === 'stock-vouchers' && isAdminRole">
                        <button @click="openVoucherModal"
                            class="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/10 transition">
                            <Plus :size="15" /> Log Stock Voucher
                        </button>
                    </template>
                    <template v-if="activeTab === 'daily-reports'">
                        <DateRangeFilter v-model="dateFilter" placeholder="Filter by date" />
                        <button v-if="canInput || isAdminRole" @click="openDailyModal"
                            class="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/10 transition">
                            <Plus :size="15" /> Add Data
                        </button>
                    </template>
                </div>
            </div>

            <!-- ── Tabs ─────────────────────────────────────────────────── -->
            <div class="flex gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-2xl w-fit">
                <button @click="activeTab = 'stock-vouchers'"
                    class="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition"
                    :class="activeTab === 'stock-vouchers' ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'">
                    <ArrowUpRight :size="14" /> Stock Vouchers
                </button>
                <button @click="activeTab = 'daily-reports'"
                    class="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition"
                    :class="activeTab === 'daily-reports' ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'">
                    <ClipboardList :size="14" /> Daily Reports
                    <span v-if="reports.length > 0" class="px-1.5 py-0.5 bg-emerald-100 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 rounded-full text-[9px] font-bold">{{ reports.length }}</span>
                </button>
            </div>

            <!-- ══════════════════════════════════════════════════════════ -->
            <!-- TAB 1 — STOCK VOUCHERS                                    -->
            <!-- ══════════════════════════════════════════════════════════ -->
            <div v-if="activeTab === 'stock-vouchers'" class="space-y-4">
                <div class="p-4 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
                    <div class="relative flex-1 max-w-md">
                        <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400"><Search :size="16" /></span>
                        <input v-model="searchQuery" type="text" class="w-full pl-9 pr-4 py-2 rounded-xl border border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-600/30" placeholder="Search product, voucher ref, operator…" />
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-gray-400 font-medium">Type:</span>
                        <select v-model="selectedType" class="px-3 py-2 border border-gray-100 dark:border-gray-800 rounded-xl bg-gray-50 dark:bg-gray-950 text-xs focus:outline-none">
                            <option value="">All Transactions</option>
                            <option value="stock-in">Stock-In (Receipt)</option>
                            <option value="stock-out">Stock-Out (Release)</option>
                            <option value="adjustment">Stock Adjustment</option>
                            <option value="transfer">Stock Transfer</option>
                        </select>
                    </div>
                </div>
                <div class="overflow-x-auto bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
                    <table class="w-full text-left border-collapse text-xs md:text-sm">
                        <thead class="bg-gray-50 dark:bg-gray-800/80 text-gray-400 border-b border-gray-100 dark:border-gray-800 uppercase text-[10px] tracking-wider font-bold">
                            <tr>
                                <th class="px-6 py-4">Transaction Details</th>
                                <th class="px-6 py-4">Voucher Ref</th>
                                <th class="px-6 py-4">Qty Altered</th>
                                <th class="px-6 py-4">Operator / Time</th>
                                <th class="px-6 py-4">Remarks</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-50 dark:divide-gray-800/50">
                            <tr v-if="filteredTransactions.length === 0"><td colspan="5" class="px-6 py-12 text-center text-gray-400">No stock vouchers registered.</td></tr>
                            <tr v-for="t in filteredTransactions" :key="t.id" class="hover:bg-gray-50/50 dark:hover:bg-gray-850 transition">
                                <td class="px-6 py-4">
                                    <div class="flex items-center gap-3">
                                        <div class="h-8 w-8 rounded-lg flex items-center justify-center" :class="t.type === 'stock-in' ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600' : t.type === 'stock-out' ? 'bg-red-50 dark:bg-red-950/20 text-red-600' : 'bg-gray-100 dark:bg-gray-800 text-gray-500'">
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
                                <td class="px-6 py-4 font-mono text-xs font-semibold text-gray-600 dark:text-gray-400">{{ t.referenceNumber || 'N/A' }}</td>
                                <td class="px-6 py-4">
                                    <span class="font-extrabold text-sm" :class="t.type === 'stock-in' ? 'text-emerald-600' : t.type === 'stock-out' ? 'text-red-500' : 'text-gray-600 dark:text-gray-300'">{{ t.type === 'stock-in' ? '+' : '-' }}{{ t.quantity }}</span>
                                    <span class="text-[9px] font-bold uppercase mt-1 block px-2 py-0.5 rounded w-fit" :class="t.type === 'stock-in' ? 'bg-emerald-50 text-emerald-700' : t.type === 'stock-out' ? 'bg-red-50 text-red-700' : 'bg-gray-100 text-gray-700'">{{ t.type.replace('-', ' ') }}</span>
                                </td>
                                <td class="px-6 py-4 text-xs"><p class="font-bold text-gray-800 dark:text-gray-200">{{ t.userName }}</p><p class="text-[10px] text-gray-400 mt-0.5">{{ t.createdAt }}</p></td>
                                <td class="px-6 py-4 text-xs text-gray-500 max-w-xs truncate"><div class="flex items-center gap-1"><Info :size="12" class="text-gray-400 shrink-0" /><span>{{ t.notes || 'No remarks.' }}</span></div></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- ══════════════════════════════════════════════════════════ -->
            <!-- TAB 2 — DAILY REPORTS                                     -->
            <!-- ══════════════════════════════════════════════════════════ -->
            <div v-if="activeTab === 'daily-reports'" class="space-y-4">

                <!-- Post-submission Pie Chart -->
                <Transition name="slide-up">
                <div v-if="successReport" id="pie-section"
                    class="grid grid-cols-1 lg:grid-cols-2 gap-6 bg-white dark:bg-gray-900 border border-emerald-200 dark:border-emerald-800 rounded-2xl p-6 shadow-md">
                    <div>
                        <div class="flex items-center gap-2 mb-1"><CheckCircle2 :size="18" class="text-emerald-600" /><h3 class="text-base font-bold text-gray-900 dark:text-white">Report Submitted!</h3></div>
                        <p class="text-xs text-gray-500 mb-4">{{ successReport.reportDate }} · {{ successReport.userName ?? 'You' }}</p>
                        <div class="grid grid-cols-2 gap-3 text-xs">
                            <div class="p-3 bg-emerald-50 dark:bg-emerald-950/20 rounded-xl"><p class="text-gray-500">Total Sales</p><p class="font-extrabold text-emerald-700 dark:text-emerald-400 text-sm mt-0.5">{{ fmtPeso(successReport.totalSales) }}</p></div>
                            <div class="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-xl"><p class="text-gray-500">Cash Collection</p><p class="font-extrabold text-blue-700 dark:text-blue-400 text-sm mt-0.5">{{ fmtPeso(successReport.cashCollection) }}</p></div>
                            <div class="p-3 bg-amber-50 dark:bg-amber-950/20 rounded-xl"><p class="text-gray-500">Expenses</p><p class="font-extrabold text-amber-700 text-sm mt-0.5">{{ fmtPeso(successReport.expenses) }}</p></div>
                            <div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl"><p class="text-gray-500">Balance</p><p class="font-extrabold text-gray-800 dark:text-gray-200 text-sm mt-0.5">{{ fmtPeso(successReport.balance) }}</p></div>
                        </div>
                    </div>
                    <div class="flex flex-col items-center justify-center">
                        <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Sales by Category</p>
                        <div class="relative w-60 h-60"><canvas id="daily-pie-chart"></canvas></div>
                    </div>
                </div>
                </Transition>

                <!-- History list -->
                <div>
                    <div class="flex items-center gap-2 mb-3"><FileText :size="14" class="text-gray-500" /><span class="text-sm font-bold text-gray-700 dark:text-gray-300">Report History</span></div>
                    <div v-if="isLoadingRpt" class="space-y-3"><div v-for="i in 3" :key="i" class="h-16 bg-gray-100 dark:bg-gray-800 rounded-2xl animate-pulse" /></div>
                    <div v-else-if="reports.length === 0" class="flex flex-col items-center justify-center py-16 bg-white dark:bg-gray-900 border border-dashed border-gray-200 dark:border-gray-700 rounded-2xl">
                        <ClipboardList :size="32" class="text-gray-300 dark:text-gray-600 mb-3" />
                        <p class="font-bold text-gray-500">No reports yet</p>
                        <p class="text-xs text-gray-400 mt-1">{{ (canInput || isAdminRole) ? 'Click "Add Data" to submit your first daily report.' : 'No reports found for the selected period.' }}</p>
                    </div>
                    <div v-else class="space-y-3">
                        <div v-for="report in reports" :key="report.id" class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm overflow-hidden">
                            <button @click="expandedId = expandedId === report.id ? null : report.id" class="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/40 transition text-left">
                                <div class="flex items-center gap-3">
                                    <div class="h-9 w-9 bg-emerald-50 dark:bg-emerald-950/20 rounded-xl flex items-center justify-center"><Calendar :size="16" class="text-emerald-600" /></div>
                                    <div>
                                        <p class="font-bold text-gray-900 dark:text-white text-sm">{{ report.reportDate }}</p>
                                        <p class="text-[10px] text-gray-400 mt-0.5">{{ report.userName ?? 'You' }}<span v-if="report.clientName"> · {{ report.clientName }}</span></p>
                                    </div>
                                </div>
                                <div class="flex items-center gap-4">
                                    <div class="text-right hidden sm:block"><p class="text-xs font-bold text-emerald-700 dark:text-emerald-400">{{ fmtPeso(report.totalSales) }}</p><p class="text-[10px] text-gray-400">Total Sales</p></div>
                                    <span class="px-2.5 py-1 text-[9px] font-bold rounded-full uppercase" :class="statusBadge(report.status)">{{ report.status }}</span>
                                    <component :is="expandedId === report.id ? ChevronUp : ChevronDown" :size="15" class="text-gray-400" />
                                </div>
                            </button>
                            <Transition name="expand">
                            <div v-if="expandedId === report.id" class="border-t border-gray-100 dark:border-gray-800">
                                <div class="grid grid-cols-2 md:grid-cols-4 divide-x divide-y md:divide-y-0 divide-gray-100 dark:divide-gray-800">
                                    <div class="p-4 text-center"><p class="text-[10px] text-gray-400 uppercase font-semibold">Cash</p><p class="font-bold text-sm mt-1">{{ fmtPeso(report.cashCollection) }}</p></div>
                                    <div class="p-4 text-center"><p class="text-[10px] text-gray-400 uppercase font-semibold">Checks</p><p class="font-bold text-sm mt-1">{{ fmtPeso(report.checksCollection) }}</p></div>
                                    <div class="p-4 text-center"><p class="text-[10px] text-gray-400 uppercase font-semibold">Expenses</p><p class="font-bold text-amber-600 text-sm mt-1">{{ fmtPeso(report.expenses) }}</p></div>
                                    <div class="p-4 text-center"><p class="text-[10px] text-gray-400 uppercase font-semibold">Balance</p><p class="font-bold text-blue-700 dark:text-blue-400 text-sm mt-1">{{ fmtPeso(report.balance) }}</p></div>
                                </div>
                                <div v-if="report.items.length > 0" class="overflow-x-auto border-t border-gray-100 dark:border-gray-800">
                                    <table class="w-full text-xs">
                                        <thead class="bg-gray-50 dark:bg-gray-800/60 text-gray-400 uppercase text-[9px] tracking-wider font-bold">
                                            <tr>
                                                <th class="px-4 py-2.5 text-left">Product</th>
                                                <th class="px-4 py-2.5 text-center">Load-In</th>
                                                <th class="px-4 py-2.5 text-center">Out/Bdl</th>
                                                <th class="px-4 py-2.5 text-center">Out/Pc</th>
                                                <th class="px-4 py-2.5 text-center">Sales/Bdl</th>
                                                <th class="px-4 py-2.5 text-center">Sales/Pc</th>
                                                <th class="px-4 py-2.5 text-right">₱/Bdl</th>
                                                <th class="px-4 py-2.5 text-right">₱/Pc</th>
                                                <th class="px-4 py-2.5 text-right text-emerald-700">Total ₱</th>
                                            </tr>
                                        </thead>
                                        <tbody class="divide-y divide-gray-50 dark:divide-gray-800/50">
                                            <tr v-for="item in report.items" :key="item.sort_order" class="hover:bg-gray-50/50">
                                                <td class="px-4 py-2">
                                                    <div class="flex items-center gap-2">
                                                        <span class="px-1.5 py-0.5 rounded text-[8px] font-bold shrink-0" :class="catColor(item.category)">{{ item.category }}</span>
                                                        <span class="font-semibold text-gray-800 dark:text-gray-200">{{ item.product_name }}</span>
                                                        <span v-if="item.weight" class="text-gray-400 text-[10px]">{{ item.weight }}</span>
                                                    </div>
                                                </td>
                                                <td class="px-4 py-2 text-center text-gray-600 dark:text-gray-400">{{ item.load_in ?? '—' }}</td>
                                                <td class="px-4 py-2 text-center text-gray-600 dark:text-gray-400">{{ item.load_out_bundle ?? '—' }}</td>
                                                <td class="px-4 py-2 text-center text-gray-600 dark:text-gray-400">{{ item.load_out_piece ?? '—' }}</td>
                                                <td class="px-4 py-2 text-center text-gray-600 dark:text-gray-400">{{ item.sales_bundle ?? '—' }}</td>
                                                <td class="px-4 py-2 text-center text-gray-600 dark:text-gray-400">{{ item.sales_piece ?? '—' }}</td>
                                                <td class="px-4 py-2 text-right text-gray-600 dark:text-gray-400">{{ fmtPeso(item.sales_peso_bundle) }}</td>
                                                <td class="px-4 py-2 text-right text-gray-600 dark:text-gray-400">{{ fmtPeso(item.sales_peso_piece) }}</td>
                                                <td class="px-4 py-2 text-right font-bold text-emerald-700 dark:text-emerald-400">{{ fmtPeso(item.total_sales) }}</td>
                                            </tr>
                                        </tbody>
                                        <tfoot>
                                            <tr class="bg-[#1e3a5f] text-white">
                                                <td colspan="8" class="px-4 py-2.5 font-bold text-xs uppercase tracking-wider text-right">TOTAL SALES</td>
                                                <td class="px-4 py-2.5 text-right font-black text-sm">{{ fmtPeso(report.totalSales) }}</td>
                                            </tr>
                                        </tfoot>
                                    </table>
                                </div>
                            </div>
                            </Transition>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ═══════════════════════════════════════════════════════════════ -->
        <!-- STOCK VOUCHER MODAL                                            -->
        <!-- ═══════════════════════════════════════════════════════════════ -->
        <Teleport to="body">
        <Transition name="modal-fade">
        <div v-if="isVoucherModalOpen" class="fixed inset-0 z-50 flex items-center justify-center px-4">
            <div @click="isVoucherModalOpen = false" class="fixed inset-0 bg-black/40 backdrop-blur-sm" />
            <div class="relative bg-white dark:bg-gray-900 rounded-3xl w-full max-w-md p-6 md:p-8 shadow-2xl border border-gray-100 dark:border-gray-800 space-y-6">
                <button @click="isVoucherModalOpen = false" class="absolute top-4 right-4 p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-400"><X :size="18" /></button>
                <div><h3 class="text-xl font-bold text-gray-900 dark:text-white">Log Stock Voucher</h3><p class="text-xs text-gray-400 mt-1">Manual adjustment or warehouse receiving audit.</p></div>
                <form @submit.prevent="handleVoucherSave" class="space-y-4">
                    <div class="space-y-1">
                        <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Target Catalog Product</label>
                        <select v-model="formProductId" class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-950 text-sm focus:outline-none" required>
                            <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }} (SKU: {{ p.sku }})</option>
                        </select>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Adjustment Type</label>
                            <select v-model="formType" class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-950 text-sm focus:outline-none" required>
                                <option value="stock-in">Stock-In (Receipt)</option>
                                <option value="stock-out">Stock-Out (Dispatch)</option>
                                <option value="adjustment">Inventory Reconciliation</option>
                            </select>
                        </div>
                        <div class="space-y-1">
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Warehouse Node</label>
                            <select v-model="formWarehouseId" class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-950 text-sm focus:outline-none" required>
                                <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
                            </select>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="space-y-1"><label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Quantity</label><input v-model.number="formQty" type="number" min="1" class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none" required /></div>
                        <div class="space-y-1"><label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Voucher Reference</label><input v-model="formRef" type="text" class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none" placeholder="PO-2026-000" /></div>
                    </div>
                    <div class="space-y-1"><label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Voucher Notes</label><textarea v-model="formNotes" class="w-full px-4 py-2 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-sm focus:outline-none h-16" placeholder="Explain reason for stock movement…"></textarea></div>
                    <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-100 dark:border-gray-800">
                        <button type="button" @click="isVoucherModalOpen = false" class="px-4 py-2.5 border border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300 text-xs font-semibold rounded-xl hover:bg-gray-50">Cancel</button>
                        <button type="submit" class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl">Submit Voucher</button>
                    </div>
                </form>
            </div>
        </div>
        </Transition>
        </Teleport>

        <!-- ═══════════════════════════════════════════════════════════════ -->
        <!-- DAILY REPORT MODAL — matches Excel layout                     -->
        <!-- ═══════════════════════════════════════════════════════════════ -->
        <Teleport to="body">
        <Transition name="modal-fade">
        <div v-if="isDailyModalOpen" class="fixed inset-0 z-50 flex items-start justify-center px-2 py-4 overflow-y-auto">
            <div @click="isDailyModalOpen = false" class="fixed inset-0 bg-black/50 backdrop-blur-sm" />
            <div class="relative bg-white dark:bg-gray-900 rounded-2xl w-full max-w-6xl shadow-2xl border border-gray-200 dark:border-gray-700 my-4">

                <!-- ── Modal Header (matches Excel header) ─────────────── -->
                <div class="bg-[#1e3a5f] text-white rounded-t-2xl px-6 py-4">
                    <h3 class="text-center text-base font-bold tracking-wide uppercase">DUQUE FOOD PRODUCTS — DAILY TRANSACTION REPORT</h3>
                    <div class="flex flex-wrap justify-center gap-6 mt-2 text-xs text-blue-200">
                        <span>Date: <input v-model="formDate" type="date" class="bg-transparent border-b border-blue-300 text-white text-xs focus:outline-none ml-1 w-36" /></span>
                        <span>Client: <input v-model="formClient" type="text" placeholder="—" class="bg-transparent border-b border-blue-300 text-white text-xs focus:outline-none ml-1 w-36" /></span>
                        <span>Prepared by: <input v-model="formPrepared" type="text" placeholder="—" class="bg-transparent border-b border-blue-300 text-white text-xs focus:outline-none ml-1 w-32" /></span>
                    </div>
                </div>

                <!-- ── Live Grand Total Banner ─────────────────────────── -->
                <div class="flex items-center justify-between px-6 py-3 bg-emerald-50 dark:bg-emerald-950/20 border-b border-emerald-200 dark:border-emerald-800">
                    <span class="text-xs font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">Running Total Sales</span>
                    <span class="text-xl font-black text-emerald-700 dark:text-emerald-400 tabular-nums transition-all">
                        ₱{{ fmtNum(grandTotal) }}
                    </span>
                </div>

                <!-- ── Product Line Items Table ─────────────────────────── -->
                <div class="overflow-x-auto">
                    <table class="w-full text-xs border-collapse">
                        <!-- Column headers matching Excel -->
                        <thead>
                            <tr class="bg-[#1e3a5f] text-white text-[10px] uppercase tracking-wide font-bold">
                                <th class="px-3 py-2.5 text-left min-w-[160px] border border-[#2d4f7c]">Description</th>
                                <th class="px-2 py-2.5 text-center min-w-[56px] border border-[#2d4f7c]">Weight</th>
                                <th class="px-2 py-2.5 text-center min-w-[72px] border border-[#2d4f7c]">Load-in</th>
                                <th class="px-2 py-2.5 text-center min-w-[72px] border border-[#2d4f7c]">Load-out per bundle</th>
                                <th class="px-2 py-2.5 text-center min-w-[72px] border border-[#2d4f7c]">Load-out per piece</th>
                                <th class="px-2 py-2.5 text-center min-w-[72px] border border-[#2d4f7c]">Sales per bundle</th>
                                <th class="px-2 py-2.5 text-center min-w-[72px] border border-[#2d4f7c]">Sales per piece</th>
                                <th class="px-2 py-2.5 text-center min-w-[88px] border border-[#2d4f7c]">Sales (peso) per bundle</th>
                                <th class="px-2 py-2.5 text-center min-w-[88px] border border-[#2d4f7c]">Sales (peso) per piece</th>
                                <th class="px-3 py-2.5 text-right min-w-[96px] border border-[#2d4f7c] bg-[#16304f]">Total Sales</th>
                            </tr>
                        </thead>
                        <tbody>
                            <template v-for="(group, cat) in groupedItems" :key="cat">
                                <!-- Category header row -->
                                <tr class="bg-[#d6e4f0] dark:bg-[#1a3050]">
                                    <td colspan="10" class="px-3 py-1.5 font-bold text-[11px] text-[#1e3a5f] dark:text-blue-300 uppercase border border-gray-300 dark:border-gray-700">{{ cat }}</td>
                                </tr>
                                <!-- Data rows -->
                                <tr v-for="item in group" :key="item._idx"
                                    class="hover:bg-blue-50/40 dark:hover:bg-blue-950/10 transition"
                                    :class="item._idx % 2 === 0 ? 'bg-white dark:bg-gray-900' : 'bg-gray-50/60 dark:bg-gray-800/20'">
                                    <td class="px-3 py-1 font-medium text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700">{{ item.product_name }}</td>
                                    <td class="px-2 py-1 text-center border border-gray-200 dark:border-gray-700">
                                        <span v-if="item.weight" class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-[9px] font-bold text-gray-600 dark:text-gray-400">{{ item.weight }}</span>
                                        <span v-else class="text-gray-300">—</span>
                                    </td>
                                    <!-- Load-in: text field (accepts "20 + 7") -->
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model="formItems[item._idx].load_in" type="text" placeholder="e.g. 20+7"
                                            class="w-full px-2 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <!-- Load-out bundle: text field -->
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model="formItems[item._idx].load_out_bundle" type="text" placeholder="0"
                                            class="w-full px-2 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <!-- Remaining numeric fields -->
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model.number="formItems[item._idx].load_out_piece" type="number" min="0" placeholder="0"
                                            class="w-full px-2 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model.number="formItems[item._idx].sales_bundle" type="number" min="0" placeholder="0"
                                            class="w-full px-2 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model.number="formItems[item._idx].sales_piece" type="number" min="0" placeholder="0"
                                            class="w-full px-2 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <!-- ₱/bundle — triggers rowTotals recompute -->
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model.number="formItems[item._idx].sales_peso_bundle" type="number" min="0" step="0.01" placeholder="0.00"
                                            class="w-full px-2 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <!-- ₱/piece — triggers rowTotals recompute -->
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model.number="formItems[item._idx].sales_peso_piece" type="number" min="0" step="0.01" placeholder="0.00"
                                            class="w-full px-2 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <!-- Live auto-calculated Total Sales -->
                                    <td class="px-3 py-1.5 text-right border border-gray-200 dark:border-gray-700 bg-[#f0f7ff] dark:bg-blue-950/20">
                                        <span class="font-bold text-[#1e3a5f] dark:text-blue-300 tabular-nums">
                                            {{ rowTotals[item._idx] > 0 ? fmtNum(rowTotals[item._idx]) : '' }}
                                        </span>
                                    </td>
                                </tr>
                            </template>
                        </tbody>
                        <!-- TOTAL SALES footer row -->
                        <tfoot>
                            <tr class="bg-[#1e3a5f] text-white">
                                <td colspan="9" class="px-3 py-3 font-bold text-xs uppercase tracking-widest text-right border border-[#2d4f7c]">TOTAL SALES</td>
                                <td class="px-3 py-3 text-right font-black text-sm border border-[#2d4f7c] tabular-nums">
                                    {{ fmtNum(grandTotal) }}
                                </td>
                            </tr>
                        </tfoot>
                    </table>
                </div>

                <!-- ── Denomination & Reconciliation (matches Excel bottom) ── -->
                <div class="grid grid-cols-1 md:grid-cols-2 border-t-4 border-[#1e3a5f]">
                    <!-- Left: denominations -->
                    <div class="border-r border-gray-200 dark:border-gray-700">
                        <div class="bg-[#1e3a5f] text-white text-center py-2 text-xs font-bold uppercase tracking-wider">DENOMINATION &amp; RECONCILIATION</div>
                        <table class="w-full text-xs">
                            <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                                <tr v-for="(label, key) in { bill_1000: '1000', bill_500: '500', bill_200: '200', bill_100: '100', bill_50: '50', bill_20: '20' }" :key="key" class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                                    <td class="px-4 py-2 text-right font-semibold text-gray-600 dark:text-gray-400 w-16">{{ label }}</td>
                                    <td class="px-2 py-2 text-center text-gray-400 w-6">×</td>
                                    <td class="py-1 px-1">
                                        <input v-model.number="(formDenom as any)[key]" type="number" min="0" placeholder="0"
                                            class="w-full px-2 py-1.5 text-center border border-gray-200 dark:border-gray-700 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-emerald-500/30 text-[11px]" />
                                    </td>
                                    <td class="px-3 py-2 text-right font-semibold tabular-nums text-gray-700 dark:text-gray-300 w-24">
                                        {{ (formDenom as any)[key] > 0 ? fmtNum((formDenom as any)[key] * Number(label)) : '' }}
                                    </td>
                                </tr>
                                <!-- Coins -->
                                <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                                    <td class="px-4 py-2 text-right font-semibold text-gray-600 dark:text-gray-400">Coins</td>
                                    <td class="px-2 py-2 text-center text-gray-400">×</td>
                                    <td class="py-1 px-1"><input v-model.number="formDenom.coins" type="number" min="0" step="0.01" placeholder="0.00" class="w-full px-2 py-1.5 text-center border border-gray-200 dark:border-gray-700 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-emerald-500/30 text-[11px]" /></td>
                                    <td class="px-3 py-2 text-right font-semibold tabular-nums text-gray-700 dark:text-gray-300">{{ formDenom.coins > 0 ? fmtNum(formDenom.coins) : '' }}</td>
                                </tr>
                                <!-- Total row -->
                                <tr class="bg-gray-50 dark:bg-gray-800/40 font-bold">
                                    <td colspan="3" class="px-4 py-2.5 text-right text-xs uppercase tracking-wider text-gray-700 dark:text-gray-300">TOTAL</td>
                                    <td class="px-3 py-2.5 text-right tabular-nums text-[#1e3a5f] dark:text-blue-300 text-sm">{{ fmtNum(denomTotal) }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Right: reconciliation -->
                    <div>
                        <div class="bg-[#1e3a5f] text-white text-center py-2 text-xs font-bold uppercase tracking-wider opacity-0 pointer-events-none">pad</div>
                        <table class="w-full text-xs">
                            <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                                <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                                    <td class="px-4 py-2 text-gray-600 dark:text-gray-400">Less: Collection (cash)</td>
                                    <td class="py-1 px-2"><input v-model.number="formCash" type="number" min="0" step="0.01" placeholder="0.00" class="w-full px-3 py-1.5 text-right border border-gray-200 dark:border-gray-700 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-emerald-500/30 text-[11px]" /></td>
                                </tr>
                                <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                                    <td class="px-4 py-2 text-gray-600 dark:text-gray-400">Checks collection</td>
                                    <td class="py-1 px-2"><input v-model.number="formChecks" type="number" min="0" step="0.01" placeholder="0.00" class="w-full px-3 py-1.5 text-right border border-gray-200 dark:border-gray-700 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-emerald-500/30 text-[11px]" /></td>
                                </tr>
                                <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                                    <td class="px-4 py-2 text-gray-600 dark:text-gray-400">Sales (credit)</td>
                                    <td class="py-1 px-2"><input v-model.number="formCredit" type="number" min="0" step="0.01" placeholder="0.00" class="w-full px-3 py-1.5 text-right border border-gray-200 dark:border-gray-700 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-emerald-500/30 text-[11px]" /></td>
                                </tr>
                                <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                                    <td class="px-4 py-2 text-gray-600 dark:text-gray-400">Expenses</td>
                                    <td class="py-1 px-2"><input v-model.number="formExpenses" type="number" min="0" step="0.01" placeholder="0.00" class="w-full px-3 py-1.5 text-right border border-gray-200 dark:border-gray-700 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-emerald-500/30 text-[11px]" /></td>
                                </tr>
                                <tr class="bg-gray-50 dark:bg-gray-800/40 font-bold">
                                    <td class="px-4 py-2.5 text-xs uppercase tracking-wider text-gray-800 dark:text-gray-200">Balance</td>
                                    <td class="py-1 px-2"><input v-model.number="formBalance" type="number" step="0.01" placeholder="0.00" class="w-full px-3 py-1.5 text-right border-2 border-[#1e3a5f] dark:border-blue-600 rounded-lg bg-blue-50 dark:bg-blue-950/20 focus:outline-none focus:ring-2 focus:ring-blue-500/40 text-sm font-black text-[#1e3a5f] dark:text-blue-300 tabular-nums" /></td>
                                </tr>
                            </tbody>
                        </table>
                        <!-- Notes -->
                        <div class="px-4 pt-3 pb-2">
                            <label class="block text-[10px] font-bold text-gray-400 uppercase mb-1">Notes (optional)</label>
                            <input v-model="formRptNotes" type="text" placeholder="Any remarks…" class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-xl bg-transparent text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/30" />
                        </div>
                    </div>
                </div>

                <!-- Validation notice -->
                <div v-if="formItems.length > 0 && validationErrors.length > 0" class="mx-6 mb-3 flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-xl text-xs text-red-700 dark:text-red-400">
                    <AlertCircle :size="14" class="shrink-0" />
                    <span>{{ validationErrors.length }} field(s) still required — fill all rows before submitting.</span>
                </div>

                <!-- ── Sticky Footer ────────────────────────────────────── -->
                <div class="sticky bottom-0 flex items-center justify-between gap-3 px-6 py-4 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 rounded-b-2xl">
                    <label class="flex items-center gap-2 text-xs text-gray-500 cursor-pointer select-none">
                        <input type="checkbox" :checked="formStatus === 'submitted'" @change="formStatus = ($event.target as HTMLInputElement).checked ? 'submitted' : 'draft'" class="w-4 h-4 rounded accent-emerald-600" />
                        Mark as Submitted <span class="text-gray-400">(uncheck = draft)</span>
                    </label>
                    <div class="flex items-center gap-3">
                        <button @click="isDailyModalOpen = false" class="px-4 py-2.5 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 text-xs font-semibold rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition">
                            Cancel
                        </button>
                        <button @click="handleDailySubmit" :disabled="isSavingRpt"
                            class="flex items-center gap-2 px-6 py-2.5 bg-[#1e3a5f] hover:bg-[#16304f] disabled:opacity-50 text-white text-xs font-bold rounded-xl transition shadow-lg">
                            <Send v-if="!isSavingRpt" :size="13" />
                            <RefreshCw v-else :size="13" class="animate-spin" />
                            {{ isSavingRpt ? 'Saving…' : formStatus === 'submitted' ? 'Submit Report' : 'Save Draft' }}
                        </button>
                    </div>
                </div>
            </div>
        </div>
        </Transition>
        </Teleport>
    </AppLayout>
</template>

<style scoped>
.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.2s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
.expand-enter-active, .expand-leave-active { transition: all 0.2s ease; overflow: hidden; }
.expand-enter-from, .expand-leave-to { max-height: 0; opacity: 0; }
.expand-enter-to, .expand-leave-from { max-height: 2000px; opacity: 1; }
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1); }
.slide-up-enter-from { opacity: 0; transform: translateY(20px); }
.slide-up-leave-to { opacity: 0; }

/* Make number inputs not show spinners */
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }
</style>
