<template>
  <div class="login-container">
    <h2>Sign in</h2>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="username">Username or Email</label>
        <input id="username" v-model="form.username" type="text" name="username" required />
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input id="password" v-model="form.password" type="password" name="password" required />
      </div>

      <!-- Google reCAPTCHA v2 -->
      <div class="g-recaptcha" :data-sitekey="recaptchaSiteKey"></div>

      <div class="button-row">
        <button type="submit" :disabled="loading">
          {{ loading ? 'Signing in...' : 'Sign in' }}
        </button>
        <button type="button" @click="cancelLogin" class="cancel-btn">Cancel</button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="success" class="success">Login successful!</p>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import client from '@/utils/client';

const router = useRouter();
const recaptchaSiteKey = import.meta.env.VITE_RECAPTCHA_SITE_KEY;

const form = ref({
  username: '',
  password: '',
});

const loading = ref(false);
const error = ref('');
const success = ref(false);
let recaptchaWidgetId = null;

onMounted(() => {
  if (window.grecaptcha) {
    // render reCAPTCHA explicitly
    recaptchaWidgetId = window.grecaptcha.render(document.querySelector('.g-recaptcha'), {
      sitekey: recaptchaSiteKey,
    });
  }
});

const handleLogin = async () => {
  error.value = '';
  success.value = false;
  loading.value = true;

  try {
    const recaptchaToken = window.grecaptcha.getResponse(recaptchaWidgetId);
    if (!recaptchaToken) throw new Error('Please complete the reCAPTCHA.');

    const payload = {
      username: form.value.username,
      password: form.value.password,
      recaptcha_token: recaptchaToken,
    };

    await client.post('/api/v1/users/login/', payload);

    success.value = true;
    try {
      const me = await client.get('/api/v1/users/me/');
      localStorage.setItem('currentUser', JSON.stringify(me.data));
    } catch (e) {
      console.error('fetch me failed', e);
    }
    form.value.username = '';
    form.value.password = '';
    if (recaptchaWidgetId !== null) {
      window.grecaptcha.reset(recaptchaWidgetId);
    }

    const redirectTo = router.currentRoute.value.query.next || '/';
    setTimeout(() => {
      router.push(redirectTo);
    }, 800);
  } catch (err) {
    error.value =
      err.response?.data?.detail ||
      err.response?.data?.non_field_errors?.[0] ||
      err.message ||
      'Login failed';
  } finally {
    loading.value = false;
  }
};

function cancelLogin() {
  router.push('/');
}
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 2rem auto;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fff;
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.3rem;
  font-weight: bold;
}

input {
  width: 100%;
  padding: 0.4rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.button-row {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

button {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
}

button:disabled {
  background: #90caf9;
  cursor: not-allowed;
}

button[type='submit'] {
  background: #1976d2;
}

.cancel-btn {
  background: #6c757d;
}

.error {
  color: red;
  margin-top: 0.5rem;
}
</style>
