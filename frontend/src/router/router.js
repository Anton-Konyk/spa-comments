// src/router.js
import { createRouter, createWebHistory } from 'vue-router'
import CommentList from '../components/CommentList.vue'
import CommentDetail from '../components/CommentDetail.vue'

const routes = [
  { path: '/', name: 'CommentList', component: CommentList },
  { path: '/comment/:id', name: 'CommentDetail', component: CommentDetail, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
