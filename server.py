import asyncio, json, os, random, secrets, time
from aiohttp import web, WSMsgType
from pathlib import Path

ROOT=Path(__file__).parent
QUESTIONS=[
('管理的四項基本功能通常包括？',['規劃、組織、領導、控制','生產、銷售、研發、財務','招募、考核、獎懲、升遷'],0,'管理四功能為規劃、組織、領導與控制。'),
('主管只蒐集支持原本看法的證據，是？',['定錨效應','確認偏誤','可得性偏誤'],1,'確認偏誤是偏向尋找支持既有信念的資訊。'),
('赫茲伯格雙因子理論中，薪資與工作條件屬於？',['激勵因子','保健因子','成就需求'],1,'薪資與工作條件通常屬保健因子。'),
('SWOT 的 O 代表？',['組織','機會','目標'],1,'O 是 Opportunities，外部機會。'),
('平衡計分卡的典型四構面不包括？',['顧客','內部流程','天氣'],2,'典型構面為財務、顧客、內部流程、學習與成長。'),
('領導者運用獎勵鼓勵員工，主要是？',['獎賞權','強制權','參照權'],0,'獎賞權源自提供獎勵的能力。'),
('將年輕顧客一律視為高流量用戶，是？',['代表性偏誤','沉沒成本','後見偏誤'],0,'以刻板典型判斷個體，忽略實際資料。'),
('波特五力不包含下列哪一項？',['替代品威脅','供應商議價能力','員工滿意度'],2,'員工滿意度不屬五力之一。')]
rooms={}

def room_for(code):
 return rooms.setdefault(code, {'players':{},'boss':600,'max_boss':600,'round':0,'log':[]})

async def broadcast(code):
 r=rooms.get(code)
 if not r:return
 packet={'type':'state','players':[{'id':p['id'],'name':p['name'],'x':p['x'],'y':p['y'],'xp':p['xp']} for p in r['players'].values()],'boss':r['boss'],'max_boss':r['max_boss'],'round':r['round'],'log':r['log'][-5:]}
 for p in list(r['players'].values()):
  try: await p['ws'].send_json(packet)
  except Exception:pass

async def index(req):return web.FileResponse(ROOT/'index.html')
async def health(req):return web.json_response({'ok':True,'rooms':len(rooms)})
async def ws_handler(req):
 ws=web.WebSocketResponse(heartbeat=25,max_msg_size=2048);await ws.prepare(req)
 pid=secrets.token_hex(4);code=None;p=None
 try:
  async for msg in ws:
   if msg.type!=WSMsgType.TEXT:continue
   try:d=json.loads(msg.data)
   except Exception:continue
   kind=d.get('type')
   if kind=='join' and not p:
    code=str(d.get('room','START')).upper().strip()[:8]
    if not code.isalnum():await ws.send_json({'type':'error','message':'房間代碼限英數字'});continue
    r=room_for(code)
    if len(r['players'])>=12:await ws.send_json({'type':'error','message':'房間已滿'});continue
    name=str(d.get('name','冒險者')).strip()[:12] or '冒險者'
    p={'id':pid,'name':name,'x':random.randint(2,7),'y':random.randint(2,7),'xp':0,'ws':ws,'q':None,'last_move':0,'last_attack':0}
    r['players'][pid]=p
    await ws.send_json({'type':'joined','id':pid,'room':code})
    await broadcast(code)
   elif p and kind=='move':
    now=time.monotonic()
    if now-p['last_move']<0.08:continue
    p['last_move']=now
    dx=max(-1,min(1,int(d.get('dx',0))));dy=max(-1,min(1,int(d.get('dy',0))))
    nx=max(1,min(18,p['x']+dx));ny=max(1,min(11,p['y']+dy))
    if not (12<=nx<=15 and 4<=ny<=7):p['x']=nx;p['y']=ny
    await broadcast(code)
   elif p and kind=='question':
    qid=random.randrange(len(QUESTIONS));p['q']=qid
    q=QUESTIONS[qid]
    await ws.send_json({'type':'question','text':q[0],'options':q[1]})
   elif p and kind=='answer' and p['q'] is not None:
    q=QUESTIONS[p['q']];p['q']=None
    correct=isinstance(d.get('choice'),int) and d['choice']==q[2]
    r=room_for(code)
    if correct:
     p['xp']+=20;r['boss']=max(0,r['boss']-100)
     r['log'].append(p['name']+' 答對，對 Boss 造成 100 傷害！')
    else:r['log'].append(p['name']+' 答錯，繼續加油！')
    await ws.send_json({'type':'result','correct':correct,'answer':q[2],'explanation':q[3],'xp':p['xp']})
    if r['boss']==0:
     r['round']+=1;r['log'].append('🎉 團隊擊敗 Boss！新一輪開始')
     r['boss']=r['max_boss']
    await broadcast(code)
 finally:
  if p and code in rooms:
   rooms[code]['players'].pop(pid,None)
   await broadcast(code)
   if not rooms[code]['players']:rooms.pop(code,None)
 return ws

app=web.Application();app.router.add_get('/',index);app.router.add_get('/health',health);app.router.add_get('/ws',ws_handler)
if __name__=='__main__':web.run_app(app,host='0.0.0.0',port=int(os.environ.get('PORT','8080')))
