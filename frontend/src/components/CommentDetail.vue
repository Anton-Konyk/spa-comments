<template>
  <div class="comment-detail-page">
    <button class="back" @click="$router.back()">← Back</button>

    <div v-if="loading">Loading...</div>

    <div v-else-if="comment">
      <!-- Root with nested replies -->
      <CommentNode
        :comment="comment"
        :level="0"
        @reply="handleReply"
      />

      <!-- Conditional reply form -->
      <div
        v-if="replyTo"
        ref="replyFormEl"
        class="reply-form"
      >
        <h4 class="replying-to">
          Replying to
          <strong>{{ replyTo.user?.username || 'Anonymous' }}</strong>:
          “{{ (replyTo.text || '').replace(/\s+/g, ' ').slice(0, 120) }}”
        </h4>

        <CommentForm
          :parentId="replyTo.id"
          @comment-posted="onReplyPosted"
        />

        <button class="cancel-reply" @click="cancelReply">Cancel</button>
      </div>
    </div>

    <div v-else>
      Comment not found.
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'
import CommentNode from './CommentNode.vue'
import CommentForm from './CommentForm.vue'

export default {
  name: 'CommentDetail',
  components: { CommentNode, CommentForm },
  props: {
    id: { type: [String, Number], required: true }
  },
  setup(props) {
    const comment = ref(null)
    const loading = ref(true)

    // The comment object we are replying to (not just id)
    const replyTo = ref(null)
    const replyFormEl = ref(null)

    const fetchComment = async () => {
      loading.value = true
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/api/v1/comments/${props.id}/?format=json`
        )
        comment.value = response.data
        if (!comment.value.replies) comment.value.replies = []
      } catch (error) {
        console.error('Error fetching comment:', error)
      } finally {
        loading.value = false
      }
    }

    // Called when "Reply" button is pressed on any CommentNode
    const handleReply = async (payload) => {
      // payload is a full comment object emitted by CommentNode
      replyTo.value = payload
      await nextTick()
      // Smooth scroll to the reply form block
      replyFormEl.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }

    // Cancel replying: hide form and scroll back to the original comment anchor
    const cancelReply = async () => {
      const target = replyTo.value
      replyTo.value = null
      await nextTick()
      if (target?.id) {
        const el = document.getElementById(`comment-${target.id}`)
        el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }

    // After a reply is posted, reload thread and return to the replied comment
    const onReplyPosted = async () => {
      const target = replyTo.value
      await fetchComment()
      replyTo.value = null
      await nextTick()
      if (target?.id) {
        const el = document.getElementById(`comment-${target.id}`)
        el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }

    onMounted(fetchComment)

    return {
      comment,
      loading,
      replyTo,
      replyFormEl,
      fetchComment,
      handleReply,
      cancelReply,
      onReplyPosted
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
.back:hover { text-decoration: underline; }

.reply-form {
  margin-top: 24px;
  padding: 16px;
  border-top: 1px solid #ddd;
  background: #fafafa;
  border-radius: 6px;
}
.replying-to { margin: 0 0 8px; }

.cancel-reply {
  margin-top: 8px;
  background: transparent;
  border: none;
  color: #d00;
  cursor: pointer;
}
.cancel-reply:hover { text-decoration: underline; }
</style>
