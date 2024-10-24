import os
import subprocess
import json
import re
import humanize
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread

class VideoCompressor(Thread):
    def __init__(self, input_files, output_files, crf_value, progress_callback, log_callback, complete_callback):
        super().__init__()
        self.input_files = input_files
        self.output_files = output_files
        self.crf_value = crf_value
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.complete_callback = complete_callback

    def run(self):
        for idx, (input_file, output_file) in enumerate(zip(self.input_files, self.output_files)):
            total_frames = self.get_total_frames(input_file)
            if total_frames == 0:
                self.log_callback(f"Compression aborted for {input_file}: Unable to retrieve frame count.")
                continue

            command = [
                "ffmpeg", "-i", input_file,
                "-vcodec", "libx265", "-crf", str(self.crf_value), "-preset", "slow",
                "-acodec", "copy", "-y", output_file
            ]

            self.log_callback(f"Starting compression for {input_file} with CRF value: {self.crf_value}")
            
            process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            frame_pattern = re.compile(r'frame=\s*(\d+)')

            while process.poll() is None:
                line = process.stderr.readline()
                match = frame_pattern.search(line)
                
                if match:
                    current_frame = int(match.group(1))
                    self.progress_callback(current_frame, total_frames, idx)
                    self.log_callback(f"File {idx+1}/{len(self.input_files)} - Current frame: {current_frame}/{total_frames}")
            
            process.communicate()

            if process.returncode != 0:
                self.log_callback(f"Error: Compression failed for {input_file}.")
                continue

            compressed_size = os.path.getsize(output_file)
            original_size = os.path.getsize(input_file)
            
            compression_pct = (1 - compressed_size / original_size) * 100
            self.complete_callback(output_file, compressed_size, compression_pct, idx)

    def get_total_frames(self, input_file):
        self.log_callback(f"Getting total frames of the video {input_file}...")
        command = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-count_frames", "-show_entries", "stream=nb_read_frames",
            "-of", "json", input_file
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            probe_data = json.loads(result.stdout)
            return int(probe_data["streams"][0]["nb_read_frames"])
        except (KeyError, IndexError, json.JSONDecodeError):
            self.log_callback(f"Failed to get total frames for {input_file}.")
            return 0


class CompressorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Video Compressor")

        self.input_label = tk.Label(self, text="Input Video Files:")
        self.input_label.pack()

        self.input_path = tk.Entry(self, width=50)
        self.input_path.pack()

        self.browse_button = tk.Button(self, text="Browse Files", command=self.browse_files)
        self.browse_button.pack()

        self.crf_label = tk.Label(self, text="CRF Value (0-51):")
        self.crf_label.pack()

        self.crf_value = tk.Entry(self)
        self.crf_value.insert(0, "20")
        self.crf_value.pack()

        self.output_label = tk.Label(self, text="Output Folder:")
        self.output_label.pack()

        self.output_path = tk.Entry(self, width=50)
        self.output_path.pack()

        self.browse_output_button = tk.Button(self, text="Browse Output Folder", command=self.browse_output_folder)
        self.browse_output_button.pack()

        self.status_log = tk.Text(self, height=10, state=tk.DISABLED)
        self.status_log.pack()

        self.compress_button = tk.Button(self, text="Compress", command=self.start_compression)
        self.compress_button.pack()

        self.progress_bars = []
        self.progress_labels = []

    def browse_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Video Files", "*.mp4")])
        if file_paths:
            self.input_path.delete(0, tk.END)
            self.input_path.insert(0, ';'.join(file_paths))

    def browse_output_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_path.delete(0, tk.END)
            self.output_path.insert(0, folder_path)

    def log_status(self, message):
        self.status_log.config(state=tk.NORMAL)
        self.status_log.insert(tk.END, message + '\n')
        self.status_log.config(state=tk.DISABLED)

    def clear_logs_and_progress(self):
        self.status_log.config(state=tk.NORMAL)
        self.status_log.delete(1.0, tk.END)
        self.status_log.config(state=tk.DISABLED)

        for progress_bar in self.progress_bars:
            progress_bar.pack_forget()
        self.progress_bars.clear()

        for label in self.progress_labels:
            label.pack_forget()
        self.progress_labels.clear()

    def update_progress(self, current_frame, total_frames, idx):
        percent_complete = (current_frame / total_frames) * 100
        self.progress_bars[idx]['value'] = int(percent_complete)

    def start_compression(self):
        input_files = self.input_path.get().split(';')
        crf_value = int(self.crf_value.get())
        output_folder = self.output_path.get()

        if not input_files or not output_folder:
            messagebox.showwarning("Input Error", "Please select input files and output folder.")
            return

        self.clear_logs_and_progress()

        output_files = []
        for input_file in input_files:
            input_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = os.path.join(output_folder, f"{input_name}_compressed.mp4")
            output_files.append(output_file)

        for file in input_files:
            progress_bar = ttk.Progressbar(self, length=300)
            label = tk.Label(self, text=f"Progress for {os.path.basename(file)}:")
            label.pack()
            progress_bar.pack()
            self.progress_bars.append(progress_bar)
            self.progress_labels.append(label)

        self.compressor_thread = VideoCompressor(
            input_files, output_files, crf_value,
            self.update_progress, self.log_status, self.compression_complete
        )
        self.compressor_thread.start()

    def compression_complete(self, output_file, compressed_size, compression_pct, idx):
        self.log_status(f"File {idx+1} compressed successfully!")
        self.log_status(f"Compressed file: {output_file}")
        self.log_status(f"Compressed size: {humanize.naturalsize(compressed_size)}")
        self.log_status(f"Compression rate: {round(compression_pct, 2)}%")
        self.log_status("======================")


if __name__ == '__main__':
    app = CompressorApp()
    app.mainloop()
