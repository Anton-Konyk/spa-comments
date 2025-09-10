<template>
  <div>
    <h2>Comments</h2>

    <table border="1" cellpadding="5">
      <thead>
        <tr>
          <th>Avatar</th>
          <th @click="sortBy('username')" style="cursor: pointer">
            User Name ⇅
            <span v-if="sortField === 'username'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th @click="sortBy('email')" style="cursor: pointer">
            E-mail ⇅
            <span v-if="sortField === 'email'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th>Comment</th>
          <th @click="sortBy('created_at')" style="cursor: pointer">
            Created At ⇅
            <span v-if="sortField === 'created_at'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th>Replies</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="comment in sortedComments"
          :key="comment.id"
          @click="goToDetail(comment.id)"
          style="cursor:pointer;"
        >
          <td>
            <img
              :src="comment.user.avatar || 'https://via.placeholder.com/40'"
              alt="avatar"
              width="40"
              height="40"
            />
          </td>
          <td>{{ comment.user.username || 'Anonymous' }}</td>
          <td>{{ comment.user.email || '—' }}</td>
          <td>{{ truncateText(comment.text) }}</td>
          <td>{{ comment.created_at }}</td>
          <td>{{ comment.replies_count ?? 0 }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Pagination Controls -->
    <div v-if="totalPages > 1" style="margin-top: 10px;">
      <button @click="goToPage(1)" :disabled="currentPage === 1">First</button>
      <button @click="prevPage" :disabled="currentPage === 1">Previous</button>

      <span>Page {{ currentPage }} from {{ totalPages }}</span>

      <button @click="nextPage" :disabled="currentPage === totalPages">Next</button>
      <button @click="goToPage(totalPages)" :disabled="currentPage === totalPages">Last</button>

      <span style="margin-left: 10px;">
        Go to page:
        <input
          type="number"
          v-model.number="inputPage"
          :min="1"
          :max="totalPages"
          @keyup.enter="goToInputPage"
          style="width: 50px;"
        />
        <button @click="goToInputPage">OK</button>
      </span>
    </div>

    <div v-if="loading">Loading...</div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { usePagination } from '../composables/usePagination.js'

export default {
  name: 'CommentList',
  setup() {
    const router = useRouter()
    const comments = ref([])
    const loading = ref(true)
    const config = ref(null)
    const currentPage = ref(1)
    const totalPages = ref(1)
    const inputPage = ref(1)

    const sortField = ref(null)
    const sortDirection = ref('asc')

    let pagination

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
      await pagination.fetchPage(page)
      comments.value = pagination.items.value
      currentPage.value = pagination.currentPage.value
      totalPages.value = pagination.totalPages.value
      inputPage.value = pagination.inputPage.value
      loading.value = false
    }

    const prevPage = async () => fetchPage(currentPage.value - 1)
    const nextPage = async () => fetchPage(currentPage.value + 1)
    const goToPage = async (page) => fetchPage(page)
    const goToInputPage = async () => fetchPage(inputPage.value)

    const sortBy = (field) => {
      if (sortField.value === field) {
        sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
      } else {
        sortField.value = field
        sortDirection.value = 'asc'
      }
    }

    const sortedComments = computed(() => {
      if (!sortField.value) return comments.value
      return [...comments.value].sort((a, b) => {
        let valA = null
        let valB = null

        if (sortField.value === 'username') {
          valA = a.user.username || ''
          valB = b.user.username || ''
        } else if (sortField.value === 'email') {
          valA = a.user.email || ''
          valB = b.user.email || ''
        } else if (sortField.value === 'created_at') {
          valA = new Date(a.created_at).getTime()
          valB = new Date(b.created_at).getTime()
        }

        if (valA < valB) return sortDirection.value === 'asc' ? -1 : 1
        if (valA > valB) return sortDirection.value === 'asc' ? 1 : -1
        return 0
      })
    })

    const truncateText = (text) => {
      const limit = Number(import.meta.env.VITE_COMMENT_TRUNCATE_LENGTH || 100)
      if (!text) return ''
      return text.length > limit ? text.slice(0, limit) + '…' : text
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
      sortedComments,
      loading,
      currentPage,
      totalPages,
      inputPage,
      sortField,
      sortDirection,
      sortBy,
      prevPage,
      nextPage,
      goToPage,
      goToInputPage,
      truncateText,
      goToDetail,
    }
  },
}
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
}
th {
  background-color: #f0f0f0;
  user-select: none;
}
td,
th {
  padding: 5px 10px;
  text-align: left;
}
td img {
  border-radius: 50%;
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
