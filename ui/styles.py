"""
Material Design 3 (Material You) 风格样式表
"""

# Google Material 3 Dark Theme Colors
COLORS = {
    'primary': '#A8C7FA',          # Primary 80
    'on_primary': '#062E6F',       # Primary 20
    'primary_container': '#0842A0',# Primary 30
    'on_primary_container': '#D3E3FD', # Primary 90
    
    'secondary': '#A8C7FA',
    'secondary_container': '#004A77',
    'on_secondary_container': '#C2E7FF',
    
    'background': '#131314',       # Neutral 10
    'surface': '#131314',
    'surface_container': '#1E1F20', # Surface Container
    'surface_container_high': '#28292A', # Surface Container High
    
    'on_surface': '#E3E3E3',       # Neutral 90
    'on_surface_variant': '#C4C7C5', # Neutral Variant 80
    'outline': '#8E918F',          # Neutral Variant 60
    'outline_variant': '#444746',  # Neutral Variant 30
    
    'error': '#FFB4AB',            # Error 80
    'on_error': '#690005',
    'error_container': '#93000A',
    
    'success': '#6DD58C',
    'on_success': '#0A3818'
}

# 字体设置
FONTS = {
    'family': 'Google Sans, Roboto, Segoe UI, sans-serif',
    'display': '32px',
    'h1': '28px',
    'h2': '24px',
    'title': '20px',    # Title Large
    'body': '14px',     # Body Medium
    'label': '12px'     # Label Small
}

def get_stylesheet() -> str:
    """获取应用程序全局样式表"""
    return f"""
    QMainWindow {{
        background-color: {COLORS['background']};
    }}
    
    QWidget {{
        font-family: "{FONTS['family']}";
        color: {COLORS['on_surface']};
    }}
    
    /* 基础按钮 (Filled Button) */
    QPushButton {{
        background-color: {COLORS['primary']};
        color: {COLORS['on_primary']};
        border: none;
        border-radius: 20px; /* Pill shape */
        padding: 10px 24px;
        font-size: {FONTS['body']};
        font-weight: 600;
    }}
    
    QPushButton:hover {{
        background-color: #C2DCFA; /* Lighter on hover */
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['primary_container']};
        color: {COLORS['on_primary_container']};
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS['surface_container_high']};
        color: {COLORS['outline']};
    }}
    
    /* Tonal Button (Secondary) */
    QPushButton#secondaryById {{
        background-color: {COLORS['surface_container_high']};
        color: {COLORS['on_surface']};
        border: none;
    }}
    
    QPushButton#secondaryById:hover {{
        background-color: {COLORS['outline_variant']};
    }}
    
    /* 危险按钮 */
    QPushButton#dangerById {{
        background-color: {COLORS['error_container']};
        color: {COLORS['error']};
    }}
    
    QPushButton#dangerById:hover {{
        background-color: #FFDAD6;
        color: {COLORS['on_error']};
    }}
    
    /* 输入框 (Outlined Text Field) */
    QLineEdit, QComboBox {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['outline']};
        border-radius: 4px;
        padding: 12px 16px;
        color: {COLORS['on_surface']};
        font-size: 16px;
    }}
    
    QLineEdit:focus, QComboBox:focus {{
        border: 2px solid {COLORS['primary']};
        padding: 11px 15px;
    }}
    
    /* 滚动条 */
    QScrollBar:vertical {{
        border: none;
        background: transparent;
        width: 8px;
        border-radius: 4px;
        margin: 0px 0px 0px 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {COLORS['outline_variant']};
        min-height: 20px;
        border-radius: 4px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {COLORS['outline']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    /* 卡片 (Elevated/Outlined Card) */
    QFrame#card {{
        background-color: {COLORS['surface_container']};
        border-radius: 12px;
        border: 1px solid {COLORS['outline_variant']};
    }}
    
    QLabel#title {{
        font-size: {FONTS['title']};
        font-weight: 500;
        color: {COLORS['on_surface']};
    }}
    
    QLabel#subtitle {{
        font-size: {FONTS['body']};
        color: {COLORS['on_surface_variant']};
    }}
    
    /* 列表项 */
    QListWidget {{
        background-color: transparent;
        border: none;
        outline: none;
    }}
    
    QListWidget::item {{
        background-color: transparent;
        border: none;
        margin-bottom: 12px; 
    }}
    
    /* 导航栏容器 */
    QFrame#sidebar {{
        background-color: {COLORS['surface_container']};
        border-right: none;
        padding-right: 12px;
    }}
    
    /* 导航栏按钮 */
    QPushButton#nav_item {{
        background-color: transparent;
        color: {COLORS['on_surface_variant']};
        border: none;
        border-radius: 26px; /* High radius for pill shape */
        text-align: left;
        padding: 16px 24px;
        font-weight: 500;
        font-size: 16px;
    }}
    
    QPushButton#nav_item:hover {{
        background-color: rgba(255, 255, 255, 0.05);
        color: {COLORS['on_surface']};
    }}
    
    QPushButton#nav_item:checked {{
        background-color: {COLORS['secondary_container']};
        color: {COLORS['on_secondary_container']};
        font-weight: 600;
    }}
    
    QDialog {{
        background-color: {COLORS['surface_container']};
        border-radius: 28px;
    }}
    """
