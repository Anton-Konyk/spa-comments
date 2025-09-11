<template>
  <form class="comment-form" @submit.prevent="handleSubmit">
    <!-- Comment text -->
    <textarea
      v-model="form.text"
      name="text"
      id="comment-text"
      placeholder="Write your comment..."
      required
    ></textarea>

    <!-- reCAPTCHA container -->
    <div class="recaptcha-wrapper">
      <div id="recaptcha-container"></div>
    </div>

    <!-- Submit -->
    <button type="submit" :disabled="submitting">
      {{ submitting ? "Submitting..." : "Submit" }}
    </button>
  </form>
</template>

<script>
import axios from "axios";

export default {
  name: "CommentForm",
  data() {
    return {
      siteKey: import.meta.env.VITE_RECAPTCHA_SITE_KEY,
      submitting: false,
      form: {
        text: "",
      },
      widgetId: null,
    };
  },
  mounted() {
    if (window.grecaptcha) {
      this.widgetId = window.grecaptcha.render("recaptcha-container", {
        sitekey: this.siteKey,
      });
    } else {
      console.error("reCAPTCHA script not loaded!");
    }
  },
  methods: {
    async handleSubmit() {
      this.submitting = true;

      const tokenField = document.querySelector(
        "textarea[name='g-recaptcha-response']"
      );
      const token = tokenField ? tokenField.value : "";

      if (!token) {
        alert("Please complete the reCAPTCHA");
        this.submitting = false;
        return;
      }

      try {
        const formData = new FormData();
        formData.append("text", this.form.text);
        formData.append("recaptcha_token", token);

        await axios.post(
          `${import.meta.env.VITE_BACKEND_URL}/api/v1/comments/create/`,
          formData,
          { withCredentials: true }
        );

        alert("Comment submitted successfully!");
        this.form.text = "";

        if (this.widgetId !== null) {
          window.grecaptcha.reset(this.widgetId);
        }
      } catch (err) {
        console.error("Error creating comment:", err);
        alert("Failed to create comment");
      } finally {
        this.submitting = false;
      }
    },
  },
};
</script>

<style scoped>
button[type="submit"] {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

button[type="submit"]:hover:not(:disabled) {
  background-color: #0056b3;
}

button[type="submit"]:disabled {
  background-color: #7da6d9;
  cursor: not-allowed;
}

.comment-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 500px;
  margin: 2rem auto;
  padding: 1.5rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fff;
}

textarea {
  width: 100%;
  min-height: 100px;
  resize: vertical;
  padding: 0.5rem;
}

.recaptcha-wrapper {
  display: flex;
  justify-content: center;
  min-height: 80px;
}
</style>
