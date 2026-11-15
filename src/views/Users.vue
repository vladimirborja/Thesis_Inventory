<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/layouts/AppLayout.vue'
import { Search, Edit, Trash2, X, Shield, User, Briefcase, ToggleLeft, ToggleRight } from 'lucide-vue-next'
import type { User as UserType, UserRole } from '@/types'
import { api } from '@/lib/api'

const authStore = useAuthStore()
const currentRole = computed(() => authStore.currentUser?.role || 'employee')
const isSuperAdmin = computed(() => currentRole.value === 'super_admin')

const users = ref<UserType[]>([])
const isLoading = ref(false)
const isSaving = ref(false)
const searchQuery = ref('')

const isModalOpen = ref(false)
const isEditMode = ref(true)
const currentEditId = ref<number | null>(null)
const formName = ref('')
const formEmail = ref('')
const formRole = ref<UserRole>('employee')

const filteredUsers = computed(() => {
  const q = searchQuery.value.toLowerCase()
  if (!q) return users.value
  return users.value.filter(
    (u) =>
      u.name.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q) ||
      u.role.toLowerCase().includes(q) ||
      (u.companyName || '').toLowerCase().includes(q),
  )
})

async function loadUsers() {
  isLoading.value = true
  try {
    users.value = await api.get<UserType[]>('/users')
  } finally {
    isLoading.value = false
  }
}

onMounted(loadUsers)

function openAddModal() {
  alert(
    'New users should register themselves on the Sign Up page. You can then manage their roles and permissions here.',
  )
}

function openEditModal(user: UserType) {
  isEditMode.value = true
  currentEditId.value = user.id
  formName.value = user.name
  formEmail.value = user.email
  formRole.value = user.role
  isModalOpen.value = true
}

async function handleSave() {
  if (!currentEditId.value) return
  isSaving.value = true
  try {
    await api.put(`/users/${currentEditId.value}/role`, { role: formRole.value })
    await loadUsers()
    isModalOpen.value = false
  } finally {
    isSaving.value = false
  }
}

async function handleDelete(id: number) {
  if (authStore.currentUser?.id === id) {
    alert('You cannot delete your own account!')
    return
  }
  if (!confirm('Are you sure you want to remove this user?')) return
  await api.delete(`/users/${id}`)
  await loadUsers()
}

async function togglePermission(user: UserType) {
  try {
    const updated = await api.put<UserType>(`/users/${user.id}/permissions`, {
      can_input_transactions: !user.canInputTransactions,
    })
    const idx = users.value.findIndex((u) => u.id === user.id)
    if (idx !== -1) {
      users.value[idx] = updated
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Failed to update permission'
    alert(msg)
  }
}
</script>

<template>
  <AppLayout>
    <div class="space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
            {{ isSuperAdmin ? 'User Directory' : 'Employee Management' }}
          </h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            {{
              isSuperAdmin
                ? 'Manage internal operator accounts, administrator roles, and permissions catalog.'
                : 'Manage employee permissions and transaction input access.'
            }}
          </p>
        </div>
        <button
          v-if="isSuperAdmin"
          type="button"
          class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-600/10 transition shrink-0"
          @click="openAddModal"
        >
          Provision User
        </button>
      </div>

      <!-- Your profile card -->
      <router-link
        to="/profile"
        class="flex items-center gap-4 p-4 md:p-5 rounded-2xl ims-glass border-2 border-emerald-500/45 dark:border-emerald-500/35 shadow-sm hover:border-emerald-600 dark:hover:border-emerald-400/60 transition"
      >
        <div
          class="h-14 w-14 rounded-full overflow-hidden bg-gradient-to-br from-emerald-500 to-emerald-800 flex items-center justify-center font-bold text-white text-lg uppercase ring-2 ring-emerald-500/30 shrink-0"
        >
          <img
            v-if="authStore.currentUser?.avatarUrl"
            :src="authStore.currentUser.avatarUrl"
            alt=""
            class="h-full w-full object-cover"
          />
          <span v-else>{{ (authStore.currentUser?.name || 'U').charAt(0) }}</span>
        </div>
        <div class="min-w-0 flex-1">
          <p class="text-[10px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
            Your profile
          </p>
          <p class="font-bold text-gray-900 dark:text-white truncate">{{ authStore.currentUser?.name }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
            {{ authStore.currentUser?.email }}
            <span v-if="authStore.currentUser?.companyName">
              · {{ authStore.currentUser.companyName }}
            </span>
          </p>
        </div>
        <span
          class="hidden sm:inline-flex px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wide border-2 bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:text-red-300 dark:border-red-900"
        >
          {{ (authStore.currentUser?.role || '').replace('_', ' ') }}
        </span>
      </router-link>

      <div
        class="p-4 ims-glass border-2 border-white/60 dark:border-white/15 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm"
      >
        <div class="relative flex-1 max-w-md">
          <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
            <Search :size="16" />
          </span>
          <input
            v-model="searchQuery"
            type="text"
            class="w-full pl-9 pr-4 py-2.5 rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-950 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-600/30"
            placeholder="Search users name, email, role..."
          />
        </div>
      </div>

      <div
        class="admin-table-wrap overflow-x-auto ims-glass border-2 border-white/60 dark:border-white/15 rounded-2xl shadow-sm"
      >
        <table class="w-full text-left border-collapse text-xs md:text-sm">
          <thead
            class="bg-gray-50 dark:bg-gray-800/80 text-gray-500 dark:text-gray-300 border-b-2 border-gray-200 dark:border-gray-700 uppercase text-[10px] tracking-wider font-bold"
          >
            <tr>
              <th class="px-5 py-4">Profile</th>
              <th class="px-5 py-4">Corporate Email</th>
              <th class="px-5 py-4">Company</th>
              <th class="px-5 py-4">Security Role</th>
              <th class="px-5 py-4 text-center">Transaction Access</th>
              <th class="px-5 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!isLoading && filteredUsers.length === 0">
              <td colspan="6" class="px-5 py-12 text-center text-gray-400">
                No user profiles match the active filters.
              </td>
            </tr>
            <tr
              v-for="u in filteredUsers"
              :key="u.id"
              class="border-b-2 border-gray-100 dark:border-gray-800 hover:bg-emerald-50/40 dark:hover:bg-gray-800/50 transition last:border-b-0"
            >
              <td class="px-5 py-4">
                <div class="flex items-center gap-3">
                  <div
                    class="h-12 w-12 rounded-full overflow-hidden bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center font-bold text-emerald-700 dark:text-emerald-300 uppercase ring-2 ring-emerald-600/25 shrink-0"
                  >
                    <img
                      v-if="u.avatarUrl"
                      :src="u.avatarUrl"
                      :alt="u.name"
                      class="h-full w-full object-cover"
                    />
                    <span v-else>{{ u.name.charAt(0) }}</span>
                  </div>
                  <div class="min-w-0">
                    <p class="font-bold text-gray-900 dark:text-white text-sm truncate">{{ u.name }}</p>
                    <p class="text-[10px] text-gray-400 mt-0.5">UID: {{ u.id }}</p>
                  </div>
                </div>
              </td>
              <td class="px-5 py-4 text-xs font-semibold text-gray-600 dark:text-gray-300">
                {{ u.email }}
              </td>
              <td class="px-5 py-4 text-xs text-gray-600 dark:text-gray-400">
                {{ u.companyName || '—' }}
              </td>
              <td class="px-5 py-4">
                <span
                  class="px-2.5 py-1.5 text-[9px] font-bold rounded-lg uppercase tracking-wider inline-flex items-center gap-1 border-2"
                  :class="
                    u.role === 'super_admin'
                      ? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/20 dark:text-red-400 dark:border-red-900'
                      : u.role === 'admin'
                        ? 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/20 dark:text-blue-400 dark:border-blue-900'
                        : 'bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700'
                  "
                >
                  <Shield v-if="u.role === 'super_admin'" :size="10" />
                  <Briefcase v-else-if="u.role === 'admin'" :size="10" />
                  <User v-else :size="10" />
                  {{ u.role.replace('_', ' ') }}
                </span>
              </td>
              <td class="px-5 py-4 text-center">
                <template v-if="u.role === 'employee'">
                  <button
                    type="button"
                    class="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold transition border-2"
                    :class="
                      u.canInputTransactions
                        ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800 hover:bg-emerald-100'
                        : 'bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:bg-gray-100'
                    "
                    :title="
                      u.canInputTransactions
                        ? 'Click to revoke input access'
                        : 'Click to grant input access'
                    "
                    @click="togglePermission(u)"
                  >
                    <ToggleRight v-if="u.canInputTransactions" :size="18" class="text-emerald-600" />
                    <ToggleLeft v-else :size="18" class="text-gray-400" />
                    {{ u.canInputTransactions ? 'Granted' : 'View Only' }}
                  </button>
                </template>
                <span v-else class="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">
                  Full Access
                </span>
              </td>
              <td class="px-5 py-4 text-right">
                <div class="flex items-center justify-end gap-2">
                  <button
                    v-if="isSuperAdmin"
                    type="button"
                    class="p-2 border-2 border-gray-200 dark:border-gray-700 hover:border-emerald-400 hover:bg-emerald-50 dark:hover:bg-gray-800 rounded-lg transition text-gray-500 hover:text-emerald-600"
                    title="Edit User Role"
                    @click="openEditModal(u)"
                  >
                    <Edit :size="15" />
                  </button>
                  <button
                    v-if="isSuperAdmin"
                    type="button"
                    class="p-2 border-2 border-gray-200 dark:border-gray-700 hover:border-red-300 hover:bg-red-50 dark:hover:bg-gray-800 rounded-lg transition text-gray-500 hover:text-red-500"
                    title="Revoke Access"
                    @click="handleDelete(u.id)"
                  >
                    <Trash2 :size="15" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="isModalOpen && isSuperAdmin" class="fixed inset-0 z-50 flex items-center justify-center px-4">
        <div class="fixed inset-0 bg-black/40 backdrop-blur-xs" @click="isModalOpen = false" />
        <div
          class="relative ims-glass rounded-3xl w-full max-w-md p-6 md:p-8 shadow-2xl border-2 border-white/60 dark:border-white/15 space-y-6"
        >
          <button
            type="button"
            class="absolute top-4 right-4 p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-400"
            @click="isModalOpen = false"
          >
            <X :size="18" />
          </button>

          <div>
            <h3 class="text-xl font-bold text-gray-900 dark:text-white">Edit User Credentials</h3>
            <p class="text-xs text-gray-400 mt-1">Specify role clearance level and associate organization.</p>
          </div>

          <form class="space-y-4" @submit.prevent="handleSave">
            <div class="space-y-1">
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Full Name</label>
              <input
                v-model="formName"
                type="text"
                disabled
                class="w-full px-4 py-2.5 border-2 border-gray-200 dark:border-gray-700 rounded-xl bg-transparent text-sm disabled:opacity-60 disabled:cursor-not-allowed"
                required
              />
            </div>
            <div class="space-y-1">
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">Email Address</label>
              <input
                v-model="formEmail"
                type="email"
                disabled
                class="w-full px-4 py-2.5 border-2 border-gray-200 dark:border-gray-700 rounded-xl bg-transparent text-sm disabled:opacity-60 disabled:cursor-not-allowed"
                required
              />
            </div>
            <div class="space-y-1">
              <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider">System Role Clearance</label>
              <select
                v-model="formRole"
                class="w-full px-4 py-2.5 border-2 border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-950 text-sm focus:outline-none"
                required
              >
                <option value="employee">Employee</option>
                <option value="admin">Admin</option>
                <option value="super_admin">Super Admin</option>
              </select>
            </div>
            <div class="flex items-center justify-end gap-3 pt-4 border-t-2 border-gray-200 dark:border-gray-700">
              <button
                type="button"
                class="px-4 py-2.5 border-2 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 text-xs font-semibold rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800"
                @click="isModalOpen = false"
              >
                Cancel
              </button>
              <button
                type="submit"
                class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl"
                :disabled="isSaving"
              >
                {{ isSaving ? 'Saving…' : 'Save User' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
