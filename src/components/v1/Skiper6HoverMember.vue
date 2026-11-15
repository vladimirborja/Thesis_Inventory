<script setup lang="ts">
/**
 * Vue recreation of Skiper UI skiper6 — Hover members.
 * Original: https://skiper-ui.com/v1/skiper6 (attribution required for free use)
 */
import { computed, ref } from 'vue'
import { useMouseInElement } from '@vueuse/core'

export interface HoverMemberItem {
  name: string
  image: string
}

const props = withDefaults(
  defineProps<{
    teamMembers: HoverMemberItem[]
    defaultName?: string
    className?: string
    backgroundColor?: string
    textColor?: string
    hoverTextColor?: string
    cursorColor?: string
  }>(),
  {
    defaultName: 'Our Products',
    backgroundColor: '#0f1f14',
    textColor: 'rgba(255,255,255,0.35)',
    hoverTextColor: '#ffffff',
    cursorColor: '#F09020',
  },
)

const rootEl = ref<HTMLElement | null>(null)
const activeIndex = ref<number | null>(null)
const { x, y, isOutside } = useMouseInElement(rootEl)

const displayName = computed(() =>
  activeIndex.value === null
    ? props.defaultName
    : props.teamMembers[activeIndex.value]?.name ?? props.defaultName,
)

const isHoveringMember = computed(() => activeIndex.value !== null)

function onEnter(index: number) {
  activeIndex.value = index
}
function onLeave() {
  activeIndex.value = null
}
</script>

<template>
  <section
    ref="rootEl"
    class="skiper6 relative overflow-hidden select-none"
    :class="className"
    :style="backgroundColor === 'transparent' ? undefined : { backgroundColor }"
  >
    <!-- Cursor follower -->
    <div
      class="pointer-events-none absolute z-30 hidden md:block size-10 -translate-x-1/2 -translate-y-1/2 rounded-full mix-blend-difference transition-opacity duration-200"
      :class="isOutside ? 'opacity-0' : 'opacity-100'"
      :style="{
        left: `${x}px`,
        top: `${y}px`,
        backgroundColor: cursorColor,
      }"
    />

    <div class="relative z-10 flex min-h-[28rem] flex-col items-center justify-between gap-10 px-5 py-14 md:min-h-[32rem] md:py-16">
      <!-- Animated title -->
      <div class="flex flex-1 items-center justify-center px-4 text-center">
        <Transition name="skiper-name" mode="out-in">
          <h3
            :key="displayName"
            class="max-w-4xl text-4xl font-black uppercase leading-[0.95] tracking-tight sm:text-5xl md:text-6xl lg:text-7xl"
            :style="{ color: isHoveringMember ? hoverTextColor : textColor }"
          >
            {{ displayName }}
          </h3>
        </Transition>
      </div>

      <!-- Member / product thumbnails -->
      <ul
        class="flex w-full max-w-5xl flex-wrap items-end justify-center gap-3 sm:gap-0 sm:px-4"
        role="list"
      >
        <li
          v-for="(member, index) in teamMembers"
          :key="member.name + index"
          class="relative transition-transform duration-300 ease-out sm:-mx-2"
          :class="activeIndex === index ? 'z-20 scale-110 sm:-translate-y-3' : 'z-10 hover:z-20'"
          @mouseenter="onEnter(index)"
          @mouseleave="onLeave"
          @focusin="onEnter(index)"
          @focusout="onLeave"
        >
          <button
            type="button"
            class="group block overflow-hidden rounded-full border-[3px] border-white/90 shadow-lg outline-none ring-offset-2 focus-visible:ring-2 focus-visible:ring-[var(--brand-gold,#F09020)]"
            :aria-label="member.name"
          >
            <img
              :src="member.image"
              :alt="member.name"
              class="size-20 object-cover transition duration-300 group-hover:scale-105 sm:size-24 md:size-28"
              loading="lazy"
            />
          </button>
        </li>
      </ul>


    </div>
  </section>
</template>

<style scoped>
.skiper-name-enter-active,
.skiper-name-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}
.skiper-name-enter-from {
  opacity: 0;
  transform: translateY(18px) scale(0.96);
}
.skiper-name-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(1.02);
}
</style>
