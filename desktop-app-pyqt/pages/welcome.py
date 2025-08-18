import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QFrame, QButtonGroup, QTextBrowser, QProgressBar
from PyQt5.QtCore import Qt
from utils.design_utils import *
from utils.choosing_folder_utilts import *
import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
# from logic.ssa_logic import start_sanger_logic
from utils.ulils import *

from PIL import Image
import requests
from io import BytesIO
from PyQt5.QtWidgets import QLabel, QWidget, QApplication
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QByteArray

class WelcomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        url = 'https://i.ibb.co/S36xs7n/zewail-City-logo-large-notxt-transformed.png'
        response = requests.get(url)
        imgdata = Image.open(BytesIO(response.content))
        with BytesIO() as buffer:
            imgdata.save(buffer, format="PNG")
            buffer.seek(0)
            img_bytes = buffer.read()
        qbytearray = QByteArray(img_bytes)
        image = QImage.fromData(qbytearray)
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio)
        self.ilabel = QLabel(self)
        self.ilabel.setPixmap(scaled_pixmap)
        self.ilabel.setAlignment(Qt.AlignCenter)

        
        # Dev by
        self.tlabel = QLabel('Developed by Bioinformatics and Computational Biology Unit \n at Zewail City, Cairo, Egypt.\n\nSanger Sequencing Analyzer (SSA) ', self)
        self.tlabel.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.tlabel.setStyleSheet('color: white;')
        font = self.tlabel.font()
        font.setPointSize(20)
        font.setBold(True)
        self.tlabel.setFont(font)

        # Next Button
        self.btn_next_to_instructions = QPushButton("Next", self)
        self.btn_next_to_instructions.setStyleSheet('''
            QPushButton {
                background-color: white;
                color: #00B4D0;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #62b565;
                color: white;
            }
        ''')

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.ilabel)
        main_layout.addWidget(self.tlabel)
        main_layout.addWidget(self.btn_next_to_instructions)
        self.setLayout(main_layout)





