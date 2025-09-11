<template>
  <div class="comment-list">
    <h2>Comments</h2>

    <!-- Controls -->
    <div class="controls">
      <button
        class="sort-btn"
        :class="{ active: sortField === 'username' }"
        @click="sortBy('username')"
        title="Sort by user name"
      >
        User Name ⇅
        <span v-if="sortField === 'username'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
      </button>

      <button
        class="sort-btn"
        :class="{ active: sortField === 'email' }"
        @click="sortBy('email')"
        title="Sort by email"
      >
        Email ⇅
        <span v-if="sortField === 'email'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
      </button>

      <button
        class="sort-btn"
        :class="{ active: sortField === 'created_at' }"
        @click="sortBy('created_at')"
        title="Sort by creation date"
      >
        Created At ⇅
        <span v-if="sortField === 'created_at'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
      </button>
    </div>

    <!-- Table -->
    <div v-if="!loading">
      <table class="comments-table">
        <thead>
          <tr>
            <th class="col-avatar">Avatar</th>
            <th class="col-user">User Name</th>
            <th class="col-email">Email</th>
            <th class="col-date">Date</th>
            <th class="col-text">Text</th>
            <th class="col-replies">Replies</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="comment in visibleComments"
            :key="comment.id"
            class="row"
            @click="goToDetail(comment.id)"
          >
            <td class="cell avatar-cell">
              <img
                v-if="comment.user?.avatar"
                :src="comment.user.avatar"
                alt="avatar"
                class="avatar"
                width="40"
                height="40"
              />
            </td>

            <td class="cell user-cell">
              <div class="meta-top">
                <span class="username">{{ comment.user?.username || 'Anonymous' }}</span>
              </div>
            </td>

            <td class="cell email-cell">
              <span class="email">{{ comment.user?.email || '—' }}</span>
            </td>

            <td class="cell date-cell">
              <span class="created">{{ formatDate(comment.created_at) }}</span>
            </td>

            <td class="cell text-cell">
              {{ truncateText(comment.text) }}
            </td>

            <td class="cell replies-cell">
              <span v-if="(comment.replies_count ?? 0) > 0" class="replies-pill">
                {{ comment.replies_count }}
              </span>
              <span v-else class="replies-zero">0</span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination Controls -->
      <div v-if="totalPages > 1" class="pagination">
        <button @click="goToPage(1)" :disabled="currentPage === 1">First</button>
        <button @click="prevPage" :disabled="currentPage === 1">Previous</button>

        <span>Page {{ currentPage }} of {{ totalPages }}</span>

        <button @click="nextPage" :disabled="currentPage === totalPages">Next</button>
        <button @click="goToPage(totalPages)" :disabled="currentPage === totalPages">Last</button>

        <span class="goto">
          Go to page:
          <input
            type="number"
            v-model.number="inputPage"
            :min="1"
            :max="totalPages"
            @keyup.enter="goToInputPage"
          />
          <button @click="goToInputPage">OK</button>
        </span>
      </div>
    </div>

    <div v-else class="loading">Loading...</div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { usePagination } from '../composables/usePagination.js'

export default {
  name: 'CommentList',
  setup() {
    const router = useRouter()
    const comments = ref([])
    const allComments = ref([])
    const loading = ref(true)
    const config = ref(null)

    const currentPage = ref(1)
    const totalPages = ref(1)
    const inputPage = ref(1)

    const sortField = ref(null)        // 'username' | 'email' | 'created_at' | null
    const sortDirection = ref('asc')   // 'asc' | 'desc'
    const useClientPaging = ref(false)

    let pagination = null

    const fetchConfig = async () => {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/api/v1/config/?format=json&lang=en`
        )
        config.value = response.data
      } catch (error) {
        console.error('Error fetching config:', error)
      }
    }

    const initPagination = () => {
      if (!config.value) return
      pagination = usePagination(
        `${config.value.BACKEND_URL}/api/v1/comments/`,
        config.value.PAGE_SIZE
      )
    }

    const fetchPage = async (page) => {
      if (!pagination) return
      loading.value = true
      try {
        await pagination.fetchPage(page)
        comments.value = pagination.items.value
        currentPage.value = pagination.currentPage.value
        totalPages.value = pagination.totalPages.value
        inputPage.value = pagination.inputPage.value
      } finally {
        loading.value = false
      }
    }

    const fetchAllPages = async () => {
      if (!config.value) return
      loading.value = true
      try {
        const startUrl = `${config.value.BACKEND_URL}/api/v1/comments/?format=json`
        let url = startUrl
        const acc = []
        while (url) {
          const res = await axios.get(url)
          const data = res.data
          const batch = Array.isArray(data) ? data : (data.results || [])
          acc.push(...batch)
          url = data.next || null
        }
        allComments.value = acc
      } catch (e) {
        console.error('Error fetching all pages:', e)
      } finally {
        loading.value = false
      }
    }

    const prevPage = async () => {
      if (useClientPaging.value) {
        if (currentPage.value > 1) currentPage.value -= 1
      } else {
        await fetchPage(currentPage.value - 1)
      }
    }
    const nextPage = async () => {
      if (useClientPaging.value) {
        if (currentPage.value < totalPages.value) currentPage.value += 1
      } else {
        await fetchPage(currentPage.value + 1)
      }
    }
    const goToPage = async (page) => {
      if (useClientPaging.value) {
        if (page < 1) page = 1
        if (page > totalPages.value) page = totalPages.value
        currentPage.value = page
      } else {
        await fetchPage(page)
      }
    }
    const goToInputPage = async () => goToPage(inputPage.value)

    const sortBy = async (field) => {
      if (sortField.value === field) {
        sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
      } else {
        sortField.value = field
        sortDirection.value = 'asc'
      }
      useClientPaging.value = true
      if (!allComments.value.length) {
        await fetchAllPages()
      }
      currentPage.value = 1
    }

    const baseArray = computed(() => (useClientPaging.value ? allComments.value : comments.value))

    const sortedComments = computed(() => {
      const arr = baseArray.value || []
      if (!sortField.value) return arr

      const getVal = (item) => {
        if (sortField.value === 'username')    return (item.user?.username || '').toLowerCase()
        if (sortField.value === 'email')       return (item.user?.email || '').toLowerCase()
        if (sortField.value === 'created_at')  return new Date(item.created_at).getTime()
        return ''
      }

      return [...arr].sort((a, b) => {
        const va = getVal(a)
        const vb = getVal(b)
        if (va < vb) return sortDirection.value === 'asc' ? -1 : 1
        if (va > vb) return sortDirection.value === 'asc' ? 1 : -1
        return 0
      })
    })

    const pageSize = computed(() => Number(config.value?.PAGE_SIZE || 10))

    const visibleComments = computed(() => {
      if (!useClientPaging.value) return sortedComments.value
      const start = (currentPage.value - 1) * pageSize.value
      return sortedComments.value.slice(start, start + pageSize.value)
    })

    watch([useClientPaging, sortedComments, pageSize], () => {
      if (useClientPaging.value) {
        totalPages.value = Math.max(1, Math.ceil(sortedComments.value.length / pageSize.value))
        if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
      }
    })

    const truncateText = (text) => {
      const limit = Number(import.meta.env.VITE_COMMENT_TRUNCATE_LENGTH || 100)
      if (!text) return ''
      return text.length > limit ? text.slice(0, limit) + '…' : text
    }

    const formatDate = (iso) => {
      if (!iso) return ''
      try { return new Date(iso).toLocaleString() } catch { return iso }
    }

    const goToDetail = (id) => {
      router.push({ name: 'CommentDetail', params: { id } })
    }

    onMounted(async () => {
      await fetchConfig()
      initPagination()
      await fetchPage(1)
    })

    return {
      comments,
      allComments,
      loading,
      currentPage,
      totalPages,
      inputPage,
      sortField,
      sortDirection,
      sortBy,
      useClientPaging,
      visibleComments,
      prevPage,
      nextPage,
      goToPage,
      goToInputPage,
      truncateText,
      formatDate,
      goToDetail
    }
  },
}
</script>

<style scoped>
.comment-list {
  max-width: 1000px;
  margin: 16px auto;
  padding: 6px;
}

.controls {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.sort-btn {
  padding: 6px 10px;
  border: 1px solid rgba(0,0,0,0.12);
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.sort-btn.active {
  border-color: #1a73e8;
  box-shadow: 0 0 0 2px rgba(26,115,232,0.12);
}

.comments-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0 10px;
  table-layout: fixed;
}

.comments-table thead th,

.comments-table td {
  text-align: left;
  vertical-align: middle;
}

.comments-table .row {
  background: #fff;
  border: 1px solid rgba(0,0,0,0.12);
  box-shadow:
    inset 4px 0 0 #a8c6f7,
    0 1px 2px rgba(0,0,0,0.08);
  transition: transform 0.1s, box-shadow 0.1s, background 0.2s;
  cursor: pointer;
}
.comments-table .row:hover {
  transform: translateY(-1px);
  box-shadow:
    inset 4px 0 0 #a8c6f7,
    0 2px 4px rgba(0,0,0,0.15);
  background: #f9fbff;
}

.comments-table .cell {
  padding: 10px;
  border-top: 1px solid rgba(0,0,0,0.06);
  border-bottom: 1px solid rgba(0,0,0,0.06);
  background: transparent;
  box-sizing: border-box;
}

.col-avatar { width: 60px; }
.col-user   { width: 180px; }
.col-email  { width: 240px; }
.col-date   { width: 180px; }
.col-text   { width: auto; }
.col-replies{ width: 90px; text-align: center; }

.avatar-cell { text-align: center; }

.avatar {
  border-radius: 50%;
  object-fit: cover;
  width: 40px;
  height: 40px;
  box-shadow: 0 0 0 3px rgba(255,255,255,1);
}

.meta-top {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 14px;
}
.username { font-weight: 700; }

.email-cell .email {
  color: #555;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.created { color: #666; }

.text-cell {
  color: #222;
  line-height: 1.45;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.replies-cell { text-align: center; }
.replies-pill {
  display: inline-block;
  background: #f0f4ff;
  color: #1a73e8;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
}
.replies-zero {
  color: #999;
  font-size: 12px;
}

.pagination {
  margin-top: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.pagination button {
  padding: 6px 10px;
  border: 1px solid rgba(0,0,0,0.12);
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
}
.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.goto input {
  width: 60px;
  padding: 4px 6px;
  border: 1px solid rgba(0,0,0,0.2);
  border-radius: 6px;
}

.loading {
  text-align: center;
  padding: 20px;
  font-size: 16px;
}
</style>
