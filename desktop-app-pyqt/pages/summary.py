# Import necessary libraries
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QMessageBox,
)
from PyQt5.QtGui import QPalette, QColor, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
import pandas as pd
from utils.results_utils import find_folders_gen
from utils.design_utils import mask_image
from post_proc.analyze_nt import *
from post_proc.summary_utils import *
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTableView, QItemDelegate
from PyQt5.QtGui import QBrush, QColor

class WhiteBackgroundDelegate(QItemDelegate):
    def paint(self, painter, option, index):
        option.backgroundBrush = QBrush(QColor(Qt.white))
        option.palette.setColor(option.palette.Text, QColor(Qt.black))
        super().paint(painter, option, index)

class SummaryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.summary_df = None
        self.first_time_flag = True
        self.init_ui()

    def init_ui(self):
        # Back button
        self.back_button = QPushButton("Back", self)
        self.back_button.setStyleSheet(
            "QPushButton { color: white; font-size: 14px; background-color: #008CBA; border: none; padding: 10px; border: none;border-radius: 10px; padding: 10px 20px;}"
            "QPushButton:hover { background-color: #006400; }"
        )

        # QLabel to display the summary
        self.summary_label = QLabel(self)
        self.summary_label.setText("Summary of Folders")

        # QTableView to display the summarized DataFrame
        self.table_view = QTableView(self)

        # Apply style sheet to set the background and text color
        self.table_view.setStyleSheet("QTableView QTableWidget QTableCornerButton::section { background-color: grey; }"
                                    "QTableView QHeaderView::section { background-color: grey; color: white; }"
                                    "QTableView { alternate-background-color: white; color: white; }")



        # Set the main layout and adjust spacing
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.back_button, alignment=Qt.AlignTop | Qt.AlignLeft)
        main_layout.addWidget(self.summary_label, alignment=Qt.AlignTop | Qt.AlignHCenter)
        main_layout.addWidget(self.table_view)
        main_layout.setSpacing(12)  # Adjust the spacing as needed
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # Align the layout to the top and center
        self.setLayout(main_layout)

        # Load UI for the first time

    def showEvent(self, event):
        # self.show_warning_on_except_first_time()
        self.reload_ui()

    def show_warning_on_except_first_time(self):
        print("w1")
        # if self.first_time_flag:
        #     print("w2")
        #     self.first_time_flag = False 
        #     return
        # elif not self.parent.selected_dir:
        #     print("w3")
        if not self.parent.selected_dir:
            self.show_custom_warning("Please select a folder from the main page.")


    def reload_ui(self):
        print("nopass")
        if not self.parent.selected_dir:
            self.show_custom_warning("Please select a folder from the main page.")
        if self.parent.selected_dir and not find_folders_gen(self.parent.selected_dir):
            self.show_custom_warning("Please select a folder that contain files named like \"Samplex_F.ab1\" or \"Samplex_R.ab1\"")
        elif self.parent.selected_dir:
            print("pass")
            # Summarize folders if a directory is selected
            self.summary_df = summarize_folders(self.parent.selected_dir)

            # Convert DataFrame to QStandardItemModel
            model = QStandardItemModel()

            # Set the column names
            model.setHorizontalHeaderLabels(list(self.summary_df.columns))

            for row in range(self.summary_df.shape[0]):
                items = [QStandardItem(str(self.summary_df.iat[row, col])) for col in range(self.summary_df.shape[1])]
                model.appendRow(items)

            # Set the model to the QTableView
            self.table_view.setModel(model)

    def show_custom_warning(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Warning")
        msg_box.setText(message)

        # Set text color to white
        msg_box.setStyleSheet("QLabel{ color: black; padding: 15px }")

        # Set button background color to green and make it rounded
        palette = QPalette()
        palette.setColor(QPalette.Button, QColor(0, 128, 0))  # Green color
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # White color
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))  # White color for text
        msg_box.setPalette(palette)

        # Create an OK button
        ok_button = msg_box.addButton("OK", QMessageBox.AcceptRole)
        ok_button.setStyleSheet("background-color: #008000; border-radius: 5px; padding: 5px;")

        # Show the message box and wait for the user's response
        result = msg_box.exec_()

        if result == QMessageBox.Accepted:
            # OK button was clicked, do something if needed
            pass
