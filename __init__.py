from .nodes import SkyHowlCharacterSheetV4,SkyHowlSheetCanvasV4
from .panels import SkyHowlCharacterSheetPanels, SkyHowlSheetCompose, panel_preview
NODE_CLASS_MAPPINGS={'SkyHowlCharacterSheetV4':SkyHowlCharacterSheetV4,'SkyHowlSheetCanvasV4':SkyHowlSheetCanvasV4,'SkyHowlCharacterSheetPanels':SkyHowlCharacterSheetPanels,'SkyHowlSheetCompose':SkyHowlSheetCompose}
NODE_DISPLAY_NAME_MAPPINGS={'SkyHowlCharacterSheetV4':'SkyHowl · 角色 Sheet V4','SkyHowlSheetCanvasV4':'SkyHowl · Sheet画布尺寸 V4','SkyHowlCharacterSheetPanels':'SkyHowl · 角色设定 · 逐视图','SkyHowlSheetCompose':'SkyHowl · 自动拼版'}
WEB_DIRECTORY='./web'
try:
 from server import PromptServer
except ModuleNotFoundError as exc:
 if exc.name!='server':raise
else:
 from aiohttp import web
 from .core import compile_sheet
 from .semantic.compiler import StateValidationError,decode_json
 if not getattr(PromptServer.instance,'_skyhowl_sheet_v4',False):
  @PromptServer.instance.routes.post('/skyhowl/sheet/panels/preview')
  @PromptServer.instance.routes.post('/skyhowl/sheet/v4/preview')
  async def sheet_preview(request):
   if request.content_type!='application/json':return web.json_response({'error':{'message':'Use application/json'}},status=415)
   body=bytearray()
   async for chunk in request.content.iter_chunked(4096):
    body.extend(chunk)
    if len(body)>196608:return web.json_response({'error':{'message':'Request too large'}},status=413)
   try:
    d=decode_json(body.decode('utf-8'),byte_limit=196608)
    if type(d)is not dict or 'state_json' not in d or set(d)-{'state_json','use_layout_image','style','reference_presence'}:raise ValueError('Invalid preview request')
    result=panel_preview(**d) if request.path.endswith('/panels/preview') else compile_sheet(**d)
   except (StateValidationError,ValueError,UnicodeError) as e:return web.json_response({'error':{'code':getattr(e,'code','invalid_request'),'message':str(e)}},status=400)
   return web.json_response(result)
  PromptServer.instance._skyhowl_sheet_v4=True
