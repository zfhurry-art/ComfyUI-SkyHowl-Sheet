/** Original icon family. Left/right always means the direction on screen. */
const RECTS = {"face_front": [78, 37, 154, 207], "face_left": [692, 37, 170, 207], "face_right": [389, 37, 171, 207], "face_3q_left": [83, 349, 166, 207], "face_3q_right": [1000, 37, 180, 207], "face_back": [393, 348, 154, 207], "body_front": [731, 329, 107, 277], "body_left": [1076, 330, 48, 275], "body_back": [103, 644, 111, 277], "clothing_front": [405, 649, 130, 268], "clothing_back": [719, 650, 130, 267], "hands": [979, 695, 237, 178], "feet": [31, 1009, 253, 189]};
const MIRRORED = new Set(['body_left']);
let sequence = 0;
export function createArtwork(view, id, options = {}) {
 const rect = options.crop ?? RECTS[view];
 if (!rect) throw new RangeError(`Unknown artwork view: ${view}`);
 const frame=document.createElement('span'); frame.className='h3-artwork';
 frame.dataset.artwork=view; frame.dataset.artworkSource='skyhowl-original';
 frame.setAttribute('aria-hidden','true');
 if (MIRRORED.has(view)) frame.style.transform='scaleX(-1)';
 const ns='http://www.w3.org/2000/svg'; const svg=document.createElementNS(ns,'svg');
 svg.classList.add('h3-raster-avatar'); svg.setAttribute('viewBox',rect.join(' '));
 svg.setAttribute('preserveAspectRatio','xMidYMid meet');svg.setAttribute('overflow','hidden');
 const defs=document.createElementNS(ns,'defs');const clip=document.createElementNS(ns,'clipPath');
 clip.id=`skyhowl-original-${++sequence}`;clip.setAttribute('clipPathUnits','userSpaceOnUse');
 const box=document.createElementNS(ns,'rect');['x','y','width','height'].forEach((a,i)=>box.setAttribute(a,String(rect[i])));
 clip.append(box);defs.append(clip);svg.append(defs);
 const image=document.createElementNS(ns,'image');image.setAttribute('width','1254');image.setAttribute('height','1254');
 image.setAttribute('clip-path',`url(#${clip.id})`);image.setAttribute('href',new URL('./assets/skyhowl-original-atlas.png',import.meta.url).href);
 svg.append(image);frame.append(svg);return frame;
}
export function createGuideArtwork(panel, canvas, id) {
  const box = document.createElement('div');
  const [x, y, w, h] = panel.rect;
  Object.assign(box.style, {position: 'absolute', left: `${x/canvas[0]*100}%`, top: `${y/canvas[1]*100}%`, width: `${w/canvas[0]*100}%`, height: `${h/canvas[1]*100}%`});
  const art = createArtwork(panel.id, id, {crop: panel.crop, mirror: panel.mirror, garment: panel.source?.endsWith('_garment.png')});
  Object.assign(art.style, {width: '100%', height: '100%', display: 'block'});
  box.append(art); return box;
}
