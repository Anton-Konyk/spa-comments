import { createApp } from 'vue';
import App from './App.vue';
import router from './router/router.js';
import './style.css';
import { ensureCsrf } from '@/utils/csrf';

const app = createApp(App);
app.use(router);

ensureCsrf()
  .catch(() => {})
  .finally(() => {
    app.mount('#app');
  });
