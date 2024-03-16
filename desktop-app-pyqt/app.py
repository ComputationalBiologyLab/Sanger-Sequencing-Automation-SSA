import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QStackedWidget
from PyQt5.QtGui import QIcon
from pages.main import *
from pages.results import *
from pages.summary import *
from pages.welcome import *
from pages.instr import *
import ctypes
import platform


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(r"D:\Zewail\DrEman\Rana-project\Sanger-Sequencing-Automation-SSA\desktop-app-pyqt\assets\images\logoicon.ico"))
        self.selected_dir = ""
        self.init_ui()
        self.INDEX_WELCOME_PAGE = 0
        self.INDEX_INSTR_PAGE = 1
        self.INDEX_MAIN_PAGE = 2
        self.INDEX_RESULTS_PAGE = 3
        self.INDEX_SUMMARY_PAGE = 4

    def init_ui(self):
        self.setStyleSheet("background-color: #00B4D0;")
        
        self.stacked_widget = QStackedWidget(self)

        welcome_page = WelcomePage(self)
        instr_page= InstructionsPage(self)
        main_page = MainPage(self)
        view_results_page = ResultsPage(self)
        view_summary_page = SummaryPage(self)

        self.stacked_widget.addWidget(welcome_page)
        self.stacked_widget.addWidget(instr_page)
        self.stacked_widget.addWidget(main_page)
        self.stacked_widget.addWidget(view_results_page)
        self.stacked_widget.addWidget(view_summary_page)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked_widget)

        self.setGeometry(950, 100, 950, 800)
        self.setWindowTitle('Sanger Sequencing Automation (SSA)')
        # first page always
        self.stacked_widget.setCurrentWidget(welcome_page)
        welcome_page.btn_next_to_instructions.clicked.connect(self.show_instruction_page)
        instr_page.btn_next_to_main.clicked.connect(self.show_main_page)
        main_page.btn_view_results.clicked.connect(self.show_view_results)
        main_page.btn_view_summary.clicked.connect(self.show_view_summary)
        view_results_page.back_button.clicked.connect(self.show_main_page)
        view_summary_page.back_button.clicked.connect(self.show_main_page)

    def show_instruction_page(self):
        self.stacked_widget.setCurrentIndex(self.INDEX_INSTR_PAGE)

    def show_view_results(self):
        self.stacked_widget.setCurrentIndex(self.INDEX_RESULTS_PAGE)

    def show_view_summary(self):
        self.stacked_widget.setCurrentIndex(self.INDEX_SUMMARY_PAGE)

    def show_main_page(self):
        self.stacked_widget.setCurrentIndex(self.INDEX_MAIN_PAGE)

def set_icon_winodws():
    # Determine the platform (Windows, macOS, Linux)
    current_platform = platform.system()
    # Set the log file directory based on the platform
    if current_platform == "Windows":
        myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    set_icon_winodws()
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
