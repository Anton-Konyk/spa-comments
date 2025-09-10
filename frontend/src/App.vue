<template>
  <div id="app">
    <h1>SPA Comments</h1>
    <router-view />
  </div>
</template>

<script>
import CommentList from './components/CommentList.vue'

export default {
  name: 'App',
  components: { CommentList }
}
</script>
