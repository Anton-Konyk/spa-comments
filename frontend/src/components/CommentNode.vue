<template>
  <div
    class="comment-node"
    :id="`comment-${comment.id}`"
    :level="level"
    :style="containerStyle"
    :class="{ highlighted: isHighlighted }"
  >
    <!-- Header: avatar + meta + actions -->
    <div class="comment-header">
      <div class="header-left">
        <img v-if="avatarUrl" :src="avatarUrl" alt="avatar" class="avatar" width="48" height="48" />
        <div class="meta">
          <div class="meta-top">
            <span class="username">{{ comment?.user?.username || 'Anonymous' }}</span>
            <span class="created"> · {{ formatDate(comment?.created_at) }}</span>
          </div>
        </div>
      </div>

      <div class="header-actions">
        <button class="reply-btn" @click.stop="emitReply">Reply</button>
      </div>
    </div>

    <!-- Body: text on the left, image preview on the right -->
    <div class="comment-body">
      <div class="body-row">
        <!-- Truncated plain-text preview; click to open sanitized full text modal -->
        <div class="body-text" :title="'Click to preview full text'" @click.stop="openTextPreview">
          {{ previewText }}
        </div>

        <div v-if="fileUrl && isImage(fileUrl)" class="body-attachment">
          <img
            :src="comment.file"
            alt="attachment"
            class="attachment-thumb"
            @click.stop="openLightbox(fileUrl))"
          />
        </div>
      </div>
    </div>

    <!-- Nested replies -->
    <div v-if="comment?.replies && comment.replies.length" class="replies">
      <CommentNode
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        :level="level + 1"
        :highlight-map="highlightMap"
        @reply="$emit('reply', $event)"
      />
    </div>

    <!-- Image lightbox -->
    <VueEasyLightbox
      :visible="showLightbox"
      :imgs="lightboxImgs"
      :index="lightboxIndex"
      @hide="showLightbox = false"
    />

    <!-- Modal with sanitized full HTML text -->
    <div v-if="showTextModal" class="txt-modal">
      <div class="txt-content">
        <button class="txt-close" @click="showTextModal = false">×</button>
        <div v-html="sanitizedPreviewHtml"></div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * CommentNode.vue
 * - Renders a single comment node with avatar/meta, truncated text preview, and image thumbnail.
 * - Clicking preview opens a modal with FULL sanitized HTML (strict allow-list).
 * - Accepts `highlightMap` to temporarily highlight a node (e.g., 10s).
 *
 * Security/Sanitization (aligned with CommentForm.vue):
 *   Allowed tags: <a href="" title=""></a>, <code></code>, <i></i>, <strong></strong>
 *   Allowed attrs on <a>: href, title (href must be http(s) or mailto)
 *
 * Networking:
 *   Uses the shared Axios client baseURL to resolve relative media URLs into absolute ones.
 *   (No direct API calls here; only URL normalization.)
 */
import { defineComponent } from 'vue';
import VueEasyLightbox from 'vue-easy-lightbox';
import DOMPurify from 'dompurify';
import client from '@/utils/client.js';

const ALLOWED_TAGS = ['a', 'code', 'i', 'strong'];
const ALLOWED_ATTRS = ['href', 'title'];
const SANITIZE_OPTS = {
  ALLOWED_TAGS: ALLOWED_TAGS,
  ALLOWED_ATTR: ALLOWED_ATTRS,
  ALLOW_DATA_ATTR: false,
  ALLOW_ARIA_ATTR: false,
  ALLOWED_URI_REGEXP: /^(?:https?:|mailto:)/i,
};

function toAbs(u) {
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
}

export default defineComponent({
  name: 'CommentNode',
  components: { VueEasyLightbox },
  props: {
    comment: { type: Object, required: true },
    level: { type: Number, default: 0 },
    highlightMap: { type: Object, default: null }, // { [id]: true }
  },
  data() {
    return {
      showLightbox: false,
      lightboxImgs: [],
      lightboxIndex: 0,

      showTextModal: false,
      sanitizedPreviewHtml: '',
    };
  },
  computed: {
    containerStyle() {
      const indent = this.level * 24;
      return {
        marginLeft: this.level === 0 ? '0px' : indent + 'px',
        marginTop: '12px',
      };
    },
    truncateLen() {
      return Number(import.meta.env.VITE_COMMENT_TRUNCATE_LENGTH || 100);
    },
    previewText() {
      const raw = this.comment?.text || '';
      const div = document.createElement('div');
      div.innerHTML = raw;
      const plain = div.textContent || div.innerText || '';
      return plain.length > this.truncateLen ? plain.slice(0, this.truncateLen) + '…' : plain;
    },
    isHighlighted() {
      return !!(this.highlightMap && this.comment && this.highlightMap[this.comment.id]);
    },
    // normalized media URLs for template bindings (optional)
    avatarUrl() {
      const a = this.comment?.user?.avatar;
      return toAbs(a);
    },
    fileUrl() {
      return toAbs(this.comment?.file);
    },
  },
  methods: {
    formatDate(iso) {
      if (!iso) return '';
      try {
        return new Date(iso).toLocaleString();
      } catch {
        return iso;
      }
    },
    emitReply() {
      this.$emit('reply', {
        id: this.comment.id,
        text: this.comment.text,
        authorName: this.comment.user?.username,
      });
    },
    isImage(url) {
      return /\.(jpe?g|png|gif|webp)$/i.test(url || '');
    },
    openLightbox(url) {
      this.lightboxImgs = [toAbs(url)];
      this.lightboxIndex = 0;
      this.showLightbox = true;
    },
    openTextPreview() {
      const raw = this.comment?.text || '';
      this.sanitizedPreviewHtml = DOMPurify.sanitize(raw, SANITIZE_OPTS);
      this.showTextModal = true;
    },
  },
});
</script>

<style scoped>
.comment-node {
  border-radius: 6px;
  padding: 12px;
  margin-top: 12px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  position: relative;
  background: #ffffff;
}

/* Left pastel stripe by level */
.comment-node::before {
  content: '';
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
.username {
  font-weight: 700;
}
.created {
  color: #666;
  font-size: 0.9em;
}

.reply-btn {
  padding: 6px 10px;
  border: 1px solid rgba(26, 115, 232, 0.4);
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
.body-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.body-text {
  flex: 1 1 auto;
  min-width: 0;
  cursor: pointer;
}
.body-attachment {
  flex: 0 0 120px;
}

.attachment-thumb {
  width: 90px;
  height: 70px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

/* Links inside modal text */
.txt-content a {
  color: #1a73e8;
  text-decoration: underline;
}

/* Replies */
.replies {
  margin-top: 12px;
}

/* Pastel per level */
.comment-node[level='0'] {
  --level-color: #a8c6f7;
  background: #ffffff;
}
.comment-node[level='1'] {
  --level-color: #a8e6b0;
  background: #f9fdf9;
}
.comment-node[level='2'] {
  --level-color: #fde59c;
  background: #fffef8;
}
.comment-node[level='3'] {
  --level-color: #f6a6a0;
  background: #fff9f9;
}
.comment-node[level='4'] {
  --level-color: #d7a8e6;
  background: #fcf8ff;
}

/* 10s pulse highlight (2s * 5 iterations) */
@keyframes pulseGlow {
  0%,
  100% {
    box-shadow:
      inset 0 0 0 3px #ffe58f,
      0 1px 2px rgba(0, 0, 0, 0.08);
  }
  50% {
    box-shadow:
      inset 0 0 0 3px #ffd666,
      0 4px 10px rgba(0, 0, 0, 0.18);
  }
}
.comment-node.highlighted {
  animation: pulseGlow 2s ease-in-out 5;
  background-image: linear-gradient(0deg, rgba(255, 248, 196, 0.45), rgba(255, 248, 196, 0.45));
}

/* Modal for sanitized full-text preview */
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
  white-space: normal;
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
</style>
