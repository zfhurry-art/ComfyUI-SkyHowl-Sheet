"""Install the optional CPU head locator privately; global packages remain unchanged."""
from pathlib import Path
import subprocess, sys
if __name__ == '__main__':
    target = Path(__file__).resolve().parent / '.head-runtime'
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
                    '--no-deps', '--target', str(target), 'opencv-python-headless==4.10.0.84'], check=True)
    subprocess.run([sys.executable, '-c',
                    'import sys;sys.path.insert(0,sys.argv[1]);import cv2;assert hasattr(cv2,"CascadeClassifier");print("Private head locator",cv2.__version__)', str(target)], check=True)
