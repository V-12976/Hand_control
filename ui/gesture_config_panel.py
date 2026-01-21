"""
手势配置面板
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, 
    QDialog, QComboBox, QLineEdit, QCheckBox,
    QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from core.gesture_mapping import GestureMappingManager, GestureMapping


class GestureEditDialog(QDialog):
    """手势编辑对话框"""
    def __init__(self, mapping: GestureMapping, parent=None):
        super().__init__(parent)
        self.mapping = mapping
        self.setWindowTitle("编辑手势映射")
        self.setFixedWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 手势名称（只读）
        layout.addWidget(QLabel("手势名称:"))
        self.name_label = QLabel(self.mapping.name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(self.name_label)
        
        layout.addSpacing(10)
        
        # 动作类型
        layout.addWidget(QLabel("动作类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["key", "key_combo", "mouse"])
        self.type_combo.setCurrentText(self.mapping.action_type)
        self.type_combo.currentTextChanged.connect(self.update_value_placeholder)
        layout.addWidget(self.type_combo)
        
        # 动作值
        layout.addWidget(QLabel("动作值:"))
        self.value_input = QLineEdit()
        self.value_input.setText(self.mapping.action_value)
        layout.addWidget(self.value_input)
        
        self.helper_label = QLabel("例如: 'space', 'enter', 'a'")
        self.helper_label.setStyleSheet("color: #9aa0a6; font-size: 12px;")
        layout.addWidget(self.helper_label)
        
        layout.addSpacing(20)
        
        # 按钮
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryById")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        self.update_value_placeholder(self.mapping.action_type)
        
    def update_value_placeholder(self, type_text):
        if type_text == "key":
            self.helper_label.setText("例如: space, enter, esc, a, 1")
        elif type_text == "key_combo":
            self.helper_label.setText("例如: ctrl+c, alt+tab")
        elif type_text == "mouse":
            self.helper_label.setText("支持: left_click, right_click, scroll_up, scroll_down")
            
    def get_data(self):
        return {
            'action_type': self.type_combo.currentText(),
            'action_value': self.value_input.text().strip()
        }


from ui.create_gesture_dialog import CreateGestureDialog

class GestureItemWidget(QFrame):
    """单个手势配置项的Widget"""
    edit_clicked = pyqtSignal(str) # gesture_id
    toggle_clicked = pyqtSignal(str, bool) # gesture_id, enabled
    delete_clicked = pyqtSignal(str) # gesture_id
    
    def __init__(self, mapping: GestureMapping, is_custom: bool = False):
        super().__init__()
        self.mapping = mapping
        self.is_custom = is_custom
        self.setObjectName("card")
        self.setup_ui()
        
    def setup_ui(self):
        self.setMinimumHeight(100)  # Ensure card has enough height
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 信息部分
        info_layout = QVBoxLayout()
        name_label = QLabel(self.mapping.name)
        name_label.setObjectName("title")
        
        action_text = f"{self.mapping.action_type}: {self.mapping.action_value}"
        action_label = QLabel(action_text)
        action_label.setObjectName("subtitle")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(action_label)
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # 控制部分
        self.enable_cb = QCheckBox("启用")
        self.enable_cb.setChecked(self.mapping.enabled)
        self.enable_cb.toggled.connect(
            lambda checked: self.toggle_clicked.emit(self.mapping.id, checked)
        )
        layout.addWidget(self.enable_cb)
        
        if self.is_custom:
            delete_btn = QPushButton("删除")
            delete_btn.setObjectName("dangerById")
            # delete_btn.setFixedWidth(60) # Removing to fix padding issue
            delete_btn.clicked.connect(
                lambda: self.delete_clicked.emit(self.mapping.id)
            )
            layout.addWidget(delete_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.setObjectName("secondaryById")
        edit_btn.setFixedWidth(80)
        edit_btn.clicked.connect(
            lambda: self.edit_clicked.emit(self.mapping.id)
        )
        layout.addWidget(edit_btn)


class GestureConfigPanel(QWidget):
    """手势配置主面板"""
    config_changed = pyqtSignal() # 配置变更信号
    
    def __init__(self, mapping_manager: GestureMappingManager):
        super().__init__()
        self.manager = mapping_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 头部
        header_layout = QHBoxLayout()
        title = QLabel("手势映射配置")
        title.setObjectName("title")
        header_layout.addWidget(title)
        
        new_btn = QPushButton("+ 新建手势")
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self.create_new_gesture)
        header_layout.addWidget(new_btn)
        
        header_layout.addStretch()
        
        reset_btn = QPushButton("重置默认")
        reset_btn.setObjectName("secondaryById")
        reset_btn.clicked.connect(self.reset_defaults)
        header_layout.addWidget(reset_btn)
        
        layout.addLayout(header_layout)
        
        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(10) # Add spacing between items
        layout.addWidget(self.list_widget)
        
        self.refresh_list()
        
    def refresh_list(self):
        self.list_widget.clear()
        mappings = self.manager.get_all_mappings()
        
        # 获取所有自定义手势ID
        custom_ids = self.manager.custom_gestures_data.keys()
        
        for mapping in mappings:
            # 如果是预定义手势，且我们想要隐藏它们(虽然用户无法修改enable_predefined_gestures，但UI应该配合)
            # 用户要求 "也许可以除去预设手势"，与其彻底删除数据，不如在列表中隐藏
            is_custom = mapping.id in custom_ids
            if not is_custom:
                continue
                
            widget = GestureItemWidget(mapping, is_custom)
            widget.edit_clicked.connect(self.open_edit_dialog)
            widget.toggle_clicked.connect(self.toggle_mapping)
            widget.delete_clicked.connect(self.delete_gesture)
            
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(widget.minimumSizeHint()) # Use minimum size hint
            
            self.list_widget.setItemWidget(item, widget)
            
    def create_new_gesture(self):
        dialog = CreateGestureDialog(self)
        if dialog.exec():
            name, landmarks = dialog.get_data()
            if landmarks:
                self.manager.add_custom_gesture(name, landmarks)
                self.refresh_list()
                self.config_changed.emit()
                
    def delete_gesture(self, gesture_id):
        reply = QMessageBox.question(
            self, '确认删除', 
            "确定要删除这个自定义手势吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete_custom_gesture(gesture_id)
            self.refresh_list()
            self.config_changed.emit()

    def open_edit_dialog(self, gesture_id):
        mapping = self.manager.get_mapping(gesture_id)
        if not mapping:
            return
            
        dialog = GestureEditDialog(mapping, self)
        if dialog.exec():
            data = dialog.get_data()
            self.manager.update_mapping(
                gesture_id, 
                data['action_type'], 
                data['action_value']
            )
            self.manager.save()
            self.refresh_list()
            self.config_changed.emit()
            
    def toggle_mapping(self, gesture_id, enabled):
        self.manager.set_enabled(gesture_id, enabled)
        self.manager.save()
        self.config_changed.emit()
        
    def reset_defaults(self):
        reply = QMessageBox.question(
            self, '确认重置', 
            "确定要重置所有手势映射为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.manager._create_default_mappings()
            self.manager.save()
            self.refresh_list()
            self.config_changed.emit()
