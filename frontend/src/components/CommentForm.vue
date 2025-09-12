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

      <textarea
        v-model="text"
        placeholder="Write your comment..."
        required
      ></textarea>

      <input type="file" @change="handleFileChange" />

      <!-- reCAPTCHA v2 -->
      <div ref="captcha" class="g-recaptcha"></div>

      <div class="form-actions">
        <button type="submit" :disabled="submitting">
          {{ submitting ? "Submitting..." : "Submit" }}
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
 */
import { ref, onMounted, watch, computed } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";
import Cookies from "js-cookie";

const props = defineProps({
  currentUser: { type: Object, default: null },
  // Parent PK (can be Number or String)
  parentId: { type: [Number, String], default: null },
  // Text of the comment being replied to (for visual preview only)
  replyToText: { type: String, default: "" },
  replyToAuthor: { type: String, default: "" },
});

const emit = defineEmits(["comment-posted", "cancel"]);

const router = useRouter();

const text = ref("");
const file = ref(null);
const submitting = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

const captcha = ref(null);
let widgetId = null;

/** Render reCAPTCHA only once, after currentUser exists and DOM is ready */
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
    if (val) {
      setTimeout(renderCaptcha, 150);
    }
  }
);

/** Short preview text for the "Replying to" header */
const clippedReply = computed(() =>
  (props.replyToText || "").replace(/\s+/g, " ").slice(0, 140)
);

const handleFileChange = (e) => {
  file.value = e.target.files[0] || null;
};

const handleSubmit = async () => {
  errorMessage.value = "";
  successMessage.value = "";

  // Ensure captcha is completed
  const recaptchaToken = window.grecaptcha?.getResponse(widgetId);
  if (!recaptchaToken) {
    errorMessage.value = "Please complete the reCAPTCHA.";
    return;
  }

  // Build multipart form data
  const formData = new FormData();
  formData.append("text", text.value);

  // Append parent as PK string if valid
  if (props.parentId !== null && props.parentId !== undefined && props.parentId !== "") {
    const pkNum = Number(props.parentId);
    if (Number.isFinite(pkNum) && pkNum > 0) {
      formData.append("parent", pkNum.toString());
    }
  }

  if (file.value) formData.append("file", file.value);
  formData.append("recaptcha_token", recaptchaToken);

  submitting.value = true;
  try {
    await axios.post(
      `${import.meta.env.VITE_BACKEND_URL}/api/v1/comments/create/`,
      formData,
      {
        withCredentials: true,
        headers: {
          "X-CSRFToken": Cookies.get("csrftoken"),
        },
      }
    );

    successMessage.value = "Comment submitted!";
    text.value = "";
    file.value = null;
    if (widgetId !== null) window.grecaptcha.reset(widgetId);

    emit("comment-posted");
  } catch (err) {
    // Show server response when present
    errorMessage.value =
      err?.response?.data
        ? JSON.stringify(err.response.data)
        : "Failed to create comment.";
    console.error("Create comment error:", err?.response?.data || err);
  } finally {
    submitting.value = false;
  }
};

/** Navigation: preserve intent so user returns to reply after auth */
const goLogin = () => {
  if (props.parentId) {
    sessionStorage.setItem(
      "pendingReply",
      JSON.stringify({ commentId: String(props.parentId) })
    );
  }
  const next = window.location.pathname + window.location.search;
  sessionStorage.setItem("nextAfterAuth", next);
  router.push({ name: "Login", query: { next } });
};

const goRegister = () => {
  if (props.parentId) {
    sessionStorage.setItem(
      "pendingReply",
      JSON.stringify({ commentId: String(props.parentId) })
    );
  }
  const next = window.location.pathname + window.location.search;
  sessionStorage.setItem("nextAfterAuth", next);
  router.push({ name: "Register", query: { next } });
};

const cancelReply = () => emit("cancel");
</script>

<style scoped>
.comment-form-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  padding: 1rem;
  margin-top: 1rem;
}

.reply-preview {
  background: #f7faff;
  border: 1px solid rgba(26,115,232,0.2);
  border-radius: 6px;
  padding: 8px 10px;
  margin-bottom: 10px;
  font-size: 0.95rem;
}
.preview-text {
  color: #333;
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

button[type="submit"] {
  background-color: #007bff;
  color: white;
}
button[type="submit"]:disabled {
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
</style>
