import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush

from windows_api import get_process_monitor_info

# ============== 读内存 ===============

import pymem

base_address = [(0x04482638, [0x0, 0x0, 0x44]), (0x04482638, [0x0, 0x0, 0x68])]


def get_pointer_address(pm, base, offsets):
    # 初始地址 = 模块基址 + 第一个偏移量
    addr = pm.read_longlong(base)

    # 循环追踪多级偏移 (除了最后一个)
    for offset in offsets[:-1]:
        addr = pm.read_longlong(addr + offset)

    # 返回最终的目标地址
    return addr + offsets[-1]

# process_name 游戏进程 ,base_static_offset 起始地址,多层偏移


def read_base_address(base_static_offset, pointer_offsets, process_name="SC2_x64.exe"):
    try:
        # 1. 初始化进程
        pm = pymem.Pymem(process_name)

        # 2. 获取模块基址
        module = pymem.process.module_from_name(pm.process_handle, process_name).lpBaseOfDll

        # 3. 设置偏移量
        # "SC2_x64.exe"+05A7F2A0 对应静态偏移
        # base_static_offset = 0x05A7F2A0
        # pointer_offsets = [0x120, 0x1C0]

        # 4. 计算最终地址
        # 注意：64位游戏通常使用 longlong (8字节) 读取地址
        target_addr = get_pointer_address(pm, module + base_static_offset, pointer_offsets)

        # 5. 读取该地址的值 (假设它是整数，如果是浮点数请用 read_float)
        value = pm.read_float(target_addr)

        # print(f"基址地址: {hex(module)}")
        # print(f"目标内存地址: {hex(target_addr)}")
        # print(f"当前数值: {value}")
        return value

    except Exception as e:
        print(f"发生错误: {e}")

# ============== 读内存 ===============


# ============== 计算拉伸 ===============

def get_fitted_stretched_rect(ref_orig, boundary, target_orig):
    """
    1. 先按参考比例变形
    2. 再等比缩放至触碰边界(Aspect Fit)
    :param ref_orig: 原始参考系 (100, 100)
    :param boundary: 拉伸上限/边界 (262, 258)
    :param target_orig: 想要放大的不定长矩形 (w, h)
    """
    # Step 1: 计算基础拉伸比例 (sx, sy)
    sx_base = boundary[0] / ref_orig[0]
    sy_base = boundary[1] / ref_orig[1]

    # Step 2: 目标矩形经过“初始变形”后的逻辑尺寸
    target_deformed_w = target_orig[0] * sx_base
    target_deformed_h = target_orig[1] * sy_base

    # Step 3: 计算缩放因子 k，使得变形后的矩形适配 boundary
    k = min(boundary[0] / target_deformed_w, boundary[1] / target_deformed_h)

    # Step 4: 计算最终尺寸
    final_w = target_deformed_w * k
    final_h = target_deformed_h * k

    # 计算相对于原始 target_orig 的总面积比
    final_area_ratio = (final_w * final_h) / (target_orig[0] * target_orig[1])

    return {
        "final_dimensions": (round(final_w, 2), round(final_h, 2)),
        "limiting_factor": "Width" if (boundary[0] / target_deformed_w) < (
            boundary[1] / target_deformed_h) else "Height",
        "total_area_ratio": round(final_area_ratio, 4)
    }


def Margin(size, layout_size):
    x, y = size
    l_x, l_y = layout_size
    if x == l_x:
        Margin_x = 0
    else:
        Margin_x = round(l_x - x) / 2

    if y == l_y:
        Margin_y = 0
    else:
        Margin_y = round(l_y - y) / 2
    return (Margin_x, Margin_y)


def map_coordinate(source_pos, source_size, target_size, margin_size):
    """
    将大地图坐标映射到小地图坐标
    :param source_pos: (x, y) 大地图上的坐标
    :param source_size: (width, height) 大地图的总尺寸
    :param target_size: (width, height) 小地图的总尺寸
    :return: (x, y) 映射后的坐标
    """
    src_x, src_y = source_pos[0] - margin_size[0], source_pos[1] - margin_size[1]
    print("src_x ---25.93920898--", src_x)
    print("src_y ---138.2319336--", src_y)
    src_w, src_h = source_size

    tgt_w, tgt_h = target_size
    print("tgt_w --172--", tgt_w)
    print("tgt_h --180--", tgt_h)

    map_x = src_x * (tgt_w / src_w)
    map_y = src_y * (tgt_h / src_h)
    print("--map_x,map_y--", map_x, map_y)
    return (map_x, map_y)


def map_crood_execute(map_size, camera_size, layout_size, coord, margin_size):
    # 关键修改：将原来的 (262, 257) 替换为 layout_size
    stretched_size = get_fitted_stretched_rect((101, 100), layout_size, (172, 180))['final_dimensions']
    layout_x, layout_y = stretched_size[0], stretched_size[1]
    coord_x, coord_y = coord
    margin_size_x, margin_size_y = margin_size
    x = (coord_x - margin_size_x) / camera_size[0] * layout_x
    y = (coord_y - margin_size_y) / camera_size[1] * layout_y

    test = Margin(stretched_size, layout_size)
    x = test[0] + x
    y = test[1] + y
    return (x, y)

# ============== 计算拉伸 ===============


map_size_list = {
    "虚空撕裂": [(208, 200), (175, 160), (16, 12)],
    "克哈裂痕": [(216, 216), (196, 173), (10, 13)],
    "熔火危机": [(200, 200), (180, 172), (10, 8)],
    "聚铁成兵": [(216, 200), (178, 176), (20, 6)],
    "营救矿工": [(200, 184), (180, 156), (10, 8)],
    "黑暗杀星": [(216, 192), (181, 164), (18, 9)],
    "死亡摇篮": [(256, 256), (218, 193), (20, 30)],
    "天界封锁": [(208, 216), (172, 180), (18, 16)],
    "升格之链": [(216, 184), (196, 164), (10, 8)],
    "虚空降临": [(152, 192), (132, 164), (10, 8)],
    "机会渺茫": [(168, 184), (148, 156), (10, 8)],
    "净网行动": [(208, 192), (192, 164), (10, 8)],
    "亡者之夜": [(192, 192), (160, 160), (16, 8)],
    "往日神庙": [(192, 200), (176, 172), (8, 8)],
    "湮灭快车": [(224, 160), (192, 144), (16, 8)]
}

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


class PixelPoint(QWidget):
    def __init__(self, x=25, y=807):
        super().__init__()
        self.map_size = None
        self.base_address = base_address
        self.windows_size_crood = None
        self.crood_x = None
        self.crood_y = None
        self.data_ready = False
        self.mon_info = None
        self.current_map = ""
        self.selected_map = ""

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
            painter.drawRect(half_w, half_h, w - half_w, h - half_h)  # 右下
            painter.setBrush(QBrush(self.color_bl))
            painter.drawRect(0, half_h, half_w, h - half_h)        # 左下
        else:
            painter.setBrush(QBrush(Qt.GlobalColor.red))
            painter.drawRect(0, 0, w, h)

    def get_mon_info(self):
        if not self.mon_info:
            self.mon_info = get_process_monitor_info("SC2_X64.exe")
        if self.mon_info:
            dpr = self.mon_info["scale_factor"]
            # 根据物理分辨率选择预设
            key = (self.mon_info["actual_width"], self.mon_info["actual_height"])
            if key in PRESET_PARAMS:
                PHYS_WINDOWS_SIZE = PRESET_PARAMS[key]
                print(f"使用预设参数: {PHYS_WINDOWS_SIZE}")
            else:
                print(f"错误：未找到分辨率 {self.mon_info['actual_width']} x {self.mon_info['actual_height']} 的预设参数。")
                print("请手动测量并添加到 PRESET_PARAMS 字典中。")
                sys.exit(1)

            # 转换为当前缩放下的逻辑参数（程序内部使用）
            self.windows_size_crood = tuple(round(v / dpr) for v in PHYS_WINDOWS_SIZE)

    def up_map(self, map_name: str):
        print("=== up_map 被调用 ===")
        self.map_size = map_size_list[map_name]
        self.selected_map = map_name
        self.update_size()

    def update_size(self):
        if not self.mon_info or not self.windows_size_crood:
            return

        if self.selected_map != self.current_map:
            self.current_map = self.selected_map
        # 根据小地图宽度自动调整方块大小
        minimap_width = self.windows_size_crood[0]
        new_size = max(12, min(30, minimap_width // 25))
        self.setFixedSize(new_size, new_size)
        print(f"小地图宽度: {minimap_width}, 方块大小调整为: {new_size}")

        self.data_ready = True
        self.update()
        print("当前坐标参考地图:", self.selected_map)
        print("窗口可见性:", self.isVisible())
        print("=== up_map 结束 ===")

    def update_position(self):
        if not self.mon_info:
            self.get_mon_info()

        if self.map_size and self.mon_info and self.windows_size_crood:
            try:
                self.update_size()
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
