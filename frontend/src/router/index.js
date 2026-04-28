
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import ImageDetection from '../views/ImageDetection.vue'
import BatchDetection from '../views/BatchDetection.vue'
import VideoDetection from '../views/VideoDetection.vue'
import Training from '../views/Training.vue'
import History from '../views/History.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/detection/image',
    name: 'ImageDetection',
    component: ImageDetection
  },
  {
    path: '/detection/batch',
    name: 'BatchDetection',
    component: BatchDetection
  },
  {
    path: '/detection/video',
    name: 'VideoDetection',
    component: VideoDetection
  },
  {
    path: '/training',
    name: 'Training',
    component: Training
  },
  {
    path: '/history',
    name: 'History',
    component: History
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
