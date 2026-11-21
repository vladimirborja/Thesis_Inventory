<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  User,
  LayoutDashboard,
  Compass,
  CheckCircle2,
  ShieldAlert,
  Eye,
  Target,
  Flame,
  HeartHandshake,
  Lightbulb,
  Handshake,
} from 'lucide-vue-next'
import { LightWaves } from '@/components/ui/light-waves'
import { useDarkMode } from '@/composables/useDarkMode'

const router = useRouter()
const authStore = useAuthStore()
const { isDark } = useDarkMode()

const isLoggedIn = computed(() => !!authStore.currentUser)

const companyValues = [
  {
    title: 'Hard Work and Excellence',
    icon: Flame,
    body: 'We are driven by passion and genuine interest in everything we do, embracing the mindset of “bawal ang walang ginagawa”. We work both hard and smart to ensure productivity and are committed to delivering excellent quality in all our tasks.',
  },
  {
    title: 'Honesty, Integrity, and Loyalty',
    icon: HeartHandshake,
    body: 'We value transparency within the company. We openly and honestly communicate work-related issues with the appropriate peers or management. We uphold accountability, integrity, and loyalty to the company at all times.',
  },
  {
    title: 'Passion for Innovation',
    icon: Lightbulb,
    body: 'We believe in the entrepreneurial spirit that built the foundation of our company. We encourage every passionate and responsible team member to initiate, collaborate, and cooperate to turn innovative ideas into meaningful outcomes.',
  },
  {
    title: 'Respect',
    icon: Handshake,
    body: 'We uphold respect for our fellow workers, management, shareholders, and all stakeholders we interact with. We deal with everyone with fairness, compassion, and professionalism.',
  },
]

function handleProfileClick() {
  if (isLoggedIn.value) {
    router.push({ name: 'dashboard' })
  } else {
    router.push({ name: 'auth' })
  }
}
</script>

<template>
  <div class="landing-page relative flex min-h-screen flex-col overflow-x-hidden font-sans text-gray-900 dark:text-gray-100">
    <!-- Full-page Light Waves background -->
    <LightWaves
      class="pointer-events-none fixed inset-0 -z-10 min-h-screen bg-white dark:bg-[#050a08]"
      :colors="
        isDark
          ? ['#FF5A55', '#FFB020', '#3DDC84', '#86EFAC']
          : ['#D42D2A', '#F39C12', '#1B7C3D', '#FFFFFF']
      "
      placement="bottom"
      :amplitude="1"
      :angle="0"
      :depth="0.7"
      :fill="isDark ? 0.28 : 0.15"
      :height="0.55"
      :layers="6"
      :intensity="isDark ? 1.45 : 1"
    />

    <!-- Header -->
    <header class="liquid-glass liquid-glass--light sticky top-0 z-50 mx-4 mt-4 rounded-2xl px-5 py-3 sm:mx-6">
      <div class="mx-auto flex max-w-6xl items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <img
            src="/images/brand/logo.png"
            alt="Duque Food Products logo"
            class="h-10 w-10 rounded-full object-cover shadow-md"
          />
          <div>
            <h1 class="text-lg font-bold tracking-tight text-gray-900 dark:text-white">Duque Food Products</h1>
            <p class="text-[10px] font-semibold tracking-wider text-[var(--brand-green)] uppercase">
              DIMS Company Portal
            </p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <template v-if="isLoggedIn">
            <button
              @click="handleProfileClick"
              class="flex items-center gap-2 rounded-xl bg-[var(--brand-green)]/10 px-4 py-2 text-sm font-semibold text-[var(--brand-green-deep)] transition hover:bg-[var(--brand-green)]/15 dark:text-emerald-200"
            >
              <LayoutDashboard :size="16" />
              <span>Go to Dashboard</span>
            </button>
            <div
              class="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--brand-green)]/15 text-sm font-bold uppercase text-[var(--brand-green-deep)] dark:text-emerald-200"
            >
              {{ authStore.currentUser?.name.charAt(0) }}
            </div>
          </template>
          <template v-else>
            <button
              @click="handleProfileClick"
              class="flex h-10 w-10 items-center justify-center rounded-full text-gray-600 transition hover:bg-white/50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-white/10 dark:hover:text-white"
              title="Profile / Sign In"
            >
              <User :size="20" />
            </button>
          </template>
        </div>
      </div>
    </header>

    <!-- Hero Section -->
    <section class="relative mx-auto flex w-full max-w-3xl flex-1 flex-col items-center px-6 py-20 md:py-28">
      <div class="flex w-full flex-col items-center space-y-7 text-center">
        <h2 class="text-4xl font-extrabold leading-[1.05] tracking-tight text-gray-900 md:text-5xl lg:text-[3.4rem]">
          Duque Food
          <span class="text-[var(--brand-green)]">Products</span>.
        </h2>

        <div class="mx-auto max-w-2xl space-y-4">
          <p class="text-xl font-medium leading-snug tracking-tight text-gray-800 md:text-2xl">
            From raw ingredients to every Filipino table — tracked, safe, and ready.
          </p>
          <p class="mx-auto max-w-xl text-[15px] leading-relaxed text-gray-600 md:text-base">
            We combine modern storage, supply-chain visibility, and quality control so households
            and food businesses get fresh, nutritious products they can trust.
          </p>
        </div>

        <div class="flex flex-wrap items-center justify-center gap-3 pt-1">
          <button
            @click="handleProfileClick"
            class="rounded-2xl bg-[var(--brand-green)] px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-[var(--brand-green)]/25 transition hover:bg-[var(--brand-green-deep)]"
          >
            Access Inventory Portal
          </button>
          <button
            type="button"
            class="liquid-glass liquid-glass--light rounded-2xl px-6 py-3 text-sm font-semibold text-gray-800 transition hover:brightness-105"
            @click="router.push({ name: 'company' })"
          >
            Company Information
          </button>
        </div>
      </div>
    </section>

    <!-- Vision and Values Section -->
    <section id="vision" class="relative px-6 py-20">
      <div class="mx-auto max-w-6xl">
        <div class="mx-auto mb-14 max-w-2xl space-y-3 text-center">
          <h3 class="text-3xl font-bold tracking-tight text-gray-900">Our Pillars of Excellence</h3>
          <p class="text-[15px] leading-relaxed text-gray-600 md:text-base">
            Guided by safety, responsible sourcing, and less waste — so every product leaving our
            plant meets the standard Filipino families deserve.
          </p>
        </div>

        <div class="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div class="liquid-glass liquid-glass--light group rounded-3xl p-8 transition hover:brightness-[1.03]">
            <div
              class="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--brand-green)]/12 text-[var(--brand-green)] transition group-hover:scale-110"
            >
              <CheckCircle2 :size="24" />
            </div>
            <h4 class="mb-2 text-lg font-bold text-gray-900">Uncompromised Safety</h4>
            <p class="text-sm leading-relaxed text-gray-600">
              Continuous hygiene telemetry and automated lot tracking keep production lines clean
              and compliant with food-handling standards.
            </p>
          </div>

          <div class="liquid-glass liquid-glass--light group rounded-3xl p-8 transition hover:brightness-[1.03]">
            <div
              class="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--brand-green)]/12 text-[var(--brand-green)] transition group-hover:scale-110"
            >
              <Compass :size="24" />
            </div>
            <h4 class="mb-2 text-lg font-bold text-gray-900">Sustainable Sourcing</h4>
            <p class="text-sm leading-relaxed text-gray-600">
              Direct partnerships with trusted farms bring fresh ingredients into our chain with
              clear provenance from source to plant.
            </p>
          </div>

          <div class="liquid-glass liquid-glass--light group rounded-3xl p-8 transition hover:brightness-[1.03]">
            <div
              class="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--brand-green)]/12 text-[var(--brand-green)] transition group-hover:scale-110"
            >
              <ShieldAlert :size="24" />
            </div>
            <h4 class="mb-2 text-lg font-bold text-gray-900">Zero Waste Philosophy</h4>
            <p class="text-sm leading-relaxed text-gray-600">
              Smarter shelf-life planning and multi-warehouse stock control help us cut waste while
              keeping shelves reliably stocked.
            </p>
          </div>
        </div>

        <!-- Vision & Mission -->
        <div class="mt-16 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <article class="liquid-glass liquid-glass--light rounded-3xl p-8 md:p-10">
            <div
              class="mb-5 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--brand-green)] text-white"
            >
              <Eye :size="22" />
            </div>
            <p class="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--brand-green)]">
              Our Vision
            </p>
            <p class="mt-3 text-base leading-relaxed text-gray-700 md:text-lg">
              To be the leading provider of trusted and innovative processed food products that
              bring joy, nourishment, and real goodness to every household.
            </p>
          </article>

          <article class="liquid-glass liquid-glass--light rounded-3xl p-8 md:p-10">
            <div
              class="mb-5 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--brand-red)] text-white"
            >
              <Target :size="22" />
            </div>
            <p class="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--brand-red)]">
              Our Mission
            </p>
            <p class="mt-3 text-base leading-relaxed text-gray-700 md:text-lg">
              To create high-quality, safe, and delicious food products through innovation and
              excellence, while fostering a culture of integrity, respect, and teamwork that
              benefits our customers, employees, and community.
            </p>
          </article>
        </div>

        <!-- Values -->
        <div class="mt-16 space-y-8">
          <div class="space-y-2 text-center">
            <p class="text-[11px] font-bold uppercase tracking-[0.18em] text-[#F39C12]">
              Our Values
            </p>
            <h4 class="text-2xl font-bold tracking-tight text-gray-900 md:text-3xl">
              What guides every team member
            </h4>
          </div>

          <div class="grid grid-cols-1 gap-5 md:grid-cols-2">
            <article
              v-for="value in companyValues"
              :key="value.title"
              class="liquid-glass liquid-glass--light rounded-2xl p-6 transition hover:brightness-[1.03] md:p-7"
            >
              <div class="mb-4 flex items-start gap-3">
                <div
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--brand-gold)]/15 text-[var(--brand-gold)]"
                >
                  <component :is="value.icon" :size="20" />
                </div>
                <h5 class="pt-1.5 text-base font-bold text-gray-900 md:text-lg">
                  {{ value.title }}
                </h5>
              </div>
              <p class="text-sm leading-relaxed text-gray-600">
                {{ value.body }}
              </p>
            </article>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="relative px-6 pb-10 pt-4 text-center text-sm text-gray-500">
      <div class="liquid-glass liquid-glass--light mx-auto max-w-6xl space-y-4 rounded-3xl px-6 py-8">
        <div class="flex items-center justify-center gap-2 font-semibold text-gray-800">
          <img src="/images/brand/logo.png" alt="" class="h-6 w-6 rounded-full object-cover" />
          Duque Food Products - DIMS Company Portal
        </div>
        <p>© {{ new Date().getFullYear() }} Built by Justine Ryan Juco. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.liquid-glass {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  background: color-mix(in srgb, var(--brand-green-deep) 72%, #04110a);
  border: 2px solid rgba(255, 255, 255, 0.55);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 -12px 28px rgba(0, 0, 0, 0.22) inset,
    0 18px 48px rgba(0, 48, 28, 0.18),
    0 4px 16px rgba(0, 0, 0, 0.1);
}

@supports ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .liquid-glass {
    background: linear-gradient(
      155deg,
      rgba(255, 255, 255, 0.2) 0%,
      rgba(16, 128, 64, 0.32) 40%,
      rgba(8, 40, 24, 0.58) 100%
    );
    -webkit-backdrop-filter: blur(28px) saturate(180%);
    backdrop-filter: blur(28px) saturate(180%);
  }

  .liquid-glass--light {
    background: linear-gradient(
      155deg,
      rgba(255, 255, 255, 0.78) 0%,
      rgba(255, 255, 255, 0.48) 45%,
      rgba(232, 242, 236, 0.58) 100%
    );
    -webkit-backdrop-filter: blur(22px) saturate(160%);
    backdrop-filter: blur(22px) saturate(160%);
  }
}

.liquid-glass--light {
  background: rgba(255, 255, 255, 0.72);
  border-color: color-mix(in srgb, var(--brand-green) 28%, rgba(255, 255, 255, 0.85));
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 -8px 20px rgba(0, 0, 0, 0.04) inset,
    0 12px 32px rgba(0, 48, 28, 0.1),
    0 0 0 1px color-mix(in srgb, var(--brand-green) 12%, transparent);
}

.liquid-glass::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 1;
  border-radius: inherit;
  pointer-events: none;
  background: linear-gradient(
    125deg,
    rgba(255, 255, 255, 0.7) 0%,
    rgba(255, 255, 255, 0.18) 22%,
    transparent 45%,
    transparent 60%,
    rgba(255, 255, 255, 0.1) 100%
  );
  opacity: 0.85;
  mix-blend-mode: soft-light;
}

.liquid-glass::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 2;
  border-radius: inherit;
  pointer-events: none;
  padding: 2px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    color-mix(in srgb, var(--brand-green) 55%, white) 22%,
    color-mix(in srgb, var(--brand-gold) 65%, white) 48%,
    color-mix(in srgb, var(--brand-red) 50%, white) 72%,
    rgba(255, 255, 255, 0.85) 100%
  );
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  mask-composite: exclude;
}

.liquid-glass > * {
  position: relative;
  z-index: 3;
}
</style>
