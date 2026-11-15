"""Optional face locator in a separate process; never changes ComfyUI's cv2 module."""
from pathlib import Path
import sys, json, io

def locate(array, box):
    import cv2
    import numpy as np
    if not getattr(cv2, 'data', None) or not hasattr(cv2, 'CascadeClassifier'):
        return box, 'foreground-no-cascades'
    gray = cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)
    candidates = []
    for cascade, flip in [('haarcascade_frontalface_default.xml', False),
                          ('haarcascade_profileface.xml', False), ('haarcascade_profileface.xml', True)]:
        classifier = cv2.CascadeClassifier(cv2.data.haarcascades + cascade)
        if classifier.empty():
            continue
        scan = cv2.flip(gray, 1) if flip else gray
        for x, y, w, h in classifier.detectMultiScale(scan, scaleFactor=1.1, minNeighbors=5,
                                                     minSize=(max(32, array.shape[1] // 12),) * 2):
            if flip:
                x = array.shape[1] - x - w
            candidates.append((int(x), int(y), int(w), int(h)))
    if not candidates:
        return box, 'foreground-no-face'
    x, y, w, h = max(candidates, key=lambda b: b[2] * b[3])
    bottom = min(box[3], max(y + h + max(3, round(h * .12)), box[1] + 1))
    top = min(box[1], y)
    border = np.concatenate((array[0], array[-1], array[:, 0], array[:, -1]))
    background = np.median(border, axis=0)
    mask = np.max(np.abs(array.astype(float) - background), axis=2) > 18
    inset = max(1, round(min(array.shape[:2]) * .003))
    mask[:, :inset] = False; mask[:, -inset:] = False
    columns = np.flatnonzero(mask[top:bottom].sum(axis=0) >= max(2, (bottom - top) * .007))
    if len(columns):
        return (min(int(columns[0]), x), top, max(int(columns[-1]) + 1, x + w), bottom), 'face-focused'
    return box, 'foreground-no-head-mask'

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent / '.head-runtime'))
    from PIL import Image
    import numpy as np
    array = np.asarray(Image.open(io.BytesIO(sys.stdin.buffer.read())).convert('RGB'))
    print(json.dumps(locate(array, tuple(json.loads(sys.argv[1])))))
