<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/layouts/AppLayout.vue'
import {
  Camera,
  Shield,
  Mail,
  Building2,
  User as UserIcon,
  CheckCircle2,
  AlertCircle,
  BadgeCheck,
  ClipboardList,
} from 'lucide-vue-next'

const authStore = useAuthStore()
const user = computed(() => authStore.currentUser)

const name = ref('')
const companyName = ref('')
const isSaving = ref(false)
const isUploading = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const fileInput = ref<HTMLInputElement | null>(null)

const roleLabel = computed(() => (user.value?.role || 'employee').replace('_', ' '))
const roleTone = computed(() => {
  const r = user.value?.role
  if (r === 'super_admin') return 'bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-300'
  if (r === 'admin') return 'bg-sky-100 text-sky-800 dark:bg-sky-950/40 dark:text-sky-300'
  return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300'
})

const avatarSrc = computed(() => user.value?.avatarUrl || '')

onMounted(() => {
  name.value = user.value?.name || ''
  companyName.value = user.value?.companyName || ''
})

function flash(msg: string, type: 'success' | 'error' = 'success') {
  message.value = msg
  messageType.value = type
  setTimeout(() => { message.value = '' }, 4000)
}

async function saveProfile() {
  if (!name.value.trim()) {
    flash('Name is required.', 'error')
    return
  }
  isSaving.value = true
  try {
    await authStore.updateProfile({
      name: name.value.trim(),
      companyName: companyName.value.trim(),
    })
    flash('Profile saved.')
  } catch (e: unknown) {
    flash(e instanceof Error ? e.message : 'Could not save profile.', 'error')
  } finally {
    isSaving.value = false
  }
}

function pickAvatar() {
  fileInput.value?.click()
}

async function onAvatarSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    flash('Use JPEG, PNG, or WebP.', 'error')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    flash('Image must be under 5MB.', 'error')
    return
  }
  isUploading.value = true
  try {
    await authStore.uploadAvatar(file)
    flash('Profile photo updated.')
  } catch (err: unknown) {
    flash(err instanceof Error ? err.message : 'Upload failed.', 'error')
  } finally {
    isUploading.value = false
    input.value = ''
  }
}
</script>

<template>
  <AppLayout>
    <div class="mx-auto w-full max-w-3xl space-y-6">
      <div>
        <p class="text-[11px] font-bold uppercase tracking-[0.12em] text-emerald-700 dark:text-emerald-400">Account</p>
        <h2 class="text-2xl md:text-[1.75rem] font-bold tracking-tight text-gray-900 dark:text-white mt-1">My Profile</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Your identity in DIMS — role is assigned by admins and shown after every login.
        </p>
      </div>

      <Transition name="fade">
        <div
          v-if="message"
          class="flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium border"
          :class="messageType === 'success'
            ? 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-800'
            : 'bg-red-50 text-red-800 border-red-200 dark:bg-red-950/30 dark:text-red-300 dark:border-red-800'"
        >
          <CheckCircle2 v-if="messageType === 'success'" :size="16" />
          <AlertCircle v-else :size="16" />
          {{ message }}
        </div>
      </Transition>

      <!-- Identity card -->
      <section class="rounded-3xl ims-glass p-6 md:p-8 shadow-sm">
        <div class="flex flex-col sm:flex-row gap-6 items-start">
          <div class="relative group shrink-0">
            <div
              class="h-28 w-28 rounded-full overflow-hidden ring-4 ring-emerald-500/20 dark:ring-emerald-400/20 bg-gradient-to-br from-emerald-500 to-emerald-900 flex items-center justify-center text-white text-3xl font-bold uppercase shadow-lg shadow-emerald-900/20"
            >
              <img v-if="avatarSrc" :src="avatarSrc" alt="Profile" class="h-full w-full object-cover" />
              <span v-else>{{ (user?.name || 'U').charAt(0) }}</span>
            </div>
            <button
              type="button"
              class="absolute bottom-0 right-0 h-10 w-10 rounded-full bg-emerald-700 hover:bg-emerald-800 text-white flex items-center justify-center shadow-md transition disabled:opacity-60"
              :disabled="isUploading"
              title="Change photo"
              @click="pickAvatar"
            >
              <Camera :size="16" />
            </button>
            <input
              ref="fileInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              class="hidden"
              @change="onAvatarSelected"
            />
          </div>

          <div class="flex-1 min-w-0 space-y-3">
            <div>
              <h3 class="text-xl font-bold text-gray-900 dark:text-white truncate">{{ user?.name }}</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400 truncate">{{ user?.email }}</p>
            </div>
            <div class="flex flex-wrap gap-2">
              <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wide" :class="roleTone">
                <Shield :size="12" />
                {{ roleLabel }}
              </span>
              <span
                v-if="user?.canInputTransactions"
                class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wide bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300"
              >
                <ClipboardList :size="12" />
                Daily input enabled
              </span>
              <span
                v-else-if="user?.role === 'employee'"
                class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wide bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300"
              >
                View only
              </span>
            </div>
            <p class="text-[12px] text-gray-500 dark:text-gray-400 leading-relaxed max-w-md">
              <template v-if="user?.role === 'employee'">
                You are signed in as an <strong class="text-gray-800 dark:text-gray-200">Employee</strong>.
                Admins control elevated roles from User Management.
              </template>
              <template v-else-if="user?.role === 'admin'">
                You are signed in as an <strong class="text-gray-800 dark:text-gray-200">Admin</strong>
                with plant operations and compliance oversight.
              </template>
              <template v-else>
                You are signed in as <strong class="text-gray-800 dark:text-gray-200">Super Admin</strong>
                with full system access.
              </template>
            </p>
            <p v-if="isUploading" class="text-xs text-emerald-700 dark:text-emerald-400 font-medium">Uploading photo…</p>
          </div>
        </div>
      </section>

      <!-- Editable fields -->
      <section class="rounded-3xl ims-glass p-6 md:p-8 shadow-sm space-y-5">
        <div class="flex items-center gap-2">
          <BadgeCheck :size="18" class="text-emerald-600 dark:text-emerald-400" />
          <h3 class="font-bold text-gray-900 dark:text-white">Profile details</h3>
        </div>

        <form class="space-y-4" @submit.prevent="saveProfile">
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1.5">Full name</label>
            <div class="relative">
              <UserIcon :size="15" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                v-model="name"
                type="text"
                required
                class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-950 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
              />
            </div>
          </div>

          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1.5">Email</label>
            <div class="relative">
              <Mail :size="15" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                :value="user?.email"
                type="email"
                disabled
                class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-950/60 text-sm text-gray-500 dark:text-gray-400 cursor-not-allowed"
              />
            </div>
            <p class="text-[11px] text-gray-400 mt-1">Email is fixed for login identity.</p>
          </div>

          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1.5">Company</label>
            <div class="relative">
              <Building2 :size="15" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                v-model="companyName"
                type="text"
                class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-950 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
                placeholder="Duque Food Products"
              />
            </div>
          </div>

          <div class="pt-2">
            <button
              type="submit"
              :disabled="isSaving"
              class="px-5 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:opacity-60 text-white text-sm font-bold transition"
            >
              {{ isSaving ? 'Saving…' : 'Save changes' }}
            </button>
          </div>
        </form>
      </section>
    </div>
  </AppLayout>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
