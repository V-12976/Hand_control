"""
输入模拟模块 - 键盘和鼠标控制
使用pynput实现跨平台输入模拟
"""

from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
from typing import Optional, Union
from enum import Enum
import time


class ActionType(Enum):
    """动作类型"""
    KEY = "key"
    KEY_COMBO = "key_combo"
    MOUSE_CLICK = "mouse"
    MOUSE_MOVE = "mouse_move"
    MOUSE_SCROLL = "mouse_scroll"


class InputSimulator:
    """
    输入模拟器 - 发送键盘和鼠标事件
    """
    
    # 特殊键映射
    SPECIAL_KEYS = {
        'space': Key.space,
        'enter': Key.enter,
        'escape': Key.esc,
        'esc': Key.esc,
        'tab': Key.tab,
        'backspace': Key.backspace,
        'delete': Key.delete,
        'up': Key.up,
        'down': Key.down,
        'left': Key.left,
        'right': Key.right,
        'home': Key.home,
        'end': Key.end,
        'page_up': Key.page_up,
        'page_down': Key.page_down,
        'insert': Key.insert,
        'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
        'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
        'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
        'ctrl': Key.ctrl, 'ctrl_l': Key.ctrl_l, 'ctrl_r': Key.ctrl_r,
        'alt': Key.alt, 'alt_l': Key.alt_l, 'alt_r': Key.alt_r,
        'shift': Key.shift, 'shift_l': Key.shift_l, 'shift_r': Key.shift_r,
        'caps_lock': Key.caps_lock,
        'num_lock': Key.num_lock,
        'print_screen': Key.print_screen,
        'pause': Key.pause,
        'media_play_pause': Key.media_play_pause,
        'media_next': Key.media_next,
        'media_previous': Key.media_previous,
        'media_volume_up': Key.media_volume_up,
        'media_volume_down': Key.media_volume_down,
        'media_volume_mute': Key.media_volume_mute,
    }
    
    # 鼠标按钮映射
    MOUSE_BUTTONS = {
        'left_click': Button.left,
        'right_click': Button.right,
        'middle_click': Button.middle,
    }
    
    def __init__(self):
        """初始化输入模拟器"""
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self._last_action_time = 0
        self._action_cooldown = 0.5  # 动作冷却时间（秒）
        
    def can_execute(self) -> bool:
        """检查是否可以执行动作（冷却检查）"""
        current_time = time.time()
        if current_time - self._last_action_time >= self._action_cooldown:
            return True
        return False
    
    def set_cooldown(self, seconds: float):
        """设置动作冷却时间"""
        self._action_cooldown = max(0.1, seconds)
        
    def press_key(self, key_str: str) -> bool:
        """
        按下并释放一个键
        
        Args:
            key_str: 键名称（如 'a', 'space', 'enter'）
            
        Returns:
            是否成功执行
        """
        if not self.can_execute():
            return False
            
        try:
            key = self._parse_key(key_str)
            if key:
                self.keyboard.press(key)
                self.keyboard.release(key)
                self._last_action_time = time.time()
                return True
        except Exception as e:
            print(f"按键失败: {e}")
        return False
    
    def press_key_combo(self, keys: list) -> bool:
        """
        按下组合键
        
        Args:
            keys: 键列表，如 ['ctrl', 'c']
            
        Returns:
            是否成功执行
        """
        if not self.can_execute():
            return False
            
        try:
            parsed_keys = [self._parse_key(k) for k in keys]
            if all(parsed_keys):
                # 按下所有键
                for key in parsed_keys:
                    self.keyboard.press(key)
                # 释放所有键（逆序）
                for key in reversed(parsed_keys):
                    self.keyboard.release(key)
                self._last_action_time = time.time()
                return True
        except Exception as e:
            print(f"组合键失败: {e}")
        return False
    
    def mouse_click(self, button: str = 'left_click', count: int = 1) -> bool:
        """
        鼠标点击
        
        Args:
            button: 按钮类型 ('left_click', 'right_click', 'middle_click')
            count: 点击次数
            
        Returns:
            是否成功执行
        """
        if not self.can_execute():
            return False
            
        try:
            btn = self.MOUSE_BUTTONS.get(button, Button.left)
            self.mouse.click(btn, count)
            self._last_action_time = time.time()
            return True
        except Exception as e:
            print(f"鼠标点击失败: {e}")
        return False
    
    def mouse_move(self, dx: int = 0, dy: int = 0) -> bool:
        """
        移动鼠标
        
        Args:
            dx: X方向移动量
            dy: Y方向移动量
            
        Returns:
            是否成功执行
        """
        try:
            self.mouse.move(dx, dy)
            return True
        except Exception as e:
            print(f"鼠标移动失败: {e}")
        return False
    
    def mouse_scroll(self, dx: int = 0, dy: int = 0) -> bool:
        """
        鼠标滚轮
        
        Args:
            dx: 水平滚动量
            dy: 垂直滚动量
            
        Returns:
            是否成功执行
        """
        if not self.can_execute():
            return False
            
        try:
            self.mouse.scroll(dx, dy)
            self._last_action_time = time.time()
            return True
        except Exception as e:
            print(f"鼠标滚动失败: {e}")
        return False
    
    def _parse_key(self, key_str: str) -> Optional[Union[Key, str]]:
        """解析键名称"""
        key_lower = key_str.lower().strip()
        
        # 检查是否是特殊键
        if key_lower in self.SPECIAL_KEYS:
            return self.SPECIAL_KEYS[key_lower]
        
        # 单字符键
        if len(key_str) == 1:
            return key_str
        
        return None
    
    def execute_action(self, action_type: str, action_value: str) -> bool:
        """
        执行动作
        
        Args:
            action_type: 动作类型 ('key', 'key_combo', 'mouse', 'mouse_scroll')
            action_value: 动作值
            
        Returns:
            是否成功执行
        """
        if action_type == 'key':
            return self.press_key(action_value)
        elif action_type == 'key_combo':
            keys = [k.strip() for k in action_value.split('+')]
            return self.press_key_combo(keys)
        elif action_type == 'mouse':
            if 'click' in action_value:
                return self.mouse_click(action_value)
            elif action_value == 'scroll_up':
                return self.mouse_scroll(0, 3)
            elif action_value == 'scroll_down':
                return self.mouse_scroll(0, -3)
        return False
    
    @classmethod
    def get_available_keys(cls) -> list:
        """获取所有可用的特殊键名称"""
        return list(cls.SPECIAL_KEYS.keys())
    
    @classmethod
    def get_available_mouse_actions(cls) -> list:
        """获取所有可用的鼠标动作"""
        return list(cls.MOUSE_BUTTONS.keys()) + ['scroll_up', 'scroll_down']
