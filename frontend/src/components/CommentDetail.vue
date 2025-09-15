<template>
  <div class="comment-detail">
    <button @click="goBack" class="back-btn">Back</button>

    <div v-if="loading">Loading...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <!-- Pass highlight map into the tree -->
      <CommentNode :comment="comment" :highlight-map="highlights" @reply="handleReply" />

      <CommentForm
        v-if="replyToId"
        :current-user="currentUser"
        :parent-id="replyToId"
        :reply-to-text="replyToText"
        :reply-to-author="replyToAuthor"
        @comment-posted="refreshComments"
        @cancel="cancelReply"
        ref="replyFormEl"
      />
    </div>

    <!-- Floating WS toast: click to scroll to the new reply -->
    <div v-if="toast" class="ws-toast" @click="scrollToComment(toast.id)">
      <strong>New reply</strong>
      <span v-if="toast.author"> from {{ toast.author }}</span>
      — click to view
    </div>
  </div>
</template>

<script setup>
/**
 * CommentDetail.vue
 * - Loads one comment thread with nested replies.
 * - Subscribes to WS and inserts new replies into the open thread in realtime.
 * - Shows a toast for new replies and highlights the new node for 10 seconds.
 *
 * Notes:
 * - WS URL comes from useCommentsWS() which reads VITE_WS_URL or derives from location.
 * - We normalize file/avatar URLs to absolute using VITE_BACKEND_URL if backend returns relative paths.
 */
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import Cookies from 'js-cookie';
import CommentNode from './CommentNode.vue';
import CommentForm from './CommentForm.vue';
import { useCommentsWS } from '../composables/useCommentsWS.js';

const route = useRoute();
const router = useRouter();

/* ----- state ----- */
const comment = ref(null); // root comment with nested replies
const currentUser = ref(null);

const replyToId = ref(null);
const replyToText = ref('');
const replyToAuthor = ref('');
const replyFormEl = ref(null);

const loading = ref(true);
const error = ref('');

/* highlight + toast */
const highlights = ref({}); // { [id]: true } while highlighted
const toast = ref(null); // { id, author }
let wsCtl = null;

/* ----- helpers: URLs normalization ----- */
const BACKEND_BASE = (import.meta.env.VITE_BACKEND_URL || '').replace(/\/+$/, '');
const toAbs = (url) => {
  if (!url) return url;
  if (/^https?:\/\//i.test(url)) return url; // already absolute
  if (url.startsWith('/')) return `${BACKEND_BASE}${url}`;
  return url;
};

/* ----- normalize nodes from API/WS ----- */
const normalizeUser = (u) => (u ? { ...u, avatar: toAbs(u.avatar) } : u);
const normalizeNode = (n) => {
  if (!n) return n;
  const out = {
    id: n.id,
    parent: n.parent ?? null,
    text: n.text || '',
    file: toAbs(n.file),
    created_at: n.created_at || null,
    user: normalizeUser(n.user || null),
    replies_count: n.replies_count ?? 0,
    replies: Array.isArray(n.replies) ? n.replies : [], // may be filled recursively
  };
  return out;
};
const normalizeTree = (node) => {
  const base = normalizeNode(node);
  base.replies = (node?.replies || []).map(normalizeTree);
  return base;
};

/* ----- load data ----- */
const fetchComment = async () => {
  loading.value = true;
  error.value = '';
  try {
    const res = await axios.get(
      `${import.meta.env.VITE_BACKEND_URL}/api/v1/comments/${route.params.id}/`
    );
    comment.value = normalizeTree(res.data);
  } catch (e) {
    error.value = 'Failed to load comment.';
  } finally {
    loading.value = false;
  }
};

const fetchCurrentUser = async () => {
  try {
    const res = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/api/v1/users/me/`, {
      headers: { 'X-CSRFToken': Cookies.get('csrftoken') },
      withCredentials: true,
    });
    currentUser.value = res.data;
  } catch {
    currentUser.value = null;
  }
};

/* ----- reply UX ----- */
const handleReply = async ({ id, text, authorName }) => {
  replyToId.value = id;
  replyToText.value = text;
  replyToAuthor.value = authorName || '';
  await nextTick();
  replyFormEl.value?.$el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
};

const cancelReply = () => {
  replyToId.value = null;
  replyToText.value = '';
  replyToAuthor.value = '';
};

const refreshComments = async () => {
  await fetchComment();
  cancelReply();
};

const goBack = () => router.push({ name: 'CommentList' });

/* ----- tree utils ----- */
function findNodeById(node, id) {
  if (!node) return null;
  if (node.id === id) return node;
  for (const r of node.replies || []) {
    const found = findNodeById(r, id);
    if (found) return found;
  }
  return null;
}

function insertReplyUnder(parentNode, newReply) {
  if (!parentNode) return;
  if (!Array.isArray(parentNode.replies)) parentNode.replies = [];
  // Avoid duplicates
  if (parentNode.replies.some((r) => r.id === newReply.id)) return;

  // LIFO: put new reply first
  parentNode.replies.unshift(newReply);
  parentNode.replies_count = (parentNode.replies_count ?? 0) + 1;
}

/* ----- highlight + toast ----- */
function flashHighlight(id, ms = 10000) {
  if (!id) return;
  highlights.value[id] = true;
  setTimeout(() => {
    delete highlights.value[id];
  }, ms);
}

function scrollToComment(id) {
  const el = document.getElementById(`comment-${id}`);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/* ----- WS handling ----- */
function handleWsEvent(evt) {
  // We expect flat events like: { action: "comment.created", id, parent, text, file, created_at, user, ... }
  if (!evt || evt.action !== 'comment.created') return;
  if (!comment.value) return;
  if (!evt.parent) return; // only replies are relevant here

  const parent = findNodeById(comment.value, evt.parent);
  if (!parent) return; // not in this open thread

  const newReply = normalizeNode(evt);
  insertReplyUnder(parent, newReply);

  toast.value = { id: newReply.id, author: newReply?.user?.username || 'user' };
  setTimeout(() => (toast.value = null), 4500);
  flashHighlight(newReply.id, 10000);
}

/* ----- lifecycle ----- */
onMounted(async () => {
  await fetchComment();
  await fetchCurrentUser();

  wsCtl = useCommentsWS({ onEvent: handleWsEvent });
  wsCtl.connect();
});

onBeforeUnmount(() => {
  if (wsCtl) wsCtl.disconnect();
});
</script>

<style scoped>
.comment-detail {
  max-width: 800px;
  margin: 0 auto;
}
.back-btn {
  margin-bottom: 1rem;
  padding: 0.5rem 1rem;
  border: none;
  background: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}
.back-btn:hover {
  background: #0056b3;
}

/* WS toast */
.ws-toast {
  position: fixed;
  right: 16px;
  bottom: 16px;
  background: #1a73e8;
  color: #fff;
  padding: 10px 14px;
  border-radius: 10px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.18);
  cursor: pointer;
  z-index: 3000;
  font-size: 14px;
}
.ws-toast:hover {
  filter: brightness(0.95);
}
</style>
