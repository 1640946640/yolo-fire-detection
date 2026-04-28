
<template>
  <div class="app-container">
    <nav class="navbar">
      <div class="nav-content">
        <div class="logo">
          <span class="fire-icon"><img src="./assets/icons/fire.svg" alt="Fire" /></span>
          <span class="logo-text">基于YOLOv10的早期森林火灾检测</span>
        </div>
        <ul class="nav-links">
          <li v-for="item in navItems" :key="item.name">
            <router-link :to="item.path" :class="{ active: $route.path === item.path }">
              {{ item.label }}
            </router-link>
          </li>
        </ul>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
const navItems = [
  { name: 'Home', path: '/', label: '首页' },
  { name: 'ImageDetection', path: '/detection/image', label: '图片检测' },
  { name: 'BatchDetection', path: '/detection/batch', label: '批量检测' },
  { name: 'VideoDetection', path: '/detection/video', label: '视频检测' },
  { name: 'History', path: '/history', label: '检测历史' },
  { name: 'Training', path: '/training', label: '模型训练' }
]
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.nav-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.fire-icon img {
  width: 24px;
  height: 24px;
  color: #ff4757;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-links {
  display: flex;
  list-style: none;
  gap: 30px;
}

.nav-links a {
  text-decoration: none;
  color: #333;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.nav-links a:hover {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
}

.nav-links a.active {
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
  color: white;
}

.main-content {
  flex: 1;
  padding: 20px;
}
</style>
