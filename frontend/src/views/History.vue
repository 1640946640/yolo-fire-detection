<template>
  <div class="history-container">
    <div class="header-section">
      <h1>检测历史</h1>
      <p>查看所有检测记录，支持下载检测结果</p>
    </div>
    
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    
    <div v-else-if="records.length === 0" class="empty-state">
      <div class="empty-icon"><img src="../assets/icons/list.svg" alt="List" /></div>
      <p>暂无检测记录</p>
      <p class="hint">进行图片或视频检测后，记录会显示在这里</p>
    </div>
    
    <div v-else class="records-grid">
      <div v-for="record in records" :key="record.task_id" class="record-card">
        <div class="record-header">
          <div class="record-type">
            <span class="icon">
              <img v-if="record.type === 'video'" src="../assets/icons/video.svg" alt="Video" class="type-icon" />
              <img v-else-if="record.type === 'batch'" src="../assets/icons/images.svg" alt="Batch" class="type-icon" />
              <img v-else src="../assets/icons/image.svg" alt="Image" class="type-icon" />
            </span>
            <span class="type-text">
              {{ record.type === 'video' ? '视频检测' : (record.type === 'batch' ? '批量检测' : '图片检测') }}
            </span>
          </div>
          <div class="record-actions">
            <button class="btn-download" @click="downloadRecord(record.task_id)">
              <img src="../assets/icons/download.svg" alt="Download" class="icon-svg" />
              <span>下载</span>
            </button>
            <button class="btn-delete" @click="deleteRecord(record.task_id)">
              <img src="../assets/icons/delete.svg" alt="Delete" class="icon-svg" />
            </button>
          </div>
        </div>
        
        <div class="record-info">
          <div class="info-row">
            <span class="label">文件名:</span>
            <span class="value">{{ record.filename }}</span>
          </div>
          <div class="info-row">
            <span class="label">检测目标:</span>
            <span class="value">{{ record.detection_count }} 个</span>
          </div>
          <div class="info-row">
            <span class="label">烟雾:</span>
            <span class="value smoke">{{ record.smoke_count }} 个</span>
            <span class="label">火焰:</span>
            <span class="value fire">{{ record.fire_count }} 个</span>
          </div>
          <div class="info-row">
            <span class="label">检测时间:</span>
            <span class="value">{{ formatDate(record.created_at) }}</span>
          </div>
        </div>
        
        <div class="record-preview">
          <video v-if="record.type === 'video'" :src="record.result_path" controls class="preview-video" />
          <img v-else :src="record.result_path" class="preview-image" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const records = ref([])
const loading = ref(true)

const fetchHistory = async () => {
  try {
    const response = await fetch('/api/detection/history')
    const data = await response.json()
    records.value = data.records
  } catch (error) {
    console.error('获取历史记录失败:', error)
  } finally {
    loading.value = false
  }
}

const downloadRecord = async (taskId) => {
  try {
    const response = await fetch(`/api/detection/download/${taskId}`)
    const blob = await response.blob()
    
    const contentDisposition = response.headers.get('content-disposition')
    let filename = `${taskId}.zip`
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="(.+)"/)
      if (match) filename = match[1]
    }
    
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    alert('下载失败: ' + error.message)
  }
}

const deleteRecord = async (taskId) => {
  if (!confirm('确定要删除这条记录吗？')) return
  
  try {
    await fetch(`/api/detection/history/${taskId}`, {
      method: 'DELETE'
    })
    records.value = records.value.filter(r => r.task_id !== taskId)
  } catch (error) {
    alert('删除失败: ' + error.message)
  }
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.history-container {
  max-width: 1200px;
  margin: 0 auto;
}

.header-section {
  text-align: center;
  margin-bottom: 30px;
}

.header-section h1 {
  font-size: 32px;
  font-weight: 700;
  color: white;
  margin-bottom: 8px;
}

.header-section p {
  color: rgba(255, 255, 255, 0.8);
}

.loading {
  text-align: center;
  padding: 60px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
}

.empty-icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-icon img {
  width: 60px;
  height: 60px;
  color: #666;
}

.type-icon {
  width: 20px;
  height: 20px;
  color: white;
}

.icon-svg {
  width: 16px;
  height: 16px;
  color: white;
}

.empty-state p {
  color: #666;
  font-size: 16px;
}

.empty-state .hint {
  font-size: 14px;
  color: #999;
  margin-top: 8px;
}

.records-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
}

.record-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
}

.record-type {
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-type .icon {
  font-size: 20px;
}

.record-type .type-text {
  color: white;
  font-weight: 600;
}

.record-actions {
  display: flex;
  gap: 8px;
}

.btn-download, .btn-delete {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.btn-download {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.btn-download:hover {
  background: rgba(255, 255, 255, 0.3);
}

.btn-delete {
  background: rgba(231, 76, 60, 0.8);
  color: white;
  padding: 8px;
}

.btn-delete:hover {
  background: rgba(231, 76, 60, 1);
}

.record-info {
  padding: 16px 20px;
}

.info-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  color: #999;
  font-size: 14px;
}

.info-row .value {
  color: #333;
  font-weight: 500;
  font-size: 14px;
}

.info-row .value.smoke {
  color: #ffa502;
}

.info-row .value.fire {
  color: #ff4757;
}

.record-preview {
  padding: 0 20px 20px;
}

.preview-video, .preview-image {
  width: 100%;
  border-radius: 12px;
  max-height: 200px;
  object-fit: cover;
}

.preview-video {
  background: #000;
}

@media (max-width: 768px) {
  .records-grid {
    grid-template-columns: 1fr;
  }
}
</style>