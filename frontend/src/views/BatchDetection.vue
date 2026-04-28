
<template>
  <div class="batch-container">
    <div class="header-section">
      <h1>批量检测</h1>
      <p>上传多张图片进行批量火灾和烟雾检测</p>
    </div>
    
    <div class="main-content">
      <div class="upload-section">
        <div class="upload-area" @click="selectFiles" @drop.prevent="handleDrop" @dragover.prevent>
          <div v-if="selectedFiles.length === 0" class="upload-placeholder">
            <div class="upload-icon"><img src="../assets/icons/folder.svg" alt="Folder" /></div>
            <p>点击或拖拽图片到此处</p>
            <p class="hint">支持 JPG、PNG、JPEG、BMP 格式</p>
            <p class="hint">可多选上传，最多支持50张图片</p>
          </div>
          <div v-else class="files-preview">
            <div v-for="(file, index) in selectedFiles" :key="index" class="file-preview-item">
              <img :src="getPreview(file)" class="preview-thumb" />
              <span class="preview-name">{{ file.name }}</span>
              <button class="preview-remove" @click="removeFile(index)">×</button>
            </div>
          </div>
        </div>
        
        <div v-if="selectedFiles.length > 0" class="files-info">
          <span>已选择 {{ selectedFiles.length }} 张图片</span>
          <button class="btn-clear" @click="clearAll">清空全部</button>
        </div>
        
        <div class="params-section">
          <h3>检测参数</h3>
          <div class="param-item">
            <label>置信度阈值: {{ confThreshold.toFixed(2) }}</label>
            <input type="range" v-model.number="confThreshold" min="0" max="1" step="0.05" />
          </div>
          <div class="param-item">
            <label>IOU阈值: {{ iouThreshold.toFixed(2) }}</label>
            <input type="range" v-model.number="iouThreshold" min="0" max="1" step="0.05" />
          </div>
        </div>
        
        <button class="btn-detect" @click="detect" :disabled="selectedFiles.length === 0 || isDetecting">
          {{ isDetecting ? '检测中... (' + progress + '%)' : '开始批量检测' }}
        </button>
      </div>
      
      <div class="results-section">
        <div class="results-header">
          <h3>检测结果</h3>
          <div class="results-actions">
            <span v-if="detectionResults" class="result-summary">
              共检测 {{ detectionResults.total_files }} 张图片
            </span>
            <button v-if="detectionResults" class="btn-download" @click="downloadResults">
              <img src="../assets/icons/download.svg" alt="Download" class="icon-svg" />
              <span>下载全部(压缩包)</span>
            </button>
          </div>
        </div>
        
        <div v-if="detectionResults" class="results-grid">
          <div v-for="(result, index) in detectionResults.results" :key="index" class="result-card">
            <img :src="result.result_image" class="result-image" />
            <div class="result-info">
              <span class="result-filename">{{ result.filename }}</span>
              <span class="result-count" :class="{ alert: result.detection_count > 0 }">
                {{ result.detection_count }} 个目标
              </span>
            </div>
            <div v-if="result.detection_count > 0" class="detection-tags">
              <span v-for="(det, idx) in result.detections" :key="idx" 
                    class="detection-tag" :class="det.class_name">
                {{ det.class_name_cn }} {{ (det.confidence * 100).toFixed(0) }}%
              </span>
            </div>
          </div>
        </div>
        
        <div v-else class="results-placeholder">
          <div class="placeholder-icon"><img src="../assets/icons/list.svg" alt="List" /></div>
          <p>检测结果将显示在这里</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { detectBatch } from '../utils/api'

const selectedFiles = ref([])
const previews = ref({})
const confThreshold = ref(0.25)
const iouThreshold = ref(0.45)
const isDetecting = ref(false)
const progress = ref(0)
const detectionResults = ref(null)

const MAX_FILES = 50

const selectFiles = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/jpeg,image/png,image/jpg,image/bmp'
  input.multiple = true
  input.onchange = (e) => {
    const newFiles = Array.from(e.target.files).filter(file => !selectedFiles.value.find(f => f.name === file.name))
    const remaining = MAX_FILES - selectedFiles.value.length
    
    if (newFiles.length > remaining) {
      alert(`最多只能选择${MAX_FILES}张图片，还能再选择${remaining}张`)
      newFiles.splice(remaining)
    }
    
    newFiles.forEach(file => {
      selectedFiles.value.push(file)
      loadPreview(file)
    })
    detectionResults.value = null
  }
  input.click()
}

const handleDrop = (e) => {
  const newFiles = Array.from(e.dataTransfer.files).filter(file => 
    file.type.startsWith('image/') && !selectedFiles.value.find(f => f.name === file.name)
  )
  const remaining = MAX_FILES - selectedFiles.value.length
  
  if (newFiles.length > remaining) {
    alert(`最多只能选择${MAX_FILES}张图片，还能再选择${remaining}张`)
    newFiles.splice(remaining)
  }
  
  newFiles.forEach(file => {
    selectedFiles.value.push(file)
    loadPreview(file)
  })
  detectionResults.value = null
}

const loadPreview = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    previews.value[file.name] = e.target.result
  }
  reader.readAsDataURL(file)
}

const getPreview = (file) => {
  return previews.value[file.name] || ''
}

const removeFile = (index) => {
  const file = selectedFiles.value[index]
  delete previews.value[file.name]
  selectedFiles.value.splice(index, 1)
}

const clearAll = () => {
  selectedFiles.value = []
  previews.value = {}
  detectionResults.value = null
}

const detect = async () => {
  if (selectedFiles.value.length === 0) return
  
  isDetecting.value = true
  progress.value = 0
  detectionResults.value = null
  
  try {
    const result = await detectBatch(selectedFiles.value, confThreshold.value, iouThreshold.value)
    detectionResults.value = result
    
    // 模拟进度
    let p = 0
    const interval = setInterval(() => {
      p += 10
      progress.value = Math.min(p, 100)
      if (p >= 100) clearInterval(interval)
    }, 100)
  } catch (error) {
    alert('批量检测失败: ' + error.message)
  } finally {
    isDetecting.value = false
    progress.value = 100
  }
}

const downloadResults = async () => {
  if (!detectionResults.value || !detectionResults.value.task_id) return
  
  try {
    const response = await fetch(`/api/detection/download/${detectionResults.value.task_id}`)
    const blob = await response.blob()
    
    const contentDisposition = response.headers.get('content-disposition')
    let filename = `batch_detection_${Date.now()}.zip`
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
</script>

<style scoped>
.batch-container {
  max-width: 1400px;
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

.main-content {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 24px;
}

.upload-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 80px;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 16px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 200px;
}

.upload-area:hover {
  border-color: #e74c3c;
  background: rgba(231, 76, 60, 0.05);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.upload-icon {
  margin-bottom: 12px;
}

.upload-icon img {
  width: 40px;
  height: 40px;
  color: #e74c3c;
}

.icon-svg {
  width: 16px;
  height: 16px;
  color: white;
}

.upload-placeholder p {
  color: #666;
  margin-bottom: 4px;
}

.upload-placeholder .hint {
  font-size: 12px;
  color: #999;
}

.files-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.file-preview-item {
  position: relative;
  width: 80px;
  height: 80px;
}

.preview-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

.preview-name {
  display: none;
}

.preview-remove {
  position: absolute;
  top: -5px;
  right: -5px;
  width: 20px;
  height: 20px;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.files-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 8px;
}

.btn-clear {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.params-section {
  margin-top: 20px;
}

.params-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
}

.param-item {
  margin-bottom: 16px;
}

.param-item label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.param-item input[type="range"] {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #ddd;
  outline: none;
}

.btn-detect {
  width: 100%;
  padding: 14px;
  margin-top: 20px;
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-detect:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(231, 76, 60, 0.4);
}

.btn-detect:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.results-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.results-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.results-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-summary {
  background: #f5f5f5;
  color: #666;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
}

.btn-download {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.btn-download:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(231, 76, 60, 0.4);
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.result-card {
  border: 1px solid #eee;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.result-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.result-image {
  width: 100%;
  height: 150px;
  object-fit: cover;
}

.result-info {
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-filename {
  font-size: 13px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.result-count {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #2ed573;
  color: white;
}

.result-count.alert {
  background: #ff4757;
}

.detection-tags {
  padding: 0 12px 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.detection-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 8px;
}

.detection-tag.smoke {
  background: #ffa502;
  color: white;
}

.detection-tag.fire {
  background: #ff4757;
  color: white;
}

.results-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.placeholder-icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

.placeholder-icon img {
  width: 60px;
  height: 60px;
  color: #666;
}

.results-placeholder p {
  color: #999;
  font-size: 16px;
}

@media (max-width: 1024px) {
  .main-content {
    grid-template-columns: 1fr;
  }
}
</style>
