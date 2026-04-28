import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush

from mem_read import read_base_address
from map_crood import map_crood_execute

map_size_list = {
    "虚空撕裂": [(208,200), (175,160), (16,12)],
    "克哈裂痕": [(216,216), (196,173), (10,13)],
    "熔火危机": [(200,200), (180,172), (10,8)],
    "聚铁成兵": [(216,200), (178,176), (20,6)],
    "营救矿工": [(200,184), (180,156), (10,8)],
    "黑暗杀星": [(216,192), (181,164), (18,9)],
    "死亡摇篮": [(256,256), (218,193), (20,30)],
    "天界封锁": [(208,216), (172,180), (18,16)],
    "升格之链": [(216,184), (196,164), (10,8)],
    "虚空降临": [(152,192), (132,164), (10,8)],
    "机会渺茫": [(168,184), (148,156), (10,8)],
    "净网行动": [(208,192), (192,164), (10,8)],
    "亡者之夜": [(192,192), (160,160), (16,8)],
    "往日神庙": [(192,200), (176,172), (8,8)],
    "湮灭快车": [(224,160), (192,144), (16,8)]
}

class PixelPoint(QWidget):
    def __init__(self, x=25, y=807):
        super().__init__()
        self.map_size = None
        self.base_address = None
        self.windows_size_crood = None
        self.crood_x = None
        self.crood_y = None
        self.data_ready = False

        # 窗口属性：无边框、置顶、工具、点击穿透、禁止获取焦点
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # 初始大小（临时，进入地图后根据小地图宽度调整）
        self.setFixedSize(10, 10)
        self.move(x, y)

        # 位置更新定时器（间隔3秒，降低频率）
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(3000)

        # 固定四色（红、绿、蓝、黄），不旋转
        self.color_tl = QColor(255, 0, 0)    # 左上红
        self.color_tr = QColor(0, 255, 0)    # 右上绿
        self.color_br = QColor(0, 0, 255)    # 右下蓝
        self.color_bl = QColor(255, 255, 0)  # 左下黄

        print("PixelPoint 四色固定版初始化完成，初始位置:", x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)

        w = self.width()
        h = self.height()
        half_w = w // 2
        half_h = h // 2

        if self.data_ready:
            painter.setBrush(QBrush(self.color_tl))
            painter.drawRect(0, 0, half_w, half_h)                 # 左上
            painter.setBrush(QBrush(self.color_tr))
            painter.drawRect(half_w, 0, w - half_w, half_h)        # 右上
            painter.setBrush(QBrush(self.color_br))
            painter.drawRect(half_w, half_h, w - half_w, h - half_h) # 右下
            painter.setBrush(QBrush(self.color_bl))
            painter.drawRect(0, half_h, half_w, h - half_h)        # 左下
        else:
            painter.setBrush(QBrush(Qt.GlobalColor.red))
            painter.drawRect(0, 0, w, h)

    def up_map(self, map_data):
        print("=== up_map 被调用 ===")
        self.map_size = map_size_list[map_data[0]]
        self.base_address = map_data[1]
        self.windows_size_crood = map_data[2]

        # 根据小地图宽度自动调整方块大小
        minimap_width = self.windows_size_crood[0]
        new_size = max(8, min(30, minimap_width // 25))
        self.setFixedSize(new_size, new_size)
        print(f"小地图宽度: {minimap_width}, 方块大小调整为: {new_size}")

        self.data_ready = True
        self.update()
        print("当前坐标参考地图:", map_data[0])
        print("窗口可见性:", self.isVisible())
        print("=== up_map 结束 ===")

    def update_position(self):
        if self.map_size and self.base_address and self.windows_size_crood:
            try:
                y_val = read_base_address(self.base_address[0][0], self.base_address[0][1])
                x_val = read_base_address(self.base_address[1][0], self.base_address[1][1])
                if y_val is None or x_val is None:
                    print("内存读取失败，跳过本次更新")
                    return
                self.crood_y = y_val + 29
                self.crood_x = x_val
                print(f"内存读取: x={self.crood_x}, y={self.crood_y}")

                newcoord = map_crood_execute(
                    self.map_size[0],
                    self.map_size[1],
                    self.windows_size_crood[:2],
                    (self.crood_x, self.crood_y),
                    self.map_size[2]
                )
                new_x = round(self.windows_size_crood[2] + newcoord[0])
                new_y = round(self.windows_size_crood[3] - newcoord[1])

                # 边界检查
                screen = QApplication.primaryScreen().geometry()
                new_x = max(screen.x(), min(new_x, screen.x() + screen.width() - self.width()))
                new_y = max(screen.y(), min(new_y, screen.y() + screen.height() - self.height()))

                self.move(new_x, new_y)
                if not self.isVisible():
                    self.show()
            except Exception as e:
                print(f"更新坐标失败: {e}")
        else:
            pass

# def run_app():
#     app = QApplication(sys.argv)
#     point = PixelPoint(25, 807)
#     point.show()
#     sys.exit(app.exec())

# if __name__ == "__main__":
#     run_app()