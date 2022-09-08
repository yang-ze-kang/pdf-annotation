from PyQt5.QtWidgets import (QApplication, QPushButton, QLineEdit, QLabel,QGridLayout,
                             QScrollArea, QHBoxLayout, QWidget, QVBoxLayout)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from .MySlider import MyHorizontalSlider
from .utils import Size
import fitz
import sys


class Pdf():
    def __init__(self, path):
        self.path = path
        self.pdf = fitz.open(path)
        self.current_page = 1
        self.max_page = self.pdf.pageCount

    def get_current_page(self):
        page = self.pdf.loadPage(self.current_page - 1)
        return page


class PdfReader(QWidget):

    def __init__(self):
        super().__init__()
        self.pdf = None
        self.init_ui()
        # self.set_pdf(
        #     r'E:\learn\论文\CNN\2017ICCV-Deformable Convolutional Networks.pdf')

    def init_ui(self):
        self.size = Size(2, 2)
        self.base_size = Size(2, 2)
        vBox = QVBoxLayout(self)
        # pdf显示区域
        self.hBox1 = QHBoxLayout()
        self.scroll = QScrollArea()
        self.scroll.setAlignment(Qt.AlignCenter)
        self.hBox1.addWidget(self.scroll)
        vBox.addLayout(self.hBox1)

        # 换页区域和缩放
        grid = QGridLayout()
        def prevpage():
            self.pdf.current_page -= 1
            self.set_page()

        def nextpage():
            self.pdf.current_page += 1
            self.set_page()
        # 换页
        hBox2_2 = QHBoxLayout()
        self.nextpageBtn = QPushButton("下一页")
        self.pageLineEdit = QLineEdit()
        self.pageLineEdit.setText("0/0")
        self.pageLineEdit.setEnabled(False)
        self.pageLineEdit.setMaximumWidth(80)
        self.pageLineEdit.setAlignment(Qt.AlignCenter)
        self.prevpageBtn = QPushButton("上一页")
        self.nextpageBtn.clicked.connect(nextpage)
        self.prevpageBtn.clicked.connect(prevpage)
        hBox2_2.addStretch()
        hBox2_2.addWidget(self.prevpageBtn)
        hBox2_2.addWidget(self.pageLineEdit)
        hBox2_2.addWidget(self.nextpageBtn)
        hBox2_2.addStretch()
        # 缩放
        hBox2_3 = QHBoxLayout()
        self.hSlider = MyHorizontalSlider(
            mini=20, maxi=250, single_step=2, value_changed_fun=self.zoom)
        self.hSlider.set_value(100)
        hBox2_3.addWidget(self.hSlider)
        grid.addLayout(hBox2_2,0,1,alignment=Qt.AlignCenter)
        grid.addLayout(hBox2_3,0,2,alignment=Qt.AlignCenter)
        grid.setColumnStretch(0,1)
        grid.setColumnStretch(1,4)
        grid.setColumnStretch(2,1)
        vBox.addLayout(grid)
        self.update_page_num()

    def zoom(self, value):
        # 缩放pdf
        scale = value/100.0
        self.size.x = self.base_size.x * scale
        self.size.y = self.base_size.y * scale
        if self.pdf is not None:
            self.set_page()

    def set_pdf(self, path):
        # 放置pdf
        self.pdf = Pdf(path)
        self.set_page()

    def set_page(self):
        # 显示一页pdf
        page = self.pdf.get_current_page()
        zoom_matrix = fitz.Matrix(self.size.x, self.size.y)
        pagePixmap = page.getPixmap(
            matrix=zoom_matrix,
            alpha=False)
        imageFormat = QImage.Format_RGB888
        pageQImage = QImage(
            pagePixmap.samples,
            pagePixmap.width,
            pagePixmap.height,
            pagePixmap.stride,
            imageFormat)
        pixmap = QPixmap()
        pixmap.convertFromImage(pageQImage)
        label = QLabel()
        label.setPixmap(QPixmap(pixmap))
        label.setAlignment(Qt.AlignHCenter)
        self.scroll.setWidget(label)
        self.update_page_num()

    def update_page_num(self):
        # 更新pdf页码
        self.prevpageBtn.setEnabled(False)
        self.nextpageBtn.setEnabled(False)
        if self.pdf is not None:
            self.pageLineEdit.setText(
                str(self.pdf.current_page) + "/" + str(self.pdf.max_page))
            if self.pdf.current_page < self.pdf.max_page:
                self.nextpageBtn.setEnabled(True)
            if self.pdf.current_page > 1:
                self.prevpageBtn.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = PdfReader()
    win.show()
    sys.exit(app.exec_())
