<template>
  <div id="app">
    <nav class="app-nav">
      <div class="nav-brand">医学影像标注平台</div>
      <div class="nav-links">
        <router-link to="/">标注工作台</router-link>
        <router-link to="/kanban">任务看板</router-link>
        <router-link to="/qc">质控对比</router-link>
        <router-link to="/arbitration">仲裁</router-link>
        <router-link to="/stats">统计面板</router-link>
      </div>
      <div class="nav-user">
        <select v-model="userStore.currentUserId" @change="userStore.switchUser($event.target.value)">
          <option v-for="u in userStore.users" :key="u.id" :value="u.id">{{ u.username }}</option>
        </select>
      </div>
    </nav>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from './stores/user'

const userStore = useUserStore()

onMounted(() => {
  userStore.fetchUsers()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f0f2f5;
  color: #1a1a2e;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-nav {
  display: flex;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  background: #1a1a2e;
  color: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.nav-brand {
  font-size: 18px;
  font-weight: 700;
  margin-right: 40px;
  letter-spacing: 1px;
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-links a {
  color: rgba(255,255,255,0.7);
  text-decoration: none;
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 4px;
  transition: all 0.2s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: white;
  background: rgba(255,255,255,0.1);
}

.nav-user {
  margin-left: auto;
}

.nav-user select {
  padding: 6px 12px;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,0.3);
  background: rgba(255,255,255,0.1);
  color: white;
  font-size: 13px;
}

.app-main {
  flex: 1;
  padding: 24px;
}
</style>
