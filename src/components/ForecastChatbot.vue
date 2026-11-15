<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue';
import { Bot, Send, Sparkles, User } from 'lucide-vue-next';
import { api } from '@/lib/api';
import type {
    Product,
    ProductForecast,
    AbcAnalysis,
    ReorderPointItem,
    AnalyticsOverview,
} from '@/types';

interface ChatMessage {
    id: number;
    role: 'user' | 'assistant';
    text: string;
    meta?: string;
}

const props = withDefaults(
    defineProps<{
        products?: Product[];
        leadTimeDays?: number;
    }>(),
    {
        products: () => [],
        leadTimeDays: 7,
    },
);

const emit = defineEmits<{
    selectProduct: [productId: number];
}>();

const input = ref('');
const isThinking = ref(false);
const localProducts = ref<Product[]>([]);
const messages = ref<ChatMessage[]>([
    {
        id: 1,
        role: 'assistant',
        text: 'Hey! I’m your DIMS demand buddy — I can chat a bit, and when you’re ready I’ll pull live forecasts, ABC classes, or reorder alerts from the plant data.',
        meta: 'Try: “Forecast Bologna for next 4 weeks” or just say hi',
    },
]);
const listRef = ref<HTMLElement | null>(null);
let msgSeq = 2;

const catalog = computed(() =>
    (props.products?.length ? props.products : localProducts.value).slice(),
);

const suggestions = [
    'Forecast Bologna for next 4 weeks',
    'Which products need reorder?',
    'Show Class A SKUs',
    'What’s the plant overview?',
];

async function ensureProducts() {
    if (catalog.value.length) return catalog.value;
    localProducts.value = await api.get<Product[]>('/products');
    return localProducts.value;
}

function push(role: 'user' | 'assistant', text: string, meta?: string) {
    messages.value.push({ id: msgSeq++, role, text, meta });
    nextTick(() => {
        if (listRef.value) {
            listRef.value.scrollTop = listRef.value.scrollHeight;
        }
    });
}

function findProduct(query: string, products: Product[]): Product | null {
    const q = query.toLowerCase();
    // Prefer longer name matches
    const ranked = products
        .map((p) => {
            const name = p.name.toLowerCase();
            const sku = (p.sku || '').toLowerCase();
            let score = 0;
            if (q.includes(name) || name.includes(q)) score += 100 + name.length;
            if (sku && (q.includes(sku) || sku.includes(q))) score += 80;
            // token overlap
            for (const token of name.split(/\s+/)) {
                if (token.length > 2 && q.includes(token)) score += token.length;
            }
            return { p, score };
        })
        .filter((r) => r.score > 0)
        .sort((a, b) => b.score - a.score);
    return ranked[0]?.p ?? null;
}

function parseHorizon(text: string): number {
    const m = text.match(/next\s+(\d+)\s*(week|month|day)?/i) || text.match(/(\d+)\s*(week|month)s?/i);
    if (!m) return 4;
    const n = Math.min(12, Math.max(1, Number(m[1]) || 4));
    return n;
}

function parsePeriod(text: string): 'week' | 'month' {
    if (/\bmonths?\b/i.test(text)) return 'month';
    return 'week';
}

function wantsForecast(text: string) {
    return /\b(forecast|predict|demand|projection|next period|how many)\b/i.test(text);
}
function wantsRop(text: string) {
    return /\b(reorder|rop|below|stock.?out|order now|safety stock)\b/i.test(text);
}
function wantsAbc(text: string) {
    return /\b(abc|class\s*[abc]|class a|class b|class c)\b/i.test(text);
}
function wantsOverview(text: string) {
    return /\b(overview|summary|plant|dashboard|mape)\b/i.test(text);
}

function pickOne(options: string[]) {
    return options[Math.floor(Math.random() * options.length)] ?? options[0];
}

function isGreeting(text: string) {
    return /^(hi|hello|hey|yo|sup|good\s*(morning|afternoon|evening)|hola|kumusta|musta)[\s!?.]*$/i.test(
        text.trim(),
    );
}
function isThanks(text: string) {
    return /\b(thanks|thank you|ty|salamat|appreciate)\b/i.test(text);
}
function isHowAreYou(text: string) {
    return /\b(how are you|how's it going|how r u|kamusta|you good)\b/i.test(text);
}
function isWhoAreYou(text: string) {
    return /\b(who are you|what are you|your name|what can you do)\b/i.test(text);
}
function isBye(text: string) {
    return /^(bye|goodbye|see you|later|exit)[\s!?.]*$/i.test(text.trim());
}
function isCasualOnly(text: string) {
    return isGreeting(text) || isThanks(text) || isHowAreYou(text) || isWhoAreYou(text) || isBye(text);
}

function casualReply(text: string): { text: string; meta?: string } {
    if (isGreeting(text)) {
        return {
            text: pickOne([
                'Hey! Good to see you. Want a quick forecast, or should we check what’s below reorder?',
                'Hi there 👋 I’m ready when you are — try naming a product like Bologna or Tocino.',
                'Hello! I can keep it light, or we can dig into demand numbers. What’s on your mind?',
            ]),
            meta: 'Casual chat',
        };
    }
    if (isHowAreYou(text)) {
        return {
            text: pickOne([
                'Doing great — synced to your live Analytics APIs and ready to forecast. How about you?',
                'All good on my side! Stock math is loaded. Want me to peek at Class A SKUs or a product forecast?',
                'Feeling sharp today. Point me at a product and I’ll project the next few weeks.',
            ]),
            meta: 'Casual chat',
        };
    }
    if (isThanks(text)) {
        return {
            text: pickOne([
                'Anytime! Ping me if you need another forecast.',
                'Happy to help — that’s what I’m here for.',
                'You got it. Ask again anytime.',
            ]),
            meta: 'Casual chat',
        };
    }
    if (isWhoAreYou(text)) {
        return helpText();
    }
    if (isBye(text)) {
        return {
            text: pickOne([
                'Catch you later — I’ll be here on Analytics when you need me.',
                'Bye! Good luck with today’s filing.',
            ]),
            meta: 'Casual chat',
        };
    }
    return {
        text: 'I’m mostly tuned for plant demand chat — forecasts, ABC, and reorder alerts. Still, say hi anytime. What should we check?',
        meta: 'Casual chat',
    };
}

async function answerForecast(text: string, products: Product[]) {
    const period = parsePeriod(text);
    const horizon = parseHorizon(text);
    let product = findProduct(text, products);

    // If no product in message, try common “forecast <name>”
    if (!product) {
        const m = text.match(/forecast\s+(.+?)(?:\s+for|\s+next|$)/i);
        if (m) product = findProduct(m[1], products);
    }
    if (!product) {
        const sample = products.slice(0, 5).map((p) => p.name).join(', ');
        return {
            text: `I couldn’t match that product name. Try one from your catalog — e.g. ${sample || 'your SKUs'} — or say “Forecast Bologna for next 4 weeks.”`,
        };
    }

    emit('selectProduct', product.id);
    const fc = await api.get<ProductForecast>(
        `/analytics/forecast/${product.id}?period=${period}&horizon=${horizon}`,
    );

    if (!fc.history?.length && !(fc.nextPeriodDemand > 0)) {
        return {
            text: `Got **${fc.productName}**, but there’s barely any sales history yet — so I’d be guessing. Log more daily sales, then ask me again and I’ll project properly.`,
            meta: fc.method,
        };
    }

    const lines = (fc.forecast || [])
        .map((f) => `• ${f.label}: **${Math.round(f.predicted)}** units`)
        .join('\n');

    const mape =
        fc.mapePercent != null
            ? `Accuracy (MAPE): **${fc.mapePercent}%** — lower is better`
            : 'Accuracy (MAPE): need a bit more history for a score';

    return {
        text: [
            `Alright — here’s what I’m seeing for **${fc.productName}** (${fc.sku}):`,
            `Using **${fc.method}** on a **${fc.period}** grain, looking **${fc.horizon}** periods ahead.`,
            `Next period looks like about **${Math.round(fc.nextPeriodDemand)}** units.`,
            mape,
            lines ? `\nProjected periods:\n${lines}` : '',
            '\nI also synced this product on the chart below.',
        ]
            .filter(Boolean)
            .join('\n'),
        meta: 'Live forecast API · exponential smoothing',
    };
}

async function answerRop(products: Product[]) {
    const rows = await api.get<ReorderPointItem[]>(
        `/analytics/reorder-points?lead_time_days=${props.leadTimeDays}&below_rop_only=true`,
    );
    if (!rows.length) {
        return { text: 'No products or ingredients are currently below reorder point. Inventory looks healthy vs lead-time demand.' };
    }
    const top = rows.slice(0, 8);
    const body = top
        .map(
            (r) =>
                `• **${r.name}** (${r.itemType}) — on hand **${r.currentQuantity}**, ROP **${r.reorderPoint}**, suggest order **${r.recommendedOrderQty}**`,
        )
        .join('\n');
    return {
        text: `Items needing reorder (lead time ${props.leadTimeDays} days):\n${body}${rows.length > 8 ? `\n…and ${rows.length - 8} more` : ''}`,
        meta: `${rows.length} below ROP`,
    };
}

async function answerAbc(text: string) {
    const abc = await api.get<AbcAnalysis>('/analytics/abc');
    let cls: 'A' | 'B' | 'C' | null = null;
    if (/\bclass\s*a\b|\babc\s*a\b/i.test(text)) cls = 'A';
    else if (/\bclass\s*b\b/i.test(text)) cls = 'B';
    else if (/\bclass\s*c\b/i.test(text)) cls = 'C';
    else cls = 'A';

    const items = (abc.items || []).filter((i) => i.abcClass === cls).slice(0, 10);
    if (!items.length) {
        return { text: `No Class ${cls} SKUs found yet — ABC needs sales value history.` };
    }
    const body = items
        .map((i) => `• **${i.name}** · ${i.sku} · ₱${Number(i.salesValue).toLocaleString('en-PH')} (${i.valueSharePercent}%)`)
        .join('\n');
    return {
        text: `Class **${cls}** SKUs (${abc.counts?.[cls] ?? items.length} total):\n${body}`,
        meta: `A:${abc.counts?.A ?? 0} B:${abc.counts?.B ?? 0} C:${abc.counts?.C ?? 0}`,
    };
}

async function answerOverview() {
    const ov = await api.get<AnalyticsOverview>(
        `/analytics/overview?lead_time_days=${props.leadTimeDays}`,
    );
    return {
        text: [
            '**Plant analytics overview**',
            `• Products below ROP: **${ov.productsBelowRop}**`,
            `• Ingredients below ROP: **${ov.ingredientsBelowRop}**`,
            `• ABC counts — A:**${ov.classACount}** · B:**${ov.classBCount}** · C:**${ov.classCCount}**`,
            ov.avgMapePercent != null
                ? `• Average forecast MAPE: **${ov.avgMapePercent}%**`
                : '• Average forecast MAPE: not enough history yet',
        ].join('\n'),
        meta: `Lead time ${props.leadTimeDays} days`,
    };
}

function helpText() {
    return {
        text: [
            'I’m the **DIMS Demand Forecast Assistant** — part chatbot, part calculator.',
            '',
            'I can chat casually, and for plant work I plug into your live APIs:',
            '• **Forecast** — “Forecast Tocino for next 4 weeks”',
            '• **Reorder** — “Which products need reorder?”',
            '• **ABC** — “Show Class A SKUs”',
            '• **Overview** — “Plant overview”',
            '',
            'I’m not a full ChatGPT brain — demand numbers come from exponential smoothing on your sales history (same as Analytics).',
        ].join('\n'),
        meta: 'About me',
    };
}

async function handleSend(preset?: string) {
    const text = (preset ?? input.value).trim();
    if (!text || isThinking.value) return;
    input.value = '';
    push('user', text);
    isThinking.value = true;
    try {
        const products = await ensureProducts();
        let reply: { text: string; meta?: string };

        // Casual conversation first (hi / thanks / who are you)
        if (isCasualOnly(text) || (isWhoAreYou(text) && !wantsForecast(text))) {
            reply = casualReply(text);
        } else if (wantsForecast(text) || findProduct(text, products)) {
            if (wantsForecast(text) || /\bfor next\b/i.test(text) || findProduct(text, products)) {
                if (wantsRop(text) && !wantsForecast(text) && !findProduct(text, products)) {
                    reply = await answerRop(products);
                } else if (wantsAbc(text) && !wantsForecast(text) && !findProduct(text, products)) {
                    reply = await answerAbc(text);
                } else if (wantsOverview(text) && !wantsForecast(text) && !findProduct(text, products)) {
                    reply = await answerOverview();
                } else {
                    reply = await answerForecast(text, products);
                }
            } else {
                reply = await answerForecast(text, products);
            }
        } else if (wantsRop(text)) {
            reply = await answerRop(products);
        } else if (wantsAbc(text)) {
            reply = await answerAbc(text);
        } else if (wantsOverview(text)) {
            reply = await answerOverview();
        } else if (/\bhelp\b|\bwhat can\b/i.test(text)) {
            reply = helpText();
        } else {
            reply = {
                text: pickOne([
                    'Hmm, I didn’t catch a forecast ask there. You can chat casually, or try something like “Forecast Bologna for next 4 weeks.”',
                    'I’m flexible on hellos — for numbers, name a product or ask about reorder / Class A SKUs.',
                    'Not sure I follow yet. Want a demand forecast, ABC list, or what’s below ROP?',
                ]),
                meta: 'Need a nudge?',
            };
        }

        push('assistant', reply.text, reply.meta);
    } catch (e) {
        push(
            'assistant',
            e instanceof Error ? `Ah — hit a snag: ${e.message}` : 'Ah — something went wrong on that one. Try again?',
        );
    } finally {
        isThinking.value = false;
    }
}

function renderText(text: string) {
    // Minimal markdown: **bold** and newlines
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

onMounted(() => {
    ensureProducts().catch(() => undefined);
});
</script>

<template>
    <section class="ims-glass rounded-2xl overflow-hidden flex flex-col min-h-[420px] max-h-[560px]">
        <header class="px-4 py-3 border-b border-emerald-900/10 dark:border-white/10 flex items-center gap-3 bg-emerald-700/95 text-white">
            <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-white/15 ring-1 ring-white/20">
                <Sparkles :size="16" />
            </span>
            <div class="min-w-0">
                <h3 class="text-sm font-bold leading-tight">Demand Forecast Assistant</h3>
                <p class="text-[10px] text-emerald-100/90 mt-0.5">
                    NL chat over live Analytics forecast · ABC · ROP
                </p>
            </div>
        </header>

        <div ref="listRef" class="flex-1 overflow-y-auto px-3 py-3 space-y-3 bg-emerald-50/30 dark:bg-transparent">
            <div
                v-for="msg in messages"
                :key="msg.id"
                class="flex gap-2"
                :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
            >
                <div
                    v-if="msg.role === 'assistant'"
                    class="h-7 w-7 rounded-lg bg-emerald-700 text-white flex items-center justify-center shrink-0 mt-0.5"
                >
                    <Bot :size="14" />
                </div>
                <div
                    class="max-w-[85%] rounded-2xl px-3 py-2 text-[12px] leading-relaxed shadow-sm"
                    :class="msg.role === 'user'
                        ? 'bg-emerald-700 text-white rounded-br-md'
                        : 'bg-white dark:bg-gray-900 border border-emerald-900/10 dark:border-gray-700 text-gray-800 dark:text-gray-100 rounded-bl-md'"
                >
                    <div v-html="renderText(msg.text)" />
                    <p v-if="msg.meta" class="mt-1.5 text-[9px] uppercase tracking-wider opacity-60">{{ msg.meta }}</p>
                </div>
                <div
                    v-if="msg.role === 'user'"
                    class="h-7 w-7 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-200 flex items-center justify-center shrink-0 mt-0.5"
                >
                    <User :size="14" />
                </div>
            </div>
            <div v-if="isThinking" class="flex items-center gap-2 text-[11px] text-emerald-700 dark:text-emerald-400 px-1">
                <span class="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Computing forecast…
            </div>
        </div>

        <div class="px-3 pb-2 flex flex-wrap gap-1.5 border-t border-emerald-900/5 dark:border-white/5 pt-2">
            <button
                v-for="s in suggestions"
                :key="s"
                type="button"
                class="text-[10px] font-semibold px-2.5 py-1 rounded-full bg-emerald-100/80 text-emerald-800 hover:bg-emerald-200/80 dark:bg-emerald-950/40 dark:text-emerald-300 dark:hover:bg-emerald-900/50 transition"
                :disabled="isThinking"
                @click="handleSend(s)"
            >
                {{ s }}
            </button>
        </div>

        <form class="p-3 pt-1 flex items-center gap-2" @submit.prevent="handleSend()">
            <input
                v-model="input"
                type="text"
                placeholder="Ask for a demand forecast…"
                class="flex-1 px-3 py-2.5 rounded-xl border border-emerald-200 dark:border-gray-700 bg-white/80 dark:bg-gray-950 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
                :disabled="isThinking"
            />
            <button
                type="submit"
                class="h-10 w-10 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white flex items-center justify-center transition"
                :disabled="isThinking || !input.trim()"
                title="Send"
            >
                <Send :size="15" />
            </button>
        </form>
    </section>
</template>
