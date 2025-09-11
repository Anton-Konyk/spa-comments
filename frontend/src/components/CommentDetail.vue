<template>
  <div class="comment-detail-page">
    <button class="back" @click="$router.back()">← Back</button>

    <div v-if="loading">Loading...</div>

    <div v-else-if="comment">
      <!-- Use recursive CommentNode to render root comment and nested replies -->
      <CommentNode :comment="comment" :level="0" />
    </div>

    <div v-else>
      Comment not found.
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import CommentNode from './CommentNode.vue'

export default {
  name: 'CommentDetail',
  components: { CommentNode },
  props: {
    id: {
      type: [String, Number],
      required: true
    }
  },
  setup(props) {
    const comment = ref(null)
    const loading = ref(true)

    const fetchComment = async () => {
      loading.value = true
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/api/v1/comments/${props.id}/?format=json`
        )
        comment.value = response.data
        // Ensure replies array exists (backend should provide it)
        if (!comment.value.replies) comment.value.replies = []
      } catch (error) {
        console.error('Error fetching comment:', error)
      } finally {
        loading.value = false
      }
    }

    onMounted(fetchComment)

    return {
      comment,
      loading
    }
  }
}
</script>

<style scoped>
.comment-detail-page {
  max-width: 900px;
  margin: 16px auto;
  padding: 6px;
}
.back {
  margin-bottom: 12px;
  background: transparent;
  border: none;
  color: #1a73e8;
  cursor: pointer;
  font-size: 14px;
  padding: 6px;
}
.back:hover {
  text-decoration: underline;
}
</style>
