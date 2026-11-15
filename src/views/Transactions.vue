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
    (canInput.value || isAdminRole.value) ? 'daily-reports' : 'stock-vouchers'
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

/** Normalize API camelCase / snake_case line items into the sheet shape. */
function pickNum(row: Record<string, unknown>, snake: string, camel: string): number | null {
    const v = row[snake] ?? row[camel];
    if (v === null || v === undefined || v === '') return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
}

function normalizeLineItem(raw: Record<string, unknown>, fallbackOrder = 0): LineItem {
    const pesoB = pickNum(raw, 'sales_peso_bundle', 'salesPesoBundle') ?? 0;
    const pesoP = pickNum(raw, 'sales_peso_piece', 'salesPesoPiece') ?? 0;
    return {
        category: String(raw.category ?? ''),
        product_name: String(raw.product_name ?? raw.productName ?? ''),
        weight: (raw.weight as string | null | undefined) ?? null,
        load_in: raw.load_in != null || raw.loadIn != null
            ? String(raw.load_in ?? raw.loadIn)
            : null,
        load_out_bundle: raw.load_out_bundle != null || raw.loadOutBundle != null
            ? String(raw.load_out_bundle ?? raw.loadOutBundle)
            : null,
        load_out_piece: pickNum(raw, 'load_out_piece', 'loadOutPiece'),
        sales_bundle: pickNum(raw, 'sales_bundle', 'salesBundle'),
        sales_piece: pickNum(raw, 'sales_piece', 'salesPiece'),
        sales_peso_bundle: pickNum(raw, 'sales_peso_bundle', 'salesPesoBundle'),
        sales_peso_piece: pickNum(raw, 'sales_peso_piece', 'salesPesoPiece'),
        // Poka-Yoke: always recompute from peso columns (thesis — no hand-added totals)
        total_sales: Math.round((pesoB + pesoP) * 100) / 100,
        sort_order: Number(raw.sort_order ?? raw.sortOrder ?? fallbackOrder) || fallbackOrder,
    };
}

function blankFromTemplate(rows: LineItem[]): LineItem[] {
    return rows.map((r, i) => ({
        ...r,
        load_in: null,
        load_out_bundle: null,
        load_out_piece: null,
        sales_bundle: null,
        sales_piece: null,
        sales_peso_bundle: null,
        sales_peso_piece: null,
        total_sales: 0,
        sort_order: r.sort_order ?? i,
    }));
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
const formRptNotes = ref('');
const formStatus   = ref<'draft' | 'submitted'>('submitted');
const formItems    = ref<LineItem[]>([]);
const formDenom    = ref<DenomForm>({ bill_1000: 0, bill_500: 0, bill_200: 0, bill_100: 0, bill_50: 0, bill_20: 0, coins: 0 });

// ── Reactive totals (Poka-Yoke — locked, not typed by user) ─────────────────
// Thesis: totals are auto-computed so operators cannot hand-add wrong figures.
const rowTotals = computed<number[]>(() =>
    formItems.value.map((item) =>
        Math.round(((item.sales_peso_bundle ?? 0) + (item.sales_peso_piece ?? 0)) * 100) / 100,
    ),
);
const grandTotal = computed<number>(() =>
    Math.round(rowTotals.value.reduce((sum, v) => sum + v, 0) * 100) / 100,
);

const denomTotal = computed(() =>
    Math.round((
        formDenom.value.bill_1000 * 1000 + formDenom.value.bill_500 * 500 +
        formDenom.value.bill_200  * 200  + formDenom.value.bill_100 * 100 +
        formDenom.value.bill_50   * 50   + formDenom.value.bill_20  * 20  +
        formDenom.value.coins
    ) * 100) / 100,
);

// Cash collection locked to denomination count; balance auto-computed
watch(denomTotal, (v) => { formCash.value = v; }, { immediate: true });

// Keep each row's locked total_sales in sync for payload / history
watch(rowTotals, (totals) => {
    totals.forEach((t, i) => {
        if (formItems.value[i] && formItems.value[i].total_sales !== t) {
            formItems.value[i].total_sales = t;
        }
    });
}, { deep: true });

const formBalance = computed(() =>
    Math.round(
        (grandTotal.value - formCash.value - formChecks.value - formCredit.value - formExpenses.value) * 100,
    ) / 100,
);

// Grouped items for category-header rows (preserve template sort order)
const groupedItems = computed(() => {
    const groups: Record<string, Array<LineItem & { _idx: number }>> = {};
    formItems.value.forEach((item, idx) => {
        if (!groups[item.category]) groups[item.category] = [];
        groups[item.category].push({ ...item, _idx: idx });
    });
    return groups;
});

async function loadTemplate() {
    try {
        const rows = await api.get<Record<string, unknown>[]>('/daily-reports/template');
        templateRows.value = rows.map((r, i) => normalizeLineItem(r, i));
    } catch {
        templateRows.value = [];
    }
}

async function loadReports() {
    isLoadingRpt.value = true;
    try {
        const params = new URLSearchParams();
        if (dateFilter.value?.from) params.set('report_date', dateFilter.value.from);
        const qs = params.toString() ? `?${params}` : '';
        const raw = await api.get<DailyReport[]>(`/daily-reports${qs}`);
        reports.value = raw.map((report) => ({
            ...report,
            items: (report.items || []).map((item, i) =>
                normalizeLineItem(item as unknown as Record<string, unknown>, i),
            ),
        }));
    } finally {
        isLoadingRpt.value = false;
    }
}
watch(dateFilter, () => loadReports());

// Completeness only required when submitting (thesis: prevent incomplete final reports)
const validationErrors = computed(() => {
    if (formStatus.value !== 'submitted') return [];
    const errs: string[] = [];
    formItems.value.forEach((item, i) => {
        const lbl = item.weight ? `${item.product_name} (${item.weight})` : item.product_name;
        if (!item.load_in && item.load_in !== '0') errs.push(`Row ${i + 1} "${lbl}": Load-in`);
        if (!item.load_out_bundle && item.load_out_bundle !== '0') errs.push(`Row ${i + 1} "${lbl}": Load-out/Bdl`);
        if (item.load_out_piece === null) errs.push(`Row ${i + 1} "${lbl}": Load-out/Pc`);
        if (item.sales_bundle === null) errs.push(`Row ${i + 1} "${lbl}": Sales/Bdl`);
        if (item.sales_piece === null) errs.push(`Row ${i + 1} "${lbl}": Sales/Pc`);
        if (item.sales_peso_bundle === null) errs.push(`Row ${i + 1} "${lbl}": ₱/Bdl`);
        if (item.sales_peso_piece === null) errs.push(`Row ${i + 1} "${lbl}": ₱/Pc`);
    });
    return errs;
});
const isFormValid = computed(() => validationErrors.value.length === 0 && formDate.value.length > 0);

function resetBlankForm() {
    formClient.value = '';
    formPrepared.value = authStore.currentUser?.name ?? '';
    formChecks.value = 0;
    formCredit.value = 0;
    formExpenses.value = 0;
    formRptNotes.value = '';
    formStatus.value = 'draft';
    formDenom.value = { bill_1000: 0, bill_500: 0, bill_200: 0, bill_100: 0, bill_50: 0, bill_20: 0, coins: 0 };
    formItems.value = blankFromTemplate(templateRows.value);
}

async function loadReportForDate(dateStr: string) {
    if (!dateStr) return;
    try {
        const existing = await api.get<DailyReport>(`/daily-reports/by-date/${dateStr}`);
        formClient.value = existing.clientName || '';
        formPrepared.value = existing.userName || authStore.currentUser?.name || '';
        formChecks.value = existing.checksCollection ?? 0;
        formCredit.value = existing.creditSales ?? 0;
        formExpenses.value = existing.expenses ?? 0;
        formRptNotes.value = existing.notes || '';
        formStatus.value = (existing.status as 'draft' | 'submitted') || 'draft';
        if (existing.denominations) {
            formDenom.value = {
                bill_1000: existing.denominations.bill1000 ?? 0,
                bill_500: existing.denominations.bill500 ?? 0,
                bill_200: existing.denominations.bill200 ?? 0,
                bill_100: existing.denominations.bill100 ?? 0,
                bill_50: existing.denominations.bill50 ?? 0,
                bill_20: existing.denominations.bill20 ?? 0,
                coins: existing.denominations.coins ?? 0,
            };
        } else {
            formDenom.value = { bill_1000: 0, bill_500: 0, bill_200: 0, bill_100: 0, bill_50: 0, bill_20: 0, coins: 0 };
        }
        if (existing.items && existing.items.length > 0) {
            formItems.value = existing.items.map((r, i) =>
                normalizeLineItem(r as unknown as Record<string, unknown>, i),
            );
        } else {
            formItems.value = blankFromTemplate(templateRows.value);
        }
    } catch {
        resetBlankForm();
    }
}

watch(formDate, (newDate) => {
    if (isDailyModalOpen.value && newDate) {
        loadReportForDate(newDate);
    }
});

function openDailyModal() {
    const today = new Date().toISOString().slice(0, 10);
    if (formDate.value === today) {
        loadReportForDate(today);
    } else {
        formDate.value = today;
    }
    isDailyModalOpen.value = true;
}

async function handleDailySubmit() {
    if (!formDate.value) {
        alert('Report date is required.');
        return;
    }
    if (formStatus.value === 'submitted' && !isFormValid.value) {
        alert(`${validationErrors.value.length} field(s) required — fill all rows before submitting (drafts can be incomplete).`);
        return;
    }
    isSavingRpt.value = true;
    try {
        const payload = {
            report_date: formDate.value,
            client_name: formClient.value || null,
            cash_collection: formCash.value,
            checks_collection: formChecks.value,
            credit_sales: formCredit.value,
            expenses: formExpenses.value,
            balance: formBalance.value,
            status: formStatus.value,
            notes: formRptNotes.value || null,
            items: formItems.value.map((item, idx) => ({
                category: item.category,
                product_name: item.product_name,
                weight: item.weight,
                load_in: item.load_in,
                load_out_bundle: item.load_out_bundle,
                load_out_piece: item.load_out_piece,
                sales_bundle: item.sales_bundle,
                sales_piece: item.sales_piece,
                sales_peso_bundle: item.sales_peso_bundle,
                sales_peso_piece: item.sales_peso_piece,
                total_sales: rowTotals.value[idx] ?? 0,
                sort_order: item.sort_order ?? idx,
            })),
            denominations: formDenom.value,
        };
        const createdRaw = await api.post<DailyReport>('/daily-reports/upsert', payload);
        const created: DailyReport = {
            ...createdRaw,
            items: (createdRaw.items || []).map((item, i) =>
                normalizeLineItem(item as unknown as Record<string, unknown>, i),
            ),
        };
        isDailyModalOpen.value = false;
        successReport.value = created;
        await loadReports();
        await nextTick();
        await nextTick();
        renderPieChart(created);
        requestAnimationFrame(() => {
            document.getElementById('pie-section')?.scrollIntoView({ behavior: 'smooth' });
        });
    } catch (e: unknown) {
        alert(e instanceof Error ? e.message : 'Failed to save report');
    } finally {
        isSavingRpt.value = false;
    }
}

// ─── Pie Chart ────────────────────────────────────────────────────────────────
const PIE_CATEGORY_COLORS: Record<string, string> = {
    TOCINO: '#10b981',
    'PORK HOTDOG': '#3b82f6',
    'CHICKEN HOTDOG': '#f59e0b',
    LONGANISA: '#ef4444',
    EMBOTIDO: '#8b5cf6',
    'Hamburger Patties': '#059669',
    HAM: '#ec4899',
    SAUSAGES: '#84cc16',
};
const PIE_FALLBACK = ['#06b6d4', '#f97316', '#6366f1', '#14b8a6'];

function buildCategorySales(report: DailyReport): { category: string; amount: number; color: string }[] {
    const catMap = new Map<string, number>();
    (report.items || []).forEach((item, i) => {
        const normalized = normalizeLineItem(item as unknown as Record<string, unknown>, i);
        if (!normalized.category) return;
        const val = Math.round(
            ((normalized.sales_peso_bundle ?? 0) + (normalized.sales_peso_piece ?? 0)) * 100,
        ) / 100;
        // Prefer locked total_sales when present and consistent
        const locked = Number(normalized.total_sales ?? 0);
        const amount = locked > 0 ? locked : val;
        catMap.set(normalized.category, (catMap.get(normalized.category) ?? 0) + amount);
    });

    // Keep template category order when possible
    const order = [
        'TOCINO', 'PORK HOTDOG', 'CHICKEN HOTDOG', 'LONGANISA',
        'EMBOTIDO', 'Hamburger Patties', 'HAM', 'SAUSAGES',
    ];
    const keys = [
        ...order.filter((k) => catMap.has(k)),
        ...[...catMap.keys()].filter((k) => !order.includes(k)),
    ];

    return keys.map((category, idx) => ({
        category,
        amount: Math.round((catMap.get(category) ?? 0) * 100) / 100,
        color: PIE_CATEGORY_COLORS[category] ?? PIE_FALLBACK[idx % PIE_FALLBACK.length],
    }));
}

const pieLegend = computed(() =>
    successReport.value ? buildCategorySales(successReport.value) : [],
);
const pieHasData = computed(() => pieLegend.value.some((row) => row.amount > 0));

let pieInstance: Chart | null = null;
function renderPieChart(report: DailyReport, attempt = 0) {
    const canvas = document.getElementById('daily-pie-chart') as HTMLCanvasElement | null;
    if (!canvas) {
        if (attempt < 8) {
            requestAnimationFrame(() => renderPieChart(report, attempt + 1));
        }
        return;
    }
    if (pieInstance) {
        pieInstance.destroy();
        pieInstance = null;
    }

    const rows = buildCategorySales(report).filter((row) => row.amount > 0);
    if (rows.length === 0) return;

    pieInstance = new Chart(canvas, {
        type: 'pie',
        data: {
            labels: rows.map((r) => r.category),
            datasets: [{
                data: rows.map((r) => r.amount),
                backgroundColor: rows.map((r) => r.color),
                borderWidth: 2,
                borderColor: '#fff',
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                // Custom HTML legend on the right — hide Chart.js legend
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const value = Number(ctx.raw) || 0;
                            const total = rows.reduce((s, r) => s + r.amount, 0) || 1;
                            const pct = ((value / total) * 100).toFixed(1);
                            return ` ${ctx.label}: ₱${value.toLocaleString('en-PH', { minimumFractionDigits: 2 })} (${pct}%)`;
                        },
                    },
                },
            },
        },
    });
}

watch(successReport, async (report) => {
    if (!report) {
        if (pieInstance) {
            pieInstance.destroy();
            pieInstance = null;
        }
        return;
    }
    await nextTick();
    renderPieChart(report);
});

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
            <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
                <div>
                    <p class="text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-700/80 dark:text-emerald-400">DIMS core</p>
                    <h2 class="text-2xl md:text-[1.75rem] font-bold tracking-tight text-gray-900 dark:text-white mt-1">Daily Reports</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-lg">Excel-style daily sheet with locked totals — stock vouchers live in the second tab.</p>
                </div>
                <div class="flex flex-wrap items-center gap-2.5">
                    <template v-if="activeTab === 'stock-vouchers' && isAdminRole">
                        <button @click="openVoucherModal"
                            class="flex items-center gap-2 px-4 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-900/15 transition">
                            <Plus :size="15" /> Log Stock Voucher
                        </button>
                    </template>
                    <template v-if="activeTab === 'daily-reports'">
                        <DateRangeFilter v-model="dateFilter" placeholder="Filter by date" />
                        <button v-if="canInput || isAdminRole" @click="openDailyModal"
                            class="flex items-center gap-2 px-4 py-2.5 bg-emerald-700 hover:bg-emerald-800 active:scale-[0.98] text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-900/15 transition">
                            <Plus :size="15" /> File daily report
                        </button>
                    </template>
                </div>
            </div>

            <!-- ── Tabs ─────────────────────────────────────────────────── -->
            <div class="inline-flex gap-1 p-1 rounded-2xl ims-glass shadow-sm">
                <button @click="activeTab = 'daily-reports'"
                    class="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition"
                    :class="activeTab === 'daily-reports' ? 'bg-emerald-700 text-white shadow-sm' : 'text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'">
                    <ClipboardList :size="14" /> Daily Reports
                    <span v-if="reports.length > 0" class="px-1.5 py-0.5 rounded-full text-[9px] font-bold"
                        :class="activeTab === 'daily-reports' ? 'bg-white/20 text-white' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400'">{{ reports.length }}</span>
                </button>
                <button @click="activeTab = 'stock-vouchers'"
                    class="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition"
                    :class="activeTab === 'stock-vouchers' ? 'bg-emerald-700 text-white shadow-sm' : 'text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'">
                    <ArrowUpRight :size="14" /> Stock Vouchers
                </button>
            </div>

            <!-- ══════════════════════════════════════════════════════════ -->
            <!-- TAB 1 — STOCK VOUCHERS                                    -->
            <!-- ══════════════════════════════════════════════════════════ -->
            <div v-if="activeTab === 'stock-vouchers'" class="space-y-4">
                <div class="p-4 ims-glass rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
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
                <div class="overflow-x-auto ims-glass rounded-2xl shadow-sm">
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
                    class="grid grid-cols-1 lg:grid-cols-2 gap-6 ims-glass rounded-2xl p-6 shadow-md border-emerald-300/50 dark:border-emerald-700/40">
                    <div>
                        <div class="flex items-center gap-2 mb-1"><CheckCircle2 :size="18" class="text-emerald-600" /><h3 class="text-base font-bold text-gray-900 dark:text-white">Report Submitted!</h3></div>
                        <p class="text-xs text-gray-500 mb-4">{{ successReport.reportDate }} · {{ successReport.userName ?? 'You' }}</p>
                        <div class="grid grid-cols-2 gap-3 text-xs">
                            <div class="p-3 bg-emerald-50 dark:bg-emerald-950/20 rounded-xl"><p class="text-gray-500">Total Sales</p><p class="font-extrabold text-emerald-700 dark:text-emerald-400 text-sm mt-0.5">{{ fmtPeso(successReport.totalSales) }}</p></div>
                            <div class="p-3 bg-emerald-50 dark:bg-emerald-950/20 rounded-xl"><p class="text-gray-500">Cash Collection</p><p class="font-extrabold text-emerald-700 dark:text-emerald-400 text-sm mt-0.5">{{ fmtPeso(successReport.cashCollection) }}</p></div>
                            <div class="p-3 bg-amber-50 dark:bg-amber-950/20 rounded-xl"><p class="text-gray-500">Expenses</p><p class="font-extrabold text-amber-700 text-sm mt-0.5">{{ fmtPeso(successReport.expenses) }}</p></div>
                            <div class="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl"><p class="text-gray-500">Balance</p><p class="font-extrabold text-gray-800 dark:text-gray-200 text-sm mt-0.5">{{ fmtPeso(successReport.balance) }}</p></div>
                        </div>
                    </div>
                    <div class="flex flex-col min-w-0">
                        <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Sales by Category</p>
                        <div class="flex flex-col sm:flex-row items-center sm:items-stretch gap-4 sm:gap-6">
                            <div class="relative w-52 h-52 sm:w-56 sm:h-56 shrink-0">
                                <canvas v-if="pieHasData" id="daily-pie-chart"></canvas>
                                <div
                                    v-else
                                    class="w-full h-full rounded-full border-2 border-dashed border-emerald-200 dark:border-emerald-800 flex items-center justify-center text-[11px] text-gray-400 px-4 text-center"
                                >
                                    No category sales yet
                                </div>
                            </div>
                            <ul class="flex-1 w-full min-w-0 space-y-1.5 self-center">
                                <li
                                    v-for="row in pieLegend"
                                    :key="row.category"
                                    class="flex items-center gap-2.5 rounded-lg px-2 py-1.5"
                                    :class="row.amount > 0 ? 'bg-emerald-50/60 dark:bg-emerald-950/20' : 'opacity-55'"
                                >
                                    <span
                                        class="h-2.5 w-2.5 rounded-sm shrink-0 ring-1 ring-black/5"
                                        :style="{ backgroundColor: row.color }"
                                    />
                                    <span class="text-[11px] font-semibold text-gray-700 dark:text-gray-200 truncate flex-1">
                                        {{ row.category }}
                                    </span>
                                    <span class="text-[11px] font-bold tabular-nums text-gray-900 dark:text-gray-100 shrink-0">
                                        {{ fmtPeso(row.amount) }}
                                    </span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
                </Transition>

                <!-- History list -->
                <div>
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-2">
                            <FileText :size="14" class="text-emerald-700" />
                            <span class="text-sm font-bold text-gray-800 dark:text-gray-200">Report history</span>
                        </div>
                        <span class="text-[11px] text-gray-400">{{ reports.length }} record{{ reports.length === 1 ? '' : 's' }}</span>
                    </div>
                    <div v-if="isLoadingRpt" class="space-y-3"><div v-for="i in 3" :key="i" class="h-20 bg-white/60 dark:bg-gray-800 rounded-2xl animate-pulse border border-emerald-900/5" /></div>
                    <div v-else-if="reports.length === 0" class="flex flex-col items-center justify-center py-14 px-6 ims-glass border-dashed border-emerald-300/60 dark:border-emerald-800 rounded-3xl">
                        <div class="h-14 w-14 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 flex items-center justify-center mb-4">
                            <ClipboardList :size="28" class="text-emerald-600" />
                        </div>
                        <p class="font-bold text-gray-800 dark:text-gray-200">No sheets in this range</p>
                        <p class="text-xs text-gray-500 mt-1.5 text-center max-w-xs">{{ (canInput || isAdminRole) ? 'File today’s daily transaction report to start your compliance streak.' : 'No reports found for the selected period.' }}</p>
                        <button
                            v-if="canInput || isAdminRole"
                            type="button"
                            class="mt-5 px-4 py-2.5 rounded-xl bg-emerald-700 text-white text-xs font-bold hover:bg-emerald-800 transition"
                            @click="openDailyModal"
                        >
                            File daily report
                        </button>
                    </div>
                    <div v-else class="space-y-2.5">
                        <div
                            v-for="report in reports"
                            :key="report.id"
                            class="ims-glass rounded-2xl shadow-sm overflow-hidden hover:border-emerald-600/30 dark:hover:border-emerald-600/40 transition"
                        >
                            <button @click="expandedId = expandedId === report.id ? null : report.id" class="w-full flex items-center justify-between px-4 sm:px-5 py-3.5 hover:bg-emerald-50/40 dark:hover:bg-gray-800/40 transition text-left">
                                <div class="flex items-center gap-3 min-w-0">
                                    <div class="h-11 w-11 shrink-0 rounded-xl bg-gradient-to-br from-emerald-600 to-emerald-900 text-white flex flex-col items-center justify-center shadow-sm shadow-emerald-900/20">
                                        <span class="text-[9px] font-bold uppercase leading-none opacity-80">{{ String(report.reportDate).slice(5, 7) }}</span>
                                        <span class="text-sm font-extrabold leading-none mt-0.5">{{ String(report.reportDate).slice(8, 10) }}</span>
                                    </div>
                                    <div class="min-w-0">
                                        <p class="font-bold text-gray-900 dark:text-white text-sm truncate">{{ report.reportDate }}</p>
                                        <p class="text-[11px] text-gray-500 mt-0.5 truncate">{{ report.userName ?? 'You' }}<span v-if="report.clientName"> · {{ report.clientName }}</span></p>
                                    </div>
                                </div>
                                <div class="flex items-center gap-3 sm:gap-4 shrink-0">
                                    <div class="text-right hidden sm:block">
                                        <p class="text-sm font-extrabold text-emerald-800 dark:text-emerald-400 tabular-nums">{{ fmtPeso(report.totalSales) }}</p>
                                        <p class="text-[10px] text-gray-400">Total sales</p>
                                    </div>
                                    <span class="px-2.5 py-1 text-[9px] font-bold rounded-full uppercase tracking-wide" :class="statusBadge(report.status)">{{ report.status }}</span>
                                    <component :is="expandedId === report.id ? ChevronUp : ChevronDown" :size="15" class="text-gray-400" />
                                </div>
                            </button>
                            <Transition name="expand">
                            <div v-if="expandedId === report.id" class="border-t border-gray-100 dark:border-gray-800">
                                <div class="grid grid-cols-2 md:grid-cols-4 divide-x divide-y md:divide-y-0 divide-gray-100 dark:divide-gray-800">
                                    <div class="p-4 text-center"><p class="text-[10px] text-gray-400 uppercase font-semibold">Cash</p><p class="font-bold text-sm mt-1">{{ fmtPeso(report.cashCollection) }}</p></div>
                                    <div class="p-4 text-center"><p class="text-[10px] text-gray-400 uppercase font-semibold">Checks</p><p class="font-bold text-sm mt-1">{{ fmtPeso(report.checksCollection) }}</p></div>
                                    <div class="p-4 text-center"><p class="text-[10px] text-gray-400 uppercase font-semibold">Expenses</p><p class="font-bold text-amber-600 text-sm mt-1">{{ fmtPeso(report.expenses) }}</p></div>
                                    <div class="p-4 text-center"><p class="text-[10px] text-gray-400 uppercase font-semibold">Balance</p><p class="font-bold text-emerald-700 dark:text-emerald-400 text-sm mt-1">{{ fmtPeso(report.balance) }}</p></div>
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
                                            <tr class="bg-[#065f46] text-white">
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
            <div class="relative ims-glass rounded-3xl w-full max-w-md p-6 md:p-8 shadow-2xl space-y-6">
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
        <!-- DAILY REPORT MODAL — Excel layout + thesis Poka-Yoke totals   -->
        <!-- ═══════════════════════════════════════════════════════════════ -->
        <Teleport to="body">
        <Transition name="modal-fade">
        <div v-if="isDailyModalOpen" class="fixed inset-0 z-50 flex items-start justify-center px-2 sm:px-4 py-3 overflow-y-auto">
            <div @click="isDailyModalOpen = false" class="fixed inset-0 bg-black/50 backdrop-blur-sm" />
            <div class="relative bg-white dark:bg-gray-900 rounded-2xl w-full max-w-[96vw] xl:max-w-7xl shadow-2xl border border-gray-200 dark:border-gray-700 my-3 overflow-hidden">

                <!-- ── Modal Header ─────────────────────────────────────── -->
                <div class="bg-[#065f46] text-white px-4 sm:px-6 py-4">
                    <h3 class="text-center text-sm sm:text-base font-bold tracking-wide uppercase">
                        Duque Food Products — Daily Transaction Report
                    </h3>
                    <div class="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-emerald-100">
                        <label class="flex flex-col gap-1">
                            <span class="text-[10px] uppercase tracking-wider text-emerald-100/80">Date</span>
                            <input v-model="formDate" type="date" class="bg-white/10 border border-white/20 rounded-lg px-2 py-1.5 text-white focus:outline-none focus:ring-2 focus:ring-emerald-300/60" />
                        </label>
                        <label class="flex flex-col gap-1">
                            <span class="text-[10px] uppercase tracking-wider text-emerald-100/80">Client</span>
                            <input v-model="formClient" type="text" placeholder="—" class="bg-white/10 border border-white/20 rounded-lg px-2 py-1.5 text-white placeholder:text-emerald-100/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/60" />
                        </label>
                        <label class="flex flex-col gap-1">
                            <span class="text-[10px] uppercase tracking-wider text-emerald-100/80">Prepared by</span>
                            <input v-model="formPrepared" type="text" placeholder="—" class="bg-white/10 border border-white/20 rounded-lg px-2 py-1.5 text-white placeholder:text-emerald-100/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/60" />
                        </label>
                    </div>
                </div>

                <!-- ── Live Grand Total Banner (locked) ─────────────────── -->
                <div class="flex flex-wrap items-center justify-between gap-2 px-4 sm:px-6 py-3 bg-emerald-50 dark:bg-emerald-950/30 border-b border-emerald-200 dark:border-emerald-800">
                    <div>
                        <p class="text-[10px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">Running Total Sales</p>
                        <p class="text-[10px] text-emerald-700/70 dark:text-emerald-400/70 mt-0.5">Auto: Σ (₱/bundle + ₱/piece) — not editable</p>
                    </div>
                    <span class="text-2xl font-black text-emerald-700 dark:text-emerald-400 tabular-nums">
                        ₱{{ fmtNum(grandTotal) }}
                    </span>
                </div>

                <!-- ── Product Line Items Table ─────────────────────────── -->
                <div class="overflow-x-auto max-h-[min(52vh,560px)] overflow-y-auto">
                    <table class="w-full text-xs border-collapse min-w-[980px]">
                        <thead class="sticky top-0 z-20">
                            <tr class="bg-[#065f46] text-white text-[9px] uppercase tracking-wide font-bold">
                                <th class="sticky left-0 z-30 bg-[#065f46] px-3 py-2 text-left min-w-[140px] border border-[#059669]">Description</th>
                                <th class="px-2 py-2 text-center min-w-[52px] border border-[#059669]">Wt</th>
                                <th class="px-2 py-2 text-center min-w-[70px] border border-[#059669]">Load-in</th>
                                <th class="px-2 py-2 text-center min-w-[70px] border border-[#059669] leading-tight">Out<br>/Bdl</th>
                                <th class="px-2 py-2 text-center min-w-[70px] border border-[#059669] leading-tight">Out<br>/Pc</th>
                                <th class="px-2 py-2 text-center min-w-[70px] border border-[#059669] leading-tight">Sales<br>/Bdl</th>
                                <th class="px-2 py-2 text-center min-w-[70px] border border-[#059669] leading-tight">Sales<br>/Pc</th>
                                <th class="px-2 py-2 text-center min-w-[84px] border border-[#059669] leading-tight">₱ Sales<br>/Bdl</th>
                                <th class="px-2 py-2 text-center min-w-[84px] border border-[#059669] leading-tight">₱ Sales<br>/Pc</th>
                                <th class="sticky right-0 z-30 bg-[#047857] px-3 py-2 text-right min-w-[100px] border border-[#059669] leading-tight">Total<br>Sales</th>
                            </tr>
                        </thead>
                        <tbody>
                            <template v-for="(group, cat) in groupedItems" :key="cat">
                                <tr class="bg-[#d1fae5] dark:bg-[#064e3b]">
                                    <td colspan="10" class="sticky left-0 px-3 py-1.5 font-bold text-[11px] text-[#065f46] dark:text-emerald-300 uppercase border border-gray-300 dark:border-gray-700">
                                        {{ cat }}
                                    </td>
                                </tr>
                                <tr
                                    v-for="item in group"
                                    :key="item._idx"
                                    class="hover:bg-emerald-50/60 dark:hover:bg-emerald-950/20 transition"
                                    :class="item._idx % 2 === 0 ? 'bg-white dark:bg-gray-900' : 'bg-gray-50 dark:bg-gray-800/30'"
                                >
                                    <td class="sticky left-0 z-10 px-3 py-1 font-medium text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700 bg-inherit">
                                        {{ item.product_name }}
                                    </td>
                                    <td class="px-2 py-1 text-center border border-gray-200 dark:border-gray-700">
                                        <span v-if="item.weight" class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-[9px] font-bold text-gray-600 dark:text-gray-400">{{ item.weight }}</span>
                                        <span v-else class="text-gray-300">—</span>
                                    </td>
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model="formItems[item._idx].load_in" type="text" placeholder="20+7"
                                            class="w-full px-1.5 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model="formItems[item._idx].load_out_bundle" type="text" placeholder="0"
                                            class="w-full px-1.5 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model.number="formItems[item._idx].load_out_piece" type="number" min="0" placeholder="0"
                                            class="w-full px-1.5 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model.number="formItems[item._idx].sales_bundle" type="number" min="0" placeholder="0"
                                            class="w-full px-1.5 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model.number="formItems[item._idx].sales_piece" type="number" min="0" placeholder="0"
                                            class="w-full px-1.5 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model.number="formItems[item._idx].sales_peso_bundle" type="number" min="0" step="0.01" placeholder="0.00"
                                            class="w-full px-1.5 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <td class="p-0.5 border border-gray-200 dark:border-gray-700">
                                        <input v-model.number="formItems[item._idx].sales_peso_piece" type="number" min="0" step="0.01" placeholder="0.00"
                                            class="w-full px-1.5 py-1.5 text-center bg-transparent focus:outline-none focus:bg-yellow-50 dark:focus:bg-yellow-900/10 focus:ring-1 focus:ring-yellow-400 rounded text-[11px]" />
                                    </td>
                                    <!-- Locked total — always visible (incl. 0.00) -->
                                    <td class="sticky right-0 z-10 px-3 py-1.5 text-right border border-gray-200 dark:border-gray-700 bg-[#ecfdf5] dark:bg-emerald-950/40">
                                        <span class="font-bold text-[#065f46] dark:text-emerald-300 tabular-nums">
                                            {{ fmtNum(rowTotals[item._idx] ?? 0) }}
                                        </span>
                                    </td>
                                </tr>
                            </template>
                        </tbody>
                        <tfoot class="sticky bottom-0 z-20">
                            <tr class="bg-[#065f46] text-white">
                                <td colspan="9" class="px-3 py-3 font-bold text-xs uppercase tracking-widest text-right border border-[#059669]">Total Sales</td>
                                <td class="sticky right-0 bg-[#047857] px-3 py-3 text-right font-black text-sm border border-[#059669] tabular-nums">
                                    ₱{{ fmtNum(grandTotal) }}
                                </td>
                            </tr>
                        </tfoot>
                    </table>
                </div>

                <!-- ── Denomination & Reconciliation ───────────────────── -->
                <div class="border-t-4 border-[#065f46]">
                    <div class="bg-[#065f46] text-white text-center py-2 text-xs font-bold uppercase tracking-wider">
                        Denomination &amp; Reconciliation
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2">
                        <div class="border-b md:border-b-0 md:border-r border-gray-200 dark:border-gray-700">
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
                                            {{ fmtNum(((formDenom as any)[key] || 0) * Number(label)) }}
                                        </td>
                                    </tr>
                                    <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                                        <td class="px-4 py-2 text-right font-semibold text-gray-600 dark:text-gray-400">Coins</td>
                                        <td class="px-2 py-2 text-center text-gray-400">×</td>
                                        <td class="py-1 px-1">
                                            <input v-model.number="formDenom.coins" type="number" min="0" step="0.01" placeholder="0.00"
                                                class="w-full px-2 py-1.5 text-center border border-gray-200 dark:border-gray-700 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-emerald-500/30 text-[11px]" />
                                        </td>
                                        <td class="px-3 py-2 text-right font-semibold tabular-nums text-gray-700 dark:text-gray-300">{{ fmtNum(formDenom.coins || 0) }}</td>
                                    </tr>
                                    <tr class="bg-gray-50 dark:bg-gray-800/40 font-bold">
                                        <td colspan="3" class="px-4 py-2.5 text-right text-xs uppercase tracking-wider text-gray-700 dark:text-gray-300">Cash counted</td>
                                        <td class="px-3 py-2.5 text-right tabular-nums text-[#065f46] dark:text-emerald-300 text-sm">₱{{ fmtNum(denomTotal) }}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <div>
                            <table class="w-full text-xs">
                                <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
                                    <tr>
                                        <td class="px-4 py-2 text-gray-600 dark:text-gray-400">Less: Collection (cash)</td>
                                        <td class="py-1 px-2">
                                            <div class="w-full px-3 py-1.5 text-right rounded-lg bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-800 text-[11px] font-semibold tabular-nums text-emerald-800 dark:text-emerald-300" title="Locked to denomination total (Poka-Yoke)">
                                                ₱{{ fmtNum(formCash) }}
                                            </div>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td class="px-4 py-2 text-gray-600 dark:text-gray-400">Checks collection</td>
                                        <td class="py-1 px-2">
                                            <input v-model.number="formChecks" type="number" min="0" step="0.01" placeholder="0.00"
                                                class="w-full px-3 py-1.5 text-right border border-gray-200 dark:border-gray-700 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-emerald-500/30 text-[11px]" />
                                        </td>
                                    </tr>
                                    <tr>
                                        <td class="px-4 py-2 text-gray-600 dark:text-gray-400">Sales (credit)</td>
                                        <td class="py-1 px-2">
                                            <input v-model.number="formCredit" type="number" min="0" step="0.01" placeholder="0.00"
                                                class="w-full px-3 py-1.5 text-right border border-gray-200 dark:border-gray-700 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-emerald-500/30 text-[11px]" />
                                        </td>
                                    </tr>
                                    <tr>
                                        <td class="px-4 py-2 text-gray-600 dark:text-gray-400">Expenses</td>
                                        <td class="py-1 px-2">
                                            <input v-model.number="formExpenses" type="number" min="0" step="0.01" placeholder="0.00"
                                                class="w-full px-3 py-1.5 text-right border border-gray-200 dark:border-gray-700 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-emerald-500/30 text-[11px]" />
                                        </td>
                                    </tr>
                                    <tr class="bg-emerald-50/80 dark:bg-emerald-950/20 font-bold">
                                        <td class="px-4 py-2.5 text-xs uppercase tracking-wider text-gray-800 dark:text-gray-200">
                                            Balance
                                            <span class="block normal-case font-medium text-[9px] text-gray-500 mt-0.5">Sales − cash − checks − credit − expenses</span>
                                        </td>
                                        <td class="py-1 px-2">
                                            <div class="w-full px-3 py-1.5 text-right border-2 border-[#065f46] dark:border-emerald-500 rounded-lg bg-white dark:bg-gray-950 text-sm font-black text-[#065f46] dark:text-emerald-300 tabular-nums">
                                                ₱{{ fmtNum(formBalance) }}
                                            </div>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                            <div class="px-4 pt-3 pb-3">
                                <label class="block text-[10px] font-bold text-gray-400 uppercase mb-1">Notes (optional)</label>
                                <input v-model="formRptNotes" type="text" placeholder="Any remarks…"
                                    class="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-xl bg-transparent text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/30" />
                            </div>
                        </div>
                    </div>
                </div>

                <div v-if="formStatus === 'submitted' && validationErrors.length > 0" class="mx-4 sm:mx-6 mb-3 flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-xl text-xs text-red-700 dark:text-red-400">
                    <AlertCircle :size="14" class="shrink-0" />
                    <span>{{ validationErrors.length }} field(s) still required before final submit — save as draft to continue later.</span>
                </div>

                <div class="sticky bottom-0 flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-4 sm:px-6 py-4 bg-white/95 dark:bg-gray-900/95 backdrop-blur border-t border-gray-200 dark:border-gray-700">
                    <label class="flex items-center gap-2 text-xs text-gray-500 cursor-pointer select-none">
                        <input
                            type="checkbox"
                            :checked="formStatus === 'submitted'"
                            class="w-4 h-4 rounded accent-emerald-600"
                            @change="formStatus = ($event.target as HTMLInputElement).checked ? 'submitted' : 'draft'"
                        />
                        Mark as Submitted
                        <span class="text-gray-400">(uncheck = draft)</span>
                    </label>
                    <div class="flex items-center gap-3 justify-end">
                        <button type="button" @click="isDailyModalOpen = false" class="px-4 py-2.5 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 text-xs font-semibold rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition">
                            Cancel
                        </button>
                        <button
                            type="button"
                            @click="handleDailySubmit"
                            :disabled="isSavingRpt || (formStatus === 'submitted' && !isFormValid)"
                            class="flex items-center gap-2 px-6 py-2.5 bg-[#065f46] hover:bg-[#047857] disabled:opacity-50 text-white text-xs font-bold rounded-xl transition shadow-lg"
                        >
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
