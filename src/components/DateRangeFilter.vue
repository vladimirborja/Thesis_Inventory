<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { CalendarDays, ChevronLeft, ChevronRight, X } from 'lucide-vue-next';

const props = withDefaults(defineProps<{
    modelValue?: { from: string; to: string } | null;
    placeholder?: string;
}>(), {
    modelValue: null,
    placeholder: 'Filter by date range',
});

const emit = defineEmits<{
    'update:modelValue': [value: { from: string; to: string } | null];
}>();

const isOpen = ref(false);
const hoverDate = ref<string | null>(null);

// Internal selection
const selectStart = ref<string | null>(props.modelValue?.from ?? null);
const selectEnd   = ref<string | null>(props.modelValue?.to   ?? null);

// Calendar navigation
const today = new Date();
const viewYear  = ref(today.getFullYear());
const viewMonth = ref(today.getMonth()); // 0-indexed

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const DAYS   = ['Su','Mo','Tu','We','Th','Fr','Sa'];

const monthLabel = computed(() => `${MONTHS[viewMonth.value]} ${viewYear.value}`);

function prevMonth() {
    if (viewMonth.value === 0) { viewMonth.value = 11; viewYear.value--; }
    else viewMonth.value--;
}
function nextMonth() {
    if (viewMonth.value === 11) { viewMonth.value = 0; viewYear.value++; }
    else viewMonth.value++;
}

const calendarDays = computed(() => {
    const year  = viewYear.value;
    const month = viewMonth.value;
    const first = new Date(year, month, 1).getDay();
    const total = new Date(year, month + 1, 0).getDate();
    const days: Array<{ date: string; day: number; inMonth: boolean }> = [];

    // Padding from previous month
    const prevTotal = new Date(year, month, 0).getDate();
    for (let i = first - 1; i >= 0; i--) {
        const d = prevTotal - i;
        const mo = month === 0 ? 12 : month;
        const yr = month === 0 ? year - 1 : year;
        days.push({ date: fmt(yr, mo - 1, d), day: d, inMonth: false });
    }
    for (let d = 1; d <= total; d++) {
        days.push({ date: fmt(year, month, d), day: d, inMonth: true });
    }
    // Fill remaining cells
    const rem = 42 - days.length;
    for (let d = 1; d <= rem; d++) {
        const mo = month === 11 ? 0 : month + 1;
        const yr = month === 11 ? year + 1 : year;
        days.push({ date: fmt(yr, mo, d), day: d, inMonth: false });
    }
    return days;
});

function fmt(y: number, m: number, d: number) {
    return `${y}-${String(m + 1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
}

function isSelected(date: string) {
    return date === selectStart.value || date === selectEnd.value;
}
function isInRange(date: string) {
    const s = selectStart.value;
    const e = selectEnd.value || hoverDate.value;
    if (!s || !e) return false;
    const [lo, hi] = s <= e ? [s, e] : [e, s];
    return date > lo && date < hi;
}

function selectDay(date: string) {
    if (!selectStart.value || (selectStart.value && selectEnd.value)) {
        // Start fresh
        selectStart.value = date;
        selectEnd.value = null;
    } else {
        // Second click — set end
        if (date < selectStart.value) {
            selectEnd.value = selectStart.value;
            selectStart.value = date;
        } else {
            selectEnd.value = date;
        }
        // Commit
        emit('update:modelValue', { from: selectStart.value!, to: selectEnd.value! });
        isOpen.value = false;
    }
}

function clearFilter() {
    selectStart.value = null;
    selectEnd.value = null;
    emit('update:modelValue', null);
}

function setPreset(days: number) {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - days + 1);
    selectStart.value = fmt(start.getFullYear(), start.getMonth(), start.getDate());
    selectEnd.value   = fmt(end.getFullYear(), end.getMonth(), end.getDate());
    emit('update:modelValue', { from: selectStart.value, to: selectEnd.value });
    isOpen.value = false;
}

// Display label
const displayLabel = computed(() => {
    if (!selectStart.value) return null;
    if (!selectEnd.value) return `From ${selectStart.value}`;
    if (selectStart.value === selectEnd.value) return selectStart.value;
    return `${selectStart.value} → ${selectEnd.value}`;
});

// Close on outside click
function onOutsideClick(e: MouseEvent) {
    const el = (e.target as HTMLElement).closest('.dfp-date-filter');
    if (!el) isOpen.value = false;
}
watch(isOpen, (v) => {
    if (v) document.addEventListener('click', onOutsideClick);
    else document.removeEventListener('click', onOutsideClick);
});
</script>

<template>
    <div class="dfp-date-filter relative inline-block">
        <!-- Trigger button -->
        <button
            @click.stop="isOpen = !isOpen"
            class="flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-semibold transition"
            :class="displayLabel
                ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400'
                : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:border-emerald-300'"
        >
            <CalendarDays :size="14" />
            <span>{{ displayLabel || placeholder }}</span>
            <button v-if="displayLabel" @click.stop="clearFilter" class="ml-1 opacity-60 hover:opacity-100">
                <X :size="12" />
            </button>
        </button>

        <!-- Dropdown calendar -->
        <Transition name="fade-drop">
        <div
            v-if="isOpen"
            class="dfp-date-filter absolute z-50 top-full mt-2 left-0 w-72 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl shadow-2xl p-4"
        >
            <!-- Presets -->
            <div class="flex gap-1.5 mb-3 flex-wrap">
                <button @click="setPreset(7)"  class="px-2.5 py-1 bg-gray-100 dark:bg-gray-800 hover:bg-emerald-50 dark:hover:bg-emerald-950/20 hover:text-emerald-700 text-gray-600 dark:text-gray-400 rounded-lg text-[10px] font-semibold transition">Last 7d</button>
                <button @click="setPreset(30)" class="px-2.5 py-1 bg-gray-100 dark:bg-gray-800 hover:bg-emerald-50 dark:hover:bg-emerald-950/20 hover:text-emerald-700 text-gray-600 dark:text-gray-400 rounded-lg text-[10px] font-semibold transition">Last 30d</button>
                <button @click="setPreset(90)" class="px-2.5 py-1 bg-gray-100 dark:bg-gray-800 hover:bg-emerald-50 dark:hover:bg-emerald-950/20 hover:text-emerald-700 text-gray-600 dark:text-gray-400 rounded-lg text-[10px] font-semibold transition">Last 90d</button>
                <button @click="clearFilter"   class="px-2.5 py-1 bg-red-50 dark:bg-red-950/20 hover:bg-red-100 text-red-600 dark:text-red-400 rounded-lg text-[10px] font-semibold transition">Clear</button>
            </div>

            <!-- Month nav -->
            <div class="flex items-center justify-between mb-3">
                <button @click="prevMonth" class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"><ChevronLeft :size="14" /></button>
                <span class="text-xs font-bold text-gray-800 dark:text-gray-200">{{ monthLabel }}</span>
                <button @click="nextMonth" class="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"><ChevronRight :size="14" /></button>
            </div>

            <!-- Day labels -->
            <div class="grid grid-cols-7 mb-1">
                <span v-for="d in DAYS" :key="d" class="text-center text-[9px] font-bold text-gray-400 py-0.5">{{ d }}</span>
            </div>

            <!-- Dates grid -->
            <div class="grid grid-cols-7 gap-y-0.5">
                <button
                    v-for="cell in calendarDays"
                    :key="cell.date"
                    @click="selectDay(cell.date)"
                    @mouseenter="hoverDate = cell.date"
                    @mouseleave="hoverDate = null"
                    class="relative h-7 w-full flex items-center justify-center text-[11px] font-medium rounded-lg transition"
                    :class="[
                        !cell.inMonth ? 'text-gray-300 dark:text-gray-700' : 'text-gray-700 dark:text-gray-300 hover:bg-emerald-50 dark:hover:bg-emerald-950/20',
                        isSelected(cell.date) ? '!bg-emerald-600 !text-white font-bold' : '',
                        isInRange(cell.date) ? '!bg-emerald-100 dark:!bg-emerald-950/30 !rounded-none' : '',
                    ]"
                >
                    {{ cell.day }}
                </button>
            </div>

            <p v-if="selectStart && !selectEnd" class="text-center text-[10px] text-gray-400 mt-3">
                Click a second date to set end of range
            </p>
        </div>
        </Transition>
    </div>
</template>

<style scoped>
.fade-drop-enter-active, .fade-drop-leave-active { transition: opacity 0.15s, transform 0.15s; }
.fade-drop-enter-from, .fade-drop-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
