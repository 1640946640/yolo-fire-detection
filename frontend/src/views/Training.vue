
<template>
  <div class="training-container">
    <div class="header-section">
      <h1>模型训练</h1>
      <p>使用自定义数据集训练YOLO火灾检测模型</p>
    </div>
    
    <div class="main-content">
      <div class="config-panel">
        <h3>训练配置</h3>
        
        <div class="config-item">
          <label>训练轮数 (Epochs)</label>
          <input type="number" v-model.number="epochs" min="1" max="500" />
          <span class="config-hint">建议值: 50-200</span>
        </div>
        
        <div class="config-item">
          <label>批次大小 (Batch Size)</label>
          <input type="number" v-model.number="batchSize" min="1" max="64" />
          <span class="config-hint">根据GPU显存调整</span>
        </div>
        
        <div class="config-item">
          <label>学习率 (Learning Rate)</label>
          <input type="number" v-model.number="learningRate" step="0.0001" min="0.0001" max="0.1" />
          <span class="config-hint">默认: 0.001</span>
        </div>
        
        <div class="config-item">
          <label>数据集配置文件</label>
          <input type="text" v-model="dataConfig" placeholder="datasets/data.yaml" />
          <button class="btn-browse" @click="browseConfig">浏览</button>
        </div>
        
        <div class="dataset-info">
          <h4>数据集要求</h4>
          <ul>
            <li>数据集格式: YOLO格式</li>
            <li>目录结构: train/images, train/labels, val/images, val/labels</li>
            <li>配置文件: data.yaml</li>
          </ul>
        </div>
        
        <div class="button-group">
          <button class="btn-train" @click="train" :disabled="isTraining">
            {{ isTraining ? '训练中...' : '开始训练' }}
          </button>
          <button v-if="isTraining" class="btn-stop" @click="stopTrain">
            停止训练
          </button>
        </div>
      </div>
      
      <div class="status-panel">
        <div class="status-header">
          <h3>训练状态</h3>
          <span v-if="trainingStatus" :class="['status-badge', trainingStatus]">
            {{ statusText }}
          </span>
        </div>
        
        <div v-if="isTraining" class="training-progress">
          <div class="progress-bar-large">
            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          </div>
          <div class="progress-info">
            <span>Epoch {{ currentEpoch }} / {{ epochs }}</span>
            <span>进度: {{ progress }}%</span>
          </div>
        </div>
        
        <div v-if="trainingLog" class="training-log">
          <h4>训练日志</h4>
          <pre>{{ trainingLog }}</pre>
        </div>
        
        <div v-if="trainingResult" class="training-result">
          <h4>训练完成</h4>
          <div class="result-stats">
            <div class="result-item">
              <span class="result-label">训练损失</span>
              <span class="result-value">{{ trainingResult.loss.toFixed(4) }}</span>
            </div>
            <div class="result-item">
              <span class="result-label">mAP@0.5</span>
              <span class="result-value">{{ (trainingResult.map50 * 100).toFixed(2) }}%</span>
            </div>
            <div class="result-item">
              <span class="result-label">mAP@0.5:0.95</span>
              <span class="result-value">{{ (trainingResult.map * 100).toFixed(2) }}%</span>
            </div>
          </div>
          <div class="model-info">
            <p>模型已保存到: <span class="model-path">{{ trainingResult.modelPath }}</span></p>
          </div>
        </div>
        
        <div v-if="!isTraining && !trainingResult" class="status-placeholder">
          <div class="placeholder-icon"><img src="../assets/icons/settings.svg" alt="Settings" /></div>
          <p>配置训练参数后开始训练</p>
          <p class="hint">训练时间取决于数据集大小和配置</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { startTraining, getTrainingStatus, stopTraining } from '../utils/api'

const epochs = ref(100)
const batchSize = ref(16)
const learningRate = ref(0.001)
const dataConfig = ref('datasets/data.yaml')
const isTraining = ref(false)
const trainingStatus = ref('idle')
const progress = ref(0)
const currentEpoch = ref(0)
const trainingLog = ref('')
const trainingResult = ref(null)
const taskId = ref(null)

let pollInterval = null
let eventSource = null

const statusText = computed(() => {
  const texts = {
    idle: '未开始',
    running: '训练中',
    completed: '已完成',
    stopped: '已停止',
    error: '错误'
  }
  return texts[trainingStatus.value] || '未知'
})

const browseConfig = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.yaml,.yml'
  input.onchange = (e) => {
    if (e.target.files[0]) {
      dataConfig.value = e.target.files[0].name
    }
  }
  input.click()
}

const startPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
  pollInterval = setInterval(async () => {
    try {
      const status = await getTrainingStatus(taskId.value)
      updateTrainingStatus(status)
    } catch (error) {
      console.error('获取训练状态失败:', error)
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

const updateTrainingStatus = (status) => {
  if (status) {
    trainingStatus.value = status.status
    progress.value = status.progress || 0
    currentEpoch.value = status.current_epoch || 0
    trainingLog.value = status.log || ''
    trainingResult.value = status.result || null
    
    if (status.status === 'completed' || status.status === 'error' || status.status === 'stopped') {
      isTraining.value = false
      stopPolling()
      stopSSE()
      localStorage.removeItem('training_task_id')
    }
  }
}

const startSSE = () => {
  // 关闭之前的连接
  stopSSE()
  
  // 创建SSE连接
  eventSource = new EventSource(`/api/training/logs/${taskId.value}`)
  
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.log) {
        trainingLog.value += data.log
      }
      if (data.finished) {
        stopSSE()
        // 刷新状态
        getTrainingStatus(taskId.value).then(updateTrainingStatus)
      }
    } catch (error) {
      console.error('解析SSE消息失败:', error)
    }
  }
  
  eventSource.onerror = (error) => {
    console.error('SSE连接错误:', error)
    eventSource.close()
  }
}

const stopSSE = () => {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

const train = async () => {
  isTraining.value = true
  trainingStatus.value = 'running'
  progress.value = 0
  currentEpoch.value = 0
  trainingLog.value = ''
  trainingResult.value = null
  
  try {
    const response = await startTraining(epochs.value, batchSize.value, learningRate.value, dataConfig.value)
    taskId.value = response.task_id
    
    // 保存任务ID到localStorage，以便页面刷新或切换后恢复
    localStorage.setItem('training_task_id', taskId.value)
    
    // 开始轮询状态（用于进度）
    startPolling()
    
    // 开始SSE接收日志
    startSSE()
    
  } catch (error) {
    trainingStatus.value = 'error'
    trainingLog.value += `训练失败: ${error.message}`
    alert('训练失败: ' + error.message)
    isTraining.value = false
  }
}

const stopTrain = async () => {
  if (!taskId.value || !isTraining.value) return
  
  try {
    const response = await stopTraining(taskId.value)
    alert(response.message)
    // 停止轮询和SSE
    stopPolling()
    stopSSE()
    isTraining.value = false
    trainingStatus.value = 'stopped'
    localStorage.removeItem('training_task_id')
  } catch (error) {
    console.error('停止训练失败:', error)
    alert('停止训练失败: ' + error.message)
  }
}

const checkExistingTraining = async () => {
  // 检查是否有正在进行的训练任务
  const savedTaskId = localStorage.getItem('training_task_id')
  if (savedTaskId) {
    try {
      const status = await getTrainingStatus(savedTaskId)
      taskId.value = savedTaskId
      updateTrainingStatus(status)
      
      if (status.status === 'running') {
        isTraining.value = true
        startPolling()
        startSSE()
      }
    } catch (error) {
      // 任务不存在，清除存储
      localStorage.removeItem('training_task_id')
    }
  }
}

onMounted(() => {
  checkExistingTraining()
})

onUnmounted(() => {
  stopPolling()
  stopSSE()
})
</script>

<style scoped>
.training-container {
  max-width: 1000px;
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
  grid-template-columns: 400px 1fr;
  gap: 24px;
}

.config-panel {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.config-panel h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.config-item {
  margin-bottom: 20px;
}

.config-item label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.config-item input[type="number"],
.config-item input[type="text"] {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.config-hint {
  display: block;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.btn-browse {
  margin-top: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.dataset-info {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 12px;
  margin-top: 20px;
}

.dataset-info h4 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
}

.dataset-info ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.dataset-info li {
  font-size: 13px;
  color: #666;
  padding: 4px 0;
  padding-left: 20px;
  position: relative;
}

.dataset-info li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #2ed573;
}

.btn-train {
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

.btn-train:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(231, 76, 60, 0.4);
}

.btn-train:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn-stop {
  flex: 1;
  padding: 14px;
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-stop:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(231, 76, 60, 0.4);
}

.status-panel {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.status-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.status-badge.idle {
  background: #eee;
  color: #666;
}

.status-badge.running {
  background: #ffa502;
  color: white;
}

.status-badge.completed {
  background: #2ed573;
  color: white;
}

.status-badge.error {
  background: #ff4757;
  color: white;
}

.training-progress {
  margin-bottom: 20px;
}

.progress-bar-large {
  width: 100%;
  height: 20px;
  background: #eee;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #e74c3c 0%, #f39c12 100%);
  transition: width 0.3s ease;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #666;
}

.training-log {
  background: #1a1a2e;
  padding: 16px;
  border-radius: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.training-log h4 {
  color: #fff;
  font-size: 14px;
  margin-bottom: 12px;
}

.training-log pre {
  color: #ccc;
  font-size: 13px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.training-result {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 12px;
}

.training-result h4 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
}

.result-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.result-item {
  text-align: center;
}

.result-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.result-value {
  font-size: 20px;
  font-weight: 700;
  color: #e74c3c;
}

.model-info {
  padding-top: 16px;
  border-top: 1px solid #ddd;
}

.model-info p {
  font-size: 14px;
  color: #666;
}

.model-path {
  color: #e74c3c;
  font-family: monospace;
}

.status-placeholder {
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

.status-placeholder p {
  color: #666;
  font-size: 16px;
  margin-bottom: 8px;
}

.status-placeholder .hint {
  font-size: 14px;
  color: #999;
}

@media (max-width: 1024px) {
  .main-content {
    grid-template-columns: 1fr;
  }
}
</style>
