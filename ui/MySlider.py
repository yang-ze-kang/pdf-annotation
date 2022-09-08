from PyQt5.QtWidgets import (QLabel, QHBoxLayout, QWidget, QSlider)
from PyQt5.QtCore import Qt


class MyHorizontalSlider(QWidget):

    def __init__(self, mini=80, maxi=120, single_step=2, value_changed_fun=None):
        super().__init__()
        self.mini = mini
        self.maxi = maxi
        self.single_step = single_step
        self.value_changed_fun = value_changed_fun
        self.init_ui()

    def init_ui(self):
        hBox = QHBoxLayout(self)
        label1 = QLabel("缩放比例")
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(self.mini, self.maxi)
        self.slider.setSingleStep(self.single_step)
        self.slider.valueChanged.connect(self.sliderValueChanged)
        self.label2 = QLabel("100%")
        hBox.addWidget(label1)
        hBox.addWidget(self.slider)
        hBox.addWidget(self.label2)

    def set_value(self, value):
        self.slider.setValue(value)

    def sliderValueChanged(self, value):
        self.label2.setText(str(value)+"%")
        self.value_changed_fun(value)
