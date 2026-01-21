"""
手势检测模块 - 基于MediaPipe Hands
支持识别多种预定义手势
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum


class GestureType(Enum):
    """支持的手势类型"""
    NONE = "none"
    FIST = "fist"
    OPEN_PALM = "open_palm"
    THUMBS_UP = "thumbs_up"
    VICTORY = "victory"
    POINT_UP = "point_up"
    CUSTOM = "custom"


@dataclass
class HandLandmarks:
    """手部关键点数据"""
    landmarks: List[Tuple[float, float, float]]
    handedness: str  # "Left" or "Right"
    

@dataclass
class GestureResult:
    """手势识别结果"""
    gesture_type: GestureType
    gesture_id: str # 手势ID (fist, custom_123)
    name: str       # 显示名称
    confidence: float
    hand_landmarks: Optional[HandLandmarks]
    

class GestureDetector:
    """
    手势检测器 - 使用MediaPipe Hands进行实时手势识别
    """
    
    # 手指关键点索引
    WRIST = 0
    THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
    RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20
    
    def __init__(
        self,
        detection_confidence: float = 0.7,
        tracking_confidence: float = 0.5,
        max_hands: int = 2,
        enable_predefined_gestures: bool = False
    ):
        """
        初始化手势检测器
        """
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )
        
        self.custom_templates: Dict[str, List[Tuple[float, float, float]]] = {}
        self.gesture_names: Dict[str, str] = {}
        self.enable_predefined_gestures = enable_predefined_gestures
        
    def set_custom_templates(self, templates: Dict[str, List[Tuple[float, float, float]]]):
        """设置自定义手势模板"""
        new_templates = {}
        for gid, landmarks in templates.items():
            new_templates[gid] = self._normalize_landmarks(landmarks)
        self.custom_templates = new_templates
            
    def set_gesture_names(self, names: Dict[str, str]):
        """设置手势显示名称映射 {id: name}"""
        self.gesture_names = names
            
    def _normalize_landmarks(self, landmarks: List[Tuple[float, float, float]]) -> List[Tuple[float, float, float]]:
        """
        归一化关键点
        1. 将wrist移动到原点
        2. 缩放使得最大距离为1
        """
        # 转换为numpy数组方便计算
        points = np.array(landmarks)
        wrist = points[0]
        
        # 1. 相对坐标
        points = points - wrist
        
        # 2. 尺度归一化
        # 计算所有点到原点的最大距离
        max_dist = np.max(np.linalg.norm(points, axis=1))
        if max_dist > 0:
            points = points / max_dist
            
        return [tuple(p) for p in points]
        
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[GestureResult]]:
        """
        处理单帧图像，返回带标注的图像和识别结果
        """
        # 转换颜色空间
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        
        # MediaPipe处理
        results = self.hands.process(rgb_frame)
        
        rgb_frame.flags.writeable = True
        annotated_frame = frame.copy()
        
        gesture_results = []
        
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks,
                results.multi_handedness
            ):
                # 绘制手部骨架
                self.mp_drawing.draw_landmarks(
                    annotated_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
                
                # 提取关键点坐标
                landmarks = [
                    (lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark
                ]
                
                hand_data = HandLandmarks(
                    landmarks=landmarks,
                    handedness=handedness.classification[0].label
                )
                
                # 识别手势 (优先识别自定义手势)
                gesture_type, confidence, gesture_id = self._recognize_gesture(landmarks)
                
                # 显示名称
                display_name = gesture_type.value
                if gesture_id in self.gesture_names:
                    display_name = self.gesture_names[gesture_id]
                elif gesture_type == GestureType.CUSTOM:
                    display_name = "Custom"
                
                gesture_results.append(GestureResult(
                    gesture_type=gesture_type,
                    gesture_id=gesture_id,
                    name=display_name,
                    confidence=confidence,
                    hand_landmarks=hand_data
                ))
                
                # 在图像上显示手势名称 (支持中文需要特殊处理，cv2不支持中文)
                # cv2.putText不支持中文，如果display_name包含中文，会乱码或问号
                # 这里暂时回退到英文或ID，或者只显示ASCII字符
                # 既然用户想要自定义名字，可能是中文。PyQt界面可以显示中文，但cv2绘图不行。
                # 我们可以尝试使用PIL绘制中文，或者简单点，暂不解决cv2中文问题，
                # 但UI界面的status label可以显示正确中文。
                # 作为妥协，我们在cv2中只显示ASCII，或者不做cv2绘制，只靠UI。
                # 为了简单兼容，这里尽量显示。
                
                # 检查是否包含非ASCII
                safe_name = display_name
                if not all(ord(c) < 128 for c in display_name):
                    # 如果有中文，尝试显示ID的后几位或者类型
                    safe_name = gesture_type.value if gesture_type != GestureType.CUSTOM else "Custom"
                
                h, w, _ = frame.shape
                cx = int(landmarks[0][0] * w)
                cy = int(landmarks[0][1] * h) - 30
                
                cv2.putText(
                    annotated_frame,
                    safe_name,
                    (cx - 50, cy),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )
        
        return annotated_frame, gesture_results
    
    def _recognize_gesture(self, landmarks: List[Tuple[float, float, float]]) -> Tuple[GestureType, float, str]:
        """
        识别手势
        Returns: (GestureType, confidence, gesture_id)
        """
        # 1. 尝试匹配自定义手势
        normalized_current = self._normalize_landmarks(landmarks)
        best_match_id = None
        min_dist = float('inf')
        
        for gid, template in self.custom_templates.items():
            dist = self._calculate_distance(normalized_current, template)
            if dist < min_dist:
                min_dist = dist
                best_match_id = gid
        
        # 阈值判定 (平均距离小于0.15)
        # 经验值：0.1左右通常是比较好的匹配
        if best_match_id and min_dist < 0.15:
            return GestureType.CUSTOM, 1.0 - min_dist, best_match_id
            
        # 2. 匹配预定义手势 (如果启用)
        if self.enable_predefined_gestures:
            fingers_up = self._get_fingers_up(landmarks)
            thumb_up = self._is_thumb_up(landmarks)
            
            # 握拳
            if not any(fingers_up) and not thumb_up:
                return GestureType.FIST, 0.9, "fist"
            
            # 张开手掌
            if all(fingers_up) and thumb_up:
                return GestureType.OPEN_PALM, 0.9, "open_palm"
            
            # 竖起大拇指
            if thumb_up and not any(fingers_up):
                return GestureType.THUMBS_UP, 0.9, "thumbs_up"
            
            # 胜利手势
            if fingers_up[0] and fingers_up[1] and not fingers_up[2] and not fingers_up[3]:
                return GestureType.VICTORY, 0.9, "victory"
            
            # 竖起食指
            if fingers_up[0] and not fingers_up[1] and not fingers_up[2] and not fingers_up[3]:
                return GestureType.POINT_UP, 0.9, "point_up"
        
        return GestureType.NONE, 0.0, ""
        
    def _calculate_distance(self, lm1: List[Tuple[float, float, float]], lm2: List[Tuple[float, float, float]]) -> float:
        """计算两个归一化骨架的平均欧氏距离"""
        if len(lm1) != len(lm2):
            return float('inf')
        
        arr1 = np.array(lm1)
        arr2 = np.array(lm2)
        
        # 计算对应点的距离
        distances = np.linalg.norm(arr1 - arr2, axis=1)
        return np.mean(distances)
    
    def _get_fingers_up(self, landmarks: List[Tuple[float, float, float]]) -> List[bool]:
        """
        检测四根手指（食指、中指、无名指、小指）是否伸直
        
        Returns:
            [食指, 中指, 无名指, 小指] 的伸直状态
        """
        fingers_up = []
        
        # 食指
        fingers_up.append(
            landmarks[self.INDEX_TIP][1] < landmarks[self.INDEX_PIP][1]
        )
        
        # 中指
        fingers_up.append(
            landmarks[self.MIDDLE_TIP][1] < landmarks[self.MIDDLE_PIP][1]
        )
        
        # 无名指
        fingers_up.append(
            landmarks[self.RING_TIP][1] < landmarks[self.RING_PIP][1]
        )
        
        # 小指
        fingers_up.append(
            landmarks[self.PINKY_TIP][1] < landmarks[self.PINKY_PIP][1]
        )
        
        return fingers_up
    
    def _is_thumb_up(self, landmarks: List[Tuple[float, float, float]]) -> bool:
        """
        检测大拇指是否伸直
        """
        # 大拇指判断需要考虑左右手，这里用x坐标判断
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]
        thumb_mcp = landmarks[self.THUMB_MCP]
        
        # 大拇指尖到IP关节的距离应该大于IP到MCP的距离
        tip_to_ip = abs(thumb_tip[0] - thumb_ip[0])
        ip_to_mcp = abs(thumb_ip[0] - thumb_mcp[0])
        
        return tip_to_ip > ip_to_mcp * 0.5
    
    def release(self):
        """释放资源"""
        self.hands.close()


class CameraCapture:
    """摄像头采集类"""
    
    def __init__(self, source: int = 0):
        """
        初始化摄像头
        
        Args:
            source: 摄像头索引或视频流URL
        """
        self.source = source
        self.cap = None
        self._is_running = False
        
    def start(self) -> bool:
        """启动摄像头"""
        # 使用DirectShow (CAP_DSHOW) 在Windows上通常启动更快
        self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        if self.cap.isOpened():
            self._is_running = True
            # 设置分辨率
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            return True
        return False
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """读取一帧"""
        if self.cap and self._is_running:
            return self.cap.read()
        return False, None
    
    def stop(self):
        """停止摄像头"""
        self._is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
            
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    def get_fps(self) -> float:
        """获取帧率"""
        if self.cap:
            return self.cap.get(cv2.CAP_PROP_FPS)
        return 0.0
