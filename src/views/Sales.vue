<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import AppLayout from '@/layouts/AppLayout.vue';
import { 
    Search, Plus, Minus, Trash2, ShoppingCart, DollarSign, Clock, CreditCard, History, Info
} from 'lucide-vue-next';
import { formatCurrency } from '@/composables/useFormatCurrency';
import type { Product, Sale } from '@/types';
import { api } from '@/lib/api';

const authStore = useAuthStore();
const currentRole = computed(() => authStore.currentUser?.role || 'employee');

const products = ref<Product[]>([]);
const salesHistory = ref<Sale[]>([]);
const isLoading = ref(false);
const isSubmitting = ref(false);

const searchQuery = ref('');
const paymentMethod = ref('cash');
const notes = ref('');

// Cart state
interface CartItem {
    product: Product;
    quantity: number;
    unitPrice: number;
}
const cart = ref<CartItem[]>([]);

const filteredProducts = computed(() => {
    const q = searchQuery.value.toLowerCase();
    if (!q) return products.value.filter(p => p.quantity > 0);
    return products.value.filter(p => 
        (p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q)) && p.quantity > 0
    );
});

const cartTotal = computed(() => {
    return cart.value.reduce((acc, item) => acc + (item.unitPrice * item.quantity), 0);
});

async function loadData() {
    isLoading.value = true;
    try {
        [products.value, salesHistory.value] = await Promise.all([
            api.get<Product[]>('/products'),
            api.get<Sale[]>('/sales')
        ]);
    } finally {
        isLoading.value = false;
    }
}

onMounted(loadData);

function addToCart(product: Product) {
    const existing = cart.value.find(item => item.product.id === product.id);
    if (existing) {
        if (existing.quantity < product.quantity) {
            existing.quantity++;
        } else {
            alert('Cannot exceed available stock level.');
        }
    } else {
        cart.value.push({
            product,
            quantity: 1,
            unitPrice: product.sellingPrice
        });
    }
}

function updateQty(item: CartItem, delta: number) {
    const target = item.quantity + delta;
    if (target <= 0) {
        removeFromCart(item);
    } else if (target <= item.product.quantity) {
        item.quantity = target;
    } else {
        alert('Cannot exceed available stock level.');
    }
}

function removeFromCart(item: CartItem) {
    cart.value = cart.value.filter(x => x.product.id !== item.product.id);
}

async function handleCheckout() {
    if (cart.value.length === 0) return;
    isSubmitting.value = true;
    
    const payload = {
        payment_method: paymentMethod.value,
        notes: notes.value,
        items: cart.value.map(item => ({
            product_id: item.product.id,
            quantity: item.quantity,
            unit_price: item.unitPrice
        }))
    };

    try {
        await api.post('/sales', payload);
        alert('Sale completed successfully! Stock levels updated.');
        cart.value = [];
        notes.value = '';
        await loadData();
    } catch (e: unknown) {
        alert(e instanceof Error ? e.message : 'Error completing checkout');
    } finally {
        isSubmitting.value = false;
    }
}
</script>

<template>
    <AppLayout>
        <div class="space-y-6">
            <!-- Header section -->
            <div>
                <h2 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">Sales Ledger & Point of Sale</h2>
                <p class="text-sm text-gray-500 dark:text-gray-400">Record sales transactions, manage checkout flows, and automatically adjust product and ingredient levels.</p>
            </div>

            <!-- Main grid split POS / Transaction logs -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Left: Catalog & Cart -->
                <div class="lg:col-span-2 space-y-6">
                    <!-- Product catalog selector -->
                    <div class="p-6 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl space-y-4 shadow-sm">
                        <h3 class="text-base font-bold flex items-center gap-2">
                            <ShoppingCart :size="18" class="text-emerald-600" />
                            Catalog Selector
                        </h3>
                        <div class="relative">
                            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
                                <Search :size="16" />
                            </span>
                            <input 
                                v-model="searchQuery"
                                type="text"
                                class="w-full pl-9 pr-4 py-2 rounded-xl border border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                                placeholder="Search products by SKU or name..."
                            />
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[300px] overflow-y-auto pr-1">
                            <div v-for="p in filteredProducts" :key="p.id" class="p-3 bg-gray-50 dark:bg-gray-850 rounded-xl border border-gray-100 dark:border-gray-800/80 flex items-center justify-between text-xs transition hover:border-emerald-600/30">
                                <div class="space-y-1">
                                    <p class="font-bold text-gray-900 dark:text-white">{{ p.name }}</p>
                                    <p class="text-[10px] text-gray-400">SKU: {{ p.sku }} • Available: <span class="font-bold text-emerald-600">{{ p.quantity }} {{ p.unitOfMeasure }}</span></p>
                                </div>
                                <button 
                                    @click="addToCart(p)"
                                    class="px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[10px] font-bold"
                                >
                                    Add
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Cart layout -->
                    <div class="p-6 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl space-y-4 shadow-sm">
                        <h3 class="text-base font-bold">Checkout Cart</h3>
                        <div class="space-y-3" v-if="cart.length > 0">
                            <div v-for="item in cart" :key="item.product.id" class="flex items-center justify-between border-b border-gray-100 dark:border-gray-800/60 pb-3 text-xs md:text-sm">
                                <div>
                                    <p class="font-bold text-gray-900 dark:text-white">{{ item.product.name }}</p>
                                    <p class="text-[10px] text-gray-400">{{ formatCurrency(item.unitPrice) }} / unit</p>
                                </div>
                                <div class="flex items-center gap-3">
                                    <div class="flex items-center border border-gray-200 dark:border-gray-800 rounded-lg">
                                        <button @click="updateQty(item, -1)" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800"><Minus :size="12" /></button>
                                        <span class="px-2 text-xs font-bold">{{ item.quantity }}</span>
                                        <button @click="updateQty(item, 1)" class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800"><Plus :size="12" /></button>
                                    </div>
                                    <button @click="removeFromCart(item)" class="text-red-500 hover:text-red-600"><Trash2 :size="14" /></button>
                                </div>
                            </div>
                        </div>
                        <p class="text-xs text-gray-400 text-center py-6" v-else>Cart is empty. Select items from the catalog above.</p>
                    </div>
                </div>

                <!-- Right: Summary checkout Panel -->
                <div class="space-y-6">
                    <div class="p-6 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl space-y-5 shadow-sm">
                        <h3 class="text-base font-bold flex items-center gap-2">
                            <DollarSign :size="18" class="text-emerald-600" />
                            Summary Ledger
                        </h3>

                        <div class="space-y-2 border-b border-gray-100 dark:border-gray-850 pb-4">
                            <div class="flex justify-between text-xs text-gray-400">
                                <span>Cart Subtotal</span>
                                <span>{{ formatCurrency(cartTotal) }}</span>
                            </div>
                            <div class="flex justify-between text-sm font-bold text-gray-900 dark:text-white pt-2">
                                <span>Total Amount</span>
                                <span>{{ formatCurrency(cartTotal) }}</span>
                            </div>
                        </div>

                        <div class="space-y-3">
                            <div class="space-y-1">
                                <label class="block text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Payment Method</label>
                                <div class="grid grid-cols-3 gap-2">
                                    <button 
                                        @click="paymentMethod = 'cash'"
                                        class="px-2.5 py-1.5 rounded-lg border text-center text-xs font-semibold capitalize"
                                        :class="paymentMethod === 'cash' ? 'border-emerald-600 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600' : 'border-gray-200 dark:border-gray-800'"
                                    >
                                        Cash
                                    </button>
                                    <button 
                                        @click="paymentMethod = 'card'"
                                        class="px-2.5 py-1.5 rounded-lg border text-center text-xs font-semibold capitalize"
                                        :class="paymentMethod === 'card' ? 'border-emerald-600 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600' : 'border-gray-200 dark:border-gray-800'"
                                    >
                                        Card
                                    </button>
                                    <button 
                                        @click="paymentMethod = 'bank_transfer'"
                                        class="px-2.5 py-1.5 rounded-lg border text-center text-xs font-semibold capitalize"
                                        :class="paymentMethod === 'bank_transfer' ? 'border-emerald-600 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600' : 'border-gray-200 dark:border-gray-800'"
                                    >
                                        Bank
                                    </button>
                                </div>
                            </div>

                            <div class="space-y-1">
                                <label class="block text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Ledger Notes</label>
                                <textarea 
                                    v-model="notes" 
                                    class="w-full px-4 py-2 border border-gray-200 dark:border-gray-800 rounded-xl bg-transparent text-xs focus:outline-none focus:ring-2 focus:ring-emerald-600/30 h-16"
                                    placeholder="Add transaction reference or customer notes..."
                                ></textarea>
                            </div>
                        </div>

                        <button 
                            @click="handleCheckout"
                            :disabled="cart.length === 0 || isSubmitting"
                            class="w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/10 transition"
                        >
                            {{ isSubmitting ? 'Processing sale...' : 'Complete & Record Sale' }}
                        </button>
                    </div>
                </div>
            </div>

            <!-- Bottom: Sales History Logs -->
            <div class="admin-table-wrap overflow-x-auto bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-sm">
                <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-800/80 flex items-center justify-between">
                    <h3 class="text-sm font-bold flex items-center gap-2">
                        <History :size="16" class="text-emerald-600" />
                        Transactions History Ledger
                    </h3>
                </div>
                <table class="w-full text-left border-collapse text-xs md:text-sm">
                    <thead class="bg-gray-50 dark:bg-gray-800/80 text-gray-400 dark:text-gray-300 border-b border-gray-100 dark:border-gray-800 uppercase text-[10px] tracking-wider font-bold">
                        <tr>
                            <th class="px-6 py-4">Transaction ID</th>
                            <th class="px-6 py-4">Cashier</th>
                            <th class="px-6 py-4">Date</th>
                            <th class="px-6 py-4">Total Amount</th>
                            <th class="px-6 py-4">Payment</th>
                            <th class="px-6 py-4">Items Sold</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-50 dark:divide-gray-800/50">
                        <tr v-if="salesHistory.length === 0">
                            <td colspan="6" class="px-6 py-12 text-center text-gray-400">
                                No sales logs generated yet.
                            </td>
                        </tr>
                        <tr v-for="s in salesHistory" :key="s.id" class="hover:bg-gray-50/50 dark:hover:bg-gray-850 transition">
                            <td class="px-6 py-4 font-mono font-bold text-gray-500">
                                #SAL-{{ s.id }}
                            </td>
                            <td class="px-6 py-4 text-xs font-semibold">
                                {{ s.userName || 'System' }}
                            </td>
                            <td class="px-6 py-4 text-xs text-gray-500">
                                {{ s.createdAt }}
                            </td>
                            <td class="px-6 py-4 text-xs font-bold text-gray-900 dark:text-white">
                                {{ formatCurrency(s.totalAmount) }}
                            </td>
                            <td class="px-6 py-4">
                                <span class="px-2.5 py-1 text-[9px] font-bold rounded-full uppercase tracking-wider"
                                    :class="s.paymentMethod === 'cash' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20' : 'bg-blue-50 text-blue-700 dark:bg-blue-950/20'">
                                    {{ s.paymentMethod }}
                                </span>
                            </td>
                            <td class="px-6 py-4 text-xs text-gray-500">
                                {{ s.items ? s.items.map(i => `${i.productName} (x${i.quantity})`).join(', ') : 'No items' }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </AppLayout>
</template>
