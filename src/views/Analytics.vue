<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue';
import AppLayout from '@/layouts/AppLayout.vue';
import ForecastChatbot from '@/components/ForecastChatbot.vue';
import {
    LineChart, BarChart3, AlertTriangle, Package, Layers,
    Search, RefreshCw,
} from 'lucide-vue-next';
import { formatCurrency } from '@/composables/useFormatCurrency';
import { api } from '@/lib/api';
import type {
    Product, ProductForecast, AbcAnalysis, AbcItem,
    ReorderPointItem, AnalyticsOverview,
} from '@/types';

const isLoading = ref(false);
const overview = ref<AnalyticsOverview | null>(null);
const abc = ref<AbcAnalysis | null>(null);
const reorder = ref<ReorderPointItem[]>([]);
const products = ref<Product[]>([]);
const forecast = ref<ProductForecast | null>(null);

const selectedProductId = ref<number | null>(null);
const forecastPeriod = ref<'week' | 'month'>('week');
const abcFilter = ref<'all' | 'A' | 'B' | 'C'>('all');
const abcSearch = ref('');
const reorderOnly = ref(true);
const leadTimeDays = ref(7);

const filteredAbc = computed(() => {
    let rows: AbcItem[] = abc.value?.items ?? [];
    if (abcFilter.value !== 'all') {
        rows = rows.filter((r) => r.abcClass === abcFilter.value);
    }
    const q = abcSearch.value.trim().toLowerCase();
    if (q) {
        rows = rows.filter(
            (r) => r.name.toLowerCase().includes(q) || r.sku.toLowerCase().includes(q),
        );
    }
    return rows;
});

/** Combined chart series: history actuals + forecast predictions */
const chartSeries = computed(() => {
    if (!forecast.value) return [] as Array<{
        label: string;
        actual: number | null;
        predicted: number | null;
        kind: 'history' | 'forecast';
    }>;
    const hist = forecast.value.history.map((h) => ({
        label: h.label,
        actual: h.actual,
        predicted: h.fitted ?? null,
        kind: 'history' as const,
    }));
    const fut = forecast.value.forecast.map((f) => ({
        label: f.label,
        actual: null,
        predicted: f.predicted,
        kind: 'forecast' as const,
    }));
    return [...hist, ...fut];
});

const chartMax = computed(() => {
    let m = 1;
    for (const p of chartSeries.value) {
        if (p.actual != null) m = Math.max(m, p.actual);
        if (p.predicted != null) m = Math.max(m, p.predicted);
    }
    return m;
});

async function loadForecast() {
    if (!selectedProductId.value) {
        forecast.value = null;
        return;
    }
    forecast.value = await api.get<ProductForecast>(
        `/analytics/forecast/${selectedProductId.value}?period=${forecastPeriod.value}&horizon=4`,
    );
}

async function loadAll() {
    isLoading.value = true;
    try {
        const [ov, abcRes, ro, prods] = await Promise.all([
            api.get<AnalyticsOverview>(`/analytics/overview?lead_time_days=${leadTimeDays.value}`),
            api.get<AbcAnalysis>('/analytics/abc'),
            api.get<ReorderPointItem[]>(
                `/analytics/reorder-points?lead_time_days=${leadTimeDays.value}&below_rop_only=${reorderOnly.value}`,
            ),
            api.get<Product[]>('/products'),
        ]);
        overview.value = ov;
        abc.value = abcRes;
        reorder.value = ro;
        products.value = prods;
        if (!selectedProductId.value && prods.length) {
            selectedProductId.value = prods[0].id;
        }
        await loadForecast();
    } catch (e) {
        console.error(e);
    } finally {
        isLoading.value = false;
    }
}

watch([selectedProductId, forecastPeriod], () => {
    loadForecast().catch(console.error);
});

onMounted(loadAll);

function abcBadge(cls: string) {
    if (cls === 'A') return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400';
    if (cls === 'B') return 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400';
    return 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300';
}

function onChatSelectProduct(productId: number) {
    selectedProductId.value = productId;
}
</script>

<template>
    <AppLayout>
        <div class="space-y-6">
            <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
                <div>
                    <h2 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
                        Inventory Analytics
                    </h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        Demand forecast, ABC classification, and reorder-point recommendations.
                    </p>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                    <label class="text-[11px] font-semibold text-gray-500 flex items-center gap-1.5">
                        Lead time (days)
                        <input
                            v-model.number="leadTimeDays"
                            type="number"
                            min="1"
                            max="90"
                            class="w-16 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-transparent text-sm"
                        />
                    </label>
                    <button
                        type="button"
                        class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold"
                        :disabled="isLoading"
                        @click="loadAll"
                    >
                        <RefreshCw :size="14" :class="isLoading ? 'animate-spin' : ''" />
                        Refresh
                    </button>
                </div>
            </div>

            <!-- Demand forecast chatbot -->
            <ForecastChatbot
                :products="products"
                :lead-time-days="leadTimeDays"
                @select-product="onChatSelectProduct"
            />

            <!-- KPI strip -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <div class="p-4 rounded-2xl ims-glass">
                    <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400">Products below ROP</p>
                    <p class="text-2xl font-extrabold mt-1 text-amber-500">{{ overview?.productsBelowRop ?? '—' }}</p>
                </div>
                <div class="p-4 rounded-2xl ims-glass">
                    <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400">Ingredients below ROP</p>
                    <p class="text-2xl font-extrabold mt-1 text-amber-500">{{ overview?.ingredientsBelowRop ?? '—' }}</p>
                </div>
                <div class="p-4 rounded-2xl ims-glass">
                    <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400">Class A SKUs</p>
                    <p class="text-2xl font-extrabold mt-1 text-emerald-600">{{ overview?.classACount ?? '—' }}</p>
                    <p class="text-[10px] text-gray-400 mt-0.5">
                        B {{ overview?.classBCount ?? 0 }} · C {{ overview?.classCCount ?? 0 }}
                    </p>
                </div>
                <div class="p-4 rounded-2xl ims-glass">
                    <p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400">Forecast MAPE</p>
                    <p class="text-2xl font-extrabold mt-1">
                        {{ overview?.avgMapePercent != null ? `${overview.avgMapePercent}%` : 'N/A' }}
                    </p>
                    <p class="text-[10px] text-gray-400 mt-0.5">Lower is better · needs sales history</p>
                </div>
            </div>

            <!-- Demand forecast -->
            <div class="p-5 rounded-2xl ims-glass">
                <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 mb-4">
                    <div>
                        <h3 class="font-bold text-base flex items-center gap-2">
                            <LineChart :size="16" class="text-emerald-600" />
                            Demand Forecast
                        </h3>
                        <p class="text-[11px] text-gray-400 mt-0.5">
                            Exponential smoothing · actual vs fitted / predicted
                            <span v-if="forecast" class="ml-1">
                                (next: <strong>{{ forecast.nextPeriodDemand }}</strong> units ·
                                method {{ forecast.method }}
                                <template v-if="forecast.mapePercent != null"> · MAPE {{ forecast.mapePercent }}%</template>)
                            </span>
                        </p>
                    </div>
                    <div class="flex flex-wrap gap-2">
                        <select
                            v-model.number="selectedProductId"
                            class="px-3 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-transparent text-sm min-w-[200px]"
                        >
                            <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
                        </select>
                        <div class="inline-flex rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden text-xs font-semibold">
                            <button
                                type="button"
                                class="px-3 py-2"
                                :class="forecastPeriod === 'week' ? 'bg-emerald-600 text-white' : 'text-gray-500'"
                                @click="forecastPeriod = 'week'"
                            >Week</button>
                            <button
                                type="button"
                                class="px-3 py-2 border-l border-gray-200 dark:border-gray-700"
                                :class="forecastPeriod === 'month' ? 'bg-emerald-600 text-white' : 'text-gray-500'"
                                @click="forecastPeriod = 'month'"
                            >Month</button>
                        </div>
                    </div>
                </div>

                <div v-if="chartSeries.length" class="flex items-end gap-1 h-36 overflow-x-auto pb-1">
                    <div
                        v-for="(pt, idx) in chartSeries"
                        :key="idx"
                        class="flex-1 min-w-[22px] flex flex-col items-center justify-end h-full gap-0.5 group relative"
                    >
                        <span class="absolute -top-4 text-[8px] opacity-0 group-hover:opacity-100 whitespace-nowrap bg-white dark:bg-gray-800 px-1 rounded border border-gray-100 dark:border-gray-700 z-10">
                            <template v-if="pt.actual != null">act {{ pt.actual }}</template>
                            <template v-if="pt.predicted != null"> · pred {{ pt.predicted }}</template>
                        </span>
                        <div class="w-full flex items-end justify-center gap-0.5 h-[85%]">
                            <div
                                v-if="pt.actual != null"
                                class="w-[45%] rounded-t bg-emerald-500/80"
                                :style="{ height: `${Math.max(4, (pt.actual / chartMax) * 100)}%` }"
                            />
                            <div
                                v-if="pt.predicted != null"
                                class="w-[45%] rounded-t"
                                :class="pt.kind === 'forecast' ? 'bg-indigo-500/70 border border-dashed border-indigo-400' : 'bg-indigo-300/50'"
                                :style="{ height: `${Math.max(4, (pt.predicted / chartMax) * 100)}%` }"
                            />
                        </div>
                        <span class="text-[8px] text-gray-400 truncate w-full text-center">{{ pt.label }}</span>
                    </div>
                </div>
                <p v-else class="text-center text-xs text-gray-400 py-10">
                    No sales history for this SKU yet — forecast will appear after sales are recorded.
                </p>
                <div class="flex gap-4 mt-3 text-[10px] text-gray-500">
                    <span class="inline-flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-sm bg-emerald-500/80" /> Actual</span>
                    <span class="inline-flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-sm bg-indigo-300/50" /> Fitted</span>
                    <span class="inline-flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-sm bg-indigo-500/70 border border-dashed border-indigo-400" /> Forecast</span>
                </div>
            </div>

            <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <!-- ABC -->
                <div class="p-5 rounded-2xl ims-glass">
                    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
                        <h3 class="font-bold text-base flex items-center gap-2">
                            <BarChart3 :size="16" class="text-emerald-600" />
                            ABC Classification
                        </h3>
                        <div class="flex gap-2">
                            <div class="relative">
                                <Search :size="12" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    v-model="abcSearch"
                                    type="text"
                                    placeholder="Search…"
                                    class="pl-7 pr-2 py-1.5 text-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-transparent w-36"
                                />
                            </div>
                            <select
                                v-model="abcFilter"
                                class="px-2 py-1.5 text-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-transparent"
                            >
                                <option value="all">All</option>
                                <option value="A">A only</option>
                                <option value="B">B only</option>
                                <option value="C">C only</option>
                            </select>
                        </div>
                    </div>
                    <p class="text-[11px] text-gray-400 mb-3">Pareto by sales value — A ≈ top 80%, B next 15%, C last 5%.</p>
                    <div class="overflow-x-auto max-h-80 overflow-y-auto">
                        <table class="w-full text-left text-xs">
                            <thead class="sticky top-0 bg-white dark:bg-gray-900 text-gray-400 uppercase tracking-wider">
                                <tr class="border-b border-gray-100 dark:border-gray-800">
                                    <th class="pb-2 font-semibold">Class</th>
                                    <th class="pb-2 font-semibold">SKU</th>
                                    <th class="pb-2 font-semibold text-right">Value</th>
                                    <th class="pb-2 font-semibold text-right">Cum %</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-50 dark:divide-gray-800/50">
                                <tr v-for="row in filteredAbc" :key="row.productId">
                                    <td class="py-2">
                                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold" :class="abcBadge(row.abcClass)">
                                            {{ row.abcClass }}
                                        </span>
                                    </td>
                                    <td class="py-2">
                                        <p class="font-semibold text-gray-800 dark:text-gray-200">{{ row.name }}</p>
                                        <p class="text-[10px] text-gray-400">{{ row.sku }}</p>
                                    </td>
                                    <td class="py-2 text-right tabular-nums font-semibold">{{ formatCurrency(row.salesValue) }}</td>
                                    <td class="py-2 text-right tabular-nums text-gray-500">{{ row.cumulativePercent }}%</td>
                                </tr>
                                <tr v-if="filteredAbc.length === 0">
                                    <td colspan="4" class="py-8 text-center text-gray-400">No products match.</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- ROP -->
                <div class="p-5 rounded-2xl ims-glass">
                    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
                        <h3 class="font-bold text-base flex items-center gap-2">
                            <AlertTriangle :size="16" class="text-amber-500" />
                            Reorder Points
                        </h3>
                        <label class="text-[11px] font-semibold text-gray-500 flex items-center gap-1.5 cursor-pointer">
                            <input v-model="reorderOnly" type="checkbox" class="rounded" @change="loadAll" />
                            Needs reorder only
                        </label>
                    </div>
                    <p class="text-[11px] text-gray-400 mb-3">
                        ROP = (avg daily × lead time) + safety stock · z={{ 1.65 }} · lead {{ leadTimeDays }}d
                    </p>
                    <div class="overflow-x-auto max-h-80 overflow-y-auto">
                        <table class="w-full text-left text-xs">
                            <thead class="sticky top-0 bg-white dark:bg-gray-900 text-gray-400 uppercase tracking-wider">
                                <tr class="border-b border-gray-100 dark:border-gray-800">
                                    <th class="pb-2 font-semibold">Item</th>
                                    <th class="pb-2 font-semibold text-right">Qty</th>
                                    <th class="pb-2 font-semibold text-right">ROP</th>
                                    <th class="pb-2 font-semibold text-right">SS</th>
                                    <th class="pb-2 font-semibold text-right">Order</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-50 dark:divide-gray-800/50">
                                <tr v-for="r in reorder" :key="`${r.itemType}-${r.itemId}`">
                                    <td class="py-2">
                                        <div class="flex items-center gap-1.5">
                                            <Package v-if="r.itemType === 'product'" :size="12" class="text-emerald-600" />
                                            <Layers v-else :size="12" class="text-indigo-500" />
                                            <div>
                                                <p class="font-semibold text-gray-800 dark:text-gray-200">{{ r.name }}</p>
                                                <p class="text-[10px] text-gray-400">
                                                    {{ r.itemType }}{{ r.sku ? ` · ${r.sku}` : '' }}
                                                    <span v-if="r.needsReorder" class="ml-1 text-amber-500 font-bold">REORDER</span>
                                                </p>
                                            </div>
                                        </div>
                                    </td>
                                    <td class="py-2 text-right tabular-nums" :class="r.belowRop ? 'text-amber-500 font-bold' : ''">
                                        {{ r.currentQuantity }}
                                    </td>
                                    <td class="py-2 text-right tabular-nums font-semibold">{{ r.reorderPoint }}</td>
                                    <td class="py-2 text-right tabular-nums text-gray-500">{{ r.safetyStock }}</td>
                                    <td class="py-2 text-right tabular-nums font-bold text-emerald-600">{{ r.recommendedOrderQty }}</td>
                                </tr>
                                <tr v-if="reorder.length === 0">
                                    <td colspan="5" class="py-8 text-center text-gray-400">
                                        {{ reorderOnly ? 'Nothing below ROP right now.' : 'No items.' }}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </AppLayout>
</template>
