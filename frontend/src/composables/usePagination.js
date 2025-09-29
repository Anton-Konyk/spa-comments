import { ref } from 'vue';
import client from '@/utils/client.js';

export function useServerPagination({
  endpoint, // e.g. '/api/v1/comments/'
  pageSizeRef, // ref to page size (so caller controls it)
  initialOrdering = '-created_at',
  normalizer = (x) => x, // normalize each item if needed
  toServerField = (f) => f, // map UI field -> server field
}) {
  const items = ref([]);
  const loading = ref(false);
  const currentPage = ref(1);
  const totalPages = ref(1);
  const ordering = ref(initialOrdering);

  async function fetchPage(page = 1) {
    loading.value = true;
    try {
      // const params = { page, ordering: ordering.value };
      const params = { page, ordering: ordering.value, format: 'json' };
      const { data } = await client.get(endpoint, { params });

      const list = Array.isArray(data) ? data : data.results || [];
      items.value = list.map(normalizer);

      const count = typeof data?.count === 'number' ? data.count : list.length;
      const size = Number(pageSizeRef?.value || 25);
      totalPages.value = Math.max(1, Math.ceil(count / size));

      const clamped = Math.min(Math.max(1, page), totalPages.value);
      currentPage.value = clamped;
      return items.value;
    } catch (e) {
      console.error('fetchPage failed:', e);
      items.value = [];
      totalPages.value = 1;
      currentPage.value = 1;
    } finally {
      loading.value = false;
    }
  }

  async function setOrderingString(orderStr) {
    ordering.value = orderStr;
    await fetchPage(currentPage.value);
    if (currentPage.value > totalPages.value) {
      await fetchPage(totalPages.value);
    }
  }

  // Convenience: set ordering by UI field + direction
  async function sortBy(field, dir = 'asc') {
    const serverField = toServerField(field);
    const orderStr = (dir === 'desc' ? '-' : '') + serverField;
    await setOrderingString(orderStr);
  }

  async function goToPage(page) {
    await fetchPage(page);
  }

  async function next() {
    if (currentPage.value < totalPages.value) {
      await fetchPage(currentPage.value + 1);
    }
  }

  async function prev() {
    if (currentPage.value > 1) {
      await fetchPage(currentPage.value - 1);
    }
  }

  return {
    // state
    items,
    loading,
    currentPage,
    totalPages,
    ordering,
    // actions
    fetchPage,
    setOrderingString,
    sortBy,
    goToPage,
    next,
    prev,
  };
}
