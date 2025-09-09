import { ref } from 'vue'
import axios from 'axios'

export interface PaginationResponse<T> {
  results: T[]
  count: number
  next: string | null
  previous: string | null
}

export function usePagination<T>(apiUrl: string, pageSize: number) {
  const items = ref<T[]>([])
  const loading = ref<boolean>(true)
  const currentPage = ref<number>(1)
  const totalPages = ref<number>(1)
  const inputPage = ref<number>(1)

  const fetchPage = async (page: number = 1) => {
    loading.value = true
    try {
      const response = await axios.get<PaginationResponse<T>>(
        `${apiUrl}?format=json&page=${page}`
      )
      items.value = response.data.results
      currentPage.value = page
      totalPages.value = Math.ceil(response.data.count / pageSize)
      inputPage.value = currentPage.value
    } catch (error) {
      console.error('Error fetching page:', error)
    } finally {
      loading.value = false
    }
  }

  const prevPage = async () => {
    if (currentPage.value > 1) await fetchPage(currentPage.value - 1)
  }

  const nextPage = async () => {
    if (currentPage.value < totalPages.value) await fetchPage(currentPage.value + 1)
  }

  const goToPage = async (page: number) => {
    if (page >= 1 && page <= totalPages.value) await fetchPage(page)
  }

  const goToInputPage = async () => {
    await goToPage(inputPage.value)
  }

  return {
    items,
    loading,
    currentPage,
    totalPages,
    inputPage,
    fetchPage,
    prevPage,
    nextPage,
    goToPage,
    goToInputPage
  }
}
