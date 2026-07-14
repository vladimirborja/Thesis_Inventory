<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { User, LogIn, LayoutDashboard, Compass, CheckCircle2, ShieldAlert, Award, Package2 } from 'lucide-vue-next';

const router = useRouter();
const authStore = useAuthStore();

const isLoggedIn = computed(() => !!authStore.currentUser);

function handleProfileClick() {
    if (isLoggedIn.value) {
        router.push({ name: 'dashboard' });
    } else {
        router.push({ name: 'auth' });
    }
}
</script>

<template>
    <div class="min-h-screen bg-gray-50 text-gray-900 font-sans flex flex-col">
        <!-- Header -->
        <header class="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100 px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="h-10 w-10 bg-emerald-600 rounded-xl flex items-center justify-center text-white shadow-md shadow-emerald-600/20">
                    <Package2 :size="22" />
                </div>
                <div>
                    <h1 class="text-lg font-bold tracking-tight text-gray-900">Apex Food Processing</h1>
                    <p class="text-[10px] text-emerald-600 font-semibold tracking-wider uppercase">IMS Corporate</p>
                </div>
            </div>

            <!-- Profile/Login Action -->
            <button 
                @click="handleProfileClick"
                class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all"
                :class="isLoggedIn 
                    ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100' 
                    : 'bg-gray-900 text-white hover:bg-gray-800'"
            >
                <template v-if="isLoggedIn">
                    <LayoutDashboard :size="16" />
                    <span>Go to Dashboard</span>
                </template>
                <template v-else>
                    <LogIn :size="16" />
                    <span>Sign In</span>
                </template>
            </button>
        </header>

        <!-- Hero Section -->
        <section class="max-w-6xl mx-auto px-6 py-20 flex flex-col md:flex-row items-center gap-12 flex-1">
            <div class="flex-1 space-y-6">
                <div class="inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs font-semibold">
                    <Award :size="14" />
                    Vision 2030: Quality, Safety & Precision
                </div>
                <h2 class="text-4xl md:text-5xl font-extrabold tracking-tight text-gray-900 leading-tight">
                    Powering Clean Food Processing Systems <span class="text-emerald-600">Worldwide</span>.
                </h2>
                <p class="text-gray-600 leading-relaxed text-lg max-w-lg">
                    Apex Food Processing Corp integrates state-of-the-art storage, supply chain tracking, and quality control systems to deliver fresh, safe, and nutritious goods from raw ingredients to table.
                </p>
                <div class="flex items-center gap-4 pt-4">
                    <button @click="handleProfileClick" class="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-xl transition shadow-lg shadow-emerald-600/10">
                        Access Inventory Portal
                    </button>
                    <a href="#vision" class="px-6 py-3 border border-gray-200 hover:bg-gray-50 text-gray-700 font-medium rounded-xl transition">
                        Our Vision & Mission
                    </a>
                </div>
            </div>

            <!-- Visual Asset -->
            <div class="flex-1 w-full max-w-md md:max-w-none">
                <div class="relative rounded-3xl overflow-hidden shadow-2xl border-4 border-white bg-emerald-900 aspect-4/3 flex items-center justify-center p-8">
                    <!-- Clean SVG Illustration of food processing elements -->
                    <svg viewBox="0 0 400 300" class="w-full h-full text-emerald-100" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <!-- Conveyor belt -->
                        <path d="M50 200 H350" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>
                        <circle cx="70" cy="200" r="10" fill="currentColor"/>
                        <circle cx="150" cy="200" r="10" fill="currentColor"/>
                        <circle cx="230" cy="200" r="10" fill="currentColor"/>
                        <circle cx="310" cy="200" r="10" fill="currentColor"/>
                        <!-- Packaging Boxes on conveyor belt -->
                        <rect x="90" y="140" width="40" height="40" rx="4" fill="white" stroke="currentColor" stroke-width="4"/>
                        <rect x="250" y="140" width="40" height="40" rx="4" fill="white" stroke="currentColor" stroke-width="4"/>
                        <!-- Processing tank -->
                        <rect x="150" y="40" width="100" height="80" rx="12" fill="currentColor" opacity="0.2"/>
                        <rect x="150" y="40" width="100" height="80" rx="12" stroke="currentColor" stroke-width="4"/>
                        <path d="M200 120 V200" stroke="currentColor" stroke-width="4"/>
                        <!-- Control panel -->
                        <rect x="30" y="60" width="60" height="80" rx="6" stroke="currentColor" stroke-width="4" fill="currentColor" opacity="0.1"/>
                        <circle cx="50" cy="80" r="6" fill="#10B981"/>
                        <circle cx="70" cy="80" r="6" fill="#EF4444"/>
                        <rect x="45" y="100" width="30" height="6" rx="2" fill="currentColor"/>
                        <rect x="45" y="115" width="20" height="6" rx="2" fill="currentColor"/>
                        <!-- Decorative grains/leaves -->
                        <path d="M330 80 C340 70 350 80 360 70" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                        <path d="M330 90 C340 80 350 90 360 80" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                    </svg>
                    <div class="absolute bottom-4 left-4 right-4 bg-white/10 backdrop-blur-md rounded-2xl p-4 text-white text-xs border border-white/10">
                        <p class="font-bold">Automated Supply & Quality Metrics</p>
                        <p class="opacity-80 mt-1">Real-time telemetry and raw food ingredient storage safety logs active.</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Vision and Values Section -->
        <section id="vision" class="bg-white py-20 px-6 border-t border-gray-100">
            <div class="max-w-6xl mx-auto">
                <div class="text-center max-w-xl mx-auto space-y-4 mb-16">
                    <h3 class="text-3xl font-bold tracking-tight">Our Pillars of Excellence</h3>
                    <p class="text-gray-500">
                        We build high-capacity food processing technology guided by strict global food handling compliance benchmarks.
                    </p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <!-- Card 1 -->
                    <div class="p-8 rounded-2xl bg-gray-50 hover:bg-emerald-50/50 hover:border-emerald-200/50 border border-transparent transition-all group">
                        <div class="h-12 w-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-6 group-hover:scale-110 transition">
                            <CheckCircle2 :size="24" />
                        </div>
                        <h4 class="text-lg font-bold mb-2">Uncompromised Safety</h4>
                        <p class="text-gray-600 text-sm leading-relaxed">
                            Continuous hygiene telemetry and automated lot tracking ensure zero-contaminant production lines and absolute compliance with ISO food handling norms.
                        </p>
                    </div>

                    <!-- Card 2 -->
                    <div class="p-8 rounded-2xl bg-gray-50 hover:bg-emerald-50/50 hover:border-emerald-200/50 border border-transparent transition-all group">
                        <div class="h-12 w-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-6 group-hover:scale-110 transition">
                            <Compass :size="24" />
                        </div>
                        <h4 class="text-lg font-bold mb-2">Sustainable Sourcing</h4>
                        <p class="text-gray-600 text-sm leading-relaxed">
                            Direct partnerships with certified eco-farms ensure fresh grains, raw starches, and organic spices enter our production chain with full provenance logs.
                        </p>
                    </div>

                    <!-- Card 3 -->
                    <div class="p-8 rounded-2xl bg-gray-50 hover:bg-emerald-50/50 hover:border-emerald-200/50 border border-transparent transition-all group">
                        <div class="h-12 w-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-6 group-hover:scale-110 transition">
                            <ShieldAlert :size="24" />
                        </div>
                        <h4 class="text-lg font-bold mb-2">Zero Waste Philosophy</h4>
                        <p class="text-gray-600 text-sm leading-relaxed">
                            By deploying advanced product shelf-life modeling and smart multi-warehouse stocks distribution, we achieve near-zero organic waste quotients.
                        </p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer class="bg-gray-900 text-gray-400 py-12 px-6 border-t border-gray-800 text-center text-sm">
            <div class="max-w-6xl mx-auto space-y-4">
                <div class="flex items-center justify-center gap-2 text-white font-semibold">
                    <div class="h-6 w-6 bg-emerald-600 rounded flex items-center justify-center text-xs">
                        <Package2 :size="14" />
                    </div>
                    Apex Food Processing Corp
                </div>
                <p>© 2026 Apex Food Processing Corp. All rights reserved. System operations managed by IMS portal.</p>
            </div>
        </footer>
    </div>
</template>
