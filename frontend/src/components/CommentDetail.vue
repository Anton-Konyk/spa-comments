<template>
  <div class="comment-detail">
    <button @click="goBack" class="back-btn">Back</button>

    <div v-if="loading">Loading...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <CommentNode
        :comment="comment"
        @reply="handleReply"
      />

      <CommentForm
        v-if="replyToId"
        :current-user="currentUser"
        :parent-id="replyToId"
        @comment-posted="refreshComments"
        @cancel="cancelReply"
        ref="replyFormEl"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import axios from "axios";
import Cookies from "js-cookie";
import CommentNode from "./CommentNode.vue";
import CommentForm from "./CommentForm.vue";

const route = useRoute();
const router = useRouter();

const comment = ref(null);
const currentUser = ref(null);
const replyToId = ref(null);
const loading = ref(true);
const error = ref("");
const replyFormEl = ref(null);

const fetchComment = async () => {
  loading.value = true;
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_BACKEND_URL}/api/v1/comments/${route.params.id}/`
    );
    comment.value = response.data;
  } catch {
    error.value = "Failed to load comment.";
  } finally {
    loading.value = false;
  }
};

const fetchCurrentUser = async () => {
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_BACKEND_URL}/api/v1/users/me/`,
      {
        headers: {
          "X-CSRFToken": Cookies.get("csrftoken"),
        },
        withCredentials: true,
      }
    );
    currentUser.value = response.data;
  } catch {
    currentUser.value = null;
  }
};

const handleReply = async (commentId) => {
  replyToId.value = commentId;
  await nextTick();
  replyFormEl.value?.$el.scrollIntoView({ behavior: "smooth", block: "center" });
};

const cancelReply = async () => {
  replyToId.value = null;
};

const refreshComments = async () => {
  await fetchComment();
  replyToId.value = null;
};

const goBack = () => {
  router.push({ name: "CommentList" });
};

onMounted(() => {
  fetchComment();
  fetchCurrentUser();
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
</style>
