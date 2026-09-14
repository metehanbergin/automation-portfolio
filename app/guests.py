"""Property-scoped retrieval, policy routing and approved knowledge promotion."""
import math
import re
from collections import Counter
from .core import audit, notify, now, uid

LEXICON={
 'wifi':['wifi','wi-fi','internet','password','contraseña','şifre','sifre'],
 'parking':['parking','park','aparcamiento','otopark','car','coche','araba'],
 'checkout':['checkout','check-out','salida','çıkış','cikis'],
 'checkin':['checkin','check-in','entrada','giriş','giris'],
 'refund':['refund','reembolso','iade','money back'],
 'late':['late','tarde','geç','gec'], 'early':['early','temprano','erken'],
 'emergency':['fire','smoke','gas leak','fuego','humo','incendio','yangın','yangin','duman','gaz kaçağı','injured','ambulance','unconscious'],
 'towels':['towels','towel','toallas','havlu'],
 'luggage':['luggage','bags','equipaje','maleta','bagaj','valiz'],
 'pool':['pool','piscina','havuz']}


def tokens(text):
    lower=text.casefold()
    result=re.findall(r'\w+',lower)
    for topic,words in LEXICON.items():
        if any(w in lower for w in words): result.extend([topic]*3)
    return result


def detect_language(text):
    lower=text.lower()
    if any(t in lower for t in ['ş','ğ','ı','ç','merhaba','havlu','havuz','valiz','otopark']): return 'tr'
    if any(t in lower for t in ['¿','ñ','hola','gracias','dónde','puedo','fuego','contraseña','equipaje','piscina']): return 'es'
    return 'en'


def initial():
    kb=[]
    def add(scope,topic,q,en,es,tr):
        kb.append(dict(id=uid('KB'),scope=scope,topic=topic,question=q,answers=dict(en=en,es=es,tr=tr),status='approved',source='Synthetic property handbook',version=1))
    add('global','checkout','What time is checkout?', 'Standard checkout is at 11:00. Late checkout requires host approval.',
        'La salida estándar es a las 11:00. La salida tardía requiere aprobación.',
        'Standart çıkış saati 11:00. Geç çıkış için ev sahibi onayı gerekir.')
    add('global','checkin','What time is check-in?', 'Standard check-in starts at 15:00. Early check-in requires host approval.',
        'La entrada estándar es a partir de las 15:00. La entrada anticipada requiere aprobación.',
        'Standart giriş saati 15:00. Erken giriş için ev sahibi onayı gerekir.')
    add('P1','wifi','What is the Wi-Fi password?', 'Wi-Fi: Seabrook-Guest. Password: DemoStay2026. These are fictional demo credentials.',
        'Wi-Fi: Seabrook-Guest. Contraseña: DemoStay2026. Son credenciales ficticias.',
        'Wi-Fi: Seabrook-Guest. Şifre: DemoStay2026. Bunlar kurgu demo bilgileridir.')
    add('P2','wifi','What is the Wi-Fi password?', 'Wi-Fi: Orchard-Guest. Password: DemoOrchard26. These are fictional demo credentials.',
        'Wi-Fi: Orchard-Guest. Contraseña: DemoOrchard26. Son credenciales ficticias.',
        'Wi-Fi: Orchard-Guest. Şifre: DemoOrchard26. Bunlar kurgu demo bilgileridir.')
    add('P1','parking','Where can I park my car?', 'Use marked bay 12 in the courtyard. One vehicle per reservation.',
        'Utilice la plaza 12 del patio. Un vehículo por reserva.',
        'Avludaki 12 numaralı park yerini kullanabilirsiniz. Rezervasyon başına bir araç.')
    add('P2','parking','Where can I park my car?', 'Orchard Loft has no allocated parking. Ask the host for current public parking options.',
        'Orchard Loft no tiene aparcamiento asignado. Consulte al anfitrión.',
        'Orchard Loft için ayrılmış otopark yok. Güncel seçenekleri ev sahibine sorun.')
    return dict(properties=[dict(id='P1',name='Seabrook House',location='Coastal district'),dict(id='P2',name='Orchard Loft',location='Old town')],
                reservations=[dict(id='RES-101',guest='Alex Morgan',property='P1'),dict(id='RES-102',guest='Sofia Rivera',property='P2'),dict(id='RES-103',guest='Deniz Kaya',property='P1')],
                conversations=[],knowledge=kb,proposals=[])


def retrieve(kb,property_id,text):
    candidates=[k for k in kb if k['scope'] in ('global',property_id) and k['status']=='approved']
    query=Counter(tokens(text)); docs=[Counter(tokens(k['question']+' '+k['topic'])) for k in candidates]
    def vector(c):
        return {t:n*(1+math.log((len(docs)+1)/(1+sum(t in d for d in docs)))) for t,n in c.items()}
    q=vector(query); qn=math.sqrt(sum(v*v for v in q.values())) or 1
    hits=[]
    for k,d in zip(candidates,docs):
        v=vector(d);dn=math.sqrt(sum(x*x for x in v.values())) or 1
        score=sum(x*v.get(t,0) for t,x in q.items())/(qn*dn)
        hits.append(dict(id=k['id'],score=round(score,3),scope=k['scope'],question=k['question']))
    return sorted(hits,key=lambda h:h['score'],reverse=True)


STANDBY={
 'en':'I have alerted the on-call host. If there is immediate danger, move to a safe location if you can and contact local emergency services. Do not wait for a chat reply.',
 'es':'He avisado al anfitrión de guardia. Si hay peligro inmediato, vaya a un lugar seguro si puede y contacte con los servicios de emergencia locales. No espere una respuesta por chat.',
 'tr':'Nöbetçi ev sahibine haber verdim. Acil tehlike varsa güvenli bir yere geçin ve yerel acil yardım hizmetlerini arayın. Sohbet yanıtını beklemeyin.'}
HOLD={'en':'I have sent this to the host for review. I cannot confirm this request without approval.',
      'es':'He enviado su solicitud al anfitrión. No puedo confirmarla sin aprobación.',
      'tr':'Talebinizi ev sahibinin incelemesine ilettim. Onay olmadan teyit edemem.'}


def message(state,data):
    book=state['guests'];text=data.get('message','').strip()
    if not text: raise ValueError('Enter a guest message')
    reservation=next((r for r in book['reservations'] if r['id']==data.get('reservation')),None)
    lang=detect_language(text);ts=tokens(text)
    conv=dict(id=uid('CHAT'),reservation=data.get('reservation',''),guest=reservation['guest'] if reservation else 'Unidentified guest',
              property=reservation['property'] if reservation else None,message=text,language=lang,at=now(),status='escalated',
              response=HOLD[lang],reason='',sources=[],confidence=0,human_answer=None)
    book['conversations'].append(conv)
    audit(state,'guests',conv['id'],'Message received',f'Language heuristic: {lang}; reservation {conv["reservation"]}')
    if 'emergency' in ts:
        conv.update(status='emergency',response=STANDBY[lang],reason='Emergency keyword detected; urgent human response required')
        notify(state,'guests',conv['id'],'urgent_alert',f'{conv["guest"]}: {text}')
    elif not reservation: conv['reason']='Reservation could not be verified. No property-specific facts disclosed.'
    elif 'refund' in ts or ('late' in ts and 'checkout' in ts) or ('early' in ts and 'checkin' in ts):
        conv['reason']='Protected policy: refunds and arrival/departure exceptions require approval'
    else:
        hits=retrieve(book['knowledge'],reservation['property'],text)
        conv['sources']=hits[:3]
        top=hits[0] if hits else None
        topics={t for t in ts if t in LEXICON}
        relevant=[k for k in book['knowledge'] if k['scope'] in ('global',reservation['property']) and k['topic'] in topics]
        matched_topics={k['topic'] for k in relevant}
        exact_entry=next((k for k in book['knowledge'] if k['scope'] in ('global',reservation['property']) and k['status']=='approved' and k['question'].strip().casefold()==text.casefold() and k['answers'].get(lang)),None)
        if exact_entry:
            conv.update(status='auto_resolved',response=exact_entry['answers'][lang],reason='Exact question matched to approved scoped knowledge',confidence=100)
            conv['sources']=[dict(id=exact_entry['id'],score=1.0,scope=exact_entry['scope'],question=exact_entry['question'])]
        elif len(topics-matched_topics)>0 or len(topics)>1:
            conv['reason']='Multiple or unsupported topics; human review avoids incomplete answers'
        elif top and top['score']>=0.48 and (len(hits)<2 or top['score']-hits[1]['score']>=0.08):
            entry=next(k for k in book['knowledge'] if k['id']==top['id'])
            answer=entry['answers'].get(lang)
            if answer:
                conv.update(status='auto_resolved',response=answer,reason='Approved property-scoped knowledge retrieved',confidence=round(top['score']*100))
                conv['sources']=[top]
            else: conv['reason']='No approved answer for this language'
        else: conv['reason']='Insufficient knowledge or ambiguous retrieval match'
    if conv['status']=='escalated': notify(state,'guests',conv['id'],'host_queue',conv['reason'])
    notify(state,'guests',conv['id'],'guest_message',conv['response'])
    audit(state,'guests',conv['id'],'Routing decision',conv['reason'])
    return conv


def sanitize(text):
    text=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[email removed]',text)
    text=re.sub(r'\+?\d[\d\s()-]{7,}\d','[phone removed]',text)
    text=re.sub(r'(?i)(door code|access code|password|şifre)\s*[:=]\s*\S+',r'\1: [private value removed]',text)
    return text.strip()


def answer(state,entity,data):
    book=state['guests'];conv=next(c for c in book['conversations'] if c['id']==entity)
    if conv['status'] not in ['escalated','emergency']: raise ValueError('Conversation already resolved')
    text=data.get('answer','').strip()
    if not text: raise ValueError('A human answer is required')
    was_emergency=conv['status']=='emergency'
    conv.update(status='human_resolved',human_answer=text)
    notify(state,'guests',entity,'guest_message',text)
    audit(state,'guests',entity,'Human response',text,'host')
    if data.get('learn') and conv['property'] and not was_emergency:
        if any(t in tokens(conv['message']) for t in ['refund','late','early','emergency']):
            audit(state,'guests',entity,'Learning blocked','Protected policy decisions cannot become automatic answers')
        else:
            proposal=dict(id=uid('DRAFT'),conversation=entity,scope=conv['property'],question=sanitize(data.get('question',conv['message'])),
                          answer=sanitize(text),language=conv['language'],status='pending',at=now())
            book['proposals'].append(proposal)
            audit(state,'guests',entity,'Knowledge proposed','Sanitized draft awaits separate approval; names and facts still require human review')
    return conv


def approve_knowledge(state,entity,data):
    book=state['guests'];proposal=next(p for p in book['proposals'] if p['id']==entity)
    if proposal['status']!='pending': raise ValueError('Proposal already reviewed')
    if data.get('reject'):
        proposal['status']='rejected'
    else:
        question=data.get('question',proposal['question']).strip();answer=data.get('answer',proposal['answer']).strip()
        if not question or not answer: raise ValueError('Question and answer are required')
        if any(t in tokens(question+' '+answer) for t in ['refund','emergency','late','early']):
            raise ValueError('Protected policy content cannot be learned automatically')
        topics=[t for t in tokens(question) if t in LEXICON]
        entry=dict(id=uid('KB'),scope=proposal['scope'],topic=topics[0] if topics else question.lower(),question=question,
                   answers={proposal['language']:answer},status='approved',source='Human-reviewed knowledge proposal',version=1)
        book['knowledge'].append(entry);proposal['status']='approved';proposal['knowledge_id']=entry['id']
    audit(state,'guests',entity,'Knowledge '+proposal['status'],f'Property scope {proposal["scope"]}','knowledge_reviewer')
    return proposal
