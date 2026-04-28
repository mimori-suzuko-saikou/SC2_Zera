import sys
import os
import ctypes
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QLabel, QRadioButton, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal, QObject
import test8

# ---------- 资源路径处理（打包 exe 用）----------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

user32 = ctypes.windll.user32

# ---------- DPI 感知 ----------
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# ---------- 获取屏幕物理分辨率和缩放因子 ----------
app = QApplication(sys.argv)
screen = app.primaryScreen()
dpr = screen.devicePixelRatio()
logical_size = screen.size()
physical_width = round(logical_size.width() * dpr)
physical_height = round(logical_size.height() * dpr)
print(f"检测到物理分辨率: {physical_width}x{physical_height}, 缩放因子: {dpr}")

# ---------- 预设参数表（物理像素，在100%缩放下测量）----------
PRESET_PARAMS = {
    (3840, 2160): (524, 442, 57, 2097),
    (2560, 1440): (355, 347, 36, 1423),
    (2560, 1600): (395, 383, 39, 1581),
    (2048, 1536): (380, 368, 37, 1518),
    (1920, 1440): (355, 348, 36, 1425),
    (1920, 1200): (295, 288, 30, 1186),
    (1920, 1080): (267, 259, 26, 1068),
    (1680, 1050): (259, 252, 26, 1038),
    (1600, 1200): (295, 289, 30, 1187),
    (1600, 1024): (253, 245, 25, 1013),
    (1600, 900):  (224, 217, 22, 891),
    (1366, 768):  (190, 185, 19, 759),
}

# 根据物理分辨率选择预设
key = (physical_width, physical_height)
if key in PRESET_PARAMS:
    PHYS_WINDOWS_SIZE = PRESET_PARAMS[key]
    print(f"使用预设参数: {PHYS_WINDOWS_SIZE}")
else:
    print(f"错误：未找到分辨率 {physical_width}x{physical_height} 的预设参数。")
    print("请手动测量并添加到 PRESET_PARAMS 字典中。")
    sys.exit(1)

# 转换为当前缩放下的逻辑参数（程序内部使用）
windows_size_crood = tuple(round(v / dpr) for v in PHYS_WINDOWS_SIZE)

# ---------- 以下为原界面代码（基址已更新）----------
# 第一个参数是 y，第二个参数是 x
base_address = [(0x04482638, [0x0, 0x0, 0x44]), (0x04482638, [0x0, 0x0, 0x68])]

class KeySignaler(QObject):
    map_name = pyqtSignal(list)

class GamePlugin(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("泽拉图找神器挂")
        self.setFixedSize(550, 650)
        self.signaler = KeySignaler()
        self.Point = test8.PixelPoint()
        self.Point.show()
        self.signaler.map_name.connect(self.Point.up_map)

        self.setStyleSheet("background-color: #1a1a1a; color: #ffffff; font-family: 'Microsoft YaHei';")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        self.title_label = QLabel("泽拉图外挂")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 18px; font-weight: bold; color: #00ff00;
            background-color: #262626; padding: 10px; border-radius: 4px;
        """)
        layout.addWidget(self.title_label)

        grid = QGridLayout()
        self.cells = []
        for i in range(15):
            cell = QLabel()
            cell.setFixedSize(150, 85)
            cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # 使用 resource_path 加载图片
            pix = QPixmap(resource_path(f"MapName/{i+1}.png"))
            if not pix.isNull():
                cell.setPixmap(pix.scaled(140, 75, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                cell.setText(f"物品 {i + 1}")
            cell.setStyleSheet("background-color: #333; border: 2px solid transparent; border-radius: 5px;")
            cell.mousePressEvent = lambda e, c=cell, idx=i: self.on_cell_clicked(c, idx)
            grid.addWidget(cell, i // 3, i % 3)
            self.cells.append(cell)

        layout.addLayout(grid)
        self.setLayout(layout)

    def on_cell_clicked(self, clicked_cell, idx):
        MapList = ["虚空撕裂","克哈裂痕","虚空降临","往日神庙","湮灭快车",
                   "天界封锁","升格之链","熔火危机","机会渺茫","营救矿工",
                   "亡者之夜","黑暗杀星","净网行动","聚铁成兵","死亡摇篮"]
        for c in self.cells:
            c.setStyleSheet("background-color: #222; border: 2px solid transparent; border-radius: 5px; color: #555;")
        clicked_cell.setStyleSheet(
            "background-color: #222; border: 2px solid #00ff00; border-radius: 5px; color: #00ff00;")

        self.signaler.map_name.emit([MapList[idx], base_address, windows_size_crood])
        hex_iterable_x = map(hex, base_address[1][1])
        hex_iterable_y = map(hex, base_address[0][1])
        self.update_title(f"当前选中：地图 {MapList[idx]} "
                          f"\n x基址:{hex(base_address[1][0])} 偏移:{list(hex_iterable_x)} "
                          f"\n y基址:{base_address[0][0]} 偏移:{list(hex_iterable_y)}"
                          f"\n 当前屏幕小地图设定大小 {windows_size_crood}"
                          f"\n 神器x坐标:{self.Point.crood_x} "
                          f"\n 神器y坐标:{self.Point.crood_y}")
        print(f"当前选中：地图 {MapList[idx]}")

    def update_title(self, text):
        self.title_label.setText(text)
import os
os.environ["QT_OPENGL"] = "software"

if __name__ == "__main__":
    ex = GamePlugin()
    ex.show()
    sys.exit(app.exec())