"""
自定义手势创建对话框
"""

import cv2
import time
import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from core.gesture_detector import GestureDetector, GestureResult
from ui.camera_preview import CameraWorker
from ui.styles import COLORS

class CreateGestureDialog(QDialog):
    """录制新手势对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("录制新手势")
        self.setFixedSize(680, 600)
        
        # 状态
        self.captured_landmarks = None
        self.is_counting_down = False
        self.countdown_val = 3
        
        self.detector = GestureDetector()
        self.worker = CameraWorker()
        self.worker.frame_captured.connect(self.process_frame)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 1. 顶部输入区
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("手势名称:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如: OK手势")
        input_layout.addWidget(self.name_input)
        layout.addLayout(input_layout)
        
        # 2. 摄像头预览区
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(f"background-color: black; border-radius: 12px; border: 1px solid {COLORS['outline_variant']};")
        self.image_label.setFixedSize(640, 400)
        layout.addWidget(self.image_label)
        
        # 3. 提示信息和倒计时
        self.info_label = QLabel("请将手放入画面中，摆好姿势后点击捕获")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet(f"color: {COLORS['on_surface_variant']}; font-size: 14px;")
        layout.addWidget(self.info_label)
        
        # 4. 按钮区
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("secondaryById")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.capture_btn = QPushButton("开始捕获 (3秒)")
        self.capture_btn.clicked.connect(self.start_capture)
        # Use primary style by default
        
        self.save_btn = QPushButton("保存手势")
        self.save_btn.clicked.connect(self.save_gesture)
        self.save_btn.setEnabled(False) # 初始不可用
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.capture_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)

    def start_camera(self):
        self.worker.start()
        
    def stop_camera(self):
        self.worker.stop()
        
    def showEvent(self, event):
        self.start_camera()
        super().showEvent(event)
        
    def closeEvent(self, event):
        self.stop_camera()
        self.detector.release()
        super().closeEvent(event)
        
    @pyqtSlot(QImage, list)
    def process_frame(self, qt_image, results):
        self.last_results = results # Store for capture
        self.last_qt_image = qt_image # Store for capture
        
        # 直接显示图像 (qt_image is already RGB QImage from worker)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
            self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
    
    def start_capture(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "提示", "请输入手势名称")
            return
            
        self.is_counting_down = True
        self.countdown_val = 3
        self.capture_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        
        self.update_countdown()
        
    def update_countdown(self):
        if self.countdown_val > 0:
            self.info_label.setText(f"将在 {self.countdown_val} 秒后捕获...")
            self.info_label.setStyleSheet(f"color: {COLORS['primary']}; font-size: 24px; font-weight: bold;")
            self.countdown_val -= 1
            QTimer.singleShot(1000, self.update_countdown)
        else:
            self.execute_capture()

    def execute_capture(self):
        self.is_counting_down = False
        
        # 直接使用最近的一帧数据
        # Accessing self.worker.camera.read() here is unsafe and redundant
        
        if hasattr(self, 'last_results') and self.last_results and hasattr(self, 'last_qt_image'):
             # 获取第一只手的关键点
            self.captured_landmarks = self.last_results[0].hand_landmarks.landmarks
            
            # 更新界面显示定格画面
            self.image_label.setPixmap(QPixmap.fromImage(self.last_qt_image).scaled(
                self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            
            # 暂停摄像头更新 (Worker stop will stop emitting signals)
            self.worker.stop()
            
            self.info_label.setText("捕获成功！请确认骨架是否准确")
            self.info_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 16px; font-weight: 500;")
            
            self.capture_btn.setText("重新捕获")
            self.capture_btn.setObjectName("secondaryById")
            self.capture_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            
            # 重新绑定捕获按钮事件为重置
            try:
                self.capture_btn.clicked.disconnect()
            except: pass
            self.capture_btn.clicked.connect(self.reset_capture)
        else:
            self.info_label.setText("未检测到手势，请重试")
            self.info_label.setStyleSheet(f"color: {COLORS['error']}; font-size: 16px; font-weight: 500;")
            self.capture_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.is_counting_down = False

    def reset_capture(self):
        self.captured_landmarks = None
        self.capture_btn.setText("开始捕获 (3秒)")
        self.capture_btn.setObjectName("")
        self.capture_btn.clicked.disconnect()
        self.capture_btn.clicked.connect(self.start_capture)
        self.save_btn.setEnabled(False)
        self.info_label.setText("请将手放入画面中，摆好姿势后点击捕获")
        self.info_label.setStyleSheet(f"color: {COLORS['on_surface_variant']}; font-size: 14px;")
        self.worker.start() # 恢复摄像头
        
    def save_gesture(self):
        if self.captured_landmarks:
            self.accept()
            
    def get_data(self):
        """返回 (名称, 关键点数据)"""
        return self.name_input.text().strip(), self.captured_landmarks

