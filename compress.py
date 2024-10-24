import os
import subprocess
import json
import re
import argparse

class VideoCompressor:
    def __init__(self, input_files, output_files, crf_value):
        self.input_files = input_files
        self.output_files = output_files
        self.crf_value = crf_value

    def run(self):
        for idx, (input_file, output_file) in enumerate(zip(self.input_files, self.output_files)):
            total_frames = self.get_total_frames(input_file)
            if total_frames == 0:
                print(f"Compression aborted for {input_file}: Unable to retrieve frame count.")
                continue

            command = [
                "ffmpeg", "-i", input_file,
                "-vcodec", "libx265", "-crf", str(self.crf_value), "-preset", "slow",
                "-acodec", "copy", "-y", output_file
            ]

            print(f"Starting compression for {input_file} with CRF value: {self.crf_value}")

            process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            frame_pattern = re.compile(r'frame=\s*(\d+)')

            while process.poll() is None:
                line = process.stderr.readline()
                match = frame_pattern.search(line)

                if match:
                    current_frame = int(match.group(1))
                    print(f"File {idx+1}/{len(self.input_files)} - Current frame: {current_frame}/{total_frames}")

            process.communicate()

            if process.returncode != 0:
                print(f"Error: Compression failed for {input_file}.")
                continue

            compressed_size = os.path.getsize(output_file)
            original_size = os.path.getsize(input_file)
            compression_pct = (1 - compressed_size / original_size) * 100
            print(f"File {idx+1} compressed successfully!")
            print(f"Compressed file: {output_file}")
            print(f"Compressed size: {compressed_size / (1024 * 1024):.2f} MB")
            print(f"Compression rate: {round(compression_pct, 2)}%")
            print("======================")

    def get_total_frames(self, input_file):
        print(f"Getting total frames of the video {input_file}...")
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
            print(f"Failed to get total frames for {input_file}.")
            return 0

def main():
    parser = argparse.ArgumentParser(description="Compress video files using FFmpeg.")
    parser.add_argument('--input', type=str, required=True, help="Semicolon-separated list of input video files.")
    parser.add_argument('--output', type=str, required=True, help="Output folder for compressed videos.")
    parser.add_argument('--crf', type=int, required=True, help="CRF value (0-51) for compression quality.")

    args = parser.parse_args()

    input_files = args.input.split(';')
    output_folder = args.output
    crf_value = args.crf

    output_files = [
        os.path.join(output_folder, f"{os.path.splitext(os.path.basename(input_file))[0]}_compressed.mp4")
        for input_file in input_files
    ]

    compressor = VideoCompressor(input_files, output_files, crf_value)
    compressor.run()

if __name__ == "__main__":
    main()
