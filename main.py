from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QLabel, QRadioButton, QPushButton)
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtCore import Qt, QObject, QUrl, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QFont

import sys
import os
import backend
from backend import base_address
from windows_api import set_dpi_awareness

# ---------- 资源路径处理（打包 exe 用）----------


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ---------- DPI 感知 ----------
try:
    set_dpi_awareness()
except Exception as e:
    print(e)

# ---------- 获取屏幕物理分辨率和缩放因子 ----------
# app = QApplication(sys.argv)
# screen = app.primaryScreen()
# dpr = screen.devicePixelRatio()
# logical_size = screen.size()
# physical_width = round(logical_size.width() * dpr)
# physical_height = round(logical_size.height() * dpr)
# print(f"检测到物理分辨率: {physical_width}x{physical_height}, 缩放因子: {dpr}")



class KeySignaler(QObject):
    map_name = pyqtSignal(str)


class GamePlugin(QWidget):
    # 类属性：16张图片的文字描述和URL
    MapList = [
        ("虚空撕裂", "https://huiji-public.huijistatic.com/starcraft/uploads/6/68/Ui_loading_coop_gameplay_char2.png"),
        ("克哈裂痕", "https://huiji-public.huijistatic.com/starcraft/uploads/f/ff/Ui_loading_coop_gameplay_korhal.png"),
        ("虚空降临", "https://huiji-public.huijistatic.com/starcraft/uploads/8/8b/Ui_loading_coop_gameplay_kaldir1.png"),
        ("往日神庙", "https://huiji-public.huijistatic.com/starcraft/uploads/f/fe/Ui_loading_coop_gameplay_shakuras2.png"),
        ("湮灭快车", "https://huiji-public.huijistatic.com/starcraft/uploads/7/7c/Ui_loading_coop_gameplay_tarsonis1.png"),
        ("天界封锁", "https://huiji-public.huijistatic.com/starcraft/uploads/c/cd/Ui_loading_coop_gameplay_ulnar1.png"),
        ("升格之链", "https://huiji-public.huijistatic.com/starcraft/uploads/6/6f/Ui_loading_coop_gameplay_slayn2.png"),
        ("熔火危机", "https://huiji-public.huijistatic.com/starcraft/uploads/e/ea/Ui_loading_coop_gameplay_veridia2.png"),
        ("机会渺茫", "https://huiji-public.huijistatic.com/starcraft/uploads/f/fb/Ui_loading_coop_gameplay_belshir2.png"),
        ("营救矿工", "https://huiji-public.huijistatic.com/starcraft/uploads/7/75/Ui_loading_coop_gameplay_jarban1.png"),
        ("亡者之夜", "https://huiji-public.huijistatic.com/starcraft/uploads/d/db/Ui_loading_coop_gameplay_meinhoffdaynight2.png"),
        ("黑暗杀星", "https://huiji-public.huijistatic.com/starcraft/uploads/0/08/Ui_loading_coop_gameplay_scytheofamon2.png"),
        ("净网行动", "https://huiji-public.huijistatic.com/starcraft/uploads/d/d1/Ui_loading_coop_gameplay_malwarfare2.png"),
        ("聚铁成兵", "https://huiji-public.huijistatic.com/starcraft/uploads/2/2d/Ui_loading_coop_gameplay_pnp2.png"),
        ("死亡摇篮", "https://huiji-public.huijistatic.com/starcraft/uploads/9/98/Ui_loading_coop_gameplay_cradleofdeath1.png")
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("泽拉图找神器挂")
        self.setFixedSize(550, 650)
        self.signaler = KeySignaler()
        self.Point = backend.PixelPoint()
        self.Point.show()
        self.signaler.map_name.connect(self.Point.up_map)
        self.map_nums = len(self.MapList)

        self.setStyleSheet("background-color: #1a1a1a; color: #ffffff; font-family: 'Microsoft YaHei';")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        self.title_label = QLabel("泽拉图外挂")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            """font-size: 18px; font-weight: bold; color: #00ff00;background-color: #262626; padding: 10px; border-radius: 4px;""")
        layout.addWidget(self.title_label)

        # 界面布局
        grid = QGridLayout()
        self.labels = []
        self.cell_size = (150, 85)

        # 创建15个QLabel占位
        for i in range(self.map_nums):
            label = QLabel("加载中...")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedSize(*self.cell_size)
            label.setStyleSheet("background-color: #333; color: white;")
            label.mousePressEvent = lambda e, c=label, idx=i: self.on_cell_clicked(c, idx)
            row, col = divmod(i, 3)
            grid.addWidget(label, row, col)
            self.labels.append(label)

        layout.addLayout(grid)
        self.setLayout(layout)

        # 网络资源
        self.manager = QNetworkAccessManager(self)
        self.tasks: list[QNetworkReply] = []    # 保存所有进行中的请求
        self.retry_counts = [0] * self.map_nums           # 每张图已重试次数
        self.completed_count = 0               # 已完成任务数（成功或最终失败）

        # 启动所有下载
        for i in range(self.map_nums):
            self.download_image(i)

    def download_image(self, index):
        """为指定索引的图片发起下载请求"""
        url = self.MapList[index][1]
        req = QNetworkRequest(QUrl(url))
        reply = self.manager.get(req)

        self.tasks.append(reply)
        # 连接信号时用lambda绑定当前index和reply，避免闭包问题
        reply.finished.connect(lambda idx=index, rep=reply: self.on_finished(idx, rep))

    def on_finished(self, index, reply):
        """下载完成回调：成功显示图像+文字，失败则重试（最多3次）"""
        # 无论最终如何，先将该reply从tasks中移除
        if reply in self.tasks:
            self.tasks.remove(reply)

        if reply.error() == QNetworkReply.NetworkError.NoError:
            # 成功加载，读取图像数据
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)

            # 在图片底层绘制白色文字描述
            painter = QPainter(pixmap)
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
            desc = self.MapList[index][0]
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, desc)
            painter.end()

            # 缩放并显示
            cell_size_x, cell_size_y = self.cell_size
            scaled = pixmap.scaled(cell_size_x - 10, cell_size_y - 10, Qt.AspectRatioMode.KeepAspectRatio)
            self.labels[index].setPixmap(scaled)
            self.labels[index].setStyleSheet(
                "background-color: #333; border: 2px solid transparent; border-radius: 5px;")
            self._mark_task_done(index)

        else:
            # 失败处理：重试或放弃
            if self.retry_counts[index] < 3:
                self.retry_counts[index] += 1
                # 当前reply已无用，删除后重新下载
                reply.deleteLater()
                self.download_image(index)      # 新reply会被加入tasks
            else:
                # 重试次数用尽
                self.labels[index].setText("下载失败")
                self.labels[index].setStyleSheet("background-color: #600; color: white;")
                self._mark_task_done(index)

        # 注意：只有在不重试的情况下，reply才需要deleteLater
        # 重试时我们已手动deleteLater，此处避免重复
        if not (reply.error() != QNetworkReply.NetworkError.NoError and self.retry_counts[index] <= 3):
            reply.deleteLater()

    def _mark_task_done(self, index):
        """标记一个任务最终完成，全部完成后触发资源回收"""
        self.completed_count += 1
        if self.completed_count == self.map_nums:
            self.cleanup()

    def cleanup(self):
        """所有图片处理完毕后，回收网络资源"""
        # 取消并清理所有残留的请求（理论上此时tasks应为空）
        for task in self.tasks:
            task.abort()
            task.deleteLater()
        self.tasks.clear()

        # 删除网络管理器
        if self.manager:
            self.manager.deleteLater()
            self.manager = None

        # 清空辅助列表
        self.retry_counts.clear()

    def on_cell_clicked(self, clicked_cell, idx):
        for c in self.labels:
            c.setStyleSheet("background-color: #222; border: 2px solid transparent; border-radius: 5px; color: #555;")

        clicked_cell.setStyleSheet(
            "background-color: #222; border: 2px solid #00ff00; border-radius: 5px; color: #00ff00;")

        self.signaler.map_name.emit(self.MapList[idx][0])
        hex_iterable_x = map(hex, base_address[1][1])
        hex_iterable_y = map(hex, base_address[0][1])
        self.update_title(f"当前选中：地图 {self.MapList[idx][0]} "
                          f"\n x基址:{hex(base_address[1][0])} 偏移:{list(hex_iterable_x)} "
                          f"\n y基址:{hex(base_address[0][0])} 偏移:{list(hex_iterable_y)}"
                          f"\n 神器x坐标:{self.Point.crood_x} "
                          f"\n 神器y坐标:{self.Point.crood_y}")
        print(f"当前选中：地图 {self.MapList[idx][0]}")

    def update_title(self, text):
        self.title_label.setText(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = GamePlugin()
    widget.show()
    sys.exit(app.exec())
