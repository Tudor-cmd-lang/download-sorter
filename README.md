# Download Sorter

A simple Python utility that automatically sorts files in the Downloads folder by extension.

## Features
- Real-time folder monitoring
- Prevents overwriting files
- Ignores incomplete downloads
- Custom extension rules

## Requirements
Python 3.8+
watchdog

## Installation

pip install -r requirements.txt

## Usage

python download_sorter.py

## How It Works

The program watches the Downloads directory and automatically moves files into categorized folders such as:

- Documents
- Images
- Archives
- Audio
- Video
- Code

## Future Improvements

- Config file support
- Cross-platform packaging
- CLI options
- Logging system
