
# -*- coding: utf-8 -*-
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
from ultralytics import YOLO
from PIL import ImageFont
import cv2
import numpy as np
import os
import uuid
import shutil
import json
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import subprocess
import threading
from datetime import datetime
import imageio_ffmpeg as ffmpeg

# 导入数据库模块
from .database import init_db, add_detection_record, get_all_records, get_record_by_task_id, delete_record

# 初始化数据库
init_db()

# 初始化FastAPI应用
app = FastAPI(title="YOLO火灾检测API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "best.pt")
# 获取项目根目录（backend目录的父目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_PATH = os.path.join(BASE_DIR, "static", "results")
STATIC_DIR = os.path.join(BASE_DIR, "static")
CONF_THRES = 0.25
IOU_THRES = 0.45
DEVICE = "cuda:0" if cv2.cuda.getCudaEnabledDeviceCount() > 0 else "cpu"

# 确保目录存在
os.makedirs(SAVE_PATH, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "models"), exist_ok=True)

# 加载模型
model = YOLO(MODEL_PATH, task='detect')
model(np.zeros((48, 48, 3)), device=DEVICE)  # 预热模型

def create_collage(image_paths, output_path, max_images=50):
    """将多张图片合成为网格图"""
    # 限制最大图片数量
    image_paths = image_paths[:max_images]
    num_images = len(image_paths)
    
    if num_images == 0:
        return
    
    # 计算网格布局
    rows = int(np.ceil(np.sqrt(num_images)))
    cols = int(np.ceil(num_images / rows))
    
    # 读取所有图片并调整大小
    images = []
    target_size = (200, 200)  # 每张缩略图的大小
    
    for path in image_paths:
        try:
            img = cv2.imread(path)
            if img is not None:
                img = cv2.resize(img, target_size)
                images.append(img)
        except Exception as e:
            print(f"[WARN] Failed to read image {path}: {e}")
    
    if not images:
        return
    
    # 创建空白画布
    collage_width = cols * target_size[0]
    collage_height = rows * target_size[1]
    collage = np.zeros((collage_height, collage_width, 3), dtype=np.uint8)
    
    # 填充图片
    for i, img in enumerate(images):
        row = i // cols
        col = i % cols
        y = row * target_size[1]
        x = col * target_size[0]
        collage[y:y+target_size[1], x:x+target_size[0]] = img
    
    # 保存合成图
    cv2.imwrite(output_path, collage)
    print(f"[DEBUG] Created collage: {output_path}")

# 类别名称
names = {0: 'smoke', 1: 'fire'}
CH_names = ['烟雾', '火焰']

class DetectionParams(BaseModel):
    conf_threshold: Optional[float] = CONF_THRES
    iou_threshold: Optional[float] = IOU_THRES
    show_labels: Optional[bool] = True

class TrainingConfig(BaseModel):
    epochs: Optional[int] = 100
    batch_size: Optional[int] = 16
    learning_rate: Optional[float] = 0.001
    data_config: Optional[str] = "datasets/data.yaml"

# 训练任务状态存储
training_tasks = {}
# 训练进程存储（用于停止训练）
training_processes = {}
# SSE订阅者存储
sse_subscribers = {}

# 静态文件服务
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    return {"message": "YOLO火灾检测API服务运行中"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "device": DEVICE}

@app.get("/api/config")
async def get_config():
    return {
        "conf_threshold": CONF_THRES,
        "iou_threshold": IOU_THRES,
        "device": DEVICE,
        "model_path": MODEL_PATH,
        "classes": [{"id": k, "name": v, "name_cn": CH_names[k]} for k, v in names.items()]
    }

@app.post("/api/detection/image")
async def detect_image(
    file: UploadFile = File(...),
    conf_threshold: float = Form(CONF_THRES),
    iou_threshold: float = Form(IOU_THRES)
):
    try:
        # 读取图片
        contents = await file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        # 执行检测
        results = model(image, conf=conf_threshold, iou=iou_threshold, device=DEVICE)[0]
        
        # 处理检测结果
        detections = []
        if results.boxes is not None:
            for box in results.boxes:
                detections.append({
                    "class_id": int(box.cls.item()),
                    "class_name": names[int(box.cls.item())],
                    "class_name_cn": CH_names[int(box.cls.item())],
                    "confidence": round(float(box.conf.item()), 4),
                    "bbox": [int(x) for x in box.xyxy.tolist()[0]]
                })
        
        # 生成带检测框的图片
        annotated_image = results.plot()
        
        # 保存结果图片
        task_id = str(uuid.uuid4())
        result_path = os.path.join(SAVE_PATH, f"{task_id}.jpg")
        cv2.imwrite(result_path, annotated_image)
        
        # 检查文件是否保存成功
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"[DEBUG] Image detection completed. Output: {result_path}, Size: {file_size} bytes")
        else:
            print(f"[ERROR] Image output file not created: {result_path}")
        
        # 统计烟雾和火焰数量
        smoke_count = sum(1 for d in detections if d["class_name"] == "smoke")
        fire_count = sum(1 for d in detections if d["class_name"] == "fire")
        
        # 保存到数据库
        add_detection_record(
            task_id=task_id,
            type_="image",
            filename=file.filename,
            result_path=f"/static/results/{task_id}.jpg",
            detection_count=len(detections),
            smoke_count=smoke_count,
            fire_count=fire_count
        )
        
        return {
            "task_id": task_id,
            "status": "success",
            "detection_count": len(detections),
            "detections": detections,
            "result_image": f"/static/results/{task_id}.jpg"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/detection/batch")
async def detect_batch(
    files: List[UploadFile] = File(...),
    conf_threshold: float = Form(CONF_THRES),
    iou_threshold: float = Form(IOU_THRES)
):
    # 限制最多50张图片
    MAX_FILES = 50
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"最多支持一次性上传{MAX_FILES}张图片，当前上传了{len(files)}张")
    
    results = []
    task_id = str(uuid.uuid4())
    batch_dir = os.path.join(SAVE_PATH, task_id)
    os.makedirs(batch_dir, exist_ok=True)
    
    # 保存所有处理后的图片路径用于合成
    processed_images = []
    
    # 统计变量
    total_detections = 0
    total_smoke_count = 0
    total_fire_count = 0
    
    for file in files:
        try:
            contents = await file.read()
            np_arr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # 检测
            result = model(image, conf=conf_threshold, iou=iou_threshold, device=DEVICE)[0]
            
            detections = []
            if result.boxes is not None:
                for box in result.boxes:
                    detections.append({
                        "class_id": int(box.cls.item()),
                        "class_name": names[int(box.cls.item())],
                        "class_name_cn": CH_names[int(box.cls.item())],
                        "confidence": round(float(box.conf.item()), 4),
                        "bbox": [int(x) for x in box.xyxy.tolist()[0]]
                    })
            
            # 统计
            smoke_count = sum(1 for d in detections if d["class_name"] == "smoke")
            fire_count = sum(1 for d in detections if d["class_name"] == "fire")
            total_detections += len(detections)
            total_smoke_count += smoke_count
            total_fire_count += fire_count
            
            # 保存结果
            annotated_image = result.plot()
            filename = f"{uuid.uuid4()}_{file.filename}"
            save_path = os.path.join(batch_dir, filename)
            cv2.imwrite(save_path, annotated_image)
            processed_images.append(save_path)
            
            results.append({
                "filename": file.filename,
                "detection_count": len(detections),
                "detections": detections,
                "result_image": f"/static/results/{task_id}/{filename}"
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    # 生成合成图
    combined_image_path = os.path.join(batch_dir, "combined.jpg")
    if processed_images:
        create_collage(processed_images, combined_image_path)
    
    combined_image_url = f"/static/results/{task_id}/combined.jpg"
    
    # 保存到数据库（批量检测使用第一个文件作为代表）
    if files:
        first_filename = files[0].filename
        if len(files) > 1:
            first_filename = f"{first_filename} 等{len(files)}个文件"
        add_detection_record(
            task_id=task_id,
            type_="batch",
            filename=first_filename,
            result_path=combined_image_url,
            detection_count=total_detections,
            smoke_count=total_smoke_count,
            fire_count=total_fire_count
        )
    
    return {
        "task_id": task_id,
        "status": "success",
        "total_files": len(files),
        "combined_image": combined_image_url,
        "results": results
    }

@app.post("/api/training/start")
async def start_training(
    epochs: int = Form(100),
    batch_size: int = Form(16),
    learning_rate: float = Form(0.001),
    data_config: str = Form("datasets/data.yaml")
):
    # 构建绝对路径
    data_config_path = os.path.join(BASE_DIR, data_config)
    if not os.path.exists(data_config_path):
        raise HTTPException(status_code=400, detail=f"数据配置文件不存在: {data_config_path}")
    
    try:
        task_id = str(uuid.uuid4())
        
        # 初始化训练任务状态
        training_tasks[task_id] = {
            "status": "running",
            "epochs": epochs,
            "current_epoch": 0,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "data_config": data_config,
            "progress": 0,
            "log": "",
            "result": None,
            "error": None
        }
        
        # 在后台执行训练
        asyncio.create_task(run_training(task_id, epochs, batch_size, learning_rate, data_config_path))
        
        return {
            "task_id": task_id,
            "status": "training_started",
            "message": "训练任务已启动"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/training/status/{task_id}")
async def get_training_status(task_id: str):
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    return training_tasks[task_id]

@app.get("/api/training/tasks")
async def get_all_training_tasks():
    return list(training_tasks.keys())

@app.post("/api/training/stop/{task_id}")
async def stop_training(task_id: str):
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    if task_id not in training_processes:
        raise HTTPException(status_code=400, detail="没有正在运行的训练进程")
    
    try:
        process = training_processes[task_id]
        # 终止进程
        process.terminate()
        process.wait(timeout=5)
        
        # 更新状态
        training_tasks[task_id]["status"] = "stopped"
        training_tasks[task_id]["log"] += "\n训练已被用户停止\n"
        
        # 清理进程引用
        del training_processes[task_id]
        
        return {"status": "success", "message": "训练已停止"}
    except subprocess.TimeoutExpired:
        # 强制终止
        process.kill()
        process.wait()
        training_tasks[task_id]["status"] = "stopped"
        training_tasks[task_id]["log"] += "\n训练已被强制停止\n"
        del training_processes[task_id]
        return {"status": "success", "message": "训练已强制停止"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/training/logs/{task_id}")
async def stream_training_logs(task_id: str):
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    # 创建一个队列用于SSE
    queue = asyncio.Queue()
    
    # 注册订阅者
    if task_id not in sse_subscribers:
        sse_subscribers[task_id] = []
    sse_subscribers[task_id].append(queue)
    
    # 发送当前日志
    current_log = training_tasks[task_id]["log"]
    if current_log:
        await queue.put(current_log)
    
    async def event_generator():
        try:
            while True:
                # 获取新日志
                log_chunk = await queue.get()
                if log_chunk:
                    yield f"data: {json.dumps({'log': log_chunk, 'task_id': task_id})}\n\n"
                
                # 检查任务是否结束
                if task_id in training_tasks:
                    status = training_tasks[task_id]["status"]
                    if status in ["completed", "error", "stopped"]:
                        yield f"data: {json.dumps({'log': '', 'task_id': task_id, 'finished': True})}\n\n"
                        break
                else:
                    break
        finally:
            # 清理订阅者
            if task_id in sse_subscribers and queue in sse_subscribers[task_id]:
                sse_subscribers[task_id].remove(queue)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

async def run_training(task_id: str, epochs: int, batch_size: int, lr: float, data_config: str):
    global model
    try:
        # 在线程池中运行训练，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        
        def training_task():
            global model
            import subprocess
            import threading
            
            try:
                # 更新初始状态
                if task_id in training_tasks:
                    training_tasks[task_id]["log"] = "开始训练...\n"
                
                # 使用subprocess运行训练，实时捕获输出
                # 将路径中的反斜杠替换为正斜杠，避免Unicode转义错误
                base_dir = BASE_DIR.replace('\\', '/')
                model_path = MODEL_PATH.replace('\\', '/')
                data_config_path = data_config.replace('\\', '/')
                
                cmd = [
                    'python', '-c',
                    f'''
import sys
sys.path.insert(0, "{base_dir}")
from ultralytics import YOLO
model = YOLO("{model_path}", task="detect")
results = model.train(
    data="{data_config_path}",
    epochs={epochs},
    batch={batch_size},
    lr0={lr},
    device="{DEVICE}",
    verbose=True
)
                    '''
                ]
                
                # 创建进程，设置编码为utf-8
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # 保存进程引用，以便停止训练
                training_processes[task_id] = process
                
                # 实时读取输出
                def read_output():
                    for line in iter(process.stdout.readline, ''):
                        if line and task_id in training_tasks:
                            training_tasks[task_id]["log"] += line
                            # 尝试解析进度 - 匹配格式如 "2/100"
                            try:
                                import re
                                # 查找类似 "2/100" 或 "Epoch 2/100" 的模式
                                match = re.search(r'(\d+)/(\d+)', line)
                                if match:
                                    current = int(match.group(1))
                                    total = int(match.group(2))
                                    # 验证是否是epoch格式（通常epoch不会太大）
                                    if total == epochs and current <= total:
                                        training_tasks[task_id]["current_epoch"] = current
                                        training_tasks[task_id]["progress"] = int((current / epochs) * 100)
                            except:
                                pass
                            
                            # SSE推送日志更新
                            if task_id in sse_subscribers:
                                for queue in sse_subscribers[task_id]:
                                    try:
                                        queue.put_nowait(line)
                                    except:
                                        pass
                
                # 在后台线程中读取输出
                output_thread = threading.Thread(target=read_output)
                output_thread.start()
                
                # 等待训练完成
                process.wait()
                output_thread.join()
                
                # 清理进程引用
                if task_id in training_processes:
                    del training_processes[task_id]
                
                # 更新训练状态为完成
                if task_id in training_tasks:
                    if process.returncode == 0:
                        training_tasks[task_id]["status"] = "completed"
                        training_tasks[task_id]["progress"] = 100
                        training_tasks[task_id]["current_epoch"] = epochs
                        training_tasks[task_id]["log"] += "\n训练完成!\n"
                        
                        # 保存训练后的模型
                        save_dir = os.path.join(BASE_DIR, "models", f"trained_{task_id}")
                        os.makedirs(save_dir, exist_ok=True)
                        
                        # 复制最佳模型
                        best_model = os.path.join(BASE_DIR, "runs", "detect", "train", "weights", "best.pt")
                        model_path = ""
                        if os.path.exists(best_model):
                            shutil.copy(best_model, os.path.join(save_dir, "best.pt"))
                            model_path = f"models/trained_{task_id}/best.pt"
                            # 更新全局模型
                            model = YOLO(os.path.join(save_dir, "best.pt"), task='detect')
                        
                        training_tasks[task_id]["result"] = {
                            "loss": 0,
                            "map50": 0,
                            "map": 0,
                            "modelPath": model_path
                        }
                    else:
                        training_tasks[task_id]["status"] = "error"
                        training_tasks[task_id]["error"] = "训练过程出错"
            
            except Exception as e:
                if task_id in training_tasks:
                    training_tasks[task_id]["status"] = "error"
                    training_tasks[task_id]["error"] = str(e)
                    training_tasks[task_id]["log"] += f"\n训练失败: {e}\n"
        
        # 使用线程池执行训练任务
        await loop.run_in_executor(None, training_task)
    
    except Exception as e:
        if task_id in training_tasks:
            training_tasks[task_id]["status"] = "error"
            training_tasks[task_id]["error"] = str(e)
            training_tasks[task_id]["log"] += f"\n训练失败: {e}\n"
        print(f"训练失败: {e}")

# 视频检测任务状态
video_tasks = {}

# 视频上传状态（用于存储上传后的视频信息，尚未开始检测）
video_uploads = {}

@app.post("/api/detection/video/upload")
async def upload_video(
    video_file: UploadFile = File(...)
):
    """上传视频文件（仅上传，不检测）"""
    task_id = str(uuid.uuid4())
    result_dir = os.path.join(BASE_DIR, "static", "results", task_id)
    os.makedirs(result_dir, exist_ok=True)
    
    # 保存上传的视频
    video_path = os.path.join(result_dir, "input.mp4")
    with open(video_path, "wb") as f:
        f.write(await video_file.read())
    
    # 记录上传信息
    video_uploads[task_id] = {
        "video_path": video_path,
        "result_dir": result_dir,
        "filename": video_file.filename,
        "uploaded_at": datetime.now().isoformat()
    }
    
    return {
        "task_id": task_id,
        "status": "uploaded",
        "message": "视频上传成功"
    }

@app.post("/api/detection/video/start")
async def start_video_detection(
    task_id: str = Form(...),
    conf_threshold: float = Form(0.25),
    iou_threshold: float = Form(0.45)
):
    """开始视频检测（需先上传视频）"""
    global model
    
    # 检查是否已上传
    if task_id not in video_uploads:
        raise HTTPException(status_code=400, detail="请先上传视频")
    
    upload_info = video_uploads[task_id]
    video_path = upload_info["video_path"]
    result_dir = upload_info["result_dir"]
    
    # 初始化任务状态
    video_tasks[task_id] = {
        "status": "running",
        "progress": 0,
        "total_frames": 0,
        "processed_frames": 0,
        "result_video": None,
        "total_detections": 0,
        "smoke_count": 0,
        "fire_count": 0,
        "sample_frames": [],
        "error": None,
        "cancelled": False  # 添加取消标志
    }
    
    # 使用线程池在后台执行视频检测，避免阻塞事件循环
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, process_video_sync, task_id, video_path, result_dir, conf_threshold, iou_threshold)
    
    return {
        "task_id": task_id,
        "status": "started"
    }

def process_video_sync(task_id, video_path, result_dir, conf_threshold, iou_threshold):
    """同步版本的视频处理函数，在单独线程中运行"""
    global model
    
    try:
        # 使用OpenCV读取视频
        cap = cv2.VideoCapture(video_path)
        
        # 获取视频参数
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 120:
            fps = 30  # 默认帧率
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        video_tasks[task_id]["total_frames"] = total_frames
        
        # 使用imageio-ffmpeg创建兼容浏览器的视频
        output_path = os.path.join(result_dir, "output.mp4")
        
        # 获取ffmpeg可执行文件路径
        ffmpeg_path = ffmpeg.get_ffmpeg_exe()
        print(f"[DEBUG] Using ffmpeg: {ffmpeg_path}")
        
        # 创建临时文件保存所有帧
        frames_temp_dir = os.path.join(result_dir, "frames")
        os.makedirs(frames_temp_dir, exist_ok=True)
        
        total_detections = 0
        smoke_count = 0
        fire_count = 0
        frame_index = 0
        saved_frames = []
        
        while cap.isOpened():
            # 检查是否被取消
            if task_id in video_tasks and video_tasks[task_id].get("cancelled", False):
                video_tasks[task_id]["status"] = "cancelled"
                cap.release()
                # 清理临时文件
                shutil.rmtree(frames_temp_dir, ignore_errors=True)
                return
            
            ret, frame = cap.read()
            if not ret:
                break
            
            # 使用YOLO进行检测
            results = model.predict(
                source=frame,
                conf=conf_threshold,
                iou=iou_threshold,
                verbose=False
            )
            
            # 绘制检测框
            for result in results:
                for box in result.boxes:
                    total_detections += 1
                    cls = int(box.cls[0])
                    if cls == 0:
                        smoke_count += 1
                        color = (0, 255, 255)  # 黄色 - 烟雾
                        label = "smoke"
                    else:
                        fire_count += 1
                        color = (0, 0, 255)  # 红色 - 火焰
                        label = "fire"
                    
                    # 获取边界框坐标
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    # 绘制矩形框
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    # 绘制标签
                    cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # 保存帧到临时目录
            frame_file = os.path.join(frames_temp_dir, f"frame_{frame_index:06d}.png")
            cv2.imwrite(frame_file, frame)
            
            # 保存示例帧
            if frame_index % (total_frames // 3) == 0 and len(saved_frames) < 3:
                frame_path = os.path.join(result_dir, f"frame_{frame_index}.jpg")
                cv2.imwrite(frame_path, frame)
                saved_frames.append({
                    "index": frame_index,
                    "count": len(results[0].boxes),
                    "image": f"/static/results/{task_id}/frame_{frame_index}.jpg"
                })
            
            frame_index += 1
            progress = int((frame_index / total_frames) * 100)
            video_tasks[task_id]["progress"] = progress
            video_tasks[task_id]["processed_frames"] = frame_index
        
        cap.release()
        
        # 使用ffmpeg将帧合并成视频
        print(f"[DEBUG] Starting ffmpeg video encoding...")
        
        # 使用imageio-ffmpeg创建视频 - 将帧存储为临时文件然后用ffmpeg合并
        frame_pattern = os.path.join(frames_temp_dir, "frame_%06d.png")
        
        # 使用subprocess调用ffmpeg命令行，确保兼容性
        ffmpeg_path = ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg_path,
            '-framerate', str(fps),
            '-i', frame_pattern,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            '-preset', 'medium',
            '-y',  # 覆盖输出文件
            output_path
        ]
        
        print(f"[DEBUG] Running ffmpeg command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[ERROR] ffmpeg failed: {result.stderr}")
                raise Exception(f"ffmpeg encoding failed: {result.stderr}")
            else:
                print(f"[DEBUG] ffmpeg encoding succeeded")
        except Exception as e:
            print(f"[ERROR] ffmpeg error: {str(e)}")
            raise
        
        # 清理临时文件
        shutil.rmtree(frames_temp_dir, ignore_errors=True)
        
        # 检查输出文件是否存在
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"[DEBUG] Video processing completed. Output: {output_path}, Size: {file_size} bytes")
        else:
            print(f"[ERROR] Video output file not created: {output_path}")
        
        # 再次检查是否被取消
        if task_id in video_tasks and video_tasks[task_id].get("cancelled", False):
            video_tasks[task_id]["status"] = "cancelled"
            return
        
        video_tasks[task_id]["status"] = "completed"
        video_tasks[task_id]["result_video"] = f"/static/results/{task_id}/output.mp4"
        video_tasks[task_id]["total_detections"] = total_detections
        video_tasks[task_id]["smoke_count"] = smoke_count
        video_tasks[task_id]["fire_count"] = fire_count
        video_tasks[task_id]["sample_frames"] = saved_frames
        
        # 保存到数据库
        add_detection_record(
            task_id=task_id,
            type_="video",
            filename="input.mp4",
            result_path=f"/static/results/{task_id}/output.mp4",
            detection_count=total_detections,
            smoke_count=smoke_count,
            fire_count=fire_count
        )
        
    except Exception as e:
        if task_id in video_tasks and not video_tasks[task_id].get("cancelled", False):
            video_tasks[task_id]["status"] = "error"
            video_tasks[task_id]["error"] = str(e)

async def process_video(task_id, video_path, result_dir, conf_threshold, iou_threshold):
    """异步包装版本，保持向后兼容"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, process_video_sync, task_id, video_path, result_dir, conf_threshold, iou_threshold)

@app.get("/api/detection/video/status/{task_id}")
async def get_video_status(task_id: str):
    if task_id not in video_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    return video_tasks[task_id]

@app.post("/api/detection/video/cancel/{task_id}")
async def cancel_video_detection(task_id: str):
    if task_id not in video_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = video_tasks[task_id]
    if task["status"] not in ["running"]:
        raise HTTPException(status_code=400, detail="任务不在运行中")
    
    # 设置取消标志
    video_tasks[task_id]["cancelled"] = True
    
    return {"status": "success", "message": "已发送取消请求"}

@app.get("/api/detection/download/{task_id}")
async def download_result(task_id: str):
    # 构建结果目录路径
    result_dir = os.path.join(BASE_DIR, "static", "results", task_id)
    
    if not os.path.exists(result_dir):
        raise HTTPException(status_code=404, detail="检测结果不存在")
    
    # 检查是否有视频文件
    video_path = os.path.join(result_dir, "output.mp4")
    if os.path.exists(video_path):
        # 视频检测，直接下载视频文件
        return FileResponse(
            path=video_path,
            filename=f"{task_id}_detection.mp4",
            media_type="video/mp4"
        )
    
    # 查找目录中的图片文件
    files_in_dir = []
    for root, dirs, files in os.walk(result_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                files_in_dir.append(os.path.join(root, file))
    
    if len(files_in_dir) == 1:
        # 单张图片直接下载
        file_path = files_in_dir[0]
        filename = f"{task_id}_result.jpg"
        media_type = "image/jpeg"
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
    else:
        # 多张图片打包成zip
        import zipfile
        import io
        
        # 使用内存中的BytesIO创建zip
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_in_dir:
                # 使用相对路径作为arcname，避免完整路径
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname)
        
        # 重置缓冲区位置
        zip_buffer.seek(0)
        
        filename = f"{task_id}_detection.zip"
        media_type = "application/zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": media_type
            }
        )
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )

@app.get("/api/detection/history")
async def get_detection_history():
    records = get_all_records()
    return {"records": records}

@app.delete("/api/detection/history/{task_id}")
async def delete_history_record(task_id: str):
    # 删除数据库记录
    delete_record(task_id)
    
    # 删除文件
    dir_path = os.path.join(BASE_DIR, "static", "results", task_id)
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    
    return {"status": "success", "message": "记录已删除"}

@app.delete("/api/detection/results/{task_id}")
async def delete_result(task_id: str):
    try:
        # 检查是否是目录（批量检测）
        dir_path = os.path.join(SAVE_PATH, task_id)
        if os.path.isdir(dir_path):
            shutil.rmtree(dir_path)
            return {"status": "success", "message": "批量检测结果已删除"}
        
        # 检查是否是文件（单张图片检测）
        file_path = os.path.join(SAVE_PATH, f"{task_id}.jpg")
        if os.path.isfile(file_path):
            os.remove(file_path)
            return {"status": "success", "message": "检测结果已删除"}
        
        raise HTTPException(status_code=404, detail="检测结果不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
