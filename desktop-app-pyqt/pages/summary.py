from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableView, QMessageBox, QComboBox, QItemDelegate
)
from PyQt5.QtGui import QPalette, QColor, QStandardItemModel, QStandardItem, QBrush, QFont
from PyQt5.QtCore import Qt
import pandas as pd
import os
from utils.results_utils import find_folders_gen
from utils.design_utils import mask_image
from post_proc.analyze_nt import *
from post_proc.summary_utils import *

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
            "QPushButton { color: white; font-size: 14px; background-color: #008CBA; border: none; padding: 10px; border-radius: 10px; }"
            "QPushButton:hover { background-color: #006400; }"
        )

        # QLabel to display the summary
        self.summary_label = QLabel(self)
        self.summary_label.setText("Summary of results")
        font = QFont()
        font.setPointSize(20)
        self.summary_label.setFont(font)

        # QTableView to display the summarized DataFrame
        self.table_view = QTableView(self)

        # Apply style sheet to set the background and text color
        self.table_view.setStyleSheet(
            "QTableView { background-color: white; alternate-background-color: #f0f0f0; color: black; }"
            "QTableView::item { color: black; }"
            "QHeaderView::section { background-color: grey; color: white; }"
        )

        # Dropdown to select file type
        self.file_type_dropdown = QComboBox(self)
        self.file_type_dropdown.addItems(["Select file type", "nt", "nr"])
        self.file_type_dropdown.currentIndexChanged.connect(self.reload_ui)

        # Download button
        self.download_button = QPushButton("Download as CSV", self)
        self.download_button.setStyleSheet(
            "QPushButton { color: white; font-size: 14px; background-color: #008CBA; border: none; padding: 10px; border-radius: 10px; }"
            "QPushButton:hover { background-color: #006400; }"
        )
        self.download_button.clicked.connect(self.download_csv)

        # Set the main layout and adjust spacing
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.back_button, alignment=Qt.AlignTop | Qt.AlignLeft)
        main_layout.addWidget(self.summary_label, alignment=Qt.AlignTop | Qt.AlignHCenter)
        main_layout.addWidget(self.file_type_dropdown, alignment=Qt.AlignTop | Qt.AlignHCenter)
        main_layout.addWidget(self.table_view)
        main_layout.addWidget(self.download_button)
        main_layout.setSpacing(12)  # Adjust the spacing as needed
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # Align the layout to the top and center
        self.setLayout(main_layout)

    def showEvent(self, event):
        self.reload_ui()

    def reload_ui(self):
        if not self.parent.selected_dir:
            self.show_custom_warning("Please select a folder from the main page.")
        elif not find_folders_gen(self.parent.selected_dir):
            self.show_custom_warning("Please select a folder that contain files named like \"Samplex_F.ab1\" or \"Samplex_R.ab1\"")
        else:
            file_type = self.file_type_dropdown.currentText()
            if file_type not in ["nt", "nr"]:
                return

            self.summary_df = summarize_folders(self.parent.selected_dir, file_type)

            if self.summary_df.empty:
                self.show_custom_warning(f"No files of type '{file_type}' found.")
                return

            # Convert DataFrame to QStandardItemModel
            model = QStandardItemModel()

            # Set the column names
            model.setHorizontalHeaderLabels(list(self.summary_df.columns))

            for row in range(self.summary_df.shape[0]):
                items = [QStandardItem(str(self.summary_df.iat[row, col])) for col in range(self.summary_df.shape[1])]
                model.appendRow(items)

            # Set the model to the QTableView
            self.table_view.setModel(model)

    def download_csv(self):
        if self.summary_df is not None:
            save_path = os.path.join(self.parent.selected_dir, "summary_results.csv")
            self.summary_df.to_csv(save_path, index=False)
            QMessageBox.information(self, "Success", f"CSV file saved to: {save_path}")
        else:
            QMessageBox.warning(self, "Warning", "No data to save.")

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
