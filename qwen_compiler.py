"""Qwen static-image compiler. The original ReferenceV13 compiler owns all state/layout semantics."""
import json
VIEW_TEXT={
 'face_front':'FRONT HEAD-AND-NECK CLOSE-UP. Face looks straight at camera; both eyes visible. Tight head-and-neck framing. NO chest, waist, legs or feet.',
 'face_left':'PROFILE HEAD-AND-NECK CLOSE-UP, facing LEFT in the image. Nose points to the LEFT edge; exactly one eye visible. Tight head-and-neck framing. NO chest, waist, legs or feet.',
 'face_right':'PROFILE HEAD-AND-NECK CLOSE-UP, facing RIGHT in the image. Nose points to the RIGHT edge; exactly one eye visible. Tight head-and-neck framing. Preserve real asymmetries; do not mirror the character.',
 'face_3q_left':'THREE-QUARTER HEAD-AND-NECK CLOSE-UP, facing LEFT, 45 degrees. Both eyes visible, farther eye foreshortened. Tight head-and-neck framing.',
 'face_3q_right':'THREE-QUARTER HEAD-AND-NECK CLOSE-UP, facing RIGHT, 45 degrees. Both eyes visible, farther eye foreshortened. Tight head-and-neck framing.',
 'face_back':'BACK HEAD-AND-NECK CLOSE-UP. Back of head and hair only; no face visible. Tight head-and-neck framing.',
 'body_front':'FRONT FULL BODY. Face, chest and feet face the camera. Neutral standing pose; entire head and both feet visible.',
 'body_left':'PROFILE FULL BODY facing LEFT in the image. Nose, chest, knees and toes all point to the LEFT edge. Exactly one eye visible. Neutral standing pose; entire head and feet visible. Preserve real asymmetries, not a mirrored copy.',
 'body_back':'BACK FULL BODY. Direct rear view, face hidden, head not turned. Neutral standing pose; entire head and both feet visible.',
 'clothing_front':'FRONT of the complete garment set, displayed flat as clothing objects only. Empty sleeves and openings; no wearer, skin, head, body or mannequin. Include neckline through lowest hem.',
 'clothing_back':'BACK of the complete garment set, displayed flat as clothing objects only. Empty sleeves and openings; no wearer, skin, head, body or mannequin. Include neckline through lowest hem.',
 'hands':'PAIRED HANDS CLOSE-UP: exactly one left and one right complete hand. Crop at wrists. Preserve selected glove/bare-hand choice. No torso or whole person.',
 'feet':'PAIRED FEET/FOOTWEAR CLOSE-UP: exactly one left and one right complete foot or footwear, including boot shafts when present. No torso or whole person.',
}
CHOICES={('hand_state','bare'):'All visible hands are bare; no gloves. Retain compatible hand jewelry.',('hand_state','gloved'):'All visible hands wear real gloves; retain compatible glove details and openings.',('footwear_state','shod'):'Both feet wear footwear; retain compatible shoe design.',('footwear_state','unshod'):'No shoes or boots. Keep existing socks/tights if present; do not invent them.',('clothing_type','pants'):'Lower garments have two separate trouser legs; retain other compatible garment details.',('clothing_type','skirt_robe'):'Lower garment has a continuous skirt/robe hem; retain other compatible garment details.'}
def compile_prompt(result,indices,style_instruction='',guide_mode='clean_frames'):
 state=result['state'];panels=result['semantic_layout']['panels'];w,h=result['width'],result['height'];geom={p['id']:p for p in (result.get('guide_geometry') or {}).get('panels',[])}
 identity=indices['character_image'];lines=[f'Create ONE finished static character reference sheet, {w} x {h} pixels, exactly {len(panels)} distinct views. Use the SAME character from image {identity} throughout.']
 if 'layout_image' in indices:
  lines.append(f'Image {indices["layout_image"]} is ONLY a panel layout template. '+('Replace ALL gray placeholders completely with the actual rendered character.' if guide_mode=='original_mannequins' else 'Fill its empty panels with the actual character views below.')+' Preserve panel positions and sizes. Never copy gray material, polygon anatomy, blank body parts or mannequin surfaces into the result.')
 lines.append(f'Image {identity} controls baseline face identity, hair, proportions, garments, colors, materials and accessories. Retain every compatible unspecified detail. Rotate the same design, do not redesign it. Infer hidden surfaces conservatively. Plain white background, consistent soft lighting. '+(style_instruction or f'Keep the rendering style of image {identity}.'))
 lines.append('Required views in spatial order (coordinates are percentages of the entire sheet, never printed text):')
 manifest=[]
 for i,p in enumerate(sorted(panels,key=lambda p:(p['rect'][1],p['rect'][0])),1):
  x,y,pw,ph=p['rect'];view=p['id'];location=f'x={x*100:.1f}..{(x+pw)*100:.1f}%, y={y*100:.1f}..{(y+ph)*100:.1f}%';lines.append(f'Panel {i}, {location}: {VIEW_TEXT[view]}');manifest.append({'index':i,'view':view,'rect':p['rect'],'instruction':VIEW_TEXT[view]})
 # Column groups come from the allocator, including a full-width odd last row.
 by_view={p['id']:p for p in panels}
 for column,group in enumerate(result['semantic_layout'].get('column_groups',[]),1):
  x,y,pw,ph=group['rect'];rows={}
  for view in group['views']:
   cell=by_view[view];rows.setdefault(round(cell['rect'][1],5),[]).append(cell)
  row_text=[]
  for rownum,(_,cells) in enumerate(sorted(rows.items()),1):
   cells=sorted(cells,key=lambda c:c['rect'][0]);names=' then '.join(c['id'] for c in cells)
   row_text.append(f'row {rownum} from top: {names}'+(' (one panel spanning this entire group width)' if len(cells)==1 and len(rows)>1 and abs(cells[0]['rect'][2]-pw)<0.00001 else ''))
  lines.append(f'LOCKED COLUMN GROUP {column}, x={x*100:.1f}..{(x+pw)*100:.1f}%: '+'; '.join(row_text)+'. Keep all these views inside this group in exactly this row order. Never exchange them with another group.')
 lines.append('The layout is fixed, not an example composition. Preserve every group boundary and partial horizontal divider. Never repack panels, rebalance the sheet, swap groups, or place a portrait above footwear unless that exact placement is specified.')
 lines.append('Portrait panels MUST contain enlarged complete heads with only minimal neck and shoulder hints; never full figures. Full-body panels MUST include the complete feet. Each requested view exactly once; no extra people or inset views. Camera and crop override reference pose and framing.')
 for field,value in state.items():
  if isinstance(value,str) and (field,value) in CHOICES:lines.append(CHOICES[field,value])
 roles=state.get('reference_roles',{})
 role_scope={'same_character':'supplement the same identity and unseen details; baseline image wins conflicts','face':'face appearance only, never hair/clothes/pose','head':'head and hair appearance only','clothing':'garment appearance only','clothing_front':'visible front garment surfaces only','clothing_back':'visible rear garment surfaces only','hands':'hands/gloves only','footwear':'feet/footwear only'}
 for source,index in indices.items():
  if source.startswith('reference_image_'):
   role=roles.get(source,'same_character');scopes=result.get('reference_scopes',{}).get(source,{})
   if role!='same_character' and not scopes:
    lines.append(f'Image {index} has no eligible visible part in this selection. Ignore it.');continue
   scoped=(' Only in '+json.dumps(scopes,separators=(',',':'))+'.') if scopes else ''
   lines.append(f'Additional image {index}: {role_scope[role]}.{scoped} Do not transfer its identity, pose, background or camera outside that role. Later connected dedicated references win within the same role.')
 # The source state normalizer has already validated part IDs and literal text.
 for part,text in state['part_prompts'].items():
  # Scope is supplied by the caller from the original part_views implementation.
  views=result.get('part_scopes',{}).get(part,[])
  if views:lines.append(f'Literal appearance detail for {part}, only in {", ".join(views)}; never changes selected cameras/crops:\n{text}')
 for panel in panels:
  if panel['id'].startswith('face_'):
   x,y,pw,ph=panel['rect']
   lines.append(f"PORTRAIT SCALE for {panel['id']}: center the complete HEAD including hairstyle inside its own panel, horizontally and vertically. Enlarge the head as much as the panel permits with only a small safe margin, typically 5 percent. Use head, neck and at most a minimal shoulder hint, NOT a chest-length torso. Never anchor a small bust to the top edge leaving a blank lower half. Keep all hair, ears and chin inside the panel.")
 if len(panels)==1 and panels[0]['id'].startswith('face_'):
  lines.append('SINGLE PORTRAIT: place the head at the exact center of the entire canvas. This is one large centered portrait, not a reference-sheet thumbnail or a corner inset.')
 lines.append('Priority: selected view/camera/crop and garment-only rules; applicable shape/coverage choices; compatible literal part details; eligible dedicated references; same-character supplements; baseline. No sheet captions, view labels, watermarks, residual mannequins or extra panels. Preserve lettering already on the subject.')
 return '\n'.join(lines),manifest

def clean_guide(result):
 from PIL import Image,ImageDraw
 im=Image.new('RGB',(result['width'],result['height']),'white');d=ImageDraw.Draw(im)
 for p in result['semantic_layout']['panels']:
  x,y,w,h=p['rect'];left,top=round(x*im.width),round(y*im.height);right,bottom=round((x+w)*im.width),round((y+h)*im.height)
  d.rectangle((left,top,max(left,right-1),max(top,bottom-1)),outline=(160,160,160),width=1)
 return im
