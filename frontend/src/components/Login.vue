<template>
  <div class="login-container">
    <h2>Sign in</h2>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="username">Username or Email</label>
        <input
          v-model="form.username"
          id="username"
          type="text"
          required
        />
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input
          v-model="form.password"
          id="password"
          type="password"
          required
        />
      </div>

      <!-- Visible reCAPTCHA v2 -->
      <div class="recaptcha-wrapper">
        <div
          class="g-recaptcha"
          :data-sitekey="recaptchaSiteKey"
        ></div>
      </div>

      <div class="button-row">
        <button type="submit" :disabled="submitting">
          {{ submitting ? "Logging in..." : "Login" }}
        </button>
        <button type="button" class="cancel" @click="goBack">
          Cancel
        </button>
      </div>
    </form>

    <p v-if="message" class="success">{{ message }}</p>
    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";
import Cookies from "js-cookie";

const router = useRouter();
const form = ref({
  username: "",
  password: "",
});
const submitting = ref(false);
const message = ref("");
const errorMessage = ref("");

const recaptchaSiteKey = import.meta.env.VITE_RECAPTCHA_SITE_KEY;

// ensure recaptcha renders after mount
onMounted(() => {
  if (window.grecaptcha) {
    window.grecaptcha.render(
      document.querySelector(".g-recaptcha"),
      { sitekey: recaptchaSiteKey }
    );
  }
});

const handleLogin = async () => {
  errorMessage.value = "";
  message.value = "";
  submitting.value = true;

  try {
    // get token from hidden textarea created by recaptcha
    const recaptchaResponse = document.querySelector(
      'textarea[name="g-recaptcha-response"]'
    )?.value;

    if (!recaptchaResponse) {
      errorMessage.value = "Please complete the reCAPTCHA.";
      submitting.value = false;
      return;
    }

    const csrfToken = Cookies.get("csrftoken");
    const response = await axios.post(
      `${import.meta.env.VITE_BACKEND_URL}/api/v1/users/login/`,
      {
        username: form.value.username,
        password: form.value.password,
        recaptcha_token: recaptchaResponse,
      },
      {
        withCredentials: true,
        headers: { "X-CSRFToken": csrfToken },
      }
    );

    message.value = "Login successful!";
    // redirect to home after short delay
    setTimeout(() => router.push("/"), 800);
  } catch (error) {
    errorMessage.value =
      error.response?.data?.detail || "Login failed";
    console.error("Login error:", error.response?.data || error);
  } finally {
    submitting.value = false;
  }
};

const goBack = () => {
  router.push("/");
};
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 2rem auto;
  padding: 1.5rem;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
h2 {
  text-align: center;
  margin-bottom: 1.2rem;
}
.form-group {
  margin-bottom: 1rem;
}
label {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 500;
}
input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 6px;
}
.recaptcha-wrapper {
  display: flex;
  justify-content: center;
  margin: 1rem 0;
}
.button-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}
button {
  flex: 1;
  padding: 0.6rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
button[type="submit"] {
  background: #007bff;
  color: white;
}
button.cancel {
  background: #ccc;
}
.success {
  color: green;
  margin-top: 1rem;
}
.error {
  color: red;
  margin-top: 1rem;
}
</style>
