# krrsnk-video-compressor

A simple program for compressing video files using FFMpeg. This repository provides three main variants:
- `compress.py`: CLI-based video compressor.
- `compressGUI.py`: Tkinter-based GUI for video compression.
- `compressQT.py`: PyQt6-based GUI for video compression.

## How to Compile to EXE

To compile the scripts to standalone executables, use `PyInstaller` with the following commands:

```bash
pyinstaller --noconfirm --onefile --windowed --name "VideoCompressTK" "compressGUI.py"
pyinstaller --noconfirm --onefile --windowed --name "VideoCompressQT" "compressQT.py"
pyinstaller --noconfirm --onefile --console --name "VideoCompress" "compress.py"
```

## Installation

### Releases

1. Go to [releases](https://github.com/kararasenok-gd/krrsnk-video-compressor/releases)
2. Download installer or portable version
3. Run installer and install program or unzip archive somewhere

**NOTE: I'm not sure if it works. On my computer it works fine. If it doesn't, please report the issue in [issues tab](https://github.com/kararasenok-gd/krrsnk-video-compressor/issues).**

### Manual

1. Clone the repository:
   ```bash
   git clone https://github.com/kararasenok-gd/krrsnk-video-compressor.git
   ```
2. Install dependencies:
   - For `compress.py`:
     ```bash
     pip install argparse
     ```
   - For `compressGUI.py`:
     ```bash
     pip install humanize tk
     ```
   - For `compressQT.py`:
     ```bash
     pip install humanize PyQt6
     ```

3. Run the script:
   - CLI version:
     ```bash
     python compress.py
     ```
   - Tkinter GUI version:
     ```bash
     python compressGUI.py
     ```
   - PyQt6 GUI version:
     ```bash
     python compressQT.py
     ```

**NOTE: if you install program using manual method, you need download FFMpeg and FFProbe and move it in the same folder with the script. Or just make sure that path to ffmpeg `bin` folder is in PATH variable and replace `./ffmpeg.exe` with `ffmpeg` in QT script. And yeah, i recomended to use installer or portable version cuz it's already have FFMpeg in it.**

## Tested Environments

| Platform       | Supported Scripts         | Notes                          |
|----------------|---------------------------|--------------------------------|
| Windows        | All scripts               | Fully tested                   |
| Linux          | All scripts               | Experimental                   |
| macOS          | All scripts               | Experimental                    |
| Termux (Android)| `compress.py`            | Only CLI version is supported  |

## Updates

| Script          | Update Frequency             |
|-----------------|------------------------------|
| `compress.py`   | Rare updates                 |
| `compressGUI.py` | Rare updates                 |
| `compressQT.py` | Frequent updates             |

