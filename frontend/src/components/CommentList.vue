<template>
  <div class="comment-list">
    <!-- Auth bar (added) -->
    <div class="auth-bar">
      <template v-if="currentUser">
        <img v-if="currentUser.avatar" :src="currentUser.avatar" alt="avatar" class="auth-avatar" />
        <span class="auth-username">Hello, {{ currentUser.username }}</span>
        <button @click="logout" class="auth-btn">Logout</button>
      </template>
      <template v-else>
        <button @click="openLogin" class="auth-btn">Sign in</button>
        <button @click="openRegister" class="auth-btn">Register</button>
      </template>
    </div>

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

      <!-- Button to add root comment -->
      <div v-if="currentUser" class="add-root">
        <button class="add-btn" @click="showRootForm = !showRootForm">
          {{ showRootForm ? 'Cancel' : 'Add Comment' }}
        </button>
      </div>
    </div>

    <!-- Root Comment Form -->
    <div v-if="showRootForm" class="root-form">
      <CommentForm
        :current-user="currentUser"
        :parent-id="null"
        @comment-posted="onRootCreated"
        @cancel="showRootForm = false"
      />
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
            <th class="col-file">File</th>
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

            <td
              class="cell text-cell"
              @click.stop="openTextPreview(comment)"
              title="Click to preview full text"
            >
              {{ truncateText(comment.text) }}
            </td>

            <td class="cell file-cell">
              <template v-if="comment.file">
                <!-- If the file is an image -->
                <img
                  v-if="isImage(comment.file)"
                  :src="comment.file"
                  alt="Attachment"
                  class="file-thumb"
                  @click.stop="openLightbox(comment.file)"
                />
                <!-- If the file is a text file -->
                <span
                  v-else-if="comment.file.toLowerCase().endsWith('.txt')"
                  class="file-txt"
                  @click.stop="openTxtPreview(comment.file)"
                >
                  TXT File
                </span>
                <!-- Any other file types -->
                <a v-else :href="comment.file" target="_blank" rel="noopener noreferrer">
                  Download
                </a>
              </template>
              <template v-else> – </template>
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

  <VueEasyLightbox
    :visible="showLightbox"
    :imgs="lightboxImgs"
    :index="lightboxIndex"
    @hide="showLightbox = false"
  />

  <!-- Modal for TXT preview -->
  <div v-if="showTxtModal" class="txt-modal">
    <div class="txt-content">
      <button class="txt-close" @click="showTxtModal = false">×</button>
      <pre>{{ txtContent }}</pre>
    </div>
  </div>

  <!-- Modal for comment text preview -->
  <div v-if="showCommentModal" class="txt-modal">
    <div class="txt-content">
      <button class="txt-close" @click="showCommentModal = false">×</button>
      <div v-html="commentPreviewHtml"></div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import client from '@/utils/client';
import { usePagination } from '../composables/usePagination.js';
import VueEasyLightbox from 'vue-easy-lightbox';
import CommentForm from './CommentForm.vue';
import { useCommentsWS } from '../composables/useCommentsWS.js';

export default {
  name: 'CommentList',
  components: { VueEasyLightbox, CommentForm },

  setup() {
    const router = useRouter();
    const comments = ref([]);
    const allComments = ref([]);
    const loading = ref(true);
    const config = ref(null);

    // auth state (added)
    const currentUser = ref(null);

    const currentPage = ref(1);
    const totalPages = ref(1);
    const inputPage = ref(1);

    const sortField = ref(null); // 'username' | 'email' | 'created_at' | null
    const sortDirection = ref('asc'); // 'asc' | 'desc'
    const useClientPaging = ref(false);

    const showLightbox = ref(false);
    const lightboxIndex = ref(0);
    const lightboxImgs = ref([]);

    const showTxtModal = ref(false);
    const txtContent = ref('');

    const showCommentModal = ref(false);
    const commentPreviewHtml = ref('');

    const showRootForm = ref(false);

    const isImage = (url) => /\.(jpe?g|png|gif|webp)$/i.test(String(url || ''));

    let pagination = null;

    const openLightbox = (url) => {
      lightboxImgs.value = [url];
      lightboxIndex.value = 0;
      showLightbox.value = true;
    };

    // ---- AUTH (added) ----
    const fetchCurrentUser = async () => {
      try {
        const res = await client.get('/api/v1/users/me/');
        const u = res.data || null;
        if (u && u.avatar) u.avatar = toAbs(u.avatar);
        currentUser.value = u;
      } catch {
        currentUser.value = null;
      }
    };

    const logout = async () => {
      try {
        await client.post('/api/v1/users/logout/', {});
        currentUser.value = null;
      } catch (err) {
        console.error('Logout error', err);
      }
    };

    const openLogin = () => {
      router.push({ name: 'Login', query: { next: router.currentRoute.value.fullPath } });
    };
    const openRegister = () => {
      router.push({ name: 'Register', query: { next: router.currentRoute.value.fullPath } });
    };

    // ---- COMMENTS (your code) ----
    const fetchConfig = async () => {
      try {
        const response = await client.get('/api/v1/config/', {
          params: { format: 'json', lang: 'en' },
        });
        config.value = response.data;
      } catch (error) {
        console.error('Error fetching config:', error);
      }
    };

    const initPagination = () => {
      if (!config.value) return;
      pagination = usePagination(`/api/v1/comments/`, config.value.PAGE_SIZE);
    };

    const fetchPage = async (page) => {
      if (!pagination) return;
      loading.value = true;
      try {
        await pagination.fetchPage(page);
        comments.value = pagination.items.value.map(normalizeComment);
        currentPage.value = pagination.currentPage.value;
        totalPages.value = pagination.totalPages.value;
        inputPage.value = pagination.inputPage.value;
      } finally {
        loading.value = false;
      }
    };

    const fetchAllPages = async () => {
      if (!config.value) return;
      loading.value = true;
      try {
        const startUrl = `/api/v1/comments/?format=json`;
        let url = startUrl;
        const acc = [];
        while (url) {
          const res = await client.get(url);
          const data = res.data;
          const batch = Array.isArray(data) ? data : data.results || [];
          acc.push(...batch);
          url = data.next || null;
        }
        allComments.value = acc.map(normalizeComment);
      } catch (e) {
        console.error('Error fetching all pages:', e);
      } finally {
        loading.value = false;
      }
    };

    const prevPage = async () => {
      if (useClientPaging.value) {
        if (currentPage.value > 1) currentPage.value -= 1;
      } else {
        await fetchPage(currentPage.value - 1);
      }
    };
    const nextPage = async () => {
      if (useClientPaging.value) {
        if (currentPage.value < totalPages.value) currentPage.value += 1;
      } else {
        await fetchPage(currentPage.value + 1);
      }
    };
    const goToPage = async (page) => {
      if (useClientPaging.value) {
        if (page < 1) page = 1;
        if (page > totalPages.value) page = totalPages.value;
        currentPage.value = page;
      } else {
        await fetchPage(page);
      }
    };
    const goToInputPage = async () => goToPage(inputPage.value);

    const sortBy = async (field) => {
      if (sortField.value === field) {
        sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
      } else {
        sortField.value = field;
        sortDirection.value = 'asc';
      }
      useClientPaging.value = true;
      if (!allComments.value.length) {
        await fetchAllPages();
      }
      currentPage.value = 1;
    };

    const baseArray = computed(() => (useClientPaging.value ? allComments.value : comments.value));

    const sortedComments = computed(() => {
      const arr = baseArray.value || [];
      if (!sortField.value) return arr;

      const getVal = (item) => {
        if (sortField.value === 'username') return (item.user?.username || '').toLowerCase();
        if (sortField.value === 'email') return (item.user?.email || '').toLowerCase();
        if (sortField.value === 'created_at') return new Date(item.created_at).getTime();
        return '';
      };

      return [...arr].sort((a, b) => {
        const va = getVal(a);
        const vb = getVal(b);
        if (va < vb) return sortDirection.value === 'asc' ? -1 : 1;
        if (va > vb) return sortDirection.value === 'asc' ? 1 : -1;
        return 0;
      });
    });

    const pageSize = computed(() => Number(config.value?.PAGE_SIZE || 10));

    const visibleComments = computed(() => {
      if (!useClientPaging.value) return sortedComments.value;
      const start = (currentPage.value - 1) * pageSize.value;
      return sortedComments.value.slice(start, start + pageSize.value);
    });

    watch([useClientPaging, sortedComments, pageSize], () => {
      if (useClientPaging.value) {
        totalPages.value = Math.max(1, Math.ceil(sortedComments.value.length / pageSize.value));
        if (currentPage.value > totalPages.value) currentPage.value = totalPages.value;
      }
    });

    const truncateText = (text) => {
      const limit = Number(import.meta.env.VITE_COMMENT_TRUNCATE_LENGTH || 100);
      if (!text) return '';
      return text.length > limit ? text.slice(0, limit) + '…' : text;
    };

    const formatDate = (iso) => {
      if (!iso) return '';
      try {
        return new Date(iso).toLocaleString();
      } catch {
        return iso;
      }
    };

    const goToDetail = (id) => {
      router.push({ name: 'CommentDetail', params: { id } });
    };

    const openTxtPreview = async (url) => {
      try {
        const res = await fetch(url);
        txtContent.value = await res.text();
        showTxtModal.value = true;
      } catch (e) {
        txtContent.value = 'Error loading file.';
        showTxtModal.value = true;
      }
    };

    const openTextPreview = (c) => {
      commentPreviewHtml.value = c?.text || '';
      showCommentModal.value = true;
    };

    const onRootCreated = async () => {
      showRootForm.value = false;
      if (useClientPaging.value) {
        await fetchAllPages();
      } else {
        await fetchPage(currentPage.value);
      }
    };

    const toAbs = (u) => {
      if (!u) return u;
      const s = String(u);
      if (/^https?:\/\//i.test(s)) return s;
      if (s.startsWith('/')) {
        try {
          return new URL(s, client.defaults.baseURL).toString();
        } catch {
          return s;
        }
      }
      return s;
    };

    const normalizeComment = (c) => {
      if (!c) return c;
      const user = c.user ? { ...c.user, avatar: toAbs(c.user.avatar) } : null;
      return { ...c, file: toAbs(c.file), user };
    };

    function applyIncomingComment(evt) {
      if (!evt || evt.action !== 'comment.created') return;

      // normalize incoming item (absolute URLs, etc.)
      const item = normalizeComment(evt);

      // 1) bump replies_count on parent if present
      if (item.parent) {
        const pAll = allComments.value.find((c) => c.id === item.parent);
        if (pAll) pAll.replies_count = (pAll.replies_count ?? 0) + 1;

        const pPage = comments.value.find((c) => c.id === item.parent);
        if (pPage) pPage.replies_count = (pPage.replies_count ?? 0) + 1;
      }

      // 2) insert LIFO
      if (useClientPaging.value) {
        if (!allComments.value.some((c) => c.id === item.id)) {
          allComments.value.unshift(item);
        }
      } else {
        if (currentPage.value === 1 && !comments.value.some((c) => c.id === item.id)) {
          comments.value.unshift(item);
          if (comments.value.length > pageSize.value) comments.value.pop();
        }
      }
    }

    let wsCtl = null;
    function handleWsEvent(data) {
      applyIncomingComment(data);
    }

    onMounted(async () => {
      await fetchConfig();
      initPagination();
      await fetchPage(1);
      await fetchCurrentUser();

      // Connect WS
      wsCtl = useCommentsWS({ onEvent: handleWsEvent });
      wsCtl.connect();
    });

    onBeforeUnmount(() => {
      if (wsCtl) wsCtl.disconnect();
    });

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
      goToDetail,

      showLightbox,
      lightboxImgs,
      lightboxIndex,
      openLightbox,

      showTxtModal,
      txtContent,
      openTxtPreview,

      openTextPreview,
      showCommentModal,
      commentPreviewHtml,

      showRootForm,
      onRootCreated,

      // auth
      currentUser,
      logout,
      openLogin,
      openRegister,
      isImage,
    };
  },
};
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
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.sort-btn.active {
  border-color: #1a73e8;
  box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.12);
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
  border: 1px solid rgba(0, 0, 0, 0.12);
  box-shadow:
    inset 4px 0 0 #a8c6f7,
    0 1px 2px rgba(0, 0, 0, 0.08);
  transition:
    transform 0.1s,
    box-shadow 0.1s,
    background 0.2s;
  cursor: pointer;
}
.comments-table .row:hover {
  transform: translateY(-1px);
  box-shadow:
    inset 4px 0 0 #a8c6f7,
    0 2px 4px rgba(0, 0, 0, 0.15);
  background: #f9fbff;
}

.comments-table .cell {
  padding: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  background: transparent;
  box-sizing: border-box;
}

.col-avatar {
  width: 60px;
}
.col-user {
  width: 180px;
}
.col-email {
  width: 240px;
}
.col-date {
  width: 180px;
}
.col-text {
  width: auto;
}
.col-file {
  width: 100px;
}
.col-replies {
  width: 90px;
  text-align: center;
}

.avatar-cell {
  text-align: center;
}

.avatar {
  border-radius: 50%;
  object-fit: cover;
  width: 40px;
  height: 40px;
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 1);
}

.meta-top {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 14px;
}
.username {
  font-weight: 700;
}

.email-cell .email {
  color: #555;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.created {
  color: #666;
}

.file-cell {
  text-align: center;
}

.file-thumb {
  max-width: 80px;
  max-height: 60px;
  object-fit: cover;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.file-txt {
  display: inline-block;
  font-size: 12px;
  color: #1a73e8;
  font-weight: 600;
}

.file-none {
  color: #aaa;
  font-size: 12px;
}

.text-cell {
  color: #222;
  line-height: 1.45;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.replies-cell {
  text-align: center;
}
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
  border: 1px solid rgba(0, 0, 0, 0.12);
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
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 6px;
}

.loading {
  text-align: center;
  padding: 20px;
  font-size: 16px;
}

/* auth bar (added) */
.auth-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.auth-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}
.auth-btn {
  padding: 6px 12px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.auth-btn:hover {
  background: #1669c1;
}
.auth-username {
  font-weight: 600;
}

.thumb img {
  width: 100px;
  height: auto;
  margin: 5px;
  cursor: pointer;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s;
}
.thumb img:hover {
  transform: scale(1.05);
}

/* Modal for TXT preview */
.txt-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}
.txt-content {
  background: #fff;
  max-width: 80%;
  max-height: 80%;
  overflow: auto;
  padding: 16px;
  border-radius: 8px;
  position: relative;
  white-space: pre-wrap;
}
.txt-close {
  position: absolute;
  top: 8px;
  right: 12px;
  font-size: 20px;
  border: none;
  background: transparent;
  cursor: pointer;
}

/* Add root comment */
.add-root {
  margin: 12px 0;
}
.add-btn {
  padding: 8px 14px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.add-btn:hover {
  background: #1669c1;
}
.root-form {
  margin: 16px 0;
  padding: 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  background: #fafafa;
}
</style>
