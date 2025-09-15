import { createRouter, createWebHistory } from 'vue-router';
import CommentList from '../components/CommentList.vue';
import CommentDetail from '../components/CommentDetail.vue';
import Login from '../components/Login.vue';
import Register from '../components/Register.vue';

const routes = [
  { path: '/', name: 'CommentList', component: CommentList },
  { path: '/comment/:id', name: 'CommentDetail', component: CommentDetail, props: true },
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
