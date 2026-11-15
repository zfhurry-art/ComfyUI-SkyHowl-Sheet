"""One screen-facing layout for all selections; no legacy/special-case packing."""
from fractions import Fraction
from .compiler import DEFAULT_MAX_RESOLUTION,_ceil_32,_round_coordinate,_size_value
from .view_catalog_13 import PORTRAIT_IDS,BODY_IDS,CLOTHING_IDS,VIEW_DETAILS

def compute_semantic_layout(state, *, max_resolution=DEFAULT_MAX_RESOLUTION, separate_details=False):
 views,size=state['views'],state['size'];h=Fraction(size['body_height']);margin,gap=h/14,h/100
 heads=[v for v in PORTRAIT_IDS if v in views];groups=[]
 if heads:
  mixed=any(v not in PORTRAIT_IDS for v in views)
  cols=(1 if len(heads)<=4 else 2) if mixed else min(2,len(heads));rows=(len(heads)+cols-1)//cols
  ph=(h-(rows-1)*gap)/rows;pw=min(ph*Fraction(4,5),h*Fraction(3,5)) if mixed else ph*Fraction(4,5);gw=cols*pw+(cols-1)*gap;cells={}
  for i,v in enumerate(heads):
   row,col=divmod(i,cols);last_alone=cols==2 and i==len(heads)-1 and len(heads)%2
   cells[v]=(Fraction(0) if last_alone else col*(pw+gap),row*(ph+gap),gw if last_alone else pw,ph)
  groups.append((gw,cells))
 for v in (*BODY_IDS,*CLOTHING_IDS):
  if v in views:groups.append((h*Fraction(1,2),{v:(Fraction(0),Fraction(0),h*Fraction(1,2),h)}))
 details=[v for v in ('hands','feet') if v in views]
 if details:
  ph=(h-(len(details)-1)*gap)/len(details);pw=ph*Fraction(6,5)
  groups.append((pw,{v:(Fraction(0),i*(ph+gap),pw,ph) for i,v in enumerate(details)}))
 idealw=sum(w for w,_ in groups)+(len(groups)-1)*gap+2*margin;idealh=h+2*margin
 W,H=(_ceil_32(idealw),_ceil_32(idealh)) if size['mode']=='auto' else (size['manual_width'],size['manual_height'])
 _size_value(W,'output width',max_resolution);_size_value(H,'output height',max_resolution)
 scale=min(Fraction(W)/idealw,Fraction(H)/idealh) if size['mode']=='manual' else Fraction(1)
 ox,oy=(W-idealw*scale)/2,(H-idealh*scale)/2;x=margin;rects={};group_specs=[]
 for gw,cells in groups:
  group_specs.append({'views':list(cells),'rect':[_round_coordinate((ox+x*scale)/W),_round_coordinate((oy+margin*scale)/H),_round_coordinate(gw*scale/W),_round_coordinate(h*scale/H)]})
  for v,(l,t,w,ph) in cells.items():rects[v]=[_round_coordinate((ox+(x+l)*scale)/W),_round_coordinate((oy+(margin+t)*scale)/H),_round_coordinate(w*scale/W),_round_coordinate(ph*scale/H)]
  x+=gw+gap
 return {'canvas':[W,H],'panels':[{'id':v,'rect':rects[v],'view':VIEW_DETAILS[v][0],'content':VIEW_DETAILS[v][1]} for v in views], 'feet_y':_round_coordinate((oy+(margin+h)*scale)/H) if any(v in BODY_IDS for v in views) else None,'layout_version':'uniform-2','column_groups':group_specs}
