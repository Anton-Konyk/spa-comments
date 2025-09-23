import { ref } from 'vue';
import client from '@/utils/client.js';

export function usePagination(baseUrl, pageSize) {
  const items = ref([]);
  const loading = ref(false);
  const currentPage = ref(1);
  const totalPages = ref(1);
  const inputPage = ref(1);

  async function fetchPage(page = 1, extraParams = {}) {
    loading.value = true;
    try {
      const { data } = await client.get(baseUrl, {
        params: { format: 'json', page, ...extraParams },
      });

      const results = Array.isArray(data) ? data : data.results || [];
      items.value = results;

      const count = data?.count ?? results.length;
      const size = Number(pageSize) || results.length || 1;
      totalPages.value = Math.max(1, Math.ceil(count / size));

      currentPage.value = page;
      inputPage.value = page;
    } catch (error) {
      console.error('Error fetching page:', error);
    } finally {
      loading.value = false;
    }
  }

  async function prevPage() {
    if (currentPage.value > 1) await fetchPage(currentPage.value - 1);
  }

  async function nextPage() {
    if (currentPage.value < totalPages.value) await fetchPage(currentPage.value + 1);
  }

  async function goToPage(page) {
    if (page >= 1 && page <= totalPages.value) await fetchPage(page);
  }

  async function goToInputPage() {
    await goToPage(Number(inputPage.value || 1));
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
    goToInputPage,
  };
}
