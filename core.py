"""Single state -> preview/prompt/geometry. No installed custom-node imports."""
import json
from .semantic.reference_v13_compiler import compile_reference_v13_state
from .semantic.state_13 import part_views,DEFAULT_STATE
from .semantic.appearance_policy_13 import build_appearance_policy
from .semantic.reference_compiler import STYLE_PROMPTS
from .qwen_compiler import compile_prompt,clean_guide
DEFAULT_JSON=json.dumps({**DEFAULT_STATE,'views':['face_front','face_left','body_front','body_left','body_back']},ensure_ascii=False)
def compile_sheet(state_json,use_layout_image=True,style='none',reference_presence=None):
 r=compile_reference_v13_state(state_json,use_layout_image=use_layout_image,style=style,reference_presence=reference_presence or {},max_resolution=8192)
 if r['width']*r['height']>16777216:raise ValueError('Sheet canvas exceeds 16 MP')
 r['part_scopes']={p:list(part_views(r['state'],p)) for p in r['state']['part_prompts']}
 r['reference_scopes']={x['source']:x['parts'] for x in build_appearance_policy(r['state'],r['reference_plan'])}
 indices={};order=[]
 if use_layout_image:order.append('layout_image')
 order.append('character_image')
 order.extend(k for k in ('reference_image_1','reference_image_2','reference_image_3') if (reference_presence or {}).get(k,False))
 indices={k:i+1 for i,k in enumerate(order)}
 prompt,panels=compile_prompt(r,indices,STYLE_PROMPTS[style],'original_mannequins')
 r['reference_plan']=[{'source':k,'role':('layout' if k=='layout_image' else 'character' if k=='character_image' else r['state'].get('reference_roles',{}).get(k,'same_character')),'picture_number':i+1,'tag':f'<image{i+1}>'} for i,k in enumerate(order)];r['prompt']=prompt;r['qwen_order']=order;r['sheet_spec']={'version':4,'state':r['state'],'canvas':[r['width'],r['height']],'panels':panels,'image_order':order,'layout_mode':'original_mannequins'}
 return r
