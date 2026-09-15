"""Transactional demo state. Providers write receipts to a local outbox only."""
import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal, InvalidOperation

DB = Path(os.getenv('PORTFOLIO_DB', 'portfolio.db'))


def whole_number(value, label, minimum, maximum):
    """Reject fractional quantities instead of silently truncating source data."""
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number != number.to_integral_value():
            raise ValueError()
        if not minimum <= number <= maximum:
            raise ValueError()
        return int(number)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f'{label} must be a whole number between {minimum} and {maximum}')


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def uid(prefix):
    return f'{prefix}-{uuid.uuid4().hex[:8].upper()}'


def audit(state, project, entity, event, detail, actor='system'):
    entry = dict(id=uid('EVT'), project=project, entity=entity, event=event,
                 detail=detail, actor=actor, at=now())
    state['events'].append(entry)
    return entry


def notify(state, project, entity, channel, payload):
    key = f'{project}:{entity}:{channel}:{payload}'
    existing = next((x for x in state['outbox'] if x['key'] == key), None)
    if existing:
        return existing
    receipt = dict(id=uid('MSG'), project=project, entity=entity, key=key,
                   channel=channel, payload=payload, status='sandbox_delivered', at=now())
    state['outbox'].append(receipt)
    audit(state, project, entity, 'Provider receipt', f'{channel}: {payload}')
    return receipt


def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as con:
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, state TEXT NOT NULL, touched REAL NOT NULL)')


@contextmanager
def transaction(sid):
    with sqlite3.connect(DB, timeout=15) as con:
        con.execute('BEGIN IMMEDIATE')
        row = con.execute('SELECT state FROM sessions WHERE id=?', (sid,)).fetchone()
        if row is None:
            raise KeyError('Session expired. Reload to start a new sandbox.')
        state = json.loads(row[0])
        yield state
        con.execute('UPDATE sessions SET state=?, touched=? WHERE id=?', (json.dumps(state), time.time(), sid))


def create_session(state):
    sid = uuid.uuid4().hex + uuid.uuid4().hex
    with sqlite3.connect(DB) as con:
        con.execute('DELETE FROM sessions WHERE touched < ?', (time.time() - 7*86400,))
        con.execute('INSERT INTO sessions VALUES (?,?,?)', (sid, json.dumps(state), time.time()))
    return sid


def get_session(sid):
    if not sid:
        return None
    with sqlite3.connect(DB) as con:
        row = con.execute('SELECT state FROM sessions WHERE id=?', (sid,)).fetchone()
    return json.loads(row[0]) if row else None
