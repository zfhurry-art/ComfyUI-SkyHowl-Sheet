"""Independent view sampling and deterministic, CPU-only sheet composition."""
import json

from .core import compile_sheet, DEFAULT_JSON
PANELS_DEFAULT_JSON = json.dumps({**json.loads(DEFAULT_JSON), 'background': 'white'})
BACKGROUND_RGB = {'white': (255, 255, 255), 'gray': (128, 128, 128)}
from .qwen_compiler import VIEW_TEXT, CHOICES
from .semantic.reference_compiler import STYLE_PROMPTS
from .semantic.view_catalog_13 import VIEW_IDS
from .semantic.state_13 import applicable_settings


def sampling_size(view):
    if view.startswith('face_'):
        return 896, 1024
    if view.startswith('body_'):
        return 768, 1280
    if view.startswith('clothing_'):
        return 768, 1024
    return 1024, 768


def standalone_prompt(result, view):
    """No sheet coordinates, mannequins, layout images or other view requests."""
    state = result['state']
    view_instruction = VIEW_TEXT[view]
    if view.startswith('clothing_') and state['clothing_mode'] == 'worn':
        direction = 'FRONT' if view == 'clothing_front' else 'REAR'
        view_instruction = (f'{direction} CLOTHING DETAIL AS WORN by the same character. '
                            'Crop from neck to the complete lowest garment edge. Omit the head and feet. '
                            'Preserve the complete garment construction, colors and materials on this surface.')
    lines = [
        'Create exactly ONE standalone character reference image, not a collage or a character sheet.',
        view_instruction,
        'Image 1 is the character identity and appearance reference. Render the SAME character, '
        'with the same face, hairstyle, proportions, garments, materials, colors and accessories. '
        'Rotate this actual design into the requested view; do not redesign it. Preserve real asymmetries.',
        f"Use a uniform {'neutral middle gray #808080' if state.get('background') == 'gray' else 'pure white #FFFFFF'} seamless background, no gradient or cast shadow. Only the requested subject or detail "
        'belongs in the image. No grid, border, labels, extra views, inset portraits, extra people or mannequins.',
    ]
    if view.startswith('clothing_'):
        lines[2] = ('Image 1 supplies GARMENT DESIGN ONLY. Extract the empty outfit as a product photograph. '
                    'There is NO PERSON wearing it: no head, hair, face, neck, skin, hands, legs, feet, '
                    'body or mannequin. The neckline and sleeve openings are empty. '
                    'Retain garment construction, colors, materials and asymmetry only. '
                    'Ignore all identity, facial and hairstyle information in every reference.')
        lines.append('GARMENT ONLY, floating empty clothing. Remove the wearer completely, including '
                     'rear hair, topknot, head ornaments and any visible legs or shoes. '
                     'Do not crop a person at the neck; construct an empty neckline with no anatomy above it.')
    if view == 'feet':
        lines[2] = ('Image 1 supplies FOOTWEAR DESIGN ONLY. Extract exactly two isolated boots or shoes, '
                    'matching the reference material, color and construction. No complete person, '
                    'head, hair, torso, arms, hands, thighs, knees or outfit. Empty boot openings; '
                    'no legs inside the footwear. Fill the image with the pair of footwear.')
    if view == 'hands':
        lines[2] = ('Image 1 is a source photograph from which to EXTRACT THE HAND DESIGN ONLY. '
                    'Draw an isolated pair of the same character\'s hands, matching skin, fingers and any gloves. '
                    'The full person in image 1 must NOT be reproduced. Both complete hands dominate this close-up, '
                    'from wrist creases to fingertips; exclude forearms, torso, head, legs and full costume.')
        lines.append('Final composition: TWO ISOLATED HANDS ONLY, side by side on the requested uniform background. '
                     'Do not draw a person holding up hands. Enlarge both hands to fill the image.')
    if view == 'clothing_back':
        lines.append('STRICT REAR ELEVATION: camera directly behind the outfit, looking at the OUTSIDE BACK surface. Show rear neckline, back shoulder seams, back panels and rear hem. Front lapels, crossed front collar, chest ornaments and front closures must NOT appear. Preserve asymmetry physically; do not mirror the front. If the back is unseen, infer a restrained consistent construction rather than copying front details.')
    style = result.get('_style', 'none')
    lines.append(STYLE_PROMPTS[style] or 'Keep the rendering style of image 1.')
    if view.startswith('face_'):
        lines.append('One large complete head at the center of the image. Include the hairstyle top, '
                     'ears and chin, with only a short neck and minimal shoulder hints. No chest or torso. '
                     'Maximize head size within a small safe margin; never leave an empty lower half.')
    elif view.startswith('body_'):
        lines.append('One fully dressed complete figure, head through both feet. The complete outfit '
                     'must appear on the rotated character; never replace the person with a blank mannequin. '
                     'Leave a small safe margin above hair and beneath footwear.')
    for field in applicable_settings(state):
        value = state[field]
        if (field, value) in CHOICES:
            lines.append(CHOICES[field, value])
    scope = {
        'same_character': 'supplement the SAME character; the baseline wins conflicts',
        'face': 'face only', 'head': 'head and hair only',
        'clothing': 'garments only', 'clothing_front': 'front garment surfaces only',
        'clothing_back': 'rear garment surfaces only', 'hands': 'hands or gloves only',
        'footwear': 'feet or footwear only',
    }
    for item in result['reference_plan']:
        name = item['source']
        if name.startswith('reference_image_'):
            role = state.get('reference_roles', {}).get(name, 'same_character')
            lines.append(f"Image {item['picture_number']}: {scope[role]}. Do not transfer its pose, "
                         'background or camera. Keep the requested camera and crop.')
    for part, text in state['part_prompts'].items():
        if view in result.get('part_scopes', {}).get(part, ()):
            lines.append(f'Literal appearance detail for {part}, limited to this visible part:\n{text}')
    if view.startswith('clothing_'):
        lines.append('FINAL OVERRIDE: empty garment only. No human or mannequin parts, no head or hair above or behind the rear neckline. Garment-only scope overrides any request to retain the person or hairstyle.')
    if view == 'clothing_back':
        lines.append('FINAL CAMERA LOCK: REAR SIDE OF EMPTY GARMENT, product back photograph. '
                     'Show the plain rear collar seam and rear fabric panels. Never show the V-shaped '
                     'crossed front lapels, front neckline opening, chest, front sash knot or front closures. '
                     'Any front-facing design in Image 1 is reference evidence only, not the requested view. '
                     'Infer the unseen back conservatively. Do not reproduce the front product photograph.')
    if view.startswith('face_'):
        lines.append('FINAL HEAD FRAMING: complete head and hairstyle, a short neck, a small natural shoulder line and collar. '
                     'Include only the upper shoulder tips and a little collar clothing, no chest or extended torso. Use this same crop for '
                     'front, profile, three-quarter and rear head views. The rear must include the whole '
                     'hairstyle, nape and a small rear shoulder line. Keep the head dominant and maximize it with a small margin.')
    if view == 'face_back':
        lines.append('FINAL REAR HAIR LOCK: direct rear view of the SAME complete hairstyle. '
                     'Preserve reference hair length, tied sections, ponytail or bun placement, ornaments '
                     'and all loose hanging hair. Rotate the original hairstyle; never replace long hair '
                     'with a cropped short back-of-head haircut. Long hair must fall naturally down behind '
                     'the head and over the rear neck and shoulders. The nape and collar may be completely '
                     'hidden by the hair; never expose them by cutting, shortening or removing hair. '
                     'The lower frame may intersect continuing long hair at the shoulder level; this is '
                     'a portrait crop, not a shorter haircut. Preserve a small natural shoulder hint. '
                     'Face and eyes are not visible; do not turn the head toward the camera.')
    if view == 'feet':
        lines.append('FINAL SCOPE LOCK: TWO ISOLATED FOOTWEAR ITEMS ONLY; no person or full body. '
                     'This overrides any character identity or outfit request. Enlarge the footwear pair.')
    lines.append('Priority: requested single view and crop; compatible part details and appearance '
                 'choices; applicable dedicated references; same-character supplements; baseline. '
                 'Preserve lettering already present on garments, but add no captions.')
    return '\n'.join(lines)


def build_panel_plan(state_json, style='none', reference_presence=None):
    presence = reference_presence or {f'reference_image_{i}': False for i in range(1, 4)}
    sheet = compile_sheet(state_json, False, style, presence)
    items = []
    for view in sheet['state']['views']:
        state = {**sheet['state'], 'views': [view]}
        size = sampling_size(view)
        state['size'] = {**state['size'], 'mode': 'manual', 'manual_width': size[0], 'manual_height': size[1]}
        one = compile_sheet(json.dumps(state), False, style, presence)
        visible_parts = ({'head_hair', 'face'} if view.startswith('face_') else
                         {'hands'} if view == 'hands' else {'footwear'} if view == 'feet' else None)
        eligible = {name: present and (state.get('reference_roles', {}).get(name, 'same_character') == 'same_character'
                    or any(visible_parts is None or part in visible_parts
                           for part in one['reference_scopes'].get(name, {}))) for name, present in presence.items()}
        one = compile_sheet(json.dumps(state), False, style, eligible)
        one['_style'] = style
        items.append({'view': view, 'width': size[0], 'height': size[1],
                      'prompt': standalone_prompt(one, view), 'image_order': one['qwen_order']})
    plan = {'version': 5, 'mode': 'per_view', 'canvas': [sheet['width'], sheet['height']],
            'background': sheet['state'].get('background', 'white'),
            'panels': sheet['guide_geometry']['panels'],
            'samples': [{k: v for k, v in item.items() if k != 'prompt'} for item in items],
            'notes': 'Sample lists preserve view order; only real references enter the model.'}
    return sheet, items, plan


def panel_preview(state_json, use_layout_image=False, style='none', reference_presence=None):
    sheet, items, plan = build_panel_plan(state_json, style, reference_presence)
    return {**sheet, 'execution_mode': 'per_view', 'sampling_count': len(items),
            'panel_prompts': items, 'sheet_spec': plan,
            'prompt': '\n\n'.join(f"View {i + 1}: {item['view']}\n{item['prompt']}" for i, item in enumerate(items))}


class SkyHowlCharacterSheetPanels:
    CATEGORY = 'SkyHowl/Character Sheet'
    FUNCTION = 'compile'
    RETURN_TYPES = ('STRING', 'INT', 'INT', 'IMAGE', 'IMAGE', 'IMAGE', 'IMAGE', 'IMAGE', 'STRING')
    RETURN_NAMES = ('qwen_prompt', 'width', 'height', 'image_1', 'image_2', 'image_3', 'image_4', 'image_5', 'sheet_spec')
    OUTPUT_IS_LIST = (True, True, True, True, True, True, True, True, False)

    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {
            'state_json': ('STRING', {'default': PANELS_DEFAULT_JSON, 'multiline': True, 'dynamicPrompts': False}),
            'character_image': ('IMAGE',),
            'style': (list(STYLE_PROMPTS), {'default': 'none'}),
        }, 'optional': {f'reference_image_{i}': ('IMAGE',) for i in range(1, 4)}}

    def compile(self, state_json, character_image, style='none', **references):
        if character_image is None:
            raise ValueError('Connect a character reference image')
        if not hasattr(character_image, 'shape') or len(character_image.shape) != 4 or character_image.shape[0] != 1 or character_image.shape[-1] < 3:
            raise ValueError('Use one character reference image, not an image batch')
        presence = {f'reference_image_{i}': references.get(f'reference_image_{i}') is not None for i in range(1, 4)}
        _, items, plan = build_panel_plan(state_json, style, presence)
        slots = [[] for _ in range(5)]
        for item in items:
            packed = [character_image] + [references[name] for name in item['image_order'][1:]]
            for slot, image in zip(slots, packed + [None] * (5 - len(packed))):
                slot.append(image)
        return ([i['prompt'] for i in items], [i['width'] for i in items], [i['height'] for i in items],
                *slots, json.dumps(plan, ensure_ascii=False))


def estimate_background(array):
    import numpy as np
    border = np.concatenate((array[0], array[-1], array[:, 0], array[:, -1]))
    return np.median(border, axis=0)


def normalize_background(array, rgb):
    """Replace only edge-connected near-background pixels; retain enclosed light clothing."""
    import numpy as np
    from PIL import Image, ImageDraw
    bg = estimate_background(array)
    distance = np.max(np.abs(array.astype(float) - bg), axis=2)
    candidate = Image.fromarray(np.where(distance <= 14, 255, 0).astype('uint8')).copy()
    w, h = candidate.size
    # Flood from every edge segment, without crossing foreground outlines.
    for x in range(w):
        for y in (0, h - 1):
            if candidate.getpixel((x,y)) == 255: ImageDraw.floodfill(candidate, (x,y), 128)
    for y in range(h):
        for x in (0, w - 1):
            if candidate.getpixel((x,y)) == 255: ImageDraw.floodfill(candidate, (x,y), 128)
    result = array.copy()
    result[np.asarray(candidate) == 128] = rgb
    return result


def foreground_bbox(array):
    """White-background occupancy; a conservative fallback if the background is busy."""
    import numpy as np
    h, w = array.shape[:2]
    background = estimate_background(array)
    mask = np.max(np.abs(array.astype(float) - background), axis=2) > 14
    # Ignore isolated one-pixel borders and very sparse compression/shadow noise.
    inset = max(1, round(min(w, h) * .003))
    mask[:inset] = False; mask[-inset:] = False
    mask[:, :inset] = False; mask[:, -inset:] = False
    rows = np.flatnonzero(mask.sum(axis=1) >= max(2, w * .007))
    cols = np.flatnonzero(mask.sum(axis=0) >= max(2, h * .007))
    if not len(rows) or not len(cols):
        return (0, 0, w, h), mask, 'no-foreground-full-frame'
    return (int(cols[0]), int(rows[0]), int(cols[-1]) + 1, int(rows[-1]) + 1), mask, 'foreground'


def portrait_bbox(array, box, mask, view):
    """Use optional OpenCV face localization for head/neck focus, never mirror output."""
    import numpy as np
    if view == 'face_back':
        return box, 'rear-foreground'
    try:
        import cv2
    except ImportError:
        return box, 'foreground-no-opencv'
    if not getattr(cv2, 'data', None) or not hasattr(cv2, 'CascadeClassifier'):
        from pathlib import Path
        runtime = Path(__file__).resolve().parent / '.head-runtime'
        if (runtime / 'cv2').is_dir():
            import subprocess, sys, io
            from PIL import Image
            encoded = io.BytesIO(); Image.fromarray(array).save(encoded, format='PNG')
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('head_focus.py')), json.dumps(box)],
                                    input=encoded.getvalue(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    timeout=30, check=True)
            focused, method = json.loads(result.stdout)
            if len(focused) != 4 or not (0 <= focused[0] < focused[2] <= array.shape[1] and
                                         0 <= focused[1] < focused[3] <= array.shape[0]):
                raise ValueError('Invalid isolated head crop')
            return tuple(focused), method + '-isolated'
        return box, 'foreground-no-cascades'
    from .head_focus import locate
    return locate(array, box)


def validate_plan(plan, count):
    if plan.get('version') != 5 or plan.get('mode') != 'per_view':
        raise ValueError('Expected a per-view sheet plan')
    width, height = plan['canvas']
    if any(type(v) is not int or v < 32 or v > 8192 or v % 32 for v in (width, height)) or width * height > 16777216:
        raise ValueError('Invalid sheet canvas')
    panels = plan['panels']
    if not 1 <= count <= 13 or len(panels) != count or len(plan.get('samples', [])) != count:
        raise ValueError('Generated image count does not match selected views; refusing to repeat or drop views')
    ids = [p['id'] for p in panels]
    if len(set(ids)) != count or set(ids) - set(VIEW_IDS) or ids != [s['view'] for s in plan['samples']]:
        raise ValueError('Invalid view order in sheet plan')
    for index, p in enumerate(panels):
        l, t, r, b = p['bounds']
        if any(type(v) is not int for v in (l, t, r, b)) or not (0 <= l < r <= width and 0 <= t < b <= height):
            raise ValueError('Panel outside canvas')
        for q in panels[index + 1:]:
            x, y, xx, yy = q['bounds']
            if min(r, xx) > max(l, x) and min(b, yy) > max(t, y):
                raise ValueError('Overlapping panels')


class SkyHowlSheetCompose:
    CATEGORY = 'SkyHowl/Character Sheet'
    FUNCTION = 'compose'
    INPUT_IS_LIST = True
    RETURN_TYPES = ('IMAGE', 'STRING')
    RETURN_NAMES = ('sheet_image', 'composition_report')

    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'images': ('IMAGE',), 'sheet_spec': ('STRING', {'forceInput': True}),
                             'draw_frames': ('BOOLEAN', {'default': False})}}

    def compose(self, images, sheet_spec, draw_frames):
        import numpy as np
        import torch
        from PIL import Image, ImageDraw, ImageOps
        if not sheet_spec or any(x != sheet_spec[0] for x in sheet_spec):
            raise ValueError('Conflicting or missing sheet plans')
        plan = json.loads(sheet_spec[0])
        validate_plan(plan, len(images))
        width, height = plan['canvas']
        background = 'white'
        if background not in BACKGROUND_RGB: raise ValueError('Unknown background')
        # Sample only near-white edge pixels; leave every source pixel untouched.
        edge_colors = []
        for tensor in images:
            if not isinstance(tensor, torch.Tensor) or tensor.ndim != 4 or tensor.shape[0] != 1 or tensor.shape[-1] < 3:
                raise ValueError('Each view must contain exactly one RGB image')
            arr = tensor[0, :, :, :3].detach().cpu().numpy()
            if not np.isfinite(arr).all(): raise ValueError('Non-finite generated image')
            edges = np.concatenate((arr[0], arr[-1], arr[:, 0], arr[:, -1]))
            candidates = edges[(edges.min(axis=1) >= .90) & (edges.max(axis=1)-edges.min(axis=1) <= .06)]
            if len(candidates) >= max(8, len(edges)//5):
                edge_colors.append(np.median(candidates, axis=0))
        rgb = tuple(np.clip(np.rint(np.median(edge_colors, axis=0)*255), 0, 255).astype(int)) if edge_colors else (255,255,255)
        canvas = Image.new('RGB', (width, height), rgb)
        draw = ImageDraw.Draw(canvas)
        details = []
        prepared = []
        for p, tensor in zip(plan['panels'], images):
            if not isinstance(tensor, torch.Tensor) or tensor.ndim != 4 or tensor.shape[0] != 1 or tensor.shape[-1] < 3:
                raise ValueError('Each view must contain exactly one RGB image')
            a = tensor[0, :, :, :3].detach().cpu().numpy()
            if not np.isfinite(a).all():
                raise ValueError('Non-finite generated image')
            a = (np.clip(a, 0, 1) * 255).round().astype(np.uint8)
            box, mask, method = foreground_bbox(a)
            if method == 'no-foreground-full-frame':
                raise ValueError(f"Generated {p['id']} is blank; refusing to compose an empty view")
            # Rectangular whitespace trim only: never replace pixels or create a matte.
            x0, y0, x1, y1 = box
            pad = max(2, round(min(x1-x0, y1-y0) * .012))
            box = (max(0,x0-pad), max(0,y0-pad), min(a.shape[1],x1+pad), min(a.shape[0],y1+pad))
            method = 'rectangular-margin-trim-no-matte'
            image = Image.fromarray(a).crop(box)
            l, t, r, b = p['bounds']
            inset = max(0, round(min(r - l, b - t) * .025))
            available = (max(1, r - l - 2 * inset), max(1, b - t - 2 * inset))
            group = ('head' if p['id'].startswith('face_') else
                     'body' if p['id'].startswith('body_') else
                     'clothing' if p['id'].startswith('clothing_') else p['id'])
            capacity = min(available[1], available[0] * image.height / image.width)
            prepared.append((p, image, available, group, capacity, box, method, a.shape))
        targets = {}
        for p, image, available, group, capacity, box, method, shape in prepared:
            targets[group] = min(targets.get(group, capacity), capacity)
        for p, image, available, group, capacity, box, method, shape in prepared:
            l, t, r, b = p['bounds']
            target = max(1, int(targets[group]))
            size = (max(1, round(image.width * target / image.height)), target)
            image = image.resize(size, Image.Resampling.LANCZOS)
            position = (l + (r - l - image.width) // 2, t + (b - t - image.height) // 2)
            canvas.paste(image, position)
            details.append({'view': p['id'], 'source_size': [shape[1], shape[0]], 'crop': box,
                            'method': method, 'placed': [*position, image.width, image.height],
                            'bounds': p['bounds'], 'scale_group': group, 'target_height': target})
        report = json.dumps({'mode': 'per_view', 'canvas': [width, height], 'view_count': len(images),
                             'panels': details}, ensure_ascii=False)
        output = torch.from_numpy(np.asarray(canvas, dtype=np.float32) / 255).unsqueeze(0)
        return {'ui': {'text': [report]}, 'result': (output, report)}
