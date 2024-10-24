import os
import subprocess
import json
import re
import humanize
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, 
                             QProgressBar, QTextEdit, QFileDialog, QMessageBox, QMenuBar, QMainWindow)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QAction  # Импортируем QAction из QtGui


class VideoCompressor(QThread):
    progress_signal = pyqtSignal(int, int, int)  # Отправляем текущее и общее количество кадров и индекс файла
    log_signal = pyqtSignal(str)
    complete_signal = pyqtSignal(str, int, float, int)

    def __init__(self, input_files, output_files, crf_value, ffmpegcmd, ffprobecmd):
        super().__init__()
        self.input_files = input_files
        self.output_files = output_files
        self.crf_value = crf_value
        self.ffmpegcmd = ffmpegcmd
        self.ffprobecmd = ffprobecmd
        
        if self.crf_value < 0:
            self.crf_value = 0
        elif self.crf_value > 51:
            self.crf_value = 51

    def run(self):
        for idx, (input_file, output_file) in enumerate(zip(self.input_files, self.output_files)):
            total_frames = self.get_total_frames(input_file)
            if total_frames == 0:
                self.log_signal.emit(f"Compression aborted for {input_file}: Unable to retrieve frame count.")
                continue

            command = [
                self.ffmpegcmd, "-i", input_file,
                "-vcodec", "libx265", "-crf", str(self.crf_value), "-preset", "slow",
                "-acodec", "copy", "-y", output_file
            ]

            self.log_signal.emit(f"Starting compression for {input_file} with CRF value: {self.crf_value}")
            
            # self.log_signal.emit(f"FFMpeg command: {' '.join(command)}")
            
            process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            frame_pattern = re.compile(r'frame=\s*(\d+)')

            while process.poll() is None:
                line = process.stderr.readline()
                match = frame_pattern.search(line)
                
                if match:
                    current_frame = int(match.group(1))
                    self.progress_signal.emit(current_frame, total_frames, idx)
                    self.log_signal.emit(f"File {idx+1}/{len(self.input_files)} - Current frame: {current_frame}/{total_frames}")
            
            process.communicate()

            if process.returncode != 0:
                self.log_signal.emit(f"Error: Compression failed for {input_file}.")
                continue

            compressed_size = os.path.getsize(output_file)
            original_size = os.path.getsize(input_file)
            
            compression_pct = (1 - compressed_size / original_size) * 100
            self.complete_signal.emit(output_file, compressed_size, compression_pct, idx)

    def get_total_frames(self, input_file):
        self.log_signal.emit(f"Getting total frames of the video {input_file}...")
        command = [
            self.ffprobecmd, "-v", "error", "-select_streams", "v:0",
            "-count_frames", "-show_entries", "stream=nb_read_frames",
            "-of", "json", input_file
        ]
        
        # self.log_signal.emit(f"FFProbe command: {' '.join(command)}")
        
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            probe_data = json.loads(result.stdout)
            return int(probe_data["streams"][0]["nb_read_frames"])
        except (KeyError, IndexError, json.JSONDecodeError):
            self.log_signal.emit(f"Failed to get total frames for {input_file}.")
            return 0

class CompressorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Video Compressor")

        # Центральный виджет
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.input_label = QLabel("Input Video Files:")
        self.input_path = QLineEdit()
        self.browse_button = QPushButton("Browse Files")
        self.browse_button.clicked.connect(self.browse_files)

        self.crf_label = QLabel("CRF Value (0-51):")
        self.crf_value = QLineEdit("20")

        self.output_label = QLabel("Output Folder:")
        self.output_path = QLineEdit()
        self.browse_output_button = QPushButton("Browse Output Folder")
        self.browse_output_button.clicked.connect(self.browse_output_folder)
        
        self.ffmpegcommand = QLabel("FFMPEG Command:")
        self.ffmpegcommandInput = QLineEdit("./ffmpeg.exe")
        
        self.ffprobecommand = QLabel("FFPROBE Command:")
        self.ffprobecommandInput = QLineEdit("./ffprobe.exe")
        

        self.progress_bars = []
        self.progress_labels = []
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)

        self.compress_button = QPushButton("Compress")
        self.compress_button.clicked.connect(self.start_compression)

        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.input_label)
        layout.addWidget(self.input_path)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.crf_label)
        layout.addWidget(self.crf_value)
        layout.addWidget(self.output_label)
        layout.addWidget(self.output_path)
        layout.addWidget(self.browse_output_button)
        layout.addWidget(self.ffmpegcommand)
        layout.addWidget(self.ffmpegcommandInput)
        layout.addWidget(self.ffprobecommand)
        layout.addWidget(self.ffprobecommandInput)
        layout.addWidget(self.status_log)
        layout.addWidget(self.compress_button)

        # Меню бар
        main_menu = self.menuBar()
        logs_menu = main_menu.addMenu('Files')

        # Действие для очистки логов и прогресса
        clear_logs_action = QAction('Clear logs and progress', self)
        logs_menu.addAction(clear_logs_action)
        clear_logs_action.triggered.connect(self.clear_logs_and_progress)
        
        show_info_action = QAction('Information', self)
        logs_menu.addAction(show_info_action)
        show_info_action.triggered.connect(self.show_info)
        
    
    def show_info(self):
        QMessageBox.information(self, "Information", "KRRSNK Video Compressor v0.1\nCreated by kararasenok_gd\n\nInputs:\nVideo File - File to compress\nCRF Value - how to compress a file. The higher the value, the worse the quality.\nOutput folder - folder, where located compressed file\nFFMPEG Command - FFMpeg command. Can be just ffmpeg (if FFMpeg bin folder in PATH variable) or path to ffmpeg.exe\nFFPROBE Command - same, but with FFProbe")

    def browse_files(self):
        file_dialog = QFileDialog(self)
        file_paths, _ = file_dialog.getOpenFileNames(self, "Select Video Files", "", "Video Files (*.mp4)")
        if file_paths:
            self.input_path.setText(';'.join(file_paths))

    def browse_output_folder(self):
        folder_dialog = QFileDialog(self)
        folder_path = folder_dialog.getExistingDirectory(self, "Select Output Folder")
        if folder_path:
            self.output_path.setText(folder_path)

    def log_status(self, message):
        self.status_log.append(message)

    def clear_logs_and_progress(self):
        # Очищаем логи
        self.status_log.clear()

        # Удаляем старые прогресс-бары и лейблы, если они есть
        for progress_bar in self.progress_bars:
            self.central_widget.layout().removeWidget(progress_bar)
            progress_bar.deleteLater()
        self.progress_bars.clear()

        for label in self.progress_labels:
            self.central_widget.layout().removeWidget(label)
            label.deleteLater()
        self.progress_labels.clear()

    def update_progress(self, current_frame, total_frames, idx):
        percent_complete = (current_frame / total_frames) * 100
        self.progress_bars[idx].setValue(int(percent_complete))

    def start_compression(self):
        input_files = self.input_path.text().split(';')
        crf_value = int(self.crf_value.text())
        output_folder = self.output_path.text()
        ffmpegRunCMD = self.ffmpegcommandInput.text()
        ffprobeRunCMD = self.ffprobecommandInput.text()

        if not input_files or not output_folder:
            QMessageBox.warning(self, "Input Error", "Please select input files and output folder.")
            return

        # Очищаем предыдущие логи и прогресс-бары
        self.clear_logs_and_progress()

        # Создаем выходные файлы
        output_files = []
        for input_file in input_files:
            input_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = os.path.join(output_folder, f"{input_name}_compressed.mp4")
            output_files.append(output_file)

        # Создаем прогресс-бары для каждого файла
        for file in input_files:
            progress_bar = QProgressBar()
            label = QLabel(f"Progress for {os.path.basename(file)}:")
            self.central_widget.layout().addWidget(label)
            self.central_widget.layout().addWidget(progress_bar)
            self.progress_bars.append(progress_bar)
            self.progress_labels.append(label)

        self.compressor_thread = VideoCompressor(input_files, output_files, crf_value, ffmpegRunCMD, ffprobeRunCMD)
        self.compressor_thread.progress_signal.connect(self.update_progress)
        self.compressor_thread.log_signal.connect(self.log_status)
        self.compressor_thread.complete_signal.connect(self.compression_complete)
        self.compressor_thread.start()

    def compression_complete(self, output_file, compressed_size, compression_pct, idx):
        self.log_status(f"File {idx+1} compressed successfully!")
        self.log_status(f"Compressed file: {output_file}")
        self.log_status(f"Compressed size: {humanize.naturalsize(compressed_size)}")
        self.log_status(f"Compression rate: {round(compression_pct, 2)}%")
        self.log_status("======================")

if __name__ == '__main__':
    app = QApplication([])
    window = CompressorApp()
    window.show()
    app.exec()
