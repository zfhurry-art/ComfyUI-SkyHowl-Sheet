"""Compatibility guide renderer using only the project original atlas."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from .original_artwork import DATA, RECTS, MIRRORED_VIEWS
ATLAS_PATH = Path(__file__).resolve().parents[1] / 'web/assets' / DATA['file']
ATLAS_CROPS = {key: tuple(rect) for key, rect in RECTS.items()}
def render_layout_image(layout, *, multi_reference=False, clothing_mode='worn'):
    width, height = layout['canvas']
    canvas = Image.new('RGB', (width, height), 'white');draw = ImageDraw.Draw(canvas)
    with Image.open(ATLAS_PATH) as source: atlas = source.convert('RGBA')
    for panel in layout['panels']:
        x,y,w,h=panel['rect'];l,t,r,b=round(x*width),round(y*height),round((x+w)*width),round((y+h)*height)
        if not (multi_reference and clothing_mode=='garment' and panel['id'].startswith('clothing_')):
            cx,cy,cw,ch=RECTS[panel['id']];art=atlas.crop((cx,cy,cx+cw,cy+ch))
            if panel['id'] in MIRRORED_VIEWS:art=ImageOps.mirror(art)
            art=ImageOps.contain(art,(max(1,r-l),max(1,b-t)),Image.Resampling.LANCZOS)
            canvas.paste(art,(l+(r-l-art.width)//2,t+(b-t-art.height)//2),art)
        draw.rectangle((l,t,max(l,r-1),max(t,b-1)),outline='black',width=1)
    return canvas
