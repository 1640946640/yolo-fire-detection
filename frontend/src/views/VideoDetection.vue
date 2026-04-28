
<template>
  <div class="video-container">
    <div class="header-section">
      <h1>视频检测</h1>
      <p>上传视频文件进行逐帧火灾和烟雾检测</p>
    </div>
    
    <div class="main-content">
      <div class="left-panel">
        <div class="upload-area" 
             @click="selectVideo" 
             @drop.prevent="handleDrop" 
             @dragover.prevent
             :class="{ uploading: isUploading }">
          <div v-if="!selectedVideo && !isUploading" class="upload-placeholder">
            <div class="upload-icon"><img src="../assets/icons/video.svg" alt="Video" /></div>
            <p>点击或拖拽视频到此处</p>
            <p class="hint">支持 MP4、AVI、MOV 格式</p>
          </div>
          <div v-else-if="isUploading" class="upload-progress">
            <div class="upload-icon"><img src="../assets/icons/upload.svg" alt="Upload" /></div>
            <p>正在上传视频...</p>
            <div class="upload-progress-bar">
              <div class="upload-progress-fill" :style="{ width: uploadProgress + '%' }"></div>
            </div>
            <p class="upload-percent">{{ uploadProgress }}%</p>
          </div>
          <div v-else class="video-info">
            <div class="video-icon"><img src="../assets/icons/video.svg" alt="Video" /></div>
            <span>{{ selectedVideo.name }}</span>
            <span class="upload-success"><img src="../assets/icons/check.svg" alt="Check" class="icon-svg" /> 上传完成</span>
          </div>
        </div>
        
        <div v-if="selectedVideo && !isUploading" class="video-controls">
          <button class="btn-remove" @click="clearVideo">移除视频</button>
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
        
        <button class="btn-upload" 
                @click="uploadVideo" 
                :disabled="!selectedVideo || isUploading || isDetecting || isUploaded">
          {{ isUploading ? '上传中...' : (isUploaded ? '已上传' : '上传视频') }}
        </button>
        
        <button class="btn-detect" 
                @click="detect" 
                :disabled="!isUploaded || isDetecting">
          {{ isDetecting ? '检测中...' : '开始检测' }}
        </button>
      </div>
      
      <div class="right-panel">
        <div class="result-header">
          <h3>检测预览</h3>
          <button v-if="detectionResult" class="btn-download" @click="downloadVideo">
            <img src="../assets/icons/download.svg" alt="Download" class="icon-svg" />
            <span>下载视频</span>
          </button>
        </div>
        
        <div v-if="selectedVideo && !isDetecting && !isUploading" class="video-preview">
          <video 
            :key="videoUrl" 
            :src="videoUrl" 
            controls 
            class="video-player" 
            playsinline 
            muted
            autoplay
            loop
            preload="auto"
            @error="handleVideoError"
            @loadedmetadata="handleVideoLoaded"
          />
        </div>
        
        <div v-if="isDetecting" class="detection-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          </div>
          <div class="progress-info">
            <p>正在处理视频帧... {{ progress }}%</p>
            <button class="btn-cancel" @click="cancelDetection">
              <img src="../assets/icons/video.svg" alt="Stop" class="icon-svg" />
              <span>取消检测</span>
            </button>
          </div>
        </div>
        
        <div v-if="detectionResult" class="detection-stats">
          <h4>检测统计</h4>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">总帧数</span>
              <span class="stat-value">{{ totalFrames }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">检测目标</span>
              <span class="stat-value highlight">{{ totalDetections }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">烟雾数量</span>
              <span class="stat-value smoke">{{ smokeCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">火焰数量</span>
              <span class="stat-value fire">{{ fireCount }}</span>
            </div>
          </div>
          
          <div class="sample-frames">
            <h4>检测帧示例</h4>
            <div class="frames-grid">
              <div v-for="(frame, index) in sampleFrames" :key="index" class="frame-item">
                <img :src="frame.image" class="frame-image" />
                <span class="frame-info">帧 {{ frame.index }}: {{ frame.count }} 个目标</span>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="!selectedVideo && !detectionResult" class="result-placeholder">
          <div class="placeholder-icon"><img src="../assets/icons/video.svg" alt="Video" /></div>
          <p>上传视频后开始检测</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const selectedVideo = ref(null)
const videoUrl = ref('')
const confThreshold = ref(0.25)
const iouThreshold = ref(0.45)
const isDetecting = ref(false)
const isUploading = ref(false)
const isUploaded = ref(false)
const uploadProgress = ref(0)
const progress = ref(0)
const detectionResult = ref(null)

// 模拟视频检测结果
const totalFrames = ref(0)
const totalDetections = ref(0)
const smokeCount = ref(0)
const fireCount = ref(0)
const sampleFrames = ref([])

let pollInterval = null
const currentTaskId = ref(null)

const selectVideo = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'video/mp4,video/avi,video/mov'
  input.onchange = (e) => {
    handleVideo(e.target.files[0])
  }
  input.click()
}

const handleDrop = (e) => {
  const file = e.dataTransfer.files[0]
  if (file && file.type.startsWith('video/')) {
    handleVideo(file)
  }
}

const handleVideo = (file) => {
  selectedVideo.value = file
  videoUrl.value = URL.createObjectURL(file)
  detectionResult.value = null
  isUploaded.value = false
  currentTaskId.value = null
}

const handleVideoError = (e) => {
  console.error('Video playback error:', e)
  console.error('Error details:', e.target.error)
  alert(`视频播放失败: ${e.target.error?.message || '未知错误'}`)
}

const handleVideoLoaded = (e) => {
  console.log('Video loaded successfully:', e.target.duration, 'seconds')
}

const loadVideoBlob = async (videoPath) => {
  try {
    console.log('Loading video blob from:', videoPath)
    const response = await fetch(videoPath)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const blob = await response.blob()
    console.log('Video blob loaded, size:', blob.size, 'bytes')
    console.log('Blob type:', blob.type)
    
    // 释放之前的URL
    if (videoUrl.value) {
      URL.revokeObjectURL(videoUrl.value)
    }
    
    // 创建新的object URL
    videoUrl.value = URL.createObjectURL(blob)
    console.log('New video URL created:', videoUrl.value)
  } catch (error) {
    console.error('Failed to load video blob:', error)
    alert('加载检测视频失败: ' + error.message)
  }
}

const clearVideo = () => {
  selectedVideo.value = null
  videoUrl.value = ''
  detectionResult.value = null
  isUploaded.value = false
  currentTaskId.value = null
  uploadProgress.value = 0
}

const uploadVideo = async () => {
  if (!selectedVideo.value) return
  
  isUploading.value = true
  uploadProgress.value = 0
  
  try {
    const formData = new FormData()
    formData.append('video_file', selectedVideo.value)
    
    // 使用XMLHttpRequest获取上传进度
    const xhr = new XMLHttpRequest()
    xhr.open('POST', '/api/detection/video/upload')
    
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        uploadProgress.value = Math.round((e.loaded / e.total) * 100)
      }
    })
    
    xhr.addEventListener('load', () => {
      if (xhr.status === 200) {
        const result = JSON.parse(xhr.responseText)
        currentTaskId.value = result.task_id
        isUploaded.value = true
        uploadProgress.value = 100
      } else {
        alert('上传失败: ' + xhr.responseText)
      }
      isUploading.value = false
    })
    
    xhr.addEventListener('error', () => {
      alert('上传失败')
      isUploading.value = false
    })
    
    xhr.send(formData)
    
  } catch (error) {
    alert('上传失败: ' + error.message)
    isUploading.value = false
  }
}

const detect = async () => {
  if (!currentTaskId.value) return
  
  isDetecting.value = true
  progress.value = 0
  detectionResult.value = null
  
  try {
    const formData = new FormData()
    formData.append('task_id', currentTaskId.value)
    formData.append('conf_threshold', confThreshold.value)
    formData.append('iou_threshold', iouThreshold.value)
    
    // 启动检测任务
    const response = await fetch('/api/detection/video/start', {
      method: 'POST',
      body: formData
    })
    
    const result = await response.json()
    
    // 轮询获取进度
    pollInterval = setInterval(async () => {
      try {
        const statusResponse = await fetch(`/api/detection/video/status/${currentTaskId.value}`)
        const status = await statusResponse.json()
        
        progress.value = status.progress
        totalFrames.value = status.total_frames
        
        if (status.status === 'completed') {
          clearInterval(pollInterval)
          
          smokeCount.value = status.smoke_count
          fireCount.value = status.fire_count
          totalDetections.value = status.total_detections
          sampleFrames.value = status.sample_frames
          
          // 更新视频预览为检测后的视频 - 使用blob方式加载
          await loadVideoBlob(status.result_video)
          
          detectionResult.value = status
          isDetecting.value = false
        } else if (status.status === 'error') {
          clearInterval(pollInterval)
          alert('视频检测失败: ' + status.error)
          isDetecting.value = false
        } else if (status.status === 'cancelled') {
          clearInterval(pollInterval)
          alert('检测已取消')
          isDetecting.value = false
        }
      } catch (error) {
        console.error('获取检测状态失败:', error)
      }
    }, 1000)
    
  } catch (error) {
    alert('视频检测失败: ' + error.message)
    isDetecting.value = false
  }
}

const downloadVideo = async () => {
  if (!currentTaskId.value) return
  
  try {
    const response = await fetch(`/api/detection/download/${currentTaskId.value}`)
    const blob = await response.blob()
    
    const contentDisposition = response.headers.get('content-disposition')
    let filename = `detection_video_${Date.now()}.mp4`
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

const cancelDetection = async () => {
  if (!currentTaskId.value) return
  
  try {
    const response = await fetch(`/api/detection/video/cancel/${currentTaskId.value}`, {
      method: 'POST'
    })
    
    if (response.ok) {
      alert('已发送取消请求，检测将在当前帧处理完成后停止')
    } else {
      const result = await response.json()
      alert('取消失败: ' + result.detail)
    }
  } catch (error) {
    alert('取消失败: ' + error.message)
  }
}
</script>

<style scoped>
.video-container {
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

.video-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.video-icon {
}

.video-icon img {
  width: 40px;
  height: 40px;
  color: #e74c3c;
}

.video-info span {
  color: #333;
  font-weight: 500;
}

.video-info .upload-success {
  font-size: 14px;
  color: #2ed573;
  font-weight: 500;
}

.upload-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.upload-progress-bar {
  width: 100%;
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
}

.upload-progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #2ed573 0%, #7bed9f 100%);
  transition: width 0.3s ease;
}

.upload-percent {
  font-size: 14px;
  color: #2ed573;
  font-weight: 600;
}

.video-controls {
  margin-top: 16px;
}

.btn-remove {
  width: 100%;
  padding: 10px;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 8px;
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

.btn-upload {
  width: 100%;
  padding: 14px;
  margin-top: 20px;
  background: linear-gradient(135deg, #2ed573 0%, #7bed9f 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-upload:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(46, 213, 115, 0.4);
}

.btn-upload:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-detect {
  width: 100%;
  padding: 14px;
  margin-top: 12px;
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

.video-preview {
  width: 100%;
}

.video-player {
  width: 100%;
  border-radius: 12px;
  max-height: 400px;
}

.detection-progress {
  padding: 20px;
  text-align: center;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background: #eee;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
  transition: width 0.3s ease;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-cancel {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s ease;
}

.btn-cancel:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(231, 76, 60, 0.4);
}

.detection-progress p {
  color: #666;
}

.detection-stats {
  margin-top: 20px;
}

.detection-stats h4 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 12px;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #333;
}

.stat-value.highlight {
  color: #ff4757;
}

.stat-value.smoke {
  color: #ffa502;
}

.stat-value.fire {
  color: #ff4757;
}

.sample-frames {
  margin-top: 20px;
}

.sample-frames h4 {
  margin-bottom: 12px;
}

.frames-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.frame-item {
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
}

.frame-image {
  width: 100%;
  height: 100px;
  object-fit: cover;
}

.frame-info {
  display: block;
  padding: 8px;
  font-size: 12px;
  color: #666;
  text-align: center;
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
