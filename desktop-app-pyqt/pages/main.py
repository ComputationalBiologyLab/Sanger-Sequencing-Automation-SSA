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
from utils.ssa_utils import *
from logic.ssa_logic import SangerLogicWorker, UpdateProgressBarSignal

from PIL import Image
import requests
from io import BytesIO
from PyQt5.QtWidgets import QLabel, QWidget, QApplication
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QByteArray

class MainPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lst_summary = []
        self.parent = parent

        self.update_progress_signal = UpdateProgressBarSignal()
        self.update_progress_signal.update_signal.connect(self.update_progress_bar)
        self.is_mode_ab1 = True
        self.init_ui()

    def init_ui(self):
        url = 'https://i.ibb.co/72M2qKY/cbc-unit-no-back-cropped.png'
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
        

        # Instructions
        # self.tlabel = QLabel('Please read the instructions file before using the software \n Developed by a Research group in Zewail City', self)
        self.tlabel = QLabel('Developed by BCB unit', self)
        self.tlabel.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.tlabel.setStyleSheet('color: white;')
        font = self.tlabel.font()
        font.setPointSize(14)
        self.tlabel.setFont(font)

        # Separator
        separator_line = QFrame(self)
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Sunken)
        separator_line.setStyleSheet('background-color: white;')

        # is send more than 100 requests/day?
        self.label_requests = QLabel('Number of requests:', self)
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)  # Adjust the font size as needed
        self.label_requests.setFont(font)
        self.label_requests.setStyleSheet('color: white;')
        
        self.radio_button_no_snd100 = QRadioButton("More than 100", self)
        self.radio_button_snd100 = QRadioButton("Less than 100", self)

        radio_button_snd100_font = self.radio_button_no_snd100.font()
        radio_button_snd100_font.setPointSize(14)
        self.radio_button_no_snd100.setFont(radio_button_snd100_font)
        self.radio_button_snd100.setFont(radio_button_snd100_font)
        self.radio_button_no_snd100.setStyleSheet('color: white;')
        self.radio_button_snd100.setStyleSheet('color: white;')
        self.radio_button_no_snd100.clicked.connect(self.calc_final_notes)
        self.radio_button_snd100.clicked.connect(self.calc_final_notes)

        radio_layout_snd100 = QHBoxLayout()
        radio_layout_snd100.addWidget(self.label_requests, stretch=1)
        radio_layout_snd100.addWidget(self.radio_button_no_snd100, stretch=1)
        radio_layout_snd100.addWidget(self.radio_button_snd100, stretch=1)
        self.radio_button_no_snd100.setChecked(True)

        # Blastnr/Blastnt/Both?
        self.label_blast_mode = QLabel('Blast mode: ', self)
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)  # Adjust the font size as needed
        self.label_blast_mode.setFont(font)
        self.label_blast_mode.setStyleSheet('color: white;')
        
        self.radio_button_blastnr = QRadioButton("Blastnr", self)
        self.radio_button_blastnt = QRadioButton("Blastnt", self)
        self.radio_button_blastBoth = QRadioButton("Both", self)

        radio_button_blastnr_font = self.radio_button_blastnr.font()
        radio_button_blastnr_font.setPointSize(12)
        self.radio_button_blastnr.setFont(radio_button_blastnr_font)
        self.radio_button_blastnt.setFont(radio_button_blastnr_font)
        self.radio_button_blastBoth.setFont(radio_button_blastnr_font)
        self.radio_button_blastnr.setStyleSheet('color: white;')
        self.radio_button_blastnt.setStyleSheet('color: white;')
        self.radio_button_blastBoth.setStyleSheet('color: white;')
        self.radio_button_blastnr.clicked.connect(self.calc_final_notes)
        self.radio_button_blastnt.clicked.connect(self.calc_final_notes)
        self.radio_button_blastBoth.clicked.connect(self.calc_final_notes)

        radio_layout_blast = QHBoxLayout()
        radio_layout_blast.addWidget(self.label_blast_mode, stretch=1)
        radio_layout_blast.addWidget(self.radio_button_blastnr, stretch=1)
        radio_layout_blast.addWidget(self.radio_button_blastnt, stretch=1)
        radio_layout_blast.addWidget(self.radio_button_blastBoth, stretch=1)

        # Create a button group for the "Blastnr/Blastnt/Both?" radio buttons
        radio_group_blast = QButtonGroup(self)
        radio_group_blast.addButton(self.radio_button_blastnr)
        radio_group_blast.addButton(self.radio_button_blastnt)
        radio_group_blast.addButton(self.radio_button_blastBoth)

        self.radio_button_blastBoth.setChecked(True)

        # Single/Paired/Both?
        self.label_reads = QLabel('Reads: ', self)
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)  # Adjust the font size as needed
        self.label_reads.setFont(font)
        self.label_reads.setStyleSheet('color: white;')
        
        self.radio_button_single = QRadioButton("Single", self)
        self.radio_button_paired = QRadioButton("Paired", self)
        self.radio_button_both = QRadioButton("Both", self)

        radio_button_single_font = self.radio_button_single.font()
        radio_button_single_font.setPointSize(12)
        self.radio_button_single.setFont(radio_button_single_font)
        self.radio_button_paired.setFont(radio_button_single_font)
        self.radio_button_both.setFont(radio_button_single_font)
        self.radio_button_single.setStyleSheet('color: white;')
        self.radio_button_paired.setStyleSheet('color: white;')
        self.radio_button_both.setStyleSheet('color: white;')

        radio_layout_single = QHBoxLayout()
        radio_layout_single.addWidget(self.label_reads, stretch=1)
        radio_layout_single.addWidget(self.radio_button_single, stretch=1)
        radio_layout_single.addWidget(self.radio_button_paired, stretch=1)
        radio_layout_single.addWidget(self.radio_button_both, stretch=1)

        # Create a button group for the "Single/Paired/Both?" radio buttons
        radio_group_single = QButtonGroup(self)
        radio_group_single.addButton(self.radio_button_single)
        radio_group_single.addButton(self.radio_button_paired)
        radio_group_single.addButton(self.radio_button_both)

        self.radio_button_both.setChecked(True)

        # Overwrite/Skip?
        self.label_overwrite = QLabel('Overwrite generated files: ', self)
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)  # Adjust the font size as needed
        self.label_overwrite.setFont(font)
        self.label_overwrite.setStyleSheet('color: white;')
        
        self.radio_button_overwrite = QRadioButton("Yes", self)
        self.radio_button_skip = QRadioButton("No", self)

        radio_button_overwrite_font = self.radio_button_overwrite.font()
        radio_button_overwrite_font.setPointSize(12)
        self.radio_button_overwrite.setFont(radio_button_overwrite_font)
        self.radio_button_skip.setFont(radio_button_overwrite_font)
        self.radio_button_overwrite.setStyleSheet('color: white;')
        self.radio_button_skip.setStyleSheet('color: white;')

        radio_layout_overwrite = QHBoxLayout()
        radio_layout_overwrite.addWidget(self.label_overwrite, stretch=1)
        radio_layout_overwrite.addWidget(self.radio_button_overwrite, stretch=1)
        radio_layout_overwrite.addWidget(self.radio_button_skip, stretch=1)

        # Create a button group for the "Overwrite/Skip?" radio buttons
        radio_group_overwrite = QButtonGroup(self)
        radio_group_overwrite.addButton(self.radio_button_overwrite)
        radio_group_overwrite.addButton(self.radio_button_skip)

        self.radio_button_skip.setChecked(True)

        ## Skip middle stage:
        self.checkbox_skip_middle_stage = QCheckBox("Skip low quality reads trimming", self)
        self.checkbox_skip_middle_stage.setStyleSheet('color: white; font-size: 12pt;')

        checkbox_layout = QVBoxLayout()
        checkbox_layout.addWidget(self.checkbox_skip_middle_stage, alignment=Qt.AlignCenter)  # Center the checkbox



        # Choose Folder Button
        self.btn_choose_folder = QPushButton("Choose Folder", self)
        self.btn_choose_folder.clicked.connect(self.choose_folder)
        self.btn_choose_folder.setStyleSheet('''
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

        # Start Sanger Button
        self.btn_start_sanger = QPushButton("Start Sanger", self)
        self.btn_start_sanger.clicked.connect(self.start_sanger)
        self.btn_start_sanger.setStyleSheet('''
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

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.btn_choose_folder)
        button_layout.addWidget(self.btn_start_sanger)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet('''
            QProgressBar {
                background-color: #202224;
                border: 2px solid white;
                border-radius: 10px;
                font-size: 16px;
                color: white;
                text-align: center;
            }
        ''')
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)


        # # Create a separator line between sections
        # separator_line2 = QFrame(self)
        # separator_line2.setFrameShape(QFrame.HLine)
        # separator_line2.setFrameShadow(QFrame.Sunken)
        # separator_line2.setStyleSheet('background-color: white;')



        # Summary 
        self.text_browser = QTextBrowser(self)
        self.text_browser.setStyleSheet('''
            QTextBrowser {
                background-color: #202224;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                font-size: 16px;
            }
        ''')
        self.text_browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Set size policy
        self.text_browser.setPlainText(
            "Please select a folder\n"
            "and then start sanger"
        )


        # Go to summary/reults
        self.btn_view_results = QPushButton("View Results", self)
        # self.btn_view_results.clicked.connect(self.view_results)
        self.btn_view_results.setStyleSheet('''
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

        # View Summary Button
        self.btn_view_summary = QPushButton("View Summary", self)
        # self.btn_view_summary.clicked.connect(self.view_summary)
        self.btn_view_summary.setStyleSheet('''
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

        navigation_layout = QHBoxLayout()
        navigation_layout.addWidget(self.btn_view_results)
        navigation_layout.addWidget(self.btn_view_summary)

        # Connect signals to the calc_final_notes method
        self.radio_button_no_snd100.clicked.connect(self.calc_final_notes)
        self.radio_button_snd100.clicked.connect(self.calc_final_notes)
        self.radio_button_blastnr.clicked.connect(self.calc_final_notes)
        self.radio_button_blastnt.clicked.connect(self.calc_final_notes)
        self.radio_button_blastBoth.clicked.connect(self.calc_final_notes)
        self.radio_button_single.clicked.connect(self.calc_final_notes)
        self.radio_button_paired.clicked.connect(self.calc_final_notes)
        self.radio_button_both.clicked.connect(self.calc_final_notes)
        self.radio_button_overwrite.clicked.connect(self.calc_final_notes)
        self.radio_button_skip.clicked.connect(self.calc_final_notes)

        # Set the main layout and adjust spacing
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.ilabel)
        main_layout.addWidget(self.tlabel)
        main_layout.addWidget(separator_line)
        main_layout.addLayout(radio_layout_snd100)
        main_layout.addLayout(radio_layout_blast)
        main_layout.addLayout(radio_layout_single)
        main_layout.addLayout(radio_layout_overwrite)
        main_layout.addLayout(checkbox_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.progress_bar)
        # main_layout.addLayout(separator_line2)
        main_layout.addWidget(self.text_browser)
        main_layout.addLayout(navigation_layout)
        main_layout.setSpacing(12)  # Adjust the spacing as needed
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # Align the layout to the top and center
        self.setLayout(main_layout)
        
        self.calc_final_notes()

    def calc_final_notes(self):
        self.lst_summary.clear()
        self.max_limit = 0
        if self.radio_button_snd100.isChecked():
            self.lst_summary.append("Notice it will sleep for the rest of the day after reaching 100 blast requests")
            self.max_limit = float('inf')
            self.lst_summary.append(f"Max Limit = {self.max_limit}")
        else:
            if self.radio_button_blastnr.isChecked() or self.radio_button_blastnt.isChecked():
                self.max_limit = 100
            else:
                self.max_limit = 50

            self.lst_summary.append(f"Max Limit = {self.max_limit}")

        if not self.parent.selected_dir:
            self.lst_summary.append("Please select the folder to inform you exactly how many files are to be processed")
        else:
            self.lst_summary.append(f"File selected: {self.parent.selected_dir}")
            
        self.update_summary_notes()

    def update_summary_notes (self):
        if not self.parent.selected_dir == "":
            has_fastq_file = any(file.endswith('.fastq') for file in os.listdir(self.parent.selected_dir))
            if has_fastq_file:
                self.is_mode_ab1 = False
                print("At least one .fastq file is present in the directory.")
                self.update_summary_notes_fastq()
            else:
                self.is_mode_ab1 = True
                print("No .fastq files found in the directory.")
                self.update_summary_notes_ab1()
            self.text_browser.clear()
            for info_item in self.lst_summary:
                    self.text_browser.append(info_item)
            self.text_browser.verticalScrollBar().setValue(self.text_browser.verticalScrollBar().maximum())
                
    def update_summary_notes_fastq(self):
        self.lst_summary.append(f"Mode: fastq files")
        if not self.parent.selected_dir == "":
            self.lst_summary.append(f"Folders with the same sample name will be generated")
            self.handle_fastq_files_gen_folders()
            additional_info = self.cal_summary_num_files(
                self.radio_button_overwrite.isChecked(),
                self.radio_button_single.isChecked(),
                self.radio_button_paired.isChecked(),
                self.radio_button_both.isChecked()
            )

            self.lst_summary.extend(additional_info)

        
    def update_summary_notes_ab1 (self):
        self.lst_summary.append(f"Mode: AB1 files")
        if not self.parent.selected_dir == "":

            # Calculate and append additional information
            additional_info = self.cal_summary_num_files(
                self.radio_button_overwrite.isChecked(),
                self.radio_button_single.isChecked(),
                self.radio_button_paired.isChecked(),
                self.radio_button_both.isChecked()
            )

            self.lst_summary.extend(additional_info)

        
    def handle_fastq_files_gen_folders(self):
        import re
        import shutil
        if not self.parent.selected_dir == "":
            selected_dir = self.parent.selected_dir
            files = os.listdir(selected_dir)
            
            pattern = re.compile(r'^(Sample\d+)([FR])\.fastq$')
            sample_files = {}
            for file in files:
                match = pattern.match(file)
                if match:
                    sample_prefix = match.group(1)
                    direction = match.group(2)
                    if sample_prefix not in sample_files:
                        sample_files[sample_prefix] = {'F': [], 'R': []}
                    sample_files[sample_prefix][direction].append(file)

            # Create folders and copy files
            for sample_prefix, directions in sample_files.items():
                new_folder_path = os.path.join(selected_dir, sample_prefix)
                os.makedirs(new_folder_path, exist_ok=True)
                
                # Copy forward reads
                for f_file in directions['F']:
                    shutil.copy2(os.path.join(selected_dir, f_file), new_folder_path)
                
                # Copy reverse reads if they exist
                for r_file in directions['R']:
                    shutil.copy2(os.path.join(selected_dir, r_file), new_folder_path)

    def cal_summary_num_files(self, is_overwrite, is_single, is_pair, is_both):
        if not self.parent.selected_dir == "":
            self.num_files_single, self.num_files_pair = find_num_files(self.parent.selected_dir, self.is_mode_ab1)

            self.num_files_all = self.num_files_single + self.num_files_pair
            sel_option = ""
            if self.radio_button_blastBoth.isChecked(): sel_option = "Both"
            elif self.radio_button_blastnr.isChecked(): sel_option = "Blastnr"
            elif self.radio_button_blastnt.isChecked(): sel_option = "Blastnt"
            self.num_files_single_gen, self.num_files_pair_gen = find_num_files_gen(
                self.parent.selected_dir, self.radio_button_blastnr.isChecked(), self.radio_button_blastnt.isChecked(), self.radio_button_blastBoth.isChecked(), self.is_mode_ab1)
            self.num_files_all_gen = self.num_files_single_gen + self.num_files_pair_gen

            if is_overwrite:
                self.num_files_single_proc = self.num_files_single if is_single or is_both else 0
                self.num_files_pair_proc = self.num_files_pair if is_pair or is_both else 0
                self.num_files_all_proc = self.num_files_single_proc + self.num_files_pair_proc
            else:
                self.num_files_single_proc = max(self.num_files_single - self.num_files_single_gen, 0) if is_single or is_both else 0
                self.num_files_pair_proc = max(self.num_files_pair - self.num_files_all_gen, 0) if is_pair or is_both else 0
                self.num_files_all_proc = self.num_files_single_proc + self.num_files_pair_proc
            self.num_blast_requests = self.calc_num_blast_request(self.radio_button_blastBoth.isChecked())
            return [
                f"# of files single = {self.num_files_single}, " +
                f"# of files pair = {self.num_files_pair}, and " +
                f"# of all files = {self.num_files_all}",
                "*"*20,
                f"# of files single generated = {self.num_files_single_gen}, " +
                f"# of files pair generated = {self.num_files_pair_gen}, and " +
                f"# of all files generated = {self.num_files_all_gen}",
                "*"*20,
                f"# of files single to be processed = {self.num_files_single_proc}, " +
                f"# of files pair to be processed = {self.num_files_pair_proc}, and " +
                f"# of all files to be processed = {self.num_files_all_proc}",
                "*"*20,
                f"# of blast requests to be sent = {self.num_blast_requests}"
            ]
        

    def calc_num_blast_request(self, is_both):
        return self.num_files_all_proc * 2 if is_both else self.num_files_all_proc 

    def choose_folder(self):
        folder_dialog = QFileDialog()
        folder_dialog.setFileMode(QFileDialog.Directory)
        folder_dialog.setOption(QFileDialog.ShowDirsOnly, True)

        if folder_dialog.exec_() == QFileDialog.Accepted:
            selected_folder = folder_dialog.selectedFiles()[0]
            print(f"Selected Folder: {selected_folder}")
            self.parent.selected_dir = selected_folder
            self.calc_final_notes()
            trigger_logger(selected_folder)
            

    def start_sanger(self):
        self.calc_final_notes()
        if self.parent.selected_dir == "":
            self.open_dlg_folder()
            return
        if self.num_files_all_proc <= 0:
            self.open_dlg_no_files()
            return
        elif self.num_files_all_proc > self.max_limit:
            self.open_dlg_greater_max()
            return
        elif not check_internet_connection():
            self.open_dlg_internet()
            return
        else:
            self.is_blastnr, self.is_blastnt, self.is_blastBoth = self.radio_button_blastnr.isChecked(), self.radio_button_blastnt.isChecked(), self.radio_button_blastBoth.isChecked()
            self.is_single, self.is_paired, self.is_singlePair_both = self.radio_button_single.isChecked(), self.radio_button_paired.isChecked(), self.radio_button_both.isChecked()
            self.is_overwrite = self.radio_button_overwrite.isChecked()
            self.skip_middle_stage_value = self.checkbox_skip_middle_stage.isChecked()
            self.progress_bar.setVisible(True)
            self.btn_choose_folder.setVisible(False)
            self.btn_start_sanger.setVisible(False)
            # self.update_progress_bar(0)
            
            # Create an instance of the background thread
            self.sanger_thread = QThread()

            # Move the worker object to the thread
            self.sanger_logic_worker = SangerLogicWorker(self.parent.selected_dir, self.skip_middle_stage_value,
                                                        self.is_blastnr, self.is_blastnt, self.is_blastBoth,
                                                        self.is_single, self.is_paired, self.is_singlePair_both,
                                                        self.is_overwrite, self.num_blast_requests, self.is_mode_ab1)

            self.sanger_logic_worker.moveToThread(self.sanger_thread)

            # Connect the worker signals to the thread
            self.sanger_logic_worker.update_progress_signal.connect(self.update_progress_bar)
            self.sanger_thread.started.connect(self.sanger_logic_worker.start_sanger_logic)

            # Start the thread
            self.sanger_thread.start()
            self.write_log_summary()
            

    def write_log_summary(self):
        write_log("is_blastnr, is_blastnt, is_blastBoth", self.is_blastnr, self.is_blastnt, self.is_blastBoth)
        write_log("is_single, is_both, is_singlePair_both", self.is_single, self.is_paired, self.is_singlePair_both)
        write_log("is_overwrite", self.is_overwrite)
        write_log("Skip Middle Stage Checkbox Value:", self.skip_middle_stage_value)
        write_log("Chosen folder", self.parent.selected_dir)

    def open_dlg_option(self):
        QMessageBox.warning(self, "Warning", "Please select either Single, Paired, or both")
        
    def open_dlg_greater_max(self):
        QMessageBox.warning(
            self,
            "Warning",
            "You exceeded the maximum number of files to be processed, and that will result in being banned from NCBI server. "
            "Either reduce the number of files or select 'Send more than 100 blast requests per day, "
        )

    def open_dlg_no_files(self):
        QMessageBox.warning(
            self,
            "Warning",
            "There are no files in the selected folder. "
            "Please select a folder that contains files named like 'Samplex_F.ab1' or 'Samplex_R.ab1'"
        )

    def open_dlg_option(self):
        self.show_custom_warning("Please select either Single, Paired, or both")

    def open_dlg_greater_max(self):
        message = (
            "You exceeded the maximum number of files to be processed, "
            "and that will result in being banned from NCBI server. "
            "Either reduce the number of files or select 'Send more than 100 blast requests per day'"
        )
        self.show_custom_warning(message)

    def open_dlg_no_files(self):
        message = (
            "There are no files in the selected folder. "
            "Please select a folder that contains files named like 'Samplex_F.ab1' or 'Samplex_R.ab1'"
        )
        self.show_custom_warning(message)

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

    def open_dlg_folder(self):
        self.show_custom_warning("Please select a folder that contain files named like \"Samplex_F.ab1\" or \"Samplex_R.ab1\"")

    def open_dlg_internet(self):
        self.show_custom_warning("No internet connection")

    def view_results(self):
        self.stacked_widget.setCurrentIndex(1)  # Switch to the ResultsPage

    def view_summary(self):
        self.stacked_widget.setCurrentIndex(2)  # Switch to the SummaryPage


    def update_progress_bar(self, value):
        write_log("Received in update_progress_bar:", value)
        # Slot to update the progress bar
        self.progress_bar.setValue(value)
        write_log("in update_progress_bar1")

