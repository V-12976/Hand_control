"""
手势映射管理模块
负责手势与动作的映射配置管理
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class GestureMapping:
    """手势映射配置"""
    id: str              # 手势ID（如 'fist', 'open_palm'）
    name: str            # 显示名称（如 '握拳'）
    action_type: str     # 动作类型（'key', 'key_combo', 'mouse'）
    action_value: str    # 动作值（如 'space', 'ctrl+c', 'left_click'）
    enabled: bool = True # 是否启用
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GestureMapping':
        return cls(**data)


class GestureMappingManager:
    """
    手势映射管理器
    负责加载、保存和管理手势映射配置
    """
    
    # 预定义手势列表
    PREDEFINED_GESTURES = [
        ('fist', '握拳'),
        ('open_palm', '张开手掌'),
        ('thumbs_up', '竖起大拇指'),
        ('victory', '胜利手势'),
        ('point_up', '竖起食指'),
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化映射管理器
        
        Args:
            config_path: 配置文件路径，默认为项目config目录
        """
        if config_path is None:
            # 默认配置路径
            project_root = Path(__file__).parent.parent
            config_path = project_root / 'config' / 'config.json'
        
        self.config_path = Path(config_path)
        self.mappings: Dict[str, GestureMapping] = {}
        self._custom_gestures_data: Dict[str, List[Tuple[float, float, float]]] = {}
        self._settings: dict = {}
        
        # 加载配置
        self.load()
    
    @property
    def custom_gestures_data(self) -> Dict[str, List[Tuple[float, float, float]]]:
        """获取所有自定义手势的数据(关键点)"""
        return self._custom_gestures_data

    def load(self) -> bool:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 加载设置
                self._settings = {
                    'camera_source': data.get('camera_source', 0),
                    'detection_confidence': data.get('detection_confidence', 0.7),
                    'tracking_confidence': data.get('tracking_confidence', 0.5),
                    'theme': data.get('theme', 'dark'),
                }
                
                # 加载自定义手势数据
                # 格式: {id: [[x,y,z], ...]}
                self._custom_gestures_data = {}
                for gid, landmarks in data.get('custom_gestures_data', {}).items():
                    self._custom_gestures_data[gid] = [tuple(lm) for lm in landmarks]
                
                # 加载手势映射
                self.mappings.clear()
                for mapping_data in data.get('gesture_mappings', []):
                    mapping = GestureMapping.from_dict(mapping_data)
                    self.mappings[mapping.id] = mapping
                
                return True
        except Exception as e:
            print(f"加载配置失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 使用默认配置
        self._custom_gestures_data = {}
        self._create_default_mappings()
        return False
    
    def save(self) -> bool:
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                **self._settings,
                'custom_gestures_data': self._custom_gestures_data,
                'gesture_mappings': [m.to_dict() for m in self.mappings.values()]
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
        return False

    def add_custom_gesture(self, name: str, landmarks: List[Tuple[float, float, float]]) -> str:
        """
        添加自定义手势
        
        Args:
            name: 手势名称
            landmarks: 关键点数据
            
        Returns:
            生成的gesture_id
        """
        import time
        # 生成唯一ID
        gesture_id = f"custom_{int(time.time())}"
        
        # 保存数据
        self._custom_gestures_data[gesture_id] = landmarks
        
        # 创建默认映射
        self.mappings[gesture_id] = GestureMapping(
            id=gesture_id,
            name=name,
            action_type="key",
            action_value="",
            enabled=True
        )
        
        self.save()
        return gesture_id
        
    def delete_custom_gesture(self, gesture_id: str) -> bool:
        """删除自定义手势"""
        if gesture_id in self._custom_gestures_data:
            del self._custom_gestures_data[gesture_id]
            if gesture_id in self.mappings:
                del self.mappings[gesture_id]
            self.save()
            return True
        return False
    
    def _create_default_mappings(self):
        """创建默认映射"""
        default_actions = {
            'fist': ('key', 'space'),
            'open_palm': ('key', 'escape'),
            'thumbs_up': ('key', 'enter'),
            'victory': ('key', 'v'),
            'point_up': ('mouse', 'left_click'),
        }
        
        self.mappings.clear()
        for gesture_id, name in self.PREDEFINED_GESTURES:
            action_type, action_value = default_actions.get(gesture_id, ('key', 'space'))
            self.mappings[gesture_id] = GestureMapping(
                id=gesture_id,
                name=name,
                action_type=action_type,
                action_value=action_value,
                enabled=True
            )
    
    def get_mapping(self, gesture_id: str) -> Optional[GestureMapping]:
        """获取指定手势的映射"""
        return self.mappings.get(gesture_id)
    
    def update_mapping(self, gesture_id: str, action_type: str, action_value: str, enabled: bool = True) -> bool:
        """
        更新手势映射
        
        Args:
            gesture_id: 手势ID
            action_type: 动作类型
            action_value: 动作值
            enabled: 是否启用
            
        Returns:
            是否成功更新
        """
        if gesture_id in self.mappings:
            self.mappings[gesture_id].action_type = action_type
            self.mappings[gesture_id].action_value = action_value
            self.mappings[gesture_id].enabled = enabled
            return True
        return False
    
    def set_enabled(self, gesture_id: str, enabled: bool) -> bool:
        """启用或禁用手势"""
        if gesture_id in self.mappings:
            self.mappings[gesture_id].enabled = enabled
            return True
        return False
    
    def get_all_mappings(self) -> List[GestureMapping]:
        """获取所有映射"""
        return list(self.mappings.values())
    
    def get_enabled_mappings(self) -> Dict[str, GestureMapping]:
        """获取所有启用的映射"""
        return {k: v for k, v in self.mappings.items() if v.enabled}
    
    @property
    def camera_source(self) -> int:
        return self._settings.get('camera_source', 0)
    
    @camera_source.setter
    def camera_source(self, value: int):
        self._settings['camera_source'] = value
    
    @property
    def detection_confidence(self) -> float:
        return self._settings.get('detection_confidence', 0.7)
    
    @detection_confidence.setter
    def detection_confidence(self, value: float):
        self._settings['detection_confidence'] = value
    
    @property
    def tracking_confidence(self) -> float:
        return self._settings.get('tracking_confidence', 0.5)
    
    @tracking_confidence.setter
    def tracking_confidence(self, value: float):
        self._settings['tracking_confidence'] = value
    
    @property
    def theme(self) -> str:
        return self._settings.get('theme', 'dark')
    
    @theme.setter
    def theme(self, value: str):
        self._settings['theme'] = value
