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
import client from '@/utils/client.js';
import { refreshCsrf } from '@/utils/client.js';
import VueEasyLightbox from 'vue-easy-lightbox';
import CommentForm from './CommentForm.vue';
import { useCommentsWS } from '../composables/useCommentsWS.js';
// NEW: import our server-side pagination composable
import { useServerPagination } from '../composables/usePagination.js';

export default {
  name: 'CommentList',
  components: { VueEasyLightbox, CommentForm },

  setup() {
    const router = useRouter();

    // auth
    const currentUser = ref(null);

    // config
    const config = ref(null);
    const pageSize = computed(() => Number(config.value?.PAGE_SIZE || 25)); // 25 per requirements

    // UI sort state (for buttons)
    const sortField = ref('created_at');
    const sortDirection = ref('desc');

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

    const isImage = (url) => /\.(jpe?g|png|gif|webp)$/i.test(String(url || ''));

    // Map UI field -> server ordering field
    const toServerField = (field) => {
      if (field === 'username') return 'user__username';
      if (field === 'email') return 'user__email';
      return 'created_at';
    };

    // INIT server pagination composable
    const {
      items: comments,
      loading,
      currentPage,
      totalPages,
      ordering,
      fetchPage,
      setOrderingString,
      sortBy: serverSortBy,
      goToPage,
      next: nextPage,
      prev: prevPage,
    } = useServerPagination({
      endpoint: '/api/v1/comments/',
      pageSizeRef: pageSize,
      initialOrdering: '-created_at',
      normalizer: normalizeComment,
      toServerField,
    });

    const inputPage = ref(1);
    watch(currentPage, (v) => {
      inputPage.value = v;
    });

    const visibleComments = computed(() => comments.value);

    const showLightbox = ref(false);
    const lightboxIndex = ref(0);
    const lightboxImgs = ref([]);

    const showTxtModal = ref(false);
    const txtContent = ref('');

    const showCommentModal = ref(false);
    const commentPreviewHtml = ref('');

    const showRootForm = ref(false);

    const openLightbox = (url) => {
      lightboxImgs.value = [url];
      lightboxIndex.value = 0;
      showLightbox.value = true;
    };

    // auth helpers
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
        await refreshCsrf();
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

    // config fetch
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

    // Sorting click handler (UI -> server)
    const sortBy = async (field) => {
      if (sortField.value === field) {
        sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
      } else {
        sortField.value = field;
        sortDirection.value = 'asc';
      }
      await serverSortBy(sortField.value, sortDirection.value);
    };

    // Go to page via input
    const goToInputPage = async () => {
      await goToPage(inputPage.value);
    };

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

    const onRootCreated = async (created) => {
      showRootForm.value = false;
      if (created?.id) {
        await router.push({ name: 'CommentDetail', params: { id: created.id } });
        return;
      }
      await fetchPage(currentPage.value);
    };

    // WS — prepend on page 1 only
    function applyIncomingComment(evt) {
      if (!evt || evt.action !== 'comment.created') return;
      const item = normalizeComment(evt);

      if (item.parent) {
        const pPage = comments.value.find((c) => c.id === item.parent);
        if (pPage) pPage.replies_count = (pPage.replies_count ?? 0) + 1;
      }

      if (currentPage.value === 1 && !comments.value.some((c) => c.id === item.id)) {
        comments.value.unshift(item);
        const maxRows = pageSize.value;
        if (comments.value.length > maxRows) comments.value.pop();
      }
    }

    let wsCtl = null;
    function handleWsEvent(data) {
      applyIncomingComment(data);
    }

    onMounted(async () => {
      await fetchConfig();
      await fetchPage(1); // initial load with '-created_at'
      await fetchCurrentUser();

      wsCtl = useCommentsWS({ onEvent: handleWsEvent });
      wsCtl.connect();
    });

    onBeforeUnmount(() => {
      if (wsCtl) wsCtl.disconnect();
    });

    return {
      // state
      visibleComments,
      comments,
      loading,
      currentPage,
      totalPages,
      inputPage,

      // sorting
      sortField,
      sortDirection,
      sortBy,

      // paging
      prevPage,
      nextPage,
      goToPage,
      goToInputPage,

      // utils
      truncateText,
      formatDate,
      goToDetail,

      // lightbox/modals
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

      // form
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
