<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { MapPin, Phone, Mail, Clock, ArrowLeft, Facebook, Send } from 'lucide-vue-next'
import Skiper6HoverMember from '@/components/v1/Skiper6HoverMember.vue'
import { LightWaves } from '@/components/ui/light-waves'

const router = useRouter()
const CONTACT_EMAIL = 'duquefoodproducts@gmail.com'

const inquiry = reactive({
  name: '',
  email: '',
  message: '',
})

function sendInquiry() {
  const name = inquiry.name.trim()
  const email = inquiry.email.trim()
  const message = inquiry.message.trim()
  if (!name || !email || !message) return

  const subject = encodeURIComponent(`Inquiry from ${name} — Duque Food Products`)
  const body = encodeURIComponent(
    `Name: ${name}\nEmail: ${email}\n\nMessage:\n${message}`,
  )
  window.location.href = `mailto:${CONTACT_EMAIL}?subject=${subject}&body=${body}`
}

const products = [
  { name: 'Skinless Longganisa', image: '/images/products/skinless-longganisa.jpg' },
  { name: 'Pork Tocino', image: '/images/products/pork-tocino.jpg' },
  { name: 'Ham', image: '/images/products/ham.jpg' },
  { name: 'Embotido', image: '/images/products/embotido.jpg' },
  { name: 'Bologna', image: '/images/products/bologna.jpg' },
  { name: 'Burger Patties', image: '/images/products/burger-patties.jpg' },
  { name: 'Hotdog', image: '/images/products/hotdog.jpg' },
  { name: 'Skinless', image: '/images/products/skinless.jpg' },
]
</script>

<template>
  <div class="company-page relative min-h-screen overflow-x-hidden font-sans text-gray-900">
    <!-- Full-page Light Waves background -->
    <LightWaves
      class="pointer-events-none fixed inset-0 -z-10 min-h-screen bg-white"
      :colors="['#D42D2A', '#F39C12', '#1B7C3D', '#FFFFFF']"
      placement="bottom"
      :amplitude="1"
      :angle="0"
      :depth="0.7"
      :fill="0.15"
      :height="0.55"
      :layers="6"
    />

    <!-- Top bar -->
    <header class="liquid-glass liquid-glass--light sticky top-0 z-40 mx-4 mt-4 rounded-2xl px-5 py-3 sm:mx-6">
      <div class="mx-auto flex max-w-6xl items-center justify-between gap-4">
        <div class="flex min-w-0 items-center gap-3">
          <img
            src="/images/brand/logo.jpg"
            alt="Duque Food Products logo"
            class="h-11 w-11 shrink-0 rounded-full object-cover shadow-sm"
          />
          <div class="min-w-0">
            <p class="truncate font-bold tracking-tight text-gray-900">Duque Food Products</p>
            <p class="text-[10px] uppercase tracking-wider text-[var(--brand-green)]">
              Company Information
            </p>
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <button
            type="button"
            class="hidden items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold text-gray-700 transition hover:bg-black/5 sm:inline-flex"
            @click="router.push('/')"
          >
            <ArrowLeft :size="14" /> Home
          </button>
          <button
            type="button"
            class="rounded-lg bg-[var(--brand-gold)] px-3 py-2 text-xs font-bold text-[var(--brand-green-deep)] transition hover:brightness-110"
            @click="router.push('/auth')"
          >
            Staff Login
          </button>
        </div>
      </div>
    </header>

    <!-- Hero -->
    <section class="relative px-5 pt-10">
      <div
        class="liquid-glass liquid-glass--brand relative mx-auto max-w-6xl overflow-hidden rounded-[1.75rem] md:rounded-[2rem]"
      >
        <div
          class="absolute inset-0 opacity-40"
          style="
            background-image:
              radial-gradient(circle at 18% 25%, var(--brand-gold) 0%, transparent 42%),
              radial-gradient(circle at 85% 75%, #fff 0%, transparent 35%);
          "
        />
        <div
          class="relative z-10 flex flex-col items-center gap-10 px-6 py-14 md:flex-row md:px-10 md:py-16"
        >
          <img
            src="/images/brand/logo.jpg"
            alt="FDP — Duque Food Products"
            class="h-40 w-40 shrink-0 rounded-full border-4 border-white/80 object-cover shadow-2xl md:h-48 md:w-48"
          />
          <div class="space-y-3 text-center text-white md:text-left">
            <p class="text-xs font-bold uppercase tracking-[0.2em] text-[var(--brand-gold)]">
              Food Manufacturing · Pampanga
            </p>
            <h1 class="text-3xl font-extrabold leading-tight tracking-tight md:text-5xl">
              Duque Food Products
            </h1>
            <p class="max-w-xl text-sm leading-relaxed text-white/90 md:text-base">
              Processed meat products crafted for local customers and businesses — with quality, food
              safety, and satisfaction at the core.
            </p>
            <p class="pt-1 text-sm text-white/75">
              Owner: <span class="font-semibold text-white">Jesus F. Duque Jr.</span>
            </p>
          </div>
        </div>
      </div>
    </section>

    <main class="mx-auto max-w-6xl space-y-14 px-5 py-12">
      <!-- About -->
      <section class="space-y-5">
        <div class="liquid-glass liquid-glass--light space-y-3 rounded-3xl px-6 py-6 md:px-8">
          <h2 class="text-xl font-bold tracking-tight text-[var(--brand-green-deep)]">
            About the Company
          </h2>
          <p class="max-w-3xl leading-relaxed text-gray-700">
            Duque Food Products is a food manufacturing and processing company producing processed
            meat products for local customers and businesses while maintaining quality, food safety,
            and customer satisfaction.
          </p>
        </div>

        <div class="grid gap-3 text-sm sm:grid-cols-2">
          <div class="liquid-glass liquid-glass--light flex gap-3 rounded-2xl p-4">
            <MapPin :size="18" class="mt-0.5 shrink-0 text-[var(--brand-red)]" />
            <div>
              <p class="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                Business Address
              </p>
              <p class="mt-1 leading-snug text-gray-800">
                #353 St. James Street, Purok 7 Brgy. Malino, City of San Fernando, Pampanga 2000
              </p>
            </div>
          </div>
          <div class="liquid-glass liquid-glass--light flex gap-3 rounded-2xl p-4">
            <Clock :size="18" class="mt-0.5 shrink-0 text-[var(--brand-green)]" />
            <div>
              <p class="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                Business Hours
              </p>
              <p class="mt-1 italic text-gray-500">To be updated</p>
            </div>
          </div>
          <div class="liquid-glass liquid-glass--light flex gap-3 rounded-2xl p-4">
            <Phone :size="18" class="mt-0.5 shrink-0 text-[var(--brand-green)]" />
            <div>
              <p class="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                Contact Number
              </p>
              <a href="tel:+63454094033" class="mt-1 block font-medium text-gray-800 hover:underline">
                (045) 409-4033
              </a>
            </div>
          </div>
          <div class="liquid-glass liquid-glass--light flex gap-3 rounded-2xl p-4">
            <Mail :size="18" class="mt-0.5 shrink-0 text-[var(--brand-gold)]" />
            <div>
              <p class="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                Email Address
              </p>
              <a
                href="mailto:duquefoodproducts@gmail.com"
                class="mt-1 block break-all font-medium text-gray-800 hover:underline"
              >
                duquefoodproducts@gmail.com
              </a>
            </div>
          </div>
        </div>
      </section>

      <!-- Our Products -->
      <section class="space-y-5">
        <div class="liquid-glass liquid-glass--light space-y-2 rounded-3xl px-6 py-6 md:px-8">
          <h2 class="text-xl font-bold tracking-tight text-[var(--brand-green-deep)]">
            Our Products
          </h2>
          <p class="text-sm text-gray-600">
            Eight signature processed meats — hover any photo to spotlight it.
          </p>
        </div>

        <div class="liquid-glass-stage relative">
          <div
            class="pointer-events-none absolute -inset-6 -z-10 rounded-[2.5rem] opacity-90 blur-2xl"
            style="
              background:
                radial-gradient(ellipse 55% 60% at 18% 30%, color-mix(in srgb, var(--brand-red) 55%, transparent), transparent 70%),
                radial-gradient(ellipse 50% 55% at 82% 70%, color-mix(in srgb, var(--brand-green) 50%, transparent), transparent 68%),
                radial-gradient(ellipse 40% 40% at 50% 50%, color-mix(in srgb, var(--brand-gold) 35%, transparent), transparent 70%);
            "
          />
          <div class="liquid-glass liquid-glass--brand overflow-hidden rounded-[1.75rem] md:rounded-[2rem]">
            <Skiper6HoverMember
              :team-members="products"
              default-name="Our Products"
              background-color="transparent"
              text-color="rgba(255,255,255,0.32)"
              hover-text-color="#ffffff"
              cursor-color="#F09020"
              class-name="liquid-glass-inner"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          <article
            v-for="product in products"
            :key="product.name"
            class="liquid-glass liquid-glass--light group overflow-hidden rounded-2xl transition hover:-translate-y-0.5 hover:brightness-[1.03]"
          >
            <div class="aspect-[4/3] overflow-hidden bg-stone-100/60">
              <img
                :src="product.image"
                :alt="product.name"
                class="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                loading="lazy"
              />
            </div>
            <div class="border-t border-white/40 px-3 py-3">
              <p class="text-sm font-semibold text-gray-900">{{ product.name }}</p>
              <p class="mt-0.5 text-[10px] font-bold uppercase tracking-wider text-[var(--brand-red)]">
                Duque Food Products
              </p>
            </div>
          </article>
        </div>
      </section>

      <!-- Contact + Map -->
      <section id="contact" class="space-y-5">
        <div class="liquid-glass liquid-glass--light rounded-3xl px-6 py-5 md:px-8">
          <h2 class="text-xl font-bold tracking-tight text-[var(--brand-green-deep)]">
            Contact & Location
          </h2>
        </div>
        <div class="grid gap-5 lg:grid-cols-5">
          <div class="space-y-3 text-sm lg:col-span-2">
            <div class="liquid-glass liquid-glass--light space-y-3 rounded-2xl p-5">
              <p class="flex items-start gap-2">
                <MapPin :size="16" class="mt-0.5 shrink-0 text-[var(--brand-red)]" />
                <span>#353 St. James Street, Purok 7 Brgy. Malino, City of San Fernando, Pampanga 2000</span>
              </p>
              <p class="flex items-center gap-2">
                <Phone :size="16" class="shrink-0 text-[var(--brand-green)]" />
                <a href="tel:+63454094033" class="font-medium text-gray-800 hover:underline">
                  (045) 409-4033
                </a>
              </p>
              <p class="flex items-center gap-2">
                <Mail :size="16" class="shrink-0 text-[var(--brand-gold)]" />
                <a
                  href="mailto:duquefoodproducts@gmail.com"
                  class="break-all font-medium text-gray-800 hover:underline"
                >
                  duquefoodproducts@gmail.com
                </a>
              </p>
              <a
                href="https://www.facebook.com/profile.php?id=61579960800020"
                target="_blank"
                rel="noopener noreferrer"
                class="mt-2 inline-flex items-center gap-2 rounded-xl bg-[#1877F2]/10 px-3 py-2 text-xs font-bold text-[#1877F2] transition hover:bg-[#1877F2]/15"
              >
                <Facebook :size="14" /> Facebook Page
              </a>
            </div>

            <form
              class="liquid-glass liquid-glass--light space-y-4 rounded-2xl p-5"
              @submit.prevent="sendInquiry"
            >
              <div class="space-y-1">
                <p class="text-xl font-bold tracking-tight text-[var(--brand-green-deep)]">Message us for more inquiries.</p>
                <p class="text-[11px] text-gray-500">
                  Sends to
                  <span class="font-semibold text-[var(--brand-green)]">{{ CONTACT_EMAIL }}</span>
                </p>
              </div>

              <label class="block space-y-1.5">
                <span class="text-[10px] font-bold uppercase tracking-[0.16em] text-gray-400">
                  Name
                </span>
                <input
                  v-model="inquiry.name"
                  type="text"
                  required
                  autocomplete="name"
                  placeholder="Juan Dela Cruz"
                  class="inquiry-input"
                />
              </label>

              <label class="block space-y-1.5">
                <span class="text-[10px] font-bold uppercase tracking-[0.16em] text-gray-400">
                  Email
                </span>
                <input
                  v-model="inquiry.email"
                  type="email"
                  required
                  autocomplete="email"
                  placeholder="juandelacruz@gmail.com"
                  class="inquiry-input"
                />
              </label>

              <label class="block space-y-1.5">
                <span class="text-[10px] font-bold uppercase tracking-[0.16em] text-gray-400">
                  Message
                </span>
                <textarea
                  v-model="inquiry.message"
                  required
                  rows="4"
                  placeholder="Hi, I'd like to ask about…"
                  class="inquiry-input resize-none"
                />
              </label>

              <button type="submit" class="inquiry-send">
                Send Message
                <Send :size="15" />
              </button>
            </form>
          </div>
          <div class="lg:col-span-3">
            <div class="liquid-glass liquid-glass--light overflow-hidden rounded-2xl">
              <div class="relative aspect-[4/3] w-full sm:aspect-[16/10]">
                <iframe
                  class="absolute inset-0 h-full w-full border-0"
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

    <footer class="relative px-5 pb-10 pt-2 text-sm text-gray-500">
      <div
        class="liquid-glass liquid-glass--light mx-auto flex max-w-6xl flex-col items-center justify-center gap-2 rounded-3xl px-6 py-6 text-center"
      >
        <p>© {{ new Date().getFullYear() }} Built by Justine Ryan Juco. All rights reserved.</p>
        <button
          type="button"
          class="font-semibold text-[var(--brand-green)] hover:underline"
          @click="router.push('/auth')"
        >
          Employee / Admin Portal
        </button>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.liquid-glass-stage {
  isolation: isolate;
}

.liquid-glass {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.55);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 -10px 24px rgba(0, 0, 0, 0.04) inset,
    0 14px 40px rgba(0, 48, 28, 0.1),
    0 2px 10px rgba(0, 0, 0, 0.04);
}

@supports ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .liquid-glass,
  .liquid-glass--light {
    background: linear-gradient(
      155deg,
      rgba(255, 255, 255, 0.78) 0%,
      rgba(255, 255, 255, 0.42) 48%,
      rgba(255, 255, 255, 0.28) 100%
    );
    -webkit-backdrop-filter: blur(24px) saturate(170%);
    backdrop-filter: blur(24px) saturate(170%);
  }

  .liquid-glass--brand {
    background: linear-gradient(
      155deg,
      rgba(255, 255, 255, 0.18) 0%,
      rgba(16, 128, 64, 0.45) 40%,
      rgba(8, 40, 24, 0.72) 100%
    );
    -webkit-backdrop-filter: blur(28px) saturate(180%);
    backdrop-filter: blur(28px) saturate(180%);
  }
}

.liquid-glass--light {
  background: rgba(255, 255, 255, 0.55);
}

.liquid-glass--brand {
  background: color-mix(in srgb, var(--brand-green-deep) 78%, #04110a);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 -12px 28px rgba(0, 0, 0, 0.28) inset,
    0 18px 48px rgba(0, 48, 28, 0.22),
    0 4px 16px rgba(0, 0, 0, 0.12);
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
    rgba(255, 255, 255, 0.75) 0%,
    rgba(255, 255, 255, 0.18) 24%,
    transparent 48%,
    transparent 62%,
    rgba(255, 255, 255, 0.12) 100%
  );
  opacity: 0.9;
  mix-blend-mode: soft-light;
}

.liquid-glass::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 2;
  border-radius: inherit;
  pointer-events: none;
  padding: 1.5px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    rgba(255, 255, 255, 0.55) 18%,
    rgba(27, 124, 61, 0.28) 42%,
    rgba(240, 144, 32, 0.4) 68%,
    rgba(212, 45, 42, 0.35) 85%,
    rgba(255, 255, 255, 0.7) 100%
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

.liquid-glass :deep(.liquid-glass-inner) {
  background: transparent !important;
}

.inquiry-input {
  width: 100%;
  border-radius: 0.85rem;
  border: 1px solid rgba(255, 255, 255, 0.55);
  background: rgba(255, 255, 255, 0.45);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  padding: 0.75rem 0.9rem;
  font-size: 0.875rem;
  color: #111827;
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.inquiry-input::placeholder {
  color: rgba(107, 114, 128, 0.75);
}

.inquiry-input:focus {
  border-color: color-mix(in srgb, var(--brand-green) 45%, white);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand-green) 18%, transparent);
}

.inquiry-send {
  display: inline-flex;
  width: 100%;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border-radius: 0.9rem;
  border: none;
  background: linear-gradient(180deg, #2fd66a 0%, #1bb853 100%);
  padding: 0.85rem 1rem;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #04140a;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 6px 0 #0f7a3a,
    0 10px 20px rgba(16, 128, 64, 0.35);
  transition:
    transform 0.15s ease,
    filter 0.15s ease;
}

.inquiry-send:hover {
  filter: brightness(1.05);
}

.inquiry-send:active {
  transform: translateY(3px);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.35) inset,
    0 3px 0 #0f7a3a,
    0 6px 12px rgba(16, 128, 64, 0.3);
}
</style>
