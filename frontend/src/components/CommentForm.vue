<template>
  <div class="comment-form-card">
    <!-- For guests -->
    <div v-if="!currentUser" class="not-logged-in">
      <p class="info-text">You must be signed in to leave a comment.</p>
      <div class="auth-buttons">
        <button @click="goLogin">Sign in</button>
        <button @click="goRegister">Register</button>
        <button @click="cancelReply" class="cancel-btn">Cancel</button>
      </div>
    </div>

    <!-- For logged-in users -->
    <form v-else @submit.prevent="handleSubmit" class="comment-form">
      <textarea
        v-model="text"
        placeholder="Write your comment..."
        required
      ></textarea>

      <input type="file" @change="handleFileChange" />

      <div ref="captcha" class="g-recaptcha"></div>

      <div class="form-actions">
        <button type="submit" :disabled="submitting">Submit</button>
        <button type="button" class="cancel-btn" @click="cancelReply">Cancel</button>
      </div>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success">{{ successMessage }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";
import Cookies from "js-cookie";

const props = defineProps({
  currentUser: Object,
  parentId: Number,
});

const emit = defineEmits(["comment-posted", "cancel"]);

const router = useRouter();

const text = ref("");
const file = ref(null);
const errorMessage = ref("");
const successMessage = ref("");
const submitting = ref(false);
const captcha = ref(null);
let captchaWidgetId = null;

onMounted(() => {
  if (window.grecaptcha && captcha.value) {
    captchaWidgetId = window.grecaptcha.render(captcha.value, {
      sitekey: import.meta.env.VITE_RECAPTCHA_SITE_KEY,
    });
  }
});

const handleFileChange = (e) => {
  file.value = e.target.files[0];
};

const handleSubmit = async () => {
  errorMessage.value = "";
  successMessage.value = "";

  const recaptchaToken = window.grecaptcha.getResponse(captchaWidgetId);
  if (!recaptchaToken) {
    errorMessage.value = "Please complete the reCAPTCHA.";
    return;
  }

  const formData = new FormData();
  formData.append("text", text.value);
  if (props.parentId) formData.append("parent", props.parentId);
  if (file.value) formData.append("file", file.value);
  formData.append("recaptcha_token", recaptchaToken);

  submitting.value = true;
  try {
    await axios.post(
      `${import.meta.env.VITE_BACKEND_URL}/api/v1/comments/create/`,
      formData,
      {
        headers: {
          "X-CSRFToken": Cookies.get("csrftoken"),
        },
        withCredentials: true,
      }
    );

    successMessage.value = "Comment submitted!";
    text.value = "";
    file.value = null;
    window.grecaptcha.reset(captchaWidgetId);

    emit("comment-posted");
  } catch (error) {
    errorMessage.value =
      error.response?.data
        ? JSON.stringify(error.response.data)
        : "Failed to create comment.";
  } finally {
    submitting.value = false;
  }
};

const goLogin = () => router.push({ name: "Login" });
const goRegister = () => router.push({ name: "Register" });
const cancelReply = () => emit("cancel");
</script>

<style scoped>
.comment-form-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  padding: 1rem;
  margin-top: 1rem;
}

textarea {
  width: 100%;
  min-height: 80px;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
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
