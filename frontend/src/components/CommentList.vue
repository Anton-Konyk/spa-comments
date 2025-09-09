<template>
  <div>
    <h2>Comments</h2>

    <table border="1" cellpadding="5">
      <thead>
        <tr>
          <th>Avatar</th>
          <th>User Name</th>
          <th>Comment</th>
          <th>Created At</th>
          <th>Replies</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="comment in comments" :key="comment.id">
          <td>
            <img
              :src="comment.user.avatar || 'https://via.placeholder.com/40'"
              alt="avatar"
              width="40"
              height="40"
            />
          </td>
          <td>{{ comment.user.username || 'Anonymous' }}</td>
          <td>{{ comment.text || '' }}</td>
          <td>{{ comment.created_at }}</td>
          <td>{{ comment.replies_count ?? 0 }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Pagination Controls -->
    <div v-if="totalPages > 1" style="margin-top: 10px;">
      <button @click="goToPage(1)" :disabled="currentPage === 1">Первая</button>
      <button @click="prevPage" :disabled="currentPage === 1">Предыдущая</button>

      <span>Страница {{ currentPage }} из {{ totalPages }}</span>

      <button @click="nextPage" :disabled="currentPage === totalPages">Следующая</button>
      <button @click="goToPage(totalPages)" :disabled="currentPage === totalPages">Последняя</button>

      <span style="margin-left: 10px;">
        Перейти на страницу:
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

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import axios from 'axios'
import { usePagination } from '../composables/usePagination'

interface User {
  id: number
  username: string
  avatar: string | null
}

interface Comment {
  id: number
  text: string
  created_at: string
  replies_count: number
  user: User
}

interface AppConfig {
  BACKEND_URL: string
  PAGE_SIZE: number
}

export default defineComponent({
  name: 'CommentList',
  setup() {
    const comments = ref<Comment[]>([])
    const loading = ref(true)
    const config = ref<AppConfig | null>(null)
    const currentPage = ref(1)
    const totalPages = ref(1)
    const inputPage = ref(1)

    // обычная переменная для pagination, TS не будет ругаться
    let pagination: ReturnType<typeof usePagination<Comment>>

    const fetchConfig = async () => {
      try {
        const response = await axios.get<AppConfig>(
          'http://localhost:8000/api/v1/config/?format=json&lang=en'
        )
        config.value = response.data
      } catch (error) {
        console.error('Error fetching config:', error)
      }
    }

    const initPagination = () => {
      if (!config.value) return
      // инициализация пагинации с BACKEND_URL и PAGE_SIZE из конфига
      pagination = usePagination<Comment>(
        `${config.value.BACKEND_URL}/api/v1/comments/`,
        config.value.PAGE_SIZE
      )
    }

    const fetchPage = async (page: number) => {
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
    const goToPage = async (page: number) => fetchPage(page)
    const goToInputPage = async () => fetchPage(inputPage.value)

    onMounted(async () => {
      await fetchConfig()
      initPagination()
      await fetchPage(1)
    })

    return {
      comments,
      loading,
      currentPage,
      totalPages,
      inputPage,
      prevPage,
      nextPage,
      goToPage,
      goToInputPage,
    }
  },
})
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
}
th {
  background-color: #f0f0f0;
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
