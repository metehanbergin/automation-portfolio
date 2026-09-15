"""Durable, resumable order-to-cash state machine with safe retries and role checks."""
from .core import audit, notify, now, uid, whole_number

ROLES={'operator','approver','finance','viewer'}


def initial():
    return dict(clock=0,orders=[],exceptions=[],inventory={'DESK':18,'CHAIR':40,'PRINT':0},
                accounts=[dict(id='AC-101',name='Atlas Workspace',discount=10),dict(id='AC-102',name='Forma Studio',discount=0),dict(id='AC-103',name='Civic Supply',discount=5)],
                catalog=[dict(sku='DESK',name='Modular desk',price=64000,route='warehouse'),dict(sku='CHAIR',name='Task chair',price=28000,route='supplier'),dict(sku='PRINT',name='Custom wall print',price=9500,route='print_on_demand')])


def check_role(role,allowed):
    if role not in allowed: raise PermissionError('This action requires '+', '.join(allowed)+' role')


def exception(state,order,code,severity,detail,retryable=False):
    book=state['orders']
    existing=next((e for e in book['exceptions'] if e['order']==order['id'] and e['code']==code and e['status']=='open'),None)
    if existing: return existing
    e=dict(id=uid('EXC'),order=order['id'],code=code,severity=severity,detail=detail,retryable=retryable,
           due=book['clock']+(2 if severity=='critical' else 24),status='open',at=now(),resolution=None)
    book['exceptions'].append(e);order['exception']=e['id']
    audit(state,'orders',order['id'],'Exception opened',f'{code}: {detail}')
    return e


def create(state,data):
    book=state['orders']; key=data.get('key','').strip()
    if not key: raise ValueError('An idempotency key is required')
    qty=whole_number(data.get('quantity',1),'Quantity',1,100)
    price=whole_number(data['price'],'Source price in cents',0,100000000) if data.get('price') is not None else None
    scenario=data.get('scenario','normal')
    if scenario not in ['normal','supplier_failure','delayed','payment_mismatch','invoice_mismatch','manual']: raise ValueError('Unknown scenario')
    source_payload=dict(account=data.get('account'),sku=data.get('sku'),quantity=qty,price=price,scenario=scenario)
    old=next((o for o in book['orders'] if o['key']==key),None)
    if old:
        expected=old.get('source_payload',dict(account=old['account'],sku=old['sku'],quantity=old['quantity'],price=old.get('requested_price'),scenario=old['scenario']))
        if source_payload!=expected: raise ValueError('Idempotency key reused with a different order payload')
        audit(state,'orders',old['id'],'Duplicate suppressed',f'Idempotency key {key}; returning original order')
        return old
    account=next((a for a in book['accounts'] if a['id']==data.get('account')),None)
    item=next((i for i in book['catalog'] if i['sku']==data.get('sku')),None)
    if not item: raise ValueError('Select a catalog item')
    unit=item['price']*(100-account['discount'])//100 if account else item['price']
    o=dict(id=uid('ORD'),key=key,account=data.get('account'),customer=account['name'] if account else 'Unverified account',
           sku=item['sku'],product=item['name'],quantity=qty,unit=unit,total=unit*qty,requested_price=price,source_payload=source_payload,
           route='manual' if scenario=='manual' else item['route'],scenario=scenario,status='quote_approval',
           attempts=0,next_retry=None,provider_ok=False,exception=None,created=now(),history=['received','account_checked','quote_prepared'],
           reserved=False,shipment=None,invoice=None,payment=None)
    book['orders'].append(o)
    audit(state,'orders',o['id'],'Order received',f'{key}; {qty} × {item["name"]}')
    if not account:
        o['status']='blocked';exception(state,o,'missing_customer','high','A verified business account is required')
    elif price is not None and price!=unit:
        o['status']='blocked';exception(state,o,'pricing_mismatch','high',f'Account price is {unit/100:.2f} USD; source price differs')
    else: audit(state,'orders',o['id'],'Quote prepared',f'Account discount applied; total {o["total"]/100:.2f} USD')
    return o


def step(state,o):
    book=state['orders'];status=o['status']
    if status=='inventory':
        if o['route']=='warehouse':
            if book['inventory'][o['sku']]<o['quantity']:
                o['status']='blocked';exception(state,o,'stock_unavailable','high','Warehouse stock is below order quantity; approve alternative routing')
                return
            if not o['reserved']:
                book['inventory'][o['sku']]-=o['quantity'];o['reserved']=True
                audit(state,'orders',o['id'],'Inventory reserved',f'{o["quantity"]} units')
        o['status']='fulfillment';o['history'].append('inventory_checked')
    elif status=='fulfillment':
        if o['route']=='manual':
            o['status']='blocked';exception(state,o,'manual_fulfillment','high','Custom fulfillment needs an operator-confirmed dispatch')
            return
        o['attempts']+=1
        if o['scenario']=='supplier_failure' and not o['provider_ok']:
            audit(state,'orders',o['id'],'Supplier request failed',f'HTTP 503 (sandbox); attempt {o["attempts"]}; stable provider key {o["key"]}')
            if o['attempts']<3:
                o['status']='retry_wait';o['next_retry']=book['clock']+2**o['attempts']
                audit(state,'orders',o['id'],'Retry scheduled',f'Demo hour {o["next_retry"]}')
            else:
                o['status']='blocked';exception(state,o,'supplier_unavailable','critical','Three safe attempts failed. Review provider recovery before resuming.',True)
            return
        dispatch(state,o)
    elif status=='shipped':
        if o['scenario']=='delayed' and not o.get('delivery_confirmed'):
            o['status']='blocked';exception(state,o,'delayed_shipment','high','Carrier ETA exceeded; verify delivery with the warehouse')
            return
        o['status']='invoicing';o['history'].append('delivered')
    elif status=='invoicing':
        if not o['invoice']:
            o['invoice']=dict(id=uid('INV'),total=o['total']+(1000 if o['scenario']=='invoice_mismatch' else 0))
        if o['invoice']['total']!=o['total']:
            o['status']='blocked';exception(state,o,'invoice_mismatch','high','Invoice total differs from the approved quote')
            return
        o['status']='awaiting_payment';o['history'].append('invoiced')
        notify(state,'orders',o['id'],'invoice',f'{o["invoice"]["id"]}: {o["total"]/100:.2f} USD')
    elif status=='awaiting_payment':
        amount=o['total']-5000 if o['scenario']=='payment_mismatch' else o['total']
        o['payment']=dict(reference='BANK-'+o['id'],amount=amount)
        o['status']='reconciling';o['history'].append('payment_received')
    elif status=='reconciling':
        if o['payment']['amount']!=o['invoice']['total']:
            o['status']='blocked';exception(state,o,'payment_mismatch','high','Bank payment does not equal invoice balance; finance review required')
            return
        o['status']='completed';o['history'].append('reconciled')
        notify(state,'orders',o['id'],'customer_email','Order complete; payment reconciled. Thank you.')
    else: raise ValueError('Workflow is waiting for an approval, retry time, or exception resolution')
    audit(state,'orders',o['id'],'Workflow advanced',f'{status} → {o["status"]}')


def dispatch(state,o):
    if not o['shipment']:
        o['shipment']=dict(id=uid('SHIP'),tracking='DEMO-'+o['key'],provider=o['route'])
        notify(state,'orders',o['id'],'fulfillment',f'{o["route"]} accepted {o["key"]}')
        notify(state,'orders',o['id'],'customer_email',f'Order dispatched. Tracking: {o["shipment"]["tracking"]}')
    o['status']='shipped';o['history'].append('dispatched')


def action(state,entity,action,data,role):
    book=state['orders'];o=next(x for x in book['orders'] if x['id']==entity)
    if action=='approve':
        check_role(role,['approver'])
        if o['status']!='quote_approval': raise ValueError('Quote is not awaiting approval')
        o['status']='inventory';o['history'].append('quote_approved')
        audit(state,'orders',entity,'Quote approved',f'{o["total"]/100:.2f} USD',role)
    elif action=='advance':
        check_role(role,['operator','finance'])
        if o['status'] in ['awaiting_payment','reconciling'] and role!='finance': raise PermissionError('Payment and reconciliation steps require finance role')
        step(state,o)
    elif action=='resolve':
        e=next((e for e in book['exceptions'] if e['id']==o['exception'] and e['status']=='open'),None)
        if not e: raise ValueError('No open exception')
        financial=e['code'] in ['payment_mismatch','invoice_mismatch']
        check_role(role,['finance'] if financial else ['approver'])
        note=data.get('note','').strip()
        if not note: raise ValueError('Resolution evidence is required')
        code=e['code']
        if code=='missing_customer':
            account=next((a for a in book['accounts'] if a['id']==data.get('account')),None)
            if not account: raise ValueError('Select a verified account')
            item=next(i for i in book['catalog'] if i['sku']==o['sku'])
            o.update(account=account['id'],customer=account['name'],unit=item['price']*(100-account['discount'])//100)
            o['total']=o['unit']*o['quantity'];o['status']='quote_approval'
        elif code=='pricing_mismatch': o['status']='quote_approval'
        elif code=='stock_unavailable': o['route']='supplier';o['status']='fulfillment'
        elif code=='manual_fulfillment': dispatch(state,o)
        elif code=='supplier_unavailable': o['provider_ok']=True;o['status']='fulfillment'
        elif code=='delayed_shipment': o['delivery_confirmed']=True;o['status']='shipped'
        elif code=='invoice_mismatch': o['invoice']['total']=o['total'];o['status']='invoicing'
        elif code=='payment_mismatch':
            if int(data.get('amount',0))!=o['invoice']['total']: raise ValueError('Enter the verified total received in cents; must reconcile exactly')
            o['payment']['amount']=int(data['amount']);o['status']='reconciling'
        else: raise ValueError('Unsupported exception resolution')
        e.update(status='resolved',resolution=note,resolved_at=now());o['exception']=None
        audit(state,'orders',entity,'Exception resolved',f'{code}: {note}',role)
    else: raise ValueError('Unknown action')
    return o


def tick(state,hours):
    book=state['orders'];book['clock']+=hours
    for o in book['orders']:
        if o['status']=='retry_wait' and o['next_retry']<=book['clock']:
            o['status']='fulfillment';step(state,o)
    audit(state,'orders','scheduler','Demo clock advanced',f'{hours} hours; now hour {book["clock"]}')
    return book
