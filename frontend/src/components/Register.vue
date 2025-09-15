<template>
  <div class="register-card">
    <h2 class="title">Register</h2>
    <form @submit.prevent="handleRegister" enctype="multipart/form-data">
      <!-- Username -->
      <div class="form-group">
        <label for="username">Username</label>
        <input v-model="form.username" type="text" id="username" required />
      </div>

      <!-- Email -->
      <div class="form-group">
        <label for="email">Email</label>
        <input v-model="form.email" type="email" id="email" required />
      </div>

      <!-- Password -->
      <div class="form-group">
        <label for="password">Password</label>
        <input v-model="form.password" type="password" id="password" required />
      </div>

      <!-- Avatar -->
      <div class="form-group">
        <label for="avatar">Avatar</label>
        <input type="file" id="avatar" @change="handleFile" />
      </div>

      <!-- reCAPTCHA -->
      <div class="form-group captcha-wrapper">
        <div ref="captcha"></div>
      </div>

      <!-- Submit -->
      <button type="submit" :disabled="submitting">
        {{ submitting ? 'Registering...' : 'Register' }}
      </button>

      <!-- Back -->
      <button type="button" class="back-btn" @click="goBack">Back</button>
    </form>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    <p v-if="successMessage" class="success">{{ successMessage }}</p>
  </div>
</template>

<script>
import axios from 'axios';
import Cookies from 'js-cookie';
import { useRouter } from 'vue-router';

export default {
  name: 'Register',
  setup() {
    const router = useRouter();
    return { router };
  },
  data() {
    return {
      form: {
        username: '',
        email: '',
        password: '',
        avatar: null,
      },
      submitting: false,
      errorMessage: '',
      successMessage: '',
      recaptchaWidgetId: null,
      recaptchaSiteKey: import.meta.env.VITE_RECAPTCHA_SITE_KEY,
    };
  },

  methods: {
    handleFile(e) {
      this.form.avatar = e.target.files[0];
    },
    validateForm() {
      const USERNAME_REGEX = /^[A-Za-z0-9]+$/;
      const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      if (!USERNAME_REGEX.test(this.form.username)) {
        this.errorMessage = 'Username may contain only Latin letters and digits.';
        return false;
      }
      if (!EMAIL_REGEX.test(this.form.email)) {
        this.errorMessage = 'Please enter a valid email address.';
        return false;
      }
      return true;
    },
    async handleRegister() {
      this.errorMessage = '';
      this.successMessage = '';

      if (!this.validateForm()) return;

      this.submitting = true;

      const token = window.grecaptcha.getResponse(this.recaptchaWidgetId);
      if (!token) {
        this.errorMessage = 'Please complete the reCAPTCHA.';
        this.submitting = false;
        return;
      }

      try {
        const formData = new FormData();
        formData.append('username', this.form.username);
        formData.append('email', this.form.email);
        formData.append('password', this.form.password);
        if (this.form.avatar) formData.append('avatar', this.form.avatar);
        formData.append('recaptcha_token', token);

        const csrfToken = Cookies.get('csrftoken');
        const response = await axios.post(
          `${import.meta.env.VITE_BACKEND_URL}/api/v1/users/register/`,
          formData,
          {
            headers: { 'X-CSRFToken': csrfToken },
            withCredentials: true,
          }
        );

        this.successMessage = `Welcome, ${response.data.username}! Registration successful. Please sign in.`;

        // Reset form + recaptcha
        this.form = { username: '', email: '', password: '', avatar: null };
        window.grecaptcha.reset(this.recaptchaWidgetId);
        setTimeout(() => {
          const next = this.$route.query.next || '/';
          this.router.replace({ name: 'Login', query: { next, registered: 1 } });
        }, 2000);
      } catch (error) {
        if (error.response) {
          this.errorMessage = Object.values(error.response.data).flat().join(' ');
        } else if (error.request) {
          this.errorMessage = 'No response from server.';
        } else {
          this.errorMessage = 'Unexpected error.';
        }
      } finally {
        this.submitting = false;
      }
    },
    goBack() {
      this.router.push('/');
    },
  },
  mounted() {
    if (window.grecaptcha) {
      this.recaptchaWidgetId = window.grecaptcha.render(this.$refs.captcha, {
        sitekey: this.recaptchaSiteKey,
      });
    } else {
      console.error('reCAPTCHA script not loaded!');
    }
  },
};
</script>

<style scoped>
.register-card {
  max-width: 500px;
  margin: 20px auto;
  padding: 20px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}
.title {
  text-align: center;
  margin-bottom: 20px;
  font-size: 1.5rem;
}
.form-group {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
}
input[type='text'],
input[type='email'],
input[type='password'],
input[type='file'] {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 6px;
}
button {
  background-color: #2563eb;
  color: white;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  width: 100%;
  margin-top: 10px;
}
button:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}
.back-btn {
  background-color: #6b7280;
}
.error {
  color: red;
  margin-top: 10px;
}
.success {
  color: green;
  margin-top: 10px;
}
.captcha-wrapper {
  display: flex;
  justify-content: center;
  margin: 15px 0;
}
</style>
