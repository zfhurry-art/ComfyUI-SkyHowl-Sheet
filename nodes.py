import json
from .core import compile_sheet,DEFAULT_JSON
from .semantic.guide_13 import render_reference13_guide
from .semantic.reference_compiler import STYLE_PROMPTS
class SkyHowlCharacterSheetV4:
 CATEGORY='SkyHowl/Character Sheet';FUNCTION='compile'
 RETURN_TYPES=('STRING','INT','INT','IMAGE','IMAGE','IMAGE','IMAGE','IMAGE','STRING')
 RETURN_NAMES=('qwen_prompt','width','height','image_1','image_2','image_3','image_4','image_5','sheet_spec')
 @classmethod
 def INPUT_TYPES(cls):
  return {'required':{'state_json':('STRING',{'default':DEFAULT_JSON,'multiline':True,'dynamicPrompts':False}),'character_image':('IMAGE',),'use_layout_image':('BOOLEAN',{'default':True}),'style':(list(STYLE_PROMPTS),{'default':'none'})},'optional':{f'reference_image_{i}':('IMAGE',) for i in range(1,4)}}
 def compile(self,state_json,character_image,use_layout_image=True,style='none',reference_image_1=None,reference_image_2=None,reference_image_3=None):
  import numpy as np
  import torch
  if character_image is None:raise ValueError('Connect a character reference image')
  refs={f'reference_image_{i}':v for i,v in enumerate((reference_image_1,reference_image_2,reference_image_3),1)}
  r=compile_sheet(state_json,use_layout_image,style,{k:v is not None for k,v in refs.items()});images=[]
  if use_layout_image:images.append(torch.from_numpy(np.asarray(render_reference13_guide(r['guide_geometry'],r['semantic_layout']),dtype=np.float32)/255).unsqueeze(0))
  images.append(character_image);images.extend(v for v in refs.values() if v is not None)
  return (r['prompt'],r['width'],r['height'],*(images+[None]*(5-len(images))),json.dumps(r['sheet_spec'],ensure_ascii=False))
class SkyHowlSheetCanvasV4:
 CATEGORY='SkyHowl/Character Sheet';FUNCTION='resize';RETURN_TYPES=('LATENT',);RETURN_NAMES=('canvas_latent',)
 @classmethod
 def INPUT_TYPES(cls):return {'required':{'latent':('LATENT',),'width':('INT',{'forceInput':True}),'height':('INT',{'forceInput':True})}}
 def resize(self,latent,width,height):
  import torch
  if type(width)is not int or type(height)is not int or min(width,height)<32 or max(width,height)>8192 or width%32 or height%32 or width*height>16777216:raise ValueError('Invalid sheet canvas dimensions')
  s=latent['samples']
  if s.ndim!=4 or s.shape[1]!=64:raise ValueError('Qwen2.1 requires a 64-channel latent')
  if torch.count_nonzero(s).item():raise ValueError('Only empty Qwen latent is accepted; refusing to erase an encoded image')
  return ({'samples':s.new_zeros((s.shape[0],64,height//16,width//16))},)
