<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  Package2,
  MapPin,
  Phone,
  Mail,
  Clock,
  ArrowLeft,
  Facebook,
  Building2,
} from 'lucide-vue-next'

const router = useRouter()

const products = [
  'Skinless Longganisa',
  'Tocino',
  'Ham',
  'Embotido',
  'Bologna',
  'Patties',
  'Siomai',
]

const galleryPlaceholders = [1, 2, 3, 4, 5, 6]
</script>

<template>
  <div class="min-h-screen bg-[#f7f5f0] text-gray-900 font-sans">
    <!-- Top bar -->
    <header
      class="sticky top-0 z-40 bg-[#1a3a2a]/95 backdrop-blur text-white border-b border-emerald-900/40"
    >
      <div class="max-w-5xl mx-auto px-5 py-3.5 flex items-center justify-between gap-4">
        <div class="flex items-center gap-3 min-w-0">
          <div
            class="h-10 w-10 rounded-xl bg-emerald-700/80 flex items-center justify-center shrink-0"
          >
            <Package2 :size="20" />
          </div>
          <div class="min-w-0">
            <p class="font-bold tracking-tight truncate">Duque Food Products</p>
            <p class="text-[10px] text-emerald-200/80 uppercase tracking-wider">
              Company Information
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            type="button"
            class="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-emerald-100 hover:bg-white/10 transition"
            @click="router.push('/')"
          >
            <ArrowLeft :size="14" /> Home
          </button>
          <button
            type="button"
            class="px-3 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-emerald-950 text-xs font-bold transition"
            @click="router.push('/auth')"
          >
            Staff Login
          </button>
        </div>
      </div>
    </header>

    <!-- Hero / identity -->
    <section class="relative overflow-hidden border-b border-emerald-900/10">
      <div class="absolute inset-0 bg-gradient-to-br from-[#1a3a2a] via-[#234d38] to-[#0f2419]" />
      <div
        class="absolute inset-0 opacity-20"
        style="
          background-image:
            radial-gradient(circle at 20% 30%, #86efac 0%, transparent 45%),
            radial-gradient(circle at 80% 70%, #fbbf24 0%, transparent 40%);
        "
      />
      <div
        class="relative max-w-5xl mx-auto px-5 py-14 md:py-20 flex flex-col md:flex-row items-center gap-10"
      >
        <!-- Logo placeholder -->
        <div
          class="h-36 w-36 md:h-44 md:w-44 rounded-3xl bg-white/10 border border-white/20 flex flex-col items-center justify-center text-emerald-100 shrink-0 shadow-lg"
        >
          <Building2 :size="48" class="opacity-80 mb-2" />
          <span class="text-[10px] font-semibold uppercase tracking-wider opacity-70">Logo</span>
        </div>
        <div class="text-center md:text-left text-white space-y-3">
          <p class="text-emerald-300 text-xs font-bold uppercase tracking-[0.2em]">
            Food Manufacturing · Pampanga
          </p>
          <h1 class="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight">
            Duque Food Products
          </h1>
          <p class="text-emerald-100/90 text-sm md:text-base max-w-xl leading-relaxed">
            Processed meat products crafted for local customers and businesses — with quality, food
            safety, and satisfaction at the core.
          </p>
          <p class="text-sm text-emerald-200/80 pt-1">
            Owner: <span class="font-semibold text-white">Jesus F. Duque Jr.</span>
          </p>
        </div>
      </div>
    </section>

    <main class="max-w-5xl mx-auto px-5 py-12 space-y-14">
      <!-- About -->
      <section class="space-y-4">
        <h2 class="text-xl font-bold tracking-tight text-[#1a3a2a]">About the Company</h2>
        <p class="text-gray-700 leading-relaxed max-w-3xl">
          Duque Food Products is a food manufacturing and processing company producing processed
          meat products for local customers and businesses while maintaining quality, food safety,
          and customer satisfaction.
        </p>
        <div class="grid sm:grid-cols-2 gap-3 text-sm">
          <div class="flex gap-3 p-4 rounded-2xl bg-white border border-stone-200/80">
            <MapPin :size="18" class="text-emerald-700 shrink-0 mt-0.5" />
            <div>
              <p class="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                Business Address
              </p>
              <p class="mt-1 text-gray-800 leading-snug">
                Purok 7, Malino, City of San Fernando, Pampanga
              </p>
            </div>
          </div>
          <div class="flex gap-3 p-4 rounded-2xl bg-white border border-stone-200/80">
            <Clock :size="18" class="text-emerald-700 shrink-0 mt-0.5" />
            <div>
              <p class="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                Business Hours
              </p>
              <p class="mt-1 text-gray-500 italic">To be updated</p>
            </div>
          </div>
          <div class="flex gap-3 p-4 rounded-2xl bg-white border border-stone-200/80">
            <Phone :size="18" class="text-emerald-700 shrink-0 mt-0.5" />
            <div>
              <p class="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                Contact Number
              </p>
              <p class="mt-1 text-gray-500 italic">To be updated</p>
            </div>
          </div>
          <div class="flex gap-3 p-4 rounded-2xl bg-white border border-stone-200/80">
            <Mail :size="18" class="text-emerald-700 shrink-0 mt-0.5" />
            <div>
              <p class="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                Email Address
              </p>
              <p class="mt-1 text-gray-500 italic">To be updated</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Products -->
      <section class="space-y-4">
        <h2 class="text-xl font-bold tracking-tight text-[#1a3a2a]">Our Products</h2>
        <p class="text-sm text-gray-600">
          Processed meats made for everyday Filipino tables and food businesses.
        </p>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          <div
            v-for="name in products"
            :key="name"
            class="p-4 rounded-2xl bg-white border border-stone-200/80 text-center hover:border-emerald-300 transition"
          >
            <div
              class="mx-auto mb-3 h-12 w-12 rounded-full bg-emerald-50 text-emerald-800 flex items-center justify-center font-bold text-sm"
            >
              {{ name.charAt(0) }}
            </div>
            <p class="text-sm font-semibold text-gray-800">{{ name }}</p>
          </div>
        </div>
      </section>

      <!-- Gallery -->
      <section class="space-y-4">
        <h2 class="text-xl font-bold tracking-tight text-[#1a3a2a]">Gallery</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div
            v-for="n in galleryPlaceholders"
            :key="n"
            class="aspect-[4/3] rounded-2xl bg-stone-200/80 border border-stone-300/50 flex items-center justify-center text-stone-400 text-xs font-semibold"
          >
            Photo {{ n }}
          </div>
        </div>
      </section>

      <!-- Contact + Map -->
      <section id="contact" class="space-y-5">
        <h2 class="text-xl font-bold tracking-tight text-[#1a3a2a]">Contact & Location</h2>
        <div class="grid lg:grid-cols-5 gap-5">
          <div class="lg:col-span-2 space-y-3 text-sm">
            <div class="p-5 rounded-2xl bg-white border border-stone-200/80 space-y-3">
              <p class="flex gap-2 items-start">
                <MapPin :size="16" class="text-emerald-700 mt-0.5 shrink-0" />
                <span>Purok 7, Malino, City of San Fernando, Pampanga</span>
              </p>
              <p class="flex gap-2 items-center text-gray-500">
                <Phone :size="16" class="text-emerald-700 shrink-0" />
                <span class="italic">Contact number — to be updated</span>
              </p>
              <p class="flex gap-2 items-center text-gray-500">
                <Mail :size="16" class="text-emerald-700 shrink-0" />
                <span class="italic">Email — to be updated</span>
              </p>
              <a
                href="https://www.facebook.com/"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-2 mt-2 px-3 py-2 rounded-xl bg-[#1877F2]/10 text-[#1877F2] text-xs font-bold hover:bg-[#1877F2]/15 transition"
              >
                <Facebook :size="14" /> Facebook Page
              </a>
            </div>
          </div>
          <div class="lg:col-span-3">
            <div class="rounded-2xl overflow-hidden border border-stone-200/80 bg-white shadow-sm">
              <div class="relative w-full aspect-[4/3] sm:aspect-[16/10]">
                <iframe
                  class="absolute inset-0 w-full h-full border-0"
                  src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3851.585063679261!2d120.62408617498862!3d15.12618056399328!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3396f100018ce5cd%3A0x2eb80025c77db1cf!2sDuque%20Food%20Products!5e0!3m2!1sen!2sph!4v1784893906460!5m2!1sen!2sph"
                  allowfullscreen
                  loading="lazy"
                  referrerpolicy="strict-origin-when-cross-origin"
                  title="Duque Food Products location map"
                />
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer class="border-t border-stone-200 bg-white">
      <div
        class="max-w-5xl mx-auto px-5 py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-500"
      >
        <p>© {{ new Date().getFullYear() }} Built by Justine Ryan Juco. All rights reserved.</p>
        <button
          type="button"
          class="text-emerald-700 font-semibold hover:underline"
          @click="router.push('/auth')"
        >
          Employee / Admin Portal
        </button>
      </div>
    </footer>
  </div>
</template>
