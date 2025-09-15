import { ref } from 'vue';
import axios from 'axios';

export function usePagination(apiUrl, pageSize) {
  const items = ref([]);
  const loading = ref(true);
  const currentPage = ref(1);
  const totalPages = ref(1);
  const inputPage = ref(1);

  const fetchPage = async (page = 1) => {
    loading.value = true;
    try {
      const response = await axios.get(`${apiUrl}?format=json&page=${page}`);
      items.value = response.data.results;
      currentPage.value = page;
      totalPages.value = Math.ceil(response.data.count / pageSize);
      inputPage.value = currentPage.value;
    } catch (error) {
      console.error('Error fetching page:', error);
    } finally {
      loading.value = false;
    }
  };

  const prevPage = async () => {
    if (currentPage.value > 1) await fetchPage(currentPage.value - 1);
  };

  const nextPage = async () => {
    if (currentPage.value < totalPages.value) await fetchPage(currentPage.value + 1);
  };

  const goToPage = async (page) => {
    if (page >= 1 && page <= totalPages.value) await fetchPage(page);
  };

  const goToInputPage = async () => {
    await goToPage(inputPage.value);
  };

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
    goToInputPage,
  };
}
