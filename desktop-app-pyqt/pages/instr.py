import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QFrame, QButtonGroup, QTextBrowser, QProgressBar
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from utils.design_utils import *
from utils.choosing_folder_utilts import *
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QDialog
from utils.ulils import check_internet_connection
import sys
import loguru
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QFrame, QPushButton, QFileDialog
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
# from logic.ssa_logic import start_sanger_logic
from utils.ulils import *

class InstructionsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        # Instructions
        self.instructions_label = QLabel(self.get_instructions(), self)
        self.instructions_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.instructions_label.setStyleSheet('color: white;')
        font = self.instructions_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.instructions_label.setFont(font)

        # Next Button
        self.btn_next_to_main = QPushButton("Next", self)
        self.btn_next_to_main.setStyleSheet('''
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
        main_layout.addWidget(self.instructions_label)
        main_layout.addWidget(self.btn_next_to_main)
        self.setLayout(main_layout)


    def get_instructions(self):
        instr = """ \n \n
        Quick Guide:

        1. NCBI Limits: Maximum of 100 requests per day to avoid slower processing.
        2. Request Allocation: Up to 50 files for both blastnr and blastnt, or 100 for one type.
        3. Request Interval: Mandatory 10-second gap between requests for NCBI compliance.
        4. Overwrite Option: Choose 'Overwrite' to regenerate existing blast files.
        5. Naming Convention:
            - Single files: 'Samplex_F.ab1'.
            - Paired files: 'Sample27_x.ab1' & 'Samplex_R.ab1'.
        6. Folder Creation: Individual folders for each file with all necessary data.
        7. Logging: Automated log file generation for process tracking.

        Adherence to these guidelines ensures optimal SSA functionality and NCBI compliance.
        """
        return instr