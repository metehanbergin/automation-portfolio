import io
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, Request, Response, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import core, remittance, leads, guests, orders, ai

ROOT=Path(__file__).resolve().parent.parent
app=FastAPI(title='Automation Portfolio · sandbox APIs',version='1.0.0')
core.init_db()


def seed():
    state=dict(events=[],outbox=[],remittance=remittance.initial(),leads=leads.initial(),guests=guests.initial(),orders=orders.initial())
    for name,text in remittance.samples(): remittance.process(state,name,text.encode())
    lead_data=[('Maya Chen','maya@example.test','Deep cleaning for three rooms tomorrow','Central',3),
               ('Oliver Reed','oliver@example.test','Weekly clean for our studio','North',2),
               ('Leila Brooks','leila@example.test','Moving out next week, four rooms','West',4),
               ('Noah Ellis','noah@example.test','Urgent cleaning today','Outside area',2),
               ('Amelia Park','amelia@example.test','Deep clean for five rooms','Central',5),
               ('Ethan Cole','ethan@example.test','Regular weekly service','West',2)]
    for name,email,msg,loc,rooms in lead_data:
        leads.intake(state,dict(name=name,email=email,message=msg,location=loc,rooms=rooms,consent=True))
    for idx in [1,2,5]: leads.action(state,state['leads']['leads'][idx]['id'],'approve',{})
    leads.action(state,state['leads']['leads'][1]['id'],'book',{'slot':'Tomorrow · 09:00'})
    leads.action(state,state['leads']['leads'][5]['id'],'book',{'slot':'Friday · 09:00'})
    leads.action(state,state['leads']['leads'][5]['id'],'complete',{})
    for reservation,msg in [('RES-101','What is the Wi-Fi password?'),('RES-102','¿Dónde puedo aparcar el coche?'),
                            ('RES-103','Merhaba, Wi-Fi şifresi nedir?'),('RES-101','Can we store luggage after checkout?'),
                            ('RES-102','Can you approve a refund?'),('RES-101','There is smoke in the kitchen')]:
        guests.message(state,dict(reservation=reservation,message=msg))
    order_data=[('DEMO-001','AC-101','DESK',4,'normal'),('DEMO-002','AC-102','CHAIR',8,'supplier_failure'),
                ('DEMO-003','AC-103','PRINT',12,'normal'),('DEMO-004','AC-101','DESK',30,'normal'),
                ('DEMO-005','AC-102','DESK',2,'payment_mismatch'),('DEMO-006','AC-103','CHAIR',6,'delayed'),
                ('DEMO-007','AC-102','PRINT',5,'manual')]
    for key,account,sku,qty,scenario in order_data:
        orders.create(state,dict(key=key,account=account,sku=sku,quantity=qty,scenario=scenario))
    for idx in [1,3,4,5,6]:
        o=state['orders']['orders'][idx]
        orders.action(state,o['id'],'approve',{},'approver')
        for _ in range(8):
            if o['status'] in ['blocked','retry_wait','completed','quote_approval']: break
            orders.step(state,o)
    return state


@app.middleware('http')
async def security(request:Request,call_next):
    if request.method in ['POST','PUT','DELETE','PATCH']:
        origin=request.headers.get('origin')
        if origin and urlparse(origin).netloc != request.headers.get('host'):
            return JSONResponse({'detail':'Cross-origin mutations are disabled'},status_code=403)
        if int(request.headers.get('content-length','0'))>3_000_000:
            return JSONResponse({'detail':'Upload exceeds 3 MB limit'},status_code=413)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if request.url.path.startswith('/api'):
        response.headers['Cache-Control']='no-store'
    return response


class Command(BaseModel):
    action: str = Field(max_length=40)
    entity: str = Field(default='',max_length=80)
    data: dict[str,Any] = Field(default_factory=dict)
    role: str = Field(default='operator',max_length=20)


def session_id(request):
    sid=request.cookies.get('portfolio_session')
    if not core.get_session(sid): raise HTTPException(401,'Open the dashboard to initialize a sandbox')
    return sid


@app.get('/api/state')
def state(request:Request,response:Response):
    sid=request.cookies.get('portfolio_session');value=core.get_session(sid)
    if not value:
        value=seed();sid=core.create_session(value)
        response.set_cookie('portfolio_session',sid,httponly=True,samesite='strict',secure=request.url.scheme=='https',max_age=7*86400)
    return value


@app.post('/api/reset')
def reset(request:Request):
    with core.transaction(session_id(request)) as state:
        state.clear();state.update(seed())
    return {'ok':True}


@app.post('/api/{project}/command')
def command(project:str,cmd:Command,request:Request):
    if len(json.dumps(cmd.data))>30000: raise HTTPException(413,'Input exceeds demo limit')
    try:
        with core.transaction(session_id(request)) as state:
            if len(state['events'])>3000: raise ValueError('Sandbox event limit reached. Reset this sandbox.')
            if cmd.action=='ai_draft' and project in ['remittance','leads','guests']:
                task={'remittance':'extraction','leads':'qualification','guests':'knowledge'}[project]
                try:
                    result=ai.draft(task,str(cmd.data.get('source','')))
                except Exception:
                    raise ValueError('AI draft unavailable or invalid. No business action was taken; use manual review.')
                core.audit(state,project,cmd.entity or 'draft','AI draft prepared','Schema validated; human review required before any business action')
                state.setdefault('drafts',[]).append(dict(project=project,entity=cmd.entity,result=result,status='review_required'))
            elif project=='remittance':
                if cmd.action=='intake':
                    result=remittance.process(state,'email-body.txt',str(cmd.data.get('text','')).encode())
                else: result=remittance.resolve(state,cmd.entity,cmd.action,cmd.data)
            elif project=='leads':
                if cmd.action=='intake': result=leads.intake(state,cmd.data)
                elif cmd.action=='tick': result=leads.tick(state,min(30,max(1,int(cmd.data.get('days',2)))))
                else: result=leads.action(state,cmd.entity,cmd.action,cmd.data)
            elif project=='guests':
                if cmd.action=='intake': result=guests.message(state,cmd.data)
                elif cmd.action=='answer': result=guests.answer(state,cmd.entity,cmd.data)
                elif cmd.action=='knowledge': result=guests.approve_knowledge(state,cmd.entity,cmd.data)
                else: raise ValueError('Unknown guest action')
            elif project=='orders':
                if cmd.action=='intake':
                    orders.check_role(cmd.role,['operator','approver']);result=orders.create(state,cmd.data)
                elif cmd.action=='tick':
                    orders.check_role(cmd.role,['operator','approver']);result=orders.tick(state,min(48,max(1,int(cmd.data.get('hours',4)))))
                else: result=orders.action(state,cmd.entity,cmd.action,cmd.data,cmd.role)
            else: raise HTTPException(404,'Unknown project')
        return result
    except PermissionError as exc: raise HTTPException(403,str(exc))
    except (ValueError,KeyError,StopIteration,TypeError) as exc: raise HTTPException(422,str(exc) or 'Record not found')


@app.post('/api/remittance/upload')
async def upload(request:Request,file:UploadFile=File(...)):
    raw=await file.read(3_000_001)
    if len(raw)>3_000_000: raise HTTPException(413,'Upload exceeds 3 MB')
    with core.transaction(session_id(request)) as state:
        if len(state['remittance']['documents'])>=100: raise HTTPException(429,'Reset sandbox before uploading more documents')
        result=remittance.process(state,Path(file.filename or 'unknown').name,raw)
    return result


@app.get('/api/export')
def export(request:Request):
    value=core.get_session(session_id(request))
    return StreamingResponse(io.BytesIO(json.dumps(value,indent=2,ensure_ascii=False).encode()),media_type='application/json',headers={'Content-Disposition':'attachment; filename=sandbox-audit.json'})


@app.get('/health')
def health(): return {'status':'ok','mode':'synthetic sandbox','providers':'simulated','llm':'disabled by default'}


@app.get('/')
def index(): return FileResponse(ROOT/'web'/'index.html')


@app.get('/{project}')
def project_page(project:str):
    if project not in ['remittance','leads','guests','orders']: raise HTTPException(404)
    return FileResponse(ROOT/'web'/'index.html')


app.mount('/static',StaticFiles(directory=ROOT/'web'),name='static')
