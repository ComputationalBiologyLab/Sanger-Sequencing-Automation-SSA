import sys
from PyQt5.QtWidgets import (
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTableView,
)
from PyQt5.QtGui import QPixmap, QPalette, QColor, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
import os
from utils.results_utils import find_folders_gen
from utils.design_utils import mask_image
from post_proc.analyze_nt import *

from PIL import Image
import requests
from io import BytesIO

import requests
from PIL import Image, ImageOps
from PyQt5.QtWidgets import QLabel, QWidget, QApplication
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QByteArray
import sys
from PyQt5.QtWidgets import (
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTableView,
    QApplication,
)
from PyQt5.QtGui import QPixmap, QPalette, QColor, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QByteArray
import os
from utils.results_utils import find_folders_gen
from utils.design_utils import mask_image
from post_proc.analyze_nt import *
from PIL import Image
import requests
from io import BytesIO
import pandas as pd




class ResultsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.first_time_flag = True
        self.init_ui()
        self.current_df = None  # Store the current dataframe

    def init_ui(self):
        # Back button
        self.back_button = QPushButton("Back", self)
        self.back_button.setStyleSheet(
            "QPushButton { color: white; font-size: 14px; background-color: #008CBA; border: none; padding: 10px; border: none;border-radius: 10px; padding: 10px 20px;}"
            "QPushButton:hover { background-color: #006400; }"
        )

        url = 'https://i.ibb.co/k8zM2CB/zewail-City-logo-large-notxt.png'
        response = requests.get(url)
        imgdata = Image.open(BytesIO(response.content))
        with BytesIO() as buffer:
            imgdata.save(buffer, format="PNG")
            buffer.seek(0)
            img_bytes = buffer.read()
        qbytearray = QByteArray(img_bytes)
        image = QImage.fromData(qbytearray)
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio)
        self.ilabel = QLabel(self)
        self.ilabel.setPixmap(scaled_pixmap)
        self.ilabel.setAlignment(Qt.AlignCenter)

        # File type dropdown menu
        self.file_type_combo = QComboBox(self)
        self.file_type_combo.addItems(["nt", "nr"])
        self.file_type_combo.setStyleSheet("font-size: 20px; height: 40px;")  # Increase font size and height
        self.file_type_combo.activated.connect(self.on_folder_selected)
        
        # Folder dropdown menu
        self.folder_combo = QComboBox(self)
        self.folder_combo.activated.connect(self.on_folder_selected)

        # Apply styles to the combo box
        self.folder_combo.setStyleSheet("font-size: 25px;")  # Set font size
        font = self.folder_combo.font()
        font.setPointSize(70)
        self.folder_combo.setFont(font)

        # Table
        self.table_view = QTableView(self)
        self.table_view.setStyleSheet(
            "QTableView { background-color: white; alternate-background-color: #f0f0f0; color: black; }"
            "QTableView::item { color: black; }"
            "QHeaderView::section { background-color: grey; color: white; }"
        )

        # Download button
        self.download_button = QPushButton("Download as CSV", self)
        self.download_button.setStyleSheet(
            "QPushButton { color: white; font-size: 14px; background-color: #008CBA; border: none; padding: 10px; border: none;border-radius: 10px; padding: 10px 20px;}"
            "QPushButton:hover { background-color: #006400; }"
        )
        self.download_button.clicked.connect(self.download_csv)

        # Set the main layout and adjust spacing
        main_layout = QVBoxLayout(self)
        # Create a sub-layout for the back button and set its alignment
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.back_button, alignment=Qt.AlignTop | Qt.AlignLeft)

        # Add the button layout to the main layout
        main_layout.addLayout(button_layout)

        # Add the image, file type combo box, folder combo box, table, and download button to the main layout
        main_layout.addWidget(self.ilabel)
        main_layout.addWidget(self.file_type_combo)
        main_layout.addWidget(self.folder_combo)
        main_layout.addWidget(self.table_view)
        main_layout.addWidget(self.download_button)

        main_layout.setSpacing(12)  # Adjust the spacing as needed
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # Align the layout to the top and center
        self.setLayout(main_layout)

        # Load UI for the first time
        self.reload_ui()

    def show_warning_on_first_time(self):
        if not self.parent.selected_dir:
            self.show_custom_warning("Please select a folder from the main page.")

    def showEvent(self, event):
        # Override the showEvent method to reload the UI every time the widget is shown
        self.show_warning_on_first_time()
        self.reload_ui()

    def reload_ui(self):
        print("reload_ui", self.parent.selected_dir)
        if not self.parent.selected_dir:
            return
        if self.parent.selected_dir and not find_folders_gen(self.parent.selected_dir):
            self.show_custom_warning("Please select a folder that contains files named like \"Samplex_F.ab1\" or \"Samplex_R.ab1\"")

        self.get_all_folder_names()
        self.folder_combo.clear()
        self.folder_combo.addItems(self.folder_names)

    def get_all_folder_names(self):
        print("self.parent.selected_dir", self.parent.selected_dir)
        if self.parent.selected_dir:
            print("x1")
            self.folder_names = find_folders_gen(self.parent.selected_dir)
        print("get_all_folder_names", self.folder_names)

    def on_folder_selected(self):
        selected_folder = self.folder_combo.currentText()
        selected_file_type = self.file_type_combo.currentText()
        print(f"Selected Folder: {selected_folder}, Selected File Type: {selected_file_type}")
        xml_file_path = os.path.join(self.parent.selected_dir, selected_folder, f"blast_results_{selected_file_type}.xml")
        
        if not os.path.exists(xml_file_path):
            QMessageBox.warning(self, "Warning", f"No {selected_file_type} file found in the selected folder.")
            return
        
        if selected_file_type == "nt":
            df = get_results_for_nt(xml_file_path)
        else:
            df = get_results_for_nt(xml_file_path)

        self.current_df = df  # Store the dataframe
        self.display_dataframe(df)

    def view_summary(self):
        self.parent().stacked_widget.setCurrentIndex(2)  # Switch to the SummaryPage

    def display_dataframe(self, df):
        # Convert DataFrame to QStandardItemModel
        model = QStandardItemModel()

        # Set the column names
        model.setHorizontalHeaderLabels(list(df.columns))

        for row in range(df.shape[0]):
            items = [QStandardItem(str(df.iat[row, col])) for col in range(df.shape[1])]
            model.appendRow(items)

        # Set the model to the QTableView
        self.table_view.setModel(model)

    def download_csv(self):
        if self.current_df is not None:
            selected_folder = self.folder_combo.currentText()
            save_path = os.path.join(self.parent.selected_dir, selected_folder, "results.csv")
            self.current_df.to_csv(save_path, index=False)
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