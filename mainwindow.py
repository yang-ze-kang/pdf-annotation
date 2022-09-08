import os
import time
from tkinter.tix import Tree
import numpy as np
import json
import pickle
from PyQt5.QtWidgets import (QPushButton, QGroupBox, QLineEdit, QListWidget, QShortcut,
                             QLabel, QFileDialog, QScrollArea, QSpacerItem, QHBoxLayout,
                             QWidget, QMessageBox, QRadioButton, QButtonGroup, QVBoxLayout,
                             QLayout, QInputDialog, QMainWindow)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPalette
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QSizePolicy
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QSize, QRect, QPoint
import sys
from ui.PdfReader import PdfReader
from ui.utils import Size


class MyTimer(QThread):
    def __init__(self, time_label):
        super(MyTimer, self).__init__()
        self.time_label = time_label
        self.all_time = 0
        self.is_stop = False

    def terminate(self):
        super().terminate()
        self.is_stop = True

    def run(self):
        start_time = time.time()
        while True:
            if self.is_stop:
                break
            time.sleep(1)
            self.time_label.setText('{}'.format(int(time.time()-start_time)))
            self.all_time = time.time() - start_time


class Task(object):
    def __init__(self, usr_dir, path, label_type, pattern, name):
        assert usr_dir is not None
        assert name is not None
        self.need_label_ids = None
        self.start_idx = 1
        self.end_idx = 0
        self.current_idx = 1
        self.last_labeled_idx = 0
        self.usr_dir = usr_dir
        self.path = path
        self.label_type = label_type
        self.json_path = os.path.join(
            self.usr_dir, 'label_{}_{}.json'.format(self.label_type, name))
        self.is_finished = False
        self.labeled_info = []
        self.name = name
        self.load()

    def get_current_label(self):
        if self.labeled_info[self.current_idx-1]['is_labeled'] == 0:
            return None
        else:
            return self.labeled_info[self.current_idx-1]['label']

    def update_current_label(self, label, labeled_time):
        # 更新一次标注
        self.labeled_info[self.current_idx-1]['label'] = label
        self.labeled_info[self.current_idx-1]['is_labeled'] = 1
        self.labeled_info[self.current_idx-1]['labeled_time'] = labeled_time
        self.save()

    def save(self):
        info = {
            'need_label_ids': self.need_label_ids,
            'current_idx': self.current_idx,
            'start_idx': self.start_idx,
            'end_idx': self.end_idx,
            'data_type': self.label_type,
            'json_path': self.json_path,
            'labeled_info': self.labeled_info,
            'is_finished': self.is_finished,
            'name': self.name
        }
        if self.current_idx == len(self.need_label_ids):
            self.is_finished = True
        pickle.dump(info, open(self.path, 'wb'), pickle.HIGHEST_PROTOCOL)
        self.save_json()

    def save_json(self):
        json.dump(self.labeled_info, open(self.json_path, 'w',
                                          encoding='utf-8'), indent=' ', ensure_ascii=False)

    def load(self):
        if os.path.exists(self.path):
            info = pickle.load(open(self.path, 'rb'))
            self.need_label_ids = info['need_label_ids']
            self.current_idx = info['current_idx']
            self.start_idx = info['start_idx']
            self.end_idx = info['end_idx']
            self.data_type = info['data_type']
            self.json_path = info['json_path']
            self.labeled_info = info['labeled_info']
            self.is_finished = info['is_finished']
            self.name = info['name']
        else:
            pass


class Windows(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.LABELING = 0  # 正在标注
        self.UNLABELING = 1  # 没有在标注
        self.label_flag = self.UNLABELING
        self.task = None

    def center(self):
        size = self.geometry()
        self.move((self.width() - size.width()) // 2,
                  (self.height() - size.height()) // 2)

    def init_ui(self):
        # 设置窗口大小
        self.setGeometry(200, 100, 1200, 900)
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self.setWindowTitle("患者级数据标注")
        self.center()
        self.size = Size(3.6, 3.6)

        vhox = QVBoxLayout()
        hbox = QHBoxLayout()
        vhox_c_d = QVBoxLayout()
        vhox_c_d.addLayout(self.ui_c())
        vhox_c_d.addLayout(self.ui_e())
        vhox_c_d.addLayout(self.ui_d())
        hbox.addLayout(vhox_c_d)
        vhox.addLayout(self.ui_a())
        vhox.addLayout(self.ui_b())
        vhox.addLayout(hbox)
        self.setLayout(vhox)
        self.input_name()

    def ui_a(self):
        """
        标注软件区域a, 选择文件夹路径, 患者编号
        """
        # 创建提示Label
        self.qlabel_src = QLabel("文件根目录:", self)
        self.qlabel_patient_id = QLabel("标注的类型(两种, 选一个，且标注的过程中不能更改):", self)

        # 创建文件路径显示框
        self.qedit_src = QLineEdit("data/chongqing-onlyimage-pdfs", self)
        self.qedit_src.setEnabled(False)

        qradio_group = QButtonGroup(self)
        self.data_type = [line.strip('\n') for line in open(
            'data/app/type_data.txt', 'r', encoding='utf-8')]
        self.qradio_data_type = []
        for idx, item in enumerate(self.data_type):
            self.qradio_data_type.append(
                QRadioButton('{}-{}'.format(idx, item)))
        for btn in self.qradio_data_type:
            qradio_group.addButton(btn)

        # 创建点击按钮
        self.qbtn_src = QPushButton("选择文件夹", self)
        self.qbtn_src.setEnabled(False)
        self.qbtn_src.clicked.connect(self.show_diagwindow_select)
        self.qbtn_start_label = QPushButton("开始标注", self)
        self.qbtn_start_label.clicked.connect(self.start_label)

        # 创建布局
        vbox1 = QVBoxLayout()
        hbox1_1 = QHBoxLayout()
        hbox1_2 = QHBoxLayout()
        hbox1_1.addWidget(self.qlabel_src)
        hbox1_1.addWidget(self.qedit_src)
        hbox1_1.addWidget(self.qbtn_src)
        hbox1_2.addWidget(self.qlabel_patient_id)
        for type in self.qradio_data_type:
            hbox1_2.addWidget(type)
        hbox1_2.addStretch(1)
        hbox1_2.addWidget(self.qbtn_start_label)
        vbox1.addLayout(hbox1_1)
        vbox1.addLayout(hbox1_2)

        return vbox1

    def ui_b(self):
        """
        计时器区域
        """
        self.qlabel_timer = QLabel("计时:", self)
        self.qlabel_timer_obj = QLabel("0", self)

        self.my_timer_thread = None

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.qlabel_timer, alignment=Qt.AlignHCenter)
        hbox.addWidget(self.qlabel_timer_obj, alignment=Qt.AlignHCenter)
        hbox.addStretch(1)
        return hbox

    def ui_c(self):
        """
        患者编号区域
        """
        self.qlabel_patient_id_label = QLabel("患者编号?-?, 当前患者编号:?", self)
        hbox = QHBoxLayout()
        hbox.addWidget(self.qlabel_patient_id_label)
        return hbox

    def ui_d(self):
        """
        pdf显示区域
        """
        hBox = QHBoxLayout()
        self.pdf_reader = PdfReader()
        hBox.addWidget(self.pdf_reader)
        return hBox

    def page_pixmap(self, page):
        label = QLabel()
        # p = self.render_pdf_page(page, x = self.size.x, y = self.size.y)
        p = self.render_pdf_page(page, 1, 1)
        # p.scaled(200, 200)
        label.setPixmap(QPixmap(p))
        self.area.setWidget(label)
        return label

    def zoom_book(self, plus=True):
        if plus:
            self.size.x += 0.4
            self.size.y += 0.4
            self.set_page()
        elif not plus:
            self.size.x -= 0.4
            self.size.y -= 0.4
            self.set_page()

    def ui_e0(self):
        qlabel = QLabel('患者序列:')
        self.squ_vbox = QVBoxLayout()

        vbox = QVBoxLayout()
        vbox.addWidget(qlabel)
        vbox.addLayout(self.squ_vbox)
        vbox.addStretch(1)

        return vbox

    def ui_e(self):
        """
        选择区域
        """
        label_type = [line.strip('\n') for line in open(
            'data/app/type_anno.txt', 'r', encoding='utf-8')]
        self.qlabel_class = QLabel("标注类别:", self)
        self.class2qlabelId = {}
        self.qradio_class = []
        for idx, item in enumerate(label_type):
            self.class2qlabelId[item] = idx
            self.qradio_class.append(QRadioButton('{}-{}'.format(idx+1, item)))

        vbox_1 = QHBoxLayout()
        vbox_1.addWidget(self.qlabel_class)
        for index, item in enumerate(self.qradio_class):
            item.setShortcut(str(index+1))
            vbox_1.addWidget(item)

        self.qbtn_pre = QPushButton("上一个")
        self.qbtn_pre.setEnabled(False)
        self.qbtn_pre.clicked.connect(self.pre)
        self.qbtn_next = QPushButton("下一个")
        self.qbtn_next.setEnabled(False)
        self.qbtn_next.clicked.connect(self.next)
        for seq in ["q", Qt.Key_Up]:
            shorcut = QShortcut(seq, self.qbtn_pre)
            shorcut.activated.connect(self.qbtn_pre.animateClick)
        for seq in ["e", Qt.Key_Down]:
            shorcut = QShortcut(seq, self.qbtn_next)
            shorcut.activated.connect(self.qbtn_next.animateClick)

        vbox = QHBoxLayout()
        vbox.addLayout(vbox_1)
        vbox.addStretch(1)
        vbox.addWidget(self.qbtn_pre, 0, Qt.AlignRight)
        vbox.addWidget(self.qbtn_next, 0, Qt.AlignRight)

        return vbox

    def input_name(self):
        value, ok = QInputDialog.getText(
            self, '输入', '请输入您的姓名', QLineEdit.Normal, "")
        if not ok:
            sys.exit()
        self.name = value
        self.usr_dir = os.path.join('data/usr', self.name)
        if not os.path.isdir(self.usr_dir):
            os.mkdir(self.usr_dir)

    def show_diagwindow_select(self):
        dir_name = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        self.qedit_src.setText(dir_name)

    def start_label(self):
        if self.label_flag == self.UNLABELING:
            # 判断路径是否填写
            self.data_root = self.qedit_src.text()
            if self.data_root == '':
                QMessageBox.critical(self, "错误", "请选择数据路径: (当前目录下的data文件夹)",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                return
            # 检查标注类型
            data_type_list = [btn.isChecked()
                              for btn in self.qradio_data_type]
            if np.sum(data_type_list) == 0:
                QMessageBox.critical(self, "错误", "请选择一个标注类型",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                return

            # 创建task，管理标注顺序
            data_type_idx = np.argmax(data_type_list)
            data_type = self.qradio_data_type[data_type_idx].text().split(
                '-')[1]
            pkl_path = os.path.join(
                self.usr_dir, '{}.pkl'.format(data_type_idx))
            # 获取需要标注的pdfs
            self.pdfs_id2path = {int(name.split('_')[0]): os.path.join(self.data_root, data_type, name)
                                 for name in os.listdir(os.path.join(self.data_root, data_type))}
            self.pdfs_id2name = {int(name.split('_')[0]): name
                                 for name in os.listdir(os.path.join(self.data_root, data_type))}
            self.task = Task(self.usr_dir, pkl_path,
                             data_type, None, self.name)
            if not self.task.need_label_ids:
                self.task.need_label_ids = list(
                    sorted(self.pdfs_id2path.keys()))
                self.task.labeled_info = [{
                    'id': id,
                    "pdf_name": self.pdfs_id2name[id],
                    'is_labeled':0,
                    'label': "",
                    'labeled_time': "",
                }for id in self.task.need_label_ids]
                self.task.start_idx = 1
                self.task.end_idx = len(self.task.need_label_ids)
        if self.label_flag == self.UNLABELING:
            self.label_flag = self.LABELING
            self.qbtn_start_label.setText("停止标注")
            for btn in self.qradio_data_type:
                btn.setEnabled(False)
            self.qbtn_next.setEnabled(True)
            self.set_test()
            self.check_pre_next()
        else:
            self.label_flag = self.UNLABELING
            self.qbtn_start_label.setText("开始标注")
            for btn in self.qradio_data_type:
                btn.setEnabled(True)
            self.qbtn_pre.setEnabled(False)
            self.qbtn_next.setEnabled(False)
            self.end()

    def check_pre_next(self):
        if self.task.current_idx > 1:
            self.qbtn_pre.setEnabled(True)
        else:
            self.qbtn_pre.setEnabled(False)
        if self.task.current_idx < self.task.end_idx:
            self.qbtn_next.setEnabled(True)
            self.qbtn_next.setText("下一个")
        else:
            self.qbtn_next.setEnabled(True)
            self.qbtn_next.setText("完成标注")

    def pre(self):
        # 上一个
        self.task.current_idx -= 1
        self.set_test()
        self.check_pre_next()

    def next(self):
        # 下一个
        label_type_list = [btn.isChecked()
                           for btn in self.qradio_class]
        if np.sum(label_type_list) == 0:
            QMessageBox.critical(self, "错误", "请选择一个标注类型",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            return
        self.save_current_test()
        if self.task.current_idx == self.task.end_idx:
            QMessageBox.information(self, "信息", "患者{}-{}标注完毕, 请收集保存目录下生成的【{}】".format(
                self.task.start_idx, self.task.current_idx, self.task.json_path),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            self.qbtn_next.setEnabled(False)
            return
        self.task.current_idx += 1
        self.set_test()
        self.qbtn_pre.setEnabled(True)
        self.check_pre_next()

    def set_test(self):
        # 放置一个测试
        if self.my_timer_thread == None:
            self.my_timer_thread = MyTimer(self.qlabel_timer_obj)
            self.my_timer_thread.start()
        else:
            self.my_timer_thread.terminate()
            self.my_timer_thread.wait()
            self.my_timer_thread = MyTimer(self.qlabel_timer_obj)
            self.my_timer_thread.start()
        self.qlabel_patient_id_label.setText(
            'pdf序号:{}-{}, 当前pdf序号:{}, 当前pdf名称{}'.format(self.task.start_idx, self.task.end_idx, self.task.current_idx, self.pdfs_id2name[self.task.current_idx]))
        pdf_path = self.pdfs_id2path[self.task.current_idx]
        # pdf
        self.pdf_reader.set_pdf(pdf_path)
        # 标注
        if self.task.get_current_label() is None:
            for item in self.qradio_class:
                item.setAutoExclusive(False)
                item.setChecked(False)
                item.setAutoExclusive(True)
        else:
            self.qradio_class[self.class2qlabelId[self.task.get_current_label()]].setChecked(
                True)

    def save_current_test(self):
        radio_btn_isCheck = [btn.isChecked() for btn in self.qradio_class]
        label = self.qradio_class[np.argmax(
            radio_btn_isCheck)].text().split('-')[-1]
        labeled_time = self.my_timer_thread.all_time
        self.task.update_current_label(label, labeled_time)
        return 0

    def end(self):
        if self.label_flag == self.LABELING:
            self.qbtn_start_label.setText("开始标注")
            for btn in self.qradio_data_type:
                btn.setEnabled(True)
            self.qbtn_pre.setEnabled(False)
            self.qbtn_next.setEnabled(False)
            self.label_flag = self.UNLABELING
        label_type_list = [btn.isChecked() for btn in self.qradio_class]
        if np.sum(label_type_list) != 0:
            self.save_current_test()
            QMessageBox.information(self, "信息", "患者{}-{}标注完毕, 请收集保存目录下生成的【{}】".format(
                self.task.start_idx, self.task.current_idx, self.task.json_path),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        else:
            QMessageBox.information(self, "信息", "患者{}-{}标注完毕, 请收集保存目录下生成的【{}】".format(
                self.task.start_idx, self.task.current_idx - 1, self.task.json_path),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if self.my_timer_thread:
            self.my_timer_thread.terminate()
            self.my_timer_thread.wait()
            self.my_timer_thread = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Windows()
    win.setWindowIcon(QIcon("ico.ico"))
    win.show()
    sys.exit(app.exec_())
