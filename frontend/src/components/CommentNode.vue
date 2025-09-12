<template>
  <div
    class="comment-node"
    :id="`comment-${comment.id}`"
    :level="level"
    :style="containerStyle"
  >
    <!-- Header: avatar + meta + actions -->
    <div class="comment-header">
      <div class="header-left">
        <img
          v-if="comment?.user?.avatar"
          :src="comment.user.avatar"
          alt="avatar"
          class="avatar"
          width="48"
          height="48"
        />
        <div class="meta">
          <div class="meta-top">
            <span class="username">{{ comment?.user?.username || 'Anonymous' }}</span>
            <span class="created"> · {{ formatDate(comment?.created_at) }}</span>
          </div>
        </div>
      </div>

      <div class="header-actions">
        <button class="reply-btn" @click.stop="emitReply">
          Reply
        </button>
      </div>
    </div>

    <!-- Body -->
    <div class="comment-body" v-html="comment?.text || ''"></div>

    <!-- Nested replies -->
    <div v-if="comment?.replies && comment.replies.length" class="replies">
      <CommentNode
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        :level="level + 1"
        @reply="$emit('reply', $event)"
      />
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'CommentNode',
  props: {
    comment: { type: Object, required: true },
    level: { type: Number, default: 0 }
  },
  methods: {
    formatDate(iso) {
      if (!iso) return ''
      try { return new Date(iso).toLocaleString() } catch { return iso }
    },
    // Emit only id + text + authorName(safe for backend, useful for frontend preview)
    emitReply() {
      this.$emit('reply', {
        id: this.comment.id,
        text: this.comment.text,
        authorName: this.comment.user?.username
      })
    }
  },
  computed: {
    containerStyle() {
      const indent = this.level * 24
      return {
        marginLeft: this.level === 0 ? '0px' : indent + 'px',
        marginTop: '12px'
      }
    }
  }
})
</script>

<style scoped>
.comment-node {
  border-radius: 6px;
  padding: 12px;
  margin-top: 12px;
  border: 1px solid rgba(0,0,0,0.12);
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
  position: relative;
  background: #ffffff;
}

/* Left pastel stripe by level */
.comment-node::before {
  content: "";
  position: absolute;
  top: 0;
  left: -6px;
  width: 4px;
  height: 100%;
  border-radius: 4px;
  background: var(--level-color);
}

/* Header layout */
.comment-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}
.header-left {
  display: flex;
  gap: 12px;
  align-items: center;
}
.header-actions {
  flex-shrink: 0;
}

.avatar {
  border-radius: 50%;
  flex-shrink: 0;
  object-fit: cover;
  box-shadow: 0 0 0 2px #fff;
}

.meta {
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.meta-top {
  display: flex;
  gap: 8px;
  align-items: center;
}
.username { font-weight: 700; }
.created { color: #666; font-size: 0.9em; }

.reply-btn {
  padding: 6px 10px;
  border: 1px solid rgba(26,115,232,0.4);
  background: #1a73e8;
  color: #fff;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}
.reply-btn:hover {
  filter: brightness(0.95);
}

/* Body */
.comment-body {
  margin-top: 6px;
  color: #222;
  line-height: 1.45;
}
.comment-body a {
  color: #1a73e8;
  text-decoration: underline;
}

/* Replies */
.replies { margin-top: 12px; }

/* Softer pastel colors per level */
.comment-node[level="0"] { --level-color: #a8c6f7; background: #ffffff; }
.comment-node[level="1"] { --level-color: #a8e6b0; background: #f9fdf9; }
.comment-node[level="2"] { --level-color: #fde59c; background: #fffef8; }
.comment-node[level="3"] { --level-color: #f6a6a0; background: #fff9f9; }
.comment-node[level="4"] { --level-color: #d7a8e6; background: #fcf8ff; }
</style>
