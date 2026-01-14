import mediapipe as mp
import os
import sys

print(f"Python executable: {sys.executable}")
print(f"MediaPipe location: {os.path.dirname(mp.__file__)}")
print(f"MediaPipe version: {getattr(mp, '__version__', 'unknown')}")
print(f"Dir(mp): {dir(mp)}")

try:
    print(f"mp.solutions: {mp.solutions}")
except AttributeError as e:
    print(f"Error accessing mp.solutions: {e}")
