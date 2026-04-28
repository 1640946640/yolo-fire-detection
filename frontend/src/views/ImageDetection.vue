
<template>
  <div class="detection-container">
    <div class="header-section">
      <h1>图片检测</h1>
      <p>上传单张图片进行火灾和烟雾检测</p>
    </div>
    
    <div class="main-content">
      <div class="left-panel">
        <div class="upload-area" @click="selectFile" @drop.prevent="handleDrop" @dragover.prevent>
          <div v-if="!selectedFile" class="upload-placeholder">
            <div class="upload-icon"><img src="../assets/icons/image.svg" alt="Camera" /></div>
            <p>点击或拖拽图片到此处</p>
            <p class="hint">支持 JPG、PNG、JPEG、BMP 格式</p>
          </div>
          <img v-else :src="previewImage" class="preview-image" />
        </div>
        
        <div v-if="selectedFile" class="file-info">
          <span class="file-name">{{ selectedFile.name }}</span>
          <button class="btn-remove" @click="clearFile">移除</button>
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
        
        <button class="btn-detect" @click="detect" :disabled="!selectedFile || isDetecting">
          {{ isDetecting ? '检测中...' : '开始检测' }}
        </button>
      </div>
      
      <div class="right-panel">
        <div class="result-header">
          <h3>检测结果</h3>
          <div class="result-actions">
            <span v-if="detectionResult" class="result-count">检测到 {{ detectionResult.detection_count }} 个目标</span>
            <button v-if="detectionResult" class="btn-download" @click="downloadResult">
              <img src="../assets/icons/download.svg" alt="Download" class="icon-svg" />
              <span>下载结果</span>
            </button>
          </div>
        </div>
        
        <div v-if="detectionResult" class="result-content">
          <img :src="detectionResult.result_image" class="result-image" />
          
          <div v-if="detectionResult.detections.length > 0" class="detection-list">
            <h4>检测详情</h4>
            <table class="detection-table">
              <thead>
                <tr>
                  <th>序号</th>
                  <th>类别</th>
                  <th>置信度</th>
                  <th>位置</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(det, index) in detectionResult.detections" :key="index">
                  <td>{{ index + 1 }}</td>
                  <td>
                    <span class="class-badge" :class="det.class_name">
                      {{ det.class_name_cn }}
                    </span>
                  </td>
                  <td>{{ (det.confidence * 100).toFixed(1) }}%</td>
                  <td>
                    ({{ det.bbox[0] }}, {{ det.bbox[1] }}) 
                    - ({{ det.bbox[2] }}, {{ det.bbox[3] }})
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div v-else class="no-detection">
            <div class="no-detection-icon"><img src="../assets/icons/check.svg" alt="Check" /></div>
            <p>未检测到火灾或烟雾</p>
          </div>
        </div>
        
        <div v-else class="result-placeholder">
          <div class="placeholder-icon"><img src="../assets/icons/search.svg" alt="Search" /></div>
          <p>检测结果将显示在这里</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { detectImage } from '../utils/api'

const selectedFile = ref(null)
const previewImage = ref('')
const confThreshold = ref(0.25)
const iouThreshold = ref(0.45)
const isDetecting = ref(false)
const detectionResult = ref(null)

const selectFile = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/jpeg,image/png,image/jpg,image/bmp'
  input.onchange = (e) => {
    handleFile(e.target.files[0])
  }
  input.click()
}

const handleDrop = (e) => {
  const file = e.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    handleFile(file)
  }
}

const handleFile = (file) => {
  selectedFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => {
    previewImage.value = e.target.result
  }
  reader.readAsDataURL(file)
  detectionResult.value = null
}

const clearFile = () => {
  selectedFile.value = null
  previewImage.value = ''
  detectionResult.value = null
}

const detect = async () => {
  if (!selectedFile.value) return
  
  isDetecting.value = true
  detectionResult.value = null
  
  try {
    const result = await detectImage(selectedFile.value, confThreshold.value, iouThreshold.value)
    console.log('Detection result:', result)
    console.log('Result image path:', result.result_image)
    detectionResult.value = result
  } catch (error) {
    alert('检测失败: ' + error.message)
  } finally {
    isDetecting.value = false
  }
}

const downloadResult = async () => {
  if (!detectionResult.value) return
  
  try {
    const response = await fetch(detectionResult.value.result_image)
    const blob = await response.blob()
    
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `detection_result_${Date.now()}.jpg`
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
.detection-container {
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
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.left-panel, .right-panel {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 300px;
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
  margin-bottom: 16px;
}

.upload-icon img {
  width: 50px;
  height: 50px;
  color: #e74c3c;
}

.icon-svg {
  width: 16px;
  height: 16px;
  color: white;
}

.upload-placeholder p {
  color: #666;
  margin-bottom: 8px;
}

.upload-placeholder .hint {
  font-size: 12px;
  color: #999;
}

.preview-image {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: 12px;
}

.file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 8px;
}

.file-name {
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.btn-remove {
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

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.result-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.result-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-count {
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
  color: white;
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

.result-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-image {
  max-width: 100%;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.detection-list h4 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.detection-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.detection-table th, .detection-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.detection-table th {
  background: #f5f5f5;
  font-weight: 600;
  color: #666;
}

.class-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.class-badge.smoke {
  background: #ffa502;
  color: white;
}

.class-badge.fire {
  background: #ff4757;
  color: white;
}

.no-detection {
  text-align: center;
  padding: 40px;
}

.no-detection-icon {
  margin-bottom: 16px;
}

.no-detection-icon img {
  width: 50px;
  height: 50px;
  color: #27ae60;
}

.no-detection p {
  color: #666;
  font-size: 16px;
}

.result-placeholder {
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

.result-placeholder p {
  color: #999;
  font-size: 16px;
}

@media (max-width: 1024px) {
  .main-content {
    grid-template-columns: 1fr;
  }
}
</style>
