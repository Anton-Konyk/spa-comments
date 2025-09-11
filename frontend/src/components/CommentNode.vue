<template>
  <div
    class="comment-node"
    :level="level"
    :style="containerStyle"
  >
    <!-- header: avatar + meta -->
    <div class="comment-header">
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

    <!-- body: text -->
    <div class="comment-body" v-html="comment?.text || ''"></div>

    <!-- replies: recursive -->
    <div v-if="comment?.replies && comment.replies.length" class="replies">
      <CommentNode
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        :level="level + 1"
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
      try {
        return new Date(iso).toLocaleString()
      } catch {
        return iso
      }
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

/* Left stripe for nesting level */
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

/* header */
.comment-header {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
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
.username {
  font-weight: 700;
}
.created {
  color: #666;
  font-size: 0.9em;
}

/* body */
.comment-body {
  margin-top: 6px;
  color: #222;
  line-height: 1.45;
}
.comment-body a {
  color: #1a73e8;
  text-decoration: underline;
}

/* replies */
.replies {
  margin-top: 12px;
}

/* Softer pastel colors for levels */
.comment-node[level="0"] {
  --level-color: #a8c6f7; /* light blue */
  background: #ffffff;
}
.comment-node[level="1"] {
  --level-color: #a8e6b0; /* light green */
  background: #f9fdf9;
}
.comment-node[level="2"] {
  --level-color: #fde59c; /* light yellow */
  background: #fffef8;
}
.comment-node[level="3"] {
  --level-color: #f6a6a0; /* light red */
  background: #fff9f9;
}
.comment-node[level="4"] {
  --level-color: #d7a8e6; /* light purple */
  background: #fcf8ff;
}
</style>
