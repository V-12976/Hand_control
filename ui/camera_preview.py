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
    frame_captured = pyqtSignal(np.ndarray)
    
    def __init__(self, camera_source=0):
        super().__init__()
        self.camera = CameraCapture(camera_source)
        self.running = False
        
    def run(self):
        self.running = self.camera.start()
        while self.running:
            ret, frame = self.camera.read()
            if ret and frame is not None:
                self.frame_captured.emit(frame)
            else:
                self.msleep(10)
                
    def stop(self):
        self.running = False
        self.wait()
        self.camera.stop()
        
    def set_source(self, source):
        self.stop()
        self.camera = CameraCapture(source)

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
        
        self.detector = GestureDetector()
        self.worker = CameraWorker()
        self.worker.frame_captured.connect(self.process_frame)
        
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
        self.detector.set_custom_templates(templates)

    def update_gesture_names(self, names):
        """更新手势名称映射"""
        self.detector.set_gesture_names(names)

    @pyqtSlot(np.ndarray)
    def process_frame(self, frame):
        # 翻转镜像
        frame = cv2.flip(frame, 1)
        
        # 1. 手势检测处理
        annotated_frame, results = self.detector.process_frame(frame)
        
        # 2. 发送信号
        if results:
            self.gesture_detected.emit(results)
            
        # 3. 转换图像格式用于显示
        rgb_image = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # 4. 保持比例缩放
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        
    def closeEvent(self, event):
        self.stop_camera()
        self.detector.release()
        super().closeEvent(event)
