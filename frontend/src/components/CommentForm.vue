<template>
  <div class="comment-form-card">
    <!-- Guests see auth CTA -->
    <div v-if="!currentUser" class="not-logged-in">
      <p class="info-text">You must be signed in to leave a comment.</p>
      <div class="auth-buttons">
        <button @click="goLogin">Sign in</button>
        <button @click="goRegister">Register</button>
        <button @click="cancelReply" class="cancel-btn">Cancel</button>
      </div>
    </div>

    <!-- Authenticated users see the form -->
    <form v-else @submit.prevent="handleSubmit" class="comment-form">
      <!-- Reply preview (only when replying) -->
      <div v-if="replyToText" class="reply-preview">
        <strong>Replying to {{ props.replyToAuthor }}:</strong>
        <span class="preview-text">“{{ clippedReply }}”</span>
      </div>

      <p class="allowed-hint">
        Allowed HTML: &lt;a href="" title=""&gt;&lt;/a&gt;, &lt;code&gt;&lt;/code&gt;,
        &lt;i&gt;&lt;/i&gt;, &lt;strong&gt;&lt;/strong&gt;
      </p>

      <!-- Tag toolbar -->
      <div class="tag-toolbar">
        <button type="button" class="tag-btn" title="Italic <i>" @click="applyTag('i')">[i]</button>
        <button type="button" class="tag-btn" title="Bold <strong>" @click="applyTag('strong')">
          [strong]
        </button>
        <button type="button" class="tag-btn" title="Code <code>" @click="applyTag('code')">
          [code]
        </button>
        <button type="button" class="tag-btn" title="Link <a>" @click="insertLink">[a]</button>
      </div>

      <textarea ref="ta" v-model="text" placeholder="Write your comment..." required></textarea>

      <input type="file" @change="handleFileChange" />

      <!-- reCAPTCHA v2 -->
      <div ref="captcha" class="g-recaptcha"></div>

      <div class="form-actions">
        <button type="submit" :disabled="submitting">
          {{ submitting ? 'Submitting...' : 'Submit' }}
        </button>
        <button type="button" class="cancel-btn" @click="cancelReply">Cancel</button>
      </div>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success">{{ successMessage }}</p>
    </form>
  </div>
</template>

<script setup>
/**
 * CommentForm.vue
 * - Shows auth CTA for guests.
 * - For authenticated users, renders a comment form with reCAPTCHA v2.
 * - Supports replying: receives parentId (pk) and optional replyToText for preview.
 * - Posts multipart/form-data to /api/v1/comments/create/ with CSRF and credentials.
 *
 * HTML validation policy:
 * - Only these tags are allowed: <a href="" title=""></a>, <code></code>, <i></i>, <strong></strong>
 * - Attributes allowed only on <a>: href, title. href must be http(s) or mailto.
 * - Tags must be properly nested/closed AND also parse as well-formed XHTML.
 * - We sanitize with DOMPurify and also require sanitize(text) === original (strict whitelist).
 *
 * Toolbar:
 * - Buttons wrap current selection (or insert placeholders) with allowed tags.
 * - <a> asks for URL (http(s)/mailto) and optional title; inserts <a href="..." title="...">selected or placeholder</a>.
 */
import { ref, onMounted, watch, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import client from '@/utils/client.js';
import DOMPurify from 'dompurify';

const props = defineProps({
  currentUser: { type: Object, default: null },
  parentId: { type: [Number, String], default: null },
  replyToText: { type: String, default: '' },
  replyToAuthor: { type: String, default: '' },
});

const emit = defineEmits(['comment-posted', 'cancel']);
const router = useRouter();

const text = ref('');
const ta = ref(null); // textarea ref for selection handling
const file = ref(null);
const submitting = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const captcha = ref(null);
let widgetId = null;

/* ====== Allowed HTML config ====== */
const ALLOWED_TAGS = ['a', 'code', 'i', 'strong'];
const ALLOWED_ATTRS = ['href', 'title'];

// DOMPurify options — only what we need
const SANITIZE_OPTS = {
  ALLOWED_TAGS,
  ALLOWED_ATTR: ALLOWED_ATTRS,
  ALLOW_DATA_ATTR: false,
  ALLOW_ARIA_ATTR: false,
  // Accept only http(s) or mailto links
  ALLOWED_URI_REGEXP: /^(?:https?:|mailto:)/i,
};

/**
 * Stack-based check to ensure:
 * - Only allowed tags are used
 * - Proper nesting and closing of tags
 * - For <a>: only href/title attrs; href must be http(s) or mailto
 * - For <i>/<strong>/<code>: no attributes allowed
 */
function checkTagsWellFormed(html) {
  const stack = [];
  const tagRe = /<\/?([a-zA-Z]+)(\s[^>]*)?>/g;
  let m;

  const isAllowedTag = (name) => ALLOWED_TAGS.includes(name);

  while ((m = tagRe.exec(html))) {
    const raw = m[0];
    const name = (m[1] || '').toLowerCase();
    const attrStr = (m[2] || '').replace(/\s+/g, ' ').trim();

    if (!isAllowedTag(name)) {
      return { ok: false, msg: `Tag <${name}> is not allowed` };
    }

    const isClose = raw.startsWith('</');
    if (isClose) {
      const last = stack.pop();
      if (last !== name) {
        return { ok: false, msg: `Tag </${name}> closed out of order` };
      }
      continue;
    }

    // Opening tag — validate attributes
    if (name === 'a') {
      // Parse key="value" pairs; disallow anything else (single quotes, no value, etc.)
      const pairs = [...attrStr.matchAll(/\s*([a-zA-Z:-]+)\s*=\s*"([^"]*)"\s*/g)];
      const reconstructed = pairs.map((p) => p[0].trim()).join(' ');
      if ((attrStr || '') && reconstructed !== attrStr) {
        return { ok: false, msg: `Only href and title are allowed on <a> (use double quotes)` };
      }
      for (const [, key, val] of pairs) {
        const k = key.toLowerCase();
        if (!ALLOWED_ATTRS.includes(k)) {
          return { ok: false, msg: `Attribute "${key}" is not allowed on <a>` };
        }
        if (k === 'href' && !/^(https?:|mailto:)/i.test(val || '')) {
          return { ok: false, msg: `href must start with http(s):// or mailto:` };
        }
      }
    } else {
      // <i>/<strong>/<code> must not have attributes
      if (attrStr) {
        return { ok: false, msg: `Attributes are not allowed on <${name}>` };
      }
    }

    stack.push(name);
  }

  if (stack.length) {
    return { ok: false, msg: `Unclosed tag <${stack[stack.length - 1]}>` };
  }
  return { ok: true };
}

/**
 * Strict XHTML well-formedness check using DOMParser in XHTML mode.
 * We wrap the fragment into a single XHTML root node.
 */
function assertXHTMLWellFormed(fragment) {
  const xhtmlDoc =
    `<?xml version="1.0" encoding="UTF-8"?>` +
    `<div xmlns="http://www.w3.org/1999/xhtml">${fragment}</div>`;
  const doc = new DOMParser().parseFromString(xhtmlDoc, 'application/xhtml+xml');
  const hasError = doc.getElementsByTagName('parsererror').length > 0;
  if (hasError) {
    throw new Error('Markup is not well-formed XHTML (check tag nesting/closing & entities).');
  }
}

/**
 * Validate message:
 * 1) Not empty
 * 2) DOMPurify(sanitize) does not change text (strict whitelist)
 * 3) Well-formed tags (stack check)
 * 4) Parses as well-formed XHTML (DOMParser)
 */
function validateTextOrThrow(raw) {
  const trimmed = (raw || '').trim();
  if (!trimmed) throw new Error('Text is required');

  const sanitized = DOMPurify.sanitize(trimmed, SANITIZE_OPTS);
  if (sanitized !== trimmed) {
    throw new Error(
      'Only these tags are allowed: <a href="" title=""></a>, <code></code>, <i></i>, <strong></strong>'
    );
  }

  const wf = checkTagsWellFormed(trimmed);
  if (!wf.ok) throw new Error(wf.msg);

  // Extra safety: ensure the fragment parses as XHTML
  assertXHTMLWellFormed(trimmed);
}

/** Short preview for the "Replying to" header */
const clippedReply = computed(() => (props.replyToText || '').replace(/\s+/g, ' ').slice(0, 140));

const handleFileChange = (e) => {
  file.value = e.target.files[0] || null;
};

/** reCAPTCHA render */
const renderCaptcha = () => {
  if (captcha.value && window.grecaptcha && widgetId === null) {
    widgetId = window.grecaptcha.render(captcha.value, {
      sitekey: import.meta.env.VITE_RECAPTCHA_SITE_KEY,
    });
  }
};

onMounted(() => {
  if (props.currentUser) renderCaptcha();
});

/** If user logs in and returns to this page, render captcha then */
watch(
  () => props.currentUser,
  (val) => {
    if (val) setTimeout(renderCaptcha, 150);
  }
);

/* ===== Toolbar helpers ===== */

/** Get current selection range inside textarea (start, end) */
function getSel() {
  const el = ta.value;
  if (!el) return { start: text.value.length, end: text.value.length };
  return { start: el.selectionStart ?? 0, end: el.selectionEnd ?? 0 };
}

/** Replace selection with before + selected + after; set caret after inserted content */
async function wrapSelection(before, after, placeholder = '') {
  const el = ta.value;
  const value = text.value || '';
  const { start, end } = getSel();
  const selected = value.slice(start, end) || placeholder;

  const updated = value.slice(0, start) + before + selected + after + value.slice(end);

  text.value = updated;

  // restore caret after inserted block (right after closing tag)
  const caretPos = start + before.length + selected.length + after.length;
  await nextTick();
  if (el) {
    el.focus();
    el.setSelectionRange(caretPos, caretPos);
  }
}

/** Apply simple tag wrappers: i, strong, code */
function applyTag(tag) {
  // Only allowed tags are used here
  const map = {
    i: { before: '<i>', after: '</i>', ph: 'italic text' },
    strong: { before: '<strong>', after: '</strong>', ph: 'bold text' },
    code: { before: '<code>', after: '</code>', ph: 'code' },
  };
  const cfg = map[tag];
  if (!cfg) return;
  wrapSelection(cfg.before, cfg.after, cfg.ph);
}

/** Insert <a href="..."> around selection (asks for URL and optional title) */
function insertLink() {
  const url = window.prompt('Enter URL (http(s) or mailto:)', 'https://');
  if (!url) return;
  if (!/^(https?:|mailto:)/i.test(url)) {
    errorMessage.value = 'Link must start with http(s):// or mailto:';
    return;
  }
  const title = window.prompt('Optional title attribute (press Cancel to skip)', '') || '';
  const titleAttr = title ? ` title="${title.replace(/"/g, '&quot;')}"` : '';
  const before = `<a href="${url.replace(/"/g, '&quot;')}"${titleAttr}>`;
  const after = `</a>`;
  wrapSelection(before, after, 'link text');
}

const handleSubmit = async () => {
  // prevent double submit (race before the button becomes disabled)
  if (submitting.value) return;
  errorMessage.value = '';
  successMessage.value = '';

  // 0) Validate HTML content
  try {
    validateTextOrThrow(text.value);
  } catch (e) {
    errorMessage.value = e?.message || 'Invalid message';
    return;
  }

  // 1) Ensure reCAPTCHA completed
  const recaptchaToken = window.grecaptcha?.getResponse(widgetId);
  if (!recaptchaToken) {
    errorMessage.value = 'Please complete the reCAPTCHA.';
    return;
  }

  // 2) Build FormData (send sanitized text even though it equals original)
  const formData = new FormData();
  formData.append('text', DOMPurify.sanitize(text.value, SANITIZE_OPTS));

  if (props.parentId !== null && props.parentId !== undefined && props.parentId !== '') {
    const pkNum = Number(props.parentId);
    if (Number.isFinite(pkNum) && pkNum > 0) {
      formData.append('parent', pkNum.toString());
    }
  }
  if (file.value) formData.append('file', file.value);
  formData.append('recaptcha_token', recaptchaToken);

  submitting.value = true;
  try {
    // POST via shared client: CSRF & cookies handled by interceptors
    const { data } = await client.post('/api/v1/comments/create/', formData);

    successMessage.value = 'Comment submitted!';
    text.value = '';
    file.value = null;
    if (widgetId !== null) window.grecaptcha.reset(widgetId);
    // Emit with payload so parent can react (e.g., navigate)
    emit('comment-posted', data);
    // For root comments (no parent) navigate straight to the thread
    if (!props.parentId && data?.id) {
      await router.push({ name: 'CommentDetail', params: { id: data.id } });
      return;
    }
  } catch (err) {
    errorMessage.value = err?.response?.data
      ? JSON.stringify(err.response.data)
      : 'Failed to create comment.';
    console.error('Create comment error:', err?.response?.data || err);
  } finally {
    submitting.value = false;
  }
};

/** Auth navigation — preserve intent so user returns to reply after auth */
const goLogin = () => {
  if (props.parentId) {
    sessionStorage.setItem('pendingReply', JSON.stringify({ commentId: String(props.parentId) }));
  }
  const next = window.location.pathname + window.location.search;
  sessionStorage.setItem('nextAfterAuth', next);
  router.push({ name: 'Login', query: { next } });
};
const goRegister = () => {
  if (props.parentId) {
    sessionStorage.setItem('pendingReply', JSON.stringify({ commentId: String(props.parentId) }));
  }
  const next = window.location.pathname + window.location.search;
  sessionStorage.setItem('nextAfterAuth', next);
  router.push({ name: 'Register', query: { next } });
};
const cancelReply = () => emit('cancel');
</script>

<style scoped>
.comment-form-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  padding: 1rem;
  margin-top: 1rem;
}
.reply-preview {
  background: #f7faff;
  border: 1px solid rgba(26, 115, 232, 0.2);
  border-radius: 6px;
  padding: 8px 10px;
  margin-bottom: 10px;
  font-size: 0.95rem;
}
.preview-text {
  color: #333;
}

.tag-toolbar {
  display: flex;
  gap: 6px;
  margin: 6px 0 8px;
  flex-wrap: wrap;
}
.tag-btn {
  padding: 4px 8px;
  font-size: 12px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
}
.tag-btn:hover {
  background: #f5f7fb;
}

textarea {
  width: 100%;
  min-height: 80px;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 6px;
}
.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 1rem;
}
.form-actions button,
.auth-buttons button {
  flex: 1;
  padding: 0.5rem;
  border: none;
  cursor: pointer;
  border-radius: 4px;
}

button[type='submit'] {
  background-color: #007bff;
  color: white;
}

button[type='submit']:disabled {
  background-color: #6c757d;
}

.cancel-btn {
  background-color: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background-color: #5a6268;
}

.error {
  color: red;
  margin-top: 0.5rem;
}

.success {
  color: green;
  margin-top: 0.5rem;
}

.not-logged-in {
  text-align: center;
}

.info-text {
  margin-bottom: 1rem;
  font-weight: 500;
}

.auth-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.allowed-hint {
  margin: 6px 0 10px;
  font-size: 12px;
  color: #666;
}
</style>
