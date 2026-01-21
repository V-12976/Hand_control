"""
摄像头预览组件
"""

import cv2
import numpy as np
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget, QSizePolicy
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QTimer, QThread
from PyQt6.QtGui import QImage, QPixmap
from core.gesture_detector import GestureDetector, CameraCapture, GestureResult


class CameraWorker(QThread):
    """摄像头工作线程，避免UI卡顿"""
    frame_captured = pyqtSignal(QImage, list)  # 发送 (QImage, results)
    
    def __init__(self, camera_source=0):
        super().__init__()
        self.source = camera_source
        self.camera = None 
        self.running = False
        self.detector = None 
        
        # 缓存配置
        self._pending_custom_templates = None
        self._pending_gesture_names = None
        
        # 性能控制
        self.fps_limit = 30
        self.frame_delay_ms = int(1000 / self.fps_limit)
        
    def run(self):
        # 在子线程中初始化
        if self.camera is None:
            self.camera = CameraCapture(self.source)
        
        if self.detector is None:
            self.detector = GestureDetector()
            if self._pending_custom_templates:
                self.detector.set_custom_templates(self._pending_custom_templates)
            if self._pending_gesture_names:
                self.detector.set_gesture_names(self._pending_gesture_names)
            
        self.running = self.camera.start()
        
        last_frame_time = 0
        
        while self.running:
            # 简单的FPS控制
            current_time = cv2.getTickCount() / cv2.getTickFrequency() * 1000
            if current_time - last_frame_time < self.frame_delay_ms:
                self.msleep(5)
                continue
            
            last_frame_time = current_time
            
            ret, frame = self.camera.read()
            if ret and frame is not None:
                # 图像预处理 (翻转)
                frame = cv2.flip(frame, 1)
                
                # 执行检测 (耗时操作)
                annotated_frame, results = self.detector.process_frame(frame)
                
                # --- 子线程处理图像转换，减轻UI线程负担 ---
                
                # 1. 调整大小 (可选，减少传输数据量)
                # target_h = 480
                # h, w = annotated_frame.shape[:2]
                # if h > target_h:
                #     scale = target_h / h
                #     annotated_frame = cv2.resize(annotated_frame, (int(w*scale), int(h*scale)))
                
                # 2. 转换为QImage
                rgb_image = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                
                #以此方式创建的QImage共享内存，必须copy以分离所有权
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
                
                # 发送结果
                self.frame_captured.emit(qt_image, results)
            else:
                self.msleep(10)
        
        # 停止后资源释放
        if self.camera:
            self.camera.stop()
        
        # 显式释放Detector资源
        if self.detector:
            self.detector.release()
            self.detector = None
                
    def stop(self):
        self.running = False
        self.wait()
        
    def set_source(self, source):
        self.stop()
        self.source = source
        self.camera = None 
        
    def update_custom_templates(self, templates):
        """更新自定义手势模板 (线程安全)"""
        if self.detector:
            self.detector.set_custom_templates(templates)
        else:
            self._pending_custom_templates = templates

    def update_gesture_names(self, names):
        """更新手势名称映射 (线程安全)"""
        if self.detector:
            self.detector.set_gesture_names(names)
        else:
            self._pending_gesture_names = names
            
    def cleanup(self):
        """清理资源"""
        self.stop()

class CameraPreview(QWidget):
    """
    摄像头预览窗口
    - 显示实时视频流
    - 叠加手势骨架
    - 显示当前识别结果
    """
    
    gesture_detected = pyqtSignal(list)  # 发送识别到的手势结果
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # self.detector removed from here
        self.worker = CameraWorker()
        self.worker.frame_captured.connect(self.process_frame)
        self.worker.finished.connect(self.on_worker_finished)
        
        self.is_running = False
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 视频显示标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setMinimumSize(640, 480)
        self.image_label.setStyleSheet("background-color: #000; border-radius: 8px;")
        self.image_label.setText("摄像头未启动")
        
        self.layout.addWidget(self.image_label)
        
    def start_camera(self):
        if not self.is_running:
            self.worker.start()
            self.is_running = True
            self.image_label.setText("正在启动摄像头...")
            
    def stop_camera(self):
        if self.is_running:
            self.worker.stop()
            self.is_running = False
            self.image_label.setText("摄像头已停止")
            self.image_label.clear()
            
    def set_camera_source(self, source):
        self.worker.set_source(source)
        if self.is_running:
            self.start_camera()

    def update_custom_templates(self, templates):
        """更新自定义手势模板"""
        self.worker.update_custom_templates(templates)

    def update_gesture_names(self, names):
        """更新手势名称映射"""
        self.worker.update_gesture_names(names)

    @pyqtSlot(QImage, list)
    def process_frame(self, qt_image, results):
        """
        处理每一帧 (在主线程运行，但只负责UI绘制)
        Args:
            qt_image: 已经转换好的QImage
            results: 识别结果
        """
        # 1. 转发识别结果
        if results:
            self.gesture_detected.emit(results)
            
        # 2. 直接显示图像
        try:
            # 3. 保持比例缩放
            # Tip: 使用ScaledContents可能更快，但可能不保持比例。
            # 这里继续使用Pixmap缩放，但源数据已经是QImage了。
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error displaying frame: {e}")
            
    def on_worker_finished(self):
        pass
        
    def closeEvent(self, event):
        self.stop_camera()
        self.worker.cleanup() # Ensure cleanup
        super().closeEvent(event)
