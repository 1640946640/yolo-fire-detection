
<template>
  <div class="home-container">
    <div class="hero-section">
      <div class="hero-content">
        <div class="hero-icon"><img src="../assets/icons/fire.svg" alt="Fire" /></div>
        <h1 class="hero-title">基于YOLOv10的早期森林火灾检测</h1>
        <p class="hero-subtitle">基于YOLOv10的智能火灾与烟雾早期检测解决方案</p>
        <div class="hero-buttons">
          <router-link to="/detection/image" class="btn-primary">
            开始检测
          </router-link>
          <router-link to="/training" class="btn-secondary">
            模型训练
          </router-link>
        </div>
      </div>
    </div>
    
    <div class="features-section">
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon"><img src="../assets/icons/image.svg" alt="Image" /></div>
          <h3>图片检测</h3>
          <p>支持单张图片上传检测，实时识别火灾和烟雾目标</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon"><img src="../assets/icons/folder.svg" alt="Folder" /></div>
          <h3>批量检测</h3>
          <p>支持多张图片批量上传，高效处理大量检测任务</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon"><img src="../assets/icons/video.svg" alt="Video" /></div>
          <h3>视频检测</h3>
          <p>支持视频文件上传，逐帧检测火灾隐患</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon"><img src="../assets/icons/settings.svg" alt="Settings" /></div>
          <h3>模型训练</h3>
          <p>支持自定义数据集训练，优化检测精度</p>
        </div>
      </div>
    </div>
    
    <div class="stats-section">
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">98%</div>
          <div class="stat-label">检测准确率</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">0.1s</div>
          <div class="stat-label">响应时间</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">2</div>
          <div class="stat-label">检测类别</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">GPU</div>
          <div class="stat-label">加速支持</div>
        </div>
      </div>
    </div>
    
    <div class="quick-start">
      <h2>快速开始</h2>
      <div class="steps">
        <div class="step">
          <span class="step-number">1</span>
          <span class="step-text">选择检测模式</span>
        </div>
        <div class="step-arrow">→</div>
        <div class="step">
          <span class="step-number">2</span>
          <span class="step-text">上传图片或视频</span>
        </div>
        <div class="step-arrow">→</div>
        <div class="step">
          <span class="step-number">3</span>
          <span class="step-text">查看检测结果</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.home-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 20px;
}

.hero-section {
  text-align: center;
  padding: 60px 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  margin-bottom: 40px;
}

.hero-icon {
  margin-bottom: 20px;
}

.hero-icon img {
  width: 80px;
  height: 80px;
  color: #e74c3c;
}

.hero-title {
  font-size: 42px;
  font-weight: 800;
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
}

.hero-subtitle {
  font-size: 18px;
  color: #666;
  margin-bottom: 30px;
}

.hero-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-primary, .btn-secondary {
  padding: 14px 32px;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(231, 76, 60, 0.4);
}

.btn-secondary {
  background: transparent;
  color: #e74c3c;
  border: 2px solid #e74c3c;
}

.btn-secondary:hover {
  background: #e74c3c;
  color: white;
}

.features-section {
  margin-bottom: 40px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.feature-card {
  background: rgba(255, 255, 255, 0.95);
  padding: 30px;
  border-radius: 16px;
  text-align: center;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  margin-bottom: 16px;
}

.feature-icon img {
  width: 40px;
  height: 40px;
  color: #e74c3c;
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
}

.feature-card p {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.stats-section {
  margin-bottom: 40px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-item {
  background: rgba(255, 255, 255, 0.95);
  padding: 30px;
  border-radius: 16px;
  text-align: center;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.quick-start {
  background: rgba(255, 255, 255, 0.95);
  padding: 40px;
  border-radius: 20px;
  text-align: center;
}

.quick-start h2 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 30px;
}

.steps {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.step {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-number {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.step-text {
  font-weight: 500;
  color: #333;
}

.step-arrow {
  color: #e74c3c;
  font-size: 20px;
  font-weight: bold;
}
</style>
