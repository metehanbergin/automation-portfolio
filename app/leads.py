"""Cleaning-service lifecycle. Scheduling and communications use local provider receipts."""
import re
from .core import audit, notify, now, uid, whole_number


def initial():
    return dict(leads=[],bookings=[],clock=0,service_prices={'Deep clean':18000,'Move-out clean':26000,'Recurring clean':12000})


def intake(state,data):
    book=state['leads']; email=data.get('email','').strip().lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email): raise ValueError('Enter a valid email')
    old=next((x for x in book['leads'] if x['email']==email),None)
    if old:
        audit(state,'leads',old['id'],'Duplicate suppressed','Existing CRM contact matched by normalized email')
        return old
    message=data.get('message','').strip()
    if not data.get('name','').strip() or not message: raise ValueError('Name and service request are required')
    service='Move-out clean' if any(t in message.lower() for t in ['move','moving','vacate']) else 'Recurring clean' if any(t in message.lower() for t in ['weekly','recurring','regular']) else 'Deep clean'
    urgent=any(t in message.lower() for t in ['today','tomorrow','urgent'])
    location=data.get('location','Central')
    size=whole_number(data.get('rooms',2),'Rooms',1,12)
    quote=book['service_prices'][service]+max(size-2,0)*3500
    supported=location in ['Central','North','West']
    score=min(100,45+(20 if urgent else 0)+(20 if supported else 0)+(10 if size>=3 else 0))
    lead=dict(id=uid('LEAD'),name=data['name'],email=email,message=message,service=service,
              location=location,rooms=size,urgent=urgent,score=score,quote=quote,created=now(),
              status='approval' if supported else 'exception', reason='Approve fixed-price quote' if supported else 'Outside service area',
              day=book['clock'],stage_history=['intake','qualified'] if supported else ['intake'],consent=bool(data.get('consent',False)),
              tasks=[],source='Website intake',classification='Local rules · reviewable',notes=[])
    book['leads'].append(lead)
    audit(state,'leads',lead['id'],'Intake accepted',f'{service} · {location} · {size} rooms')
    audit(state,'leads',lead['id'],'Qualification',f'Score {score}/100; urgency {urgent}; {lead["reason"]}')
    return lead


def action(state,entity,action,data):
    book=state['leads'];lead=next(x for x in book['leads'] if x['id']==entity)
    transitions={'approve':(['approval'],'quoted'),'complete':(['booked'],'completed'),
                 'lose':(['approval','quoted','exception','reactivated'],'lost'),
                 'reopen':(['exception','lost'],'approval')}
    if action=='book':
        if lead['status'] not in ['quoted','reactivated']: raise ValueError('Approve and send a quote before booking')
        slot=data.get('slot','')
        if slot not in ['Tomorrow · 09:00','Tomorrow · 13:00','Friday · 09:00','Friday · 13:00']:
            raise ValueError('Choose an available demo calendar slot')
        if any(x['slot']==slot for x in book['bookings']):
            audit(state,'leads',entity,'Calendar conflict',f'{slot} already reserved')
            lead['reason']='Calendar conflict — choose another slot'
            return lead
        book['bookings'].append(dict(id=uid('CAL'),lead=entity,slot=slot))
        lead['slot']=slot;lead['status']='booked';lead['reason']='Booking confirmed';lead['stage_history'].append('booked');lead['day']=book['clock']
        notify(state,'leads',entity,'calendar',f'Cleaning appointment: {slot}')
        notify(state,'leads',entity,'email',f'Booking confirmed: {slot}. Quote ${lead["quote"]/100:.2f}.')
    elif action in transitions:
        allowed,target=transitions[action]
        if lead['status'] not in allowed: raise ValueError('Action is not valid for this lifecycle stage')
        if action=='reopen' and not data.get('note','').strip(): raise ValueError('A review note is required')
        lead['status']=target;lead['reason']={'quoted':'Quote sent; awaiting acceptance','completed':'Job completed; review request recorded','lost':'Closed as lost','approval':'Manual review complete; approve quote'}[target];lead['day']=book['clock'];lead['stage_history'].append(target)
        if action=='approve': notify(state,'leads',entity,'email',f'Quote ${lead["quote"]/100:.2f} for {lead["service"]}; awaiting acceptance.')
        if action=='complete': notify(state,'leads',entity,'email','Job completed. Please share a review of your service.')
        if data.get('note'): lead['notes'].append(data['note'])
    else: raise ValueError('Unknown action')
    audit(state,'leads',entity,action.title(),f'Lifecycle state: {lead["status"]}','operator')
    return lead


def tick(state,days):
    book=state['leads'];book['clock']+=days
    for lead in book['leads']:
        age=book['clock']-lead['day']
        def task(name,message):
            if name not in lead['tasks']:
                lead['tasks'].append(name);notify(state,'leads',lead['id'],'email',message)
        if lead['status']=='booked' and age>=1: task('reminder','Reminder: your cleaning appointment is scheduled. Reply to reschedule.')
        if lead['status']=='quoted' and age>=2: task('followup','Following up on your cleaning quote. Would you like an available appointment?')
        if lead['status']=='quoted' and age>=7:
            task('recovery','Your quote is still available. Reply if you would like us to reopen scheduling.')
        if lead['status']=='lost' and age>=30 and lead['consent']:
            task('reactivation','You opted into updates. Would you like a fresh cleaning quote?')
            lead['status']='reactivated';lead['day']=book['clock']
    audit(state,'leads','scheduler','Demo clock advanced',f'{days} days; current demo day {book["clock"]}')
    return book
