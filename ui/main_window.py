"""
主窗口
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStackedWidget, QFrame,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from core.gesture_detector import GestureResult, GestureType
from core.input_simulator import InputSimulator
from core.gesture_mapping import GestureMappingManager
from ui.camera_preview import CameraPreview
from ui.gesture_config_panel import GestureConfigPanel
from ui.styles import get_stylesheet, COLORS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI体感控制系统")
        self.resize(1000, 700)
        
        # 初始化核心模块
        self.mapping_manager = GestureMappingManager()
        self.input_simulator = InputSimulator()
        
        self.setup_ui()
        self.apply_styles()
        
        # 状态变量
        self.is_controlling = False
        self.last_gesture = GestureType.NONE
        
    def setup_ui(self):
        # 主容器
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. 左侧侧边栏 (Navigation Rail/Drawer)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        # specific style moved to styles.py
        sidebar.setFixedWidth(260) 
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(8) # Space between nav items
        
        # App Title
        app_title = QLabel("Gesture\nControl")
        app_title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLORS['primary']}; margin-left: 16px; margin-bottom: 24px;")
        sidebar_layout.addWidget(app_title)
        
        # 导航按钮
        self.btn_preview = self.create_nav_button("摄像头预览")
        self.btn_preview.clicked.connect(lambda: self.switch_page(0))
        
        self.btn_config = self.create_nav_button("手势配置")
        self.btn_config.clicked.connect(lambda: self.switch_page(1))
        
        sidebar_layout.addWidget(self.btn_preview)
        sidebar_layout.addWidget(self.btn_config)
        sidebar_layout.addStretch()
        
        # 控制开关 (FAB style or Extended FAB)
        # We'll make it a large prominent button at the bottom of sidebar
        self.control_status_label = QLabel("控制已停止")
        self.control_status_label.setStyleSheet(f"color: {COLORS['on_surface_variant']}; font-size: 14px; margin-bottom: 5px;")
        self.control_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.control_status_label)
        
        self.btn_toggle_control = QPushButton("开始控制")
        self.btn_toggle_control.setCheckable(True)
        self.btn_toggle_control.clicked.connect(self.toggle_control)
        # Use primary container color for FAB look
        self.btn_toggle_control.setMinimumHeight(56)
        self.btn_toggle_control.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {COLORS['primary_container']}; 
                color: {COLORS['on_primary_container']};
                border-radius: 16px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:checked {{ 
                background-color: {COLORS['error_container']};
                color: {COLORS['error']};
            }}
            QPushButton:hover {{
                border: 1px solid {COLORS['primary']};
            }}
        """)
        sidebar_layout.addWidget(self.btn_toggle_control)
        
        main_layout.addWidget(sidebar)
        
        # 2. 右侧内容区
        self.content_stack = QStackedWidget()
        
        # Page 1: 预览页
        preview_page = QWidget()
        preview_layout = QVBoxLayout(preview_page)
        preview_layout.setContentsMargins(24, 24, 24, 24)
        preview_layout.setSpacing(20)
        
        # 头部状态栏
        status_bar = QFrame()
        status_bar.setObjectName("card") # Reuse card style
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(24, 16, 24, 16)
        
        self.detection_label = QLabel("当前手势: 无")
        self.detection_label.setStyleSheet("font-size: 20px; font-weight: 500;")
        
        self.action_feedback_label = QLabel("")
        self.action_feedback_label.setStyleSheet(f"color: {COLORS['primary']}; font-weight: 500;")
        
        status_layout.addWidget(self.detection_label)
        status_layout.addStretch()
        status_layout.addWidget(self.action_feedback_label)
        
        preview_layout.addWidget(status_bar)
        
        # 摄像头组件
        self.camera_view = CameraPreview()
        self.camera_view.gesture_detected.connect(self.on_gesture_detected)
        self.camera_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout.addWidget(self.camera_view)
        
        self.content_stack.addWidget(preview_page)
        
        # Page 2: 配置页
        self.config_panel = GestureConfigPanel(self.mapping_manager)
        self.config_panel.config_changed.connect(self.on_config_changed) # Connect signal
        self.content_stack.addWidget(self.config_panel)
        
        main_layout.addWidget(self.content_stack)
        
        # 初始化自定义手势
        self.update_gesture_templates()
        
    def create_nav_button(self, text):
        btn = QPushButton(text)
        btn.setObjectName("nav_item")
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn
        
    def apply_styles(self):
        self.setStyleSheet(get_stylesheet())
        self.btn_preview.setChecked(True)
        
    def switch_page(self, index):
        self.content_stack.setCurrentIndex(index)
        
    def toggle_control(self, checked):
        if checked:
            self.btn_toggle_control.setText("停止控制")
            self.control_status_label.setText("正在运行...")
            self.control_status_label.setStyleSheet("color: #1e8e3e; font-weight: bold;")
            self.is_controlling = True
            
            # 确保摄像头开启
            if not self.camera_view.is_running:
                self.camera_view.start_camera()
        else:
            self.btn_toggle_control.setText("开始控制")
            self.control_status_label.setText("控制已停止")
            self.control_status_label.setStyleSheet("color: #9aa0a6;")
            self.is_controlling = False
            self.last_gesture = GestureType.NONE
            
    def on_gesture_detected(self, results: list):
        if not results:
            return
            
        # 获取第一个手的结果
        result = results[0]
        gesture_type = result.gesture_type
        
        # 更新UI
        if gesture_type != GestureType.NONE:
            # 使用result.name显示，支持自定义名称
            self.detection_label.setText(f"当前手势: {result.name}")
        else:
            self.detection_label.setText("当前手势: 无")
            
        # 如果开启了控制，则执行动作
        if self.is_controlling:
            self.process_control(result.gesture_id)
            
    def process_control(self, gesture_id: str):
        # 获取映射配置
        # gesture_id = gesture_type.name.lower() # OLD
        mapping = self.mapping_manager.get_mapping(gesture_id)
        
        if mapping and mapping.enabled:
            # 执行动作
            success = self.input_simulator.execute_action(
                mapping.action_type, 
                mapping.action_value
            )
            
            if success:
                self.show_feedback(f"执行: {mapping.name} -> {mapping.action_value}")
                
    def show_feedback(self, text):
        self.action_feedback_label.setText(text)
        # 1秒后清除
        QTimer.singleShot(1000, lambda: self.action_feedback_label.clear())
        
    def on_config_changed(self):
        """配置变更处理"""
        self.update_gesture_templates()
        
    def update_gesture_templates(self):
        """更新手势识别器的模板和名称"""
        templates = self.mapping_manager.custom_gestures_data
        self.camera_view.update_custom_templates(templates)
        
        # 提取名称
        names = {}
        # 预定义手势
        for gid, _ in self.mapping_manager.PREDEFINED_GESTURES:
            m = self.mapping_manager.get_mapping(gid)
            if m: names[gid] = m.name
            
        # 自定义手势
        for gid in templates.keys():
            m = self.mapping_manager.get_mapping(gid)
            if m: names[gid] = m.name
            
        self.camera_view.update_gesture_names(names)
        
    def closeEvent(self, event):
        self.camera_view.stop_camera()
        super().closeEvent(event)
