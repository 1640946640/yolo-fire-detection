
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000
})

export const detectImage = async (file, confThreshold, iouThreshold) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('conf_threshold', confThreshold)
  formData.append('iou_threshold', iouThreshold)
  
  const response = await api.post('/detection/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export const detectBatch = async (files, confThreshold, iouThreshold) => {
  const formData = new FormData()
  files.forEach(file => formData.append('files', file))
  formData.append('conf_threshold', confThreshold)
  formData.append('iou_threshold', iouThreshold)
  
  const response = await api.post('/detection/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export const startTraining = async (epochs, batchSize, learningRate, dataConfig) => {
  const formData = new FormData()
  formData.append('epochs', epochs)
  formData.append('batch_size', batchSize)
  formData.append('learning_rate', learningRate)
  formData.append('data_config', dataConfig)
  
  const response = await api.post('/training/start', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export const getTrainingStatus = async (taskId) => {
  const response = await api.get(`/training/status/${taskId}`)
  return response.data
}

export const getAllTrainingTasks = async () => {
  const response = await api.get('/training/tasks')
  return response.data
}

export const stopTraining = async (taskId) => {
  const response = await api.post(`/training/stop/${taskId}`)
  return response.data
}

export const getConfig = async () => {
  const response = await api.get('/config')
  return response.data
}

export const healthCheck = async () => {
  const response = await api.get('/health')
  return response.data
}

export default api
