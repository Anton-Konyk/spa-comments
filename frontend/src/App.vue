<template>
  <div id="app">
    <h1>SPA Comments</h1>
    <CommentList />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import CommentList from './components/CommentList.vue'

export default defineComponent({
  name: 'App',
  components: { CommentList }
})
</script>
