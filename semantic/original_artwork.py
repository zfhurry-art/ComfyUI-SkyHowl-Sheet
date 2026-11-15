"""Shared screen-facing camera artwork. No upstream artwork is loaded here."""
import json
from pathlib import Path
DATA=json.loads((Path(__file__).resolve().parents[1]/'web/assets/ORIGINAL-ARTWORK.json').read_text())
RECTS=DATA['rects']
MIRRORED_VIEWS=set(DATA['mirrored_views'])
