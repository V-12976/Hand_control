import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 设置应用元数据
    app.setApplicationName("AI Gesture Control")
    app.setOrganizationName("Antigravity")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
