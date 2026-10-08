"""Persistent state for the local Alella workflow demo, keyed by Zammad ticket ID.

This file is deliberately a prototype store. It is not an authorization boundary or the
multitenant Qualiteasy data model. Zammad remains the operational ticket record.
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).with_name('demo-workflow.sqlite3')


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db


def initialize():
    with connect() as db:
        db.executescript('''
          CREATE TABLE IF NOT EXISTS incident_meta (
            ticket_id INTEGER PRIMARY KEY,
            payload TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL
          );
          CREATE TABLE IF NOT EXISTS workflow_event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            actor TEXT NOT NULL,
            detail TEXT NOT NULL,
            created_at TEXT NOT NULL
          );
          CREATE TABLE IF NOT EXISTS notification_preview (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            channel TEXT NOT NULL,
            recipient TEXT NOT NULL,
            purpose TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Simulat · no enviat',
            created_at TEXT NOT NULL
          );
          CREATE TABLE IF NOT EXISTS demo_nc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL UNIQUE,
            reason TEXT NOT NULL,
            cause TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Pendent d’anàlisi',
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL
          );
        ''')


def meta(ticket_id):
    with connect() as db:
        row = db.execute('SELECT payload FROM incident_meta WHERE ticket_id=?', (ticket_id,)).fetchone()
    return json.loads(row['payload']) if row else {}


def save_meta(ticket_id, changes):
    with connect() as db:
        row = db.execute('SELECT payload FROM incident_meta WHERE ticket_id=?', (ticket_id,)).fetchone()
        payload = json.loads(row['payload']) if row else {}
        payload.update(changes)
        db.execute('''INSERT INTO incident_meta(ticket_id,payload,updated_at) VALUES(?,?,?)
                      ON CONFLICT(ticket_id) DO UPDATE SET payload=excluded.payload,
                      updated_at=excluded.updated_at''',
                   (ticket_id, json.dumps(payload, ensure_ascii=False), now()))
    return payload


def add_event(ticket_id, kind, actor, detail):
    with connect() as db:
        db.execute('INSERT INTO workflow_event(ticket_id,kind,actor,detail,created_at) VALUES(?,?,?,?,?)',
                   (ticket_id, kind, actor, detail, now()))


def events(ticket_id):
    with connect() as db:
        rows = db.execute('SELECT kind,actor,detail,created_at FROM workflow_event WHERE ticket_id=? ORDER BY id DESC',
                          (ticket_id,)).fetchall()
    return [dict(row) for row in rows]


def add_notification(ticket_id, channel, recipient, purpose, message):
    with connect() as db:
        db.execute('''INSERT INTO notification_preview(ticket_id,channel,recipient,purpose,message,created_at)
                      VALUES(?,?,?,?,?,?)''', (ticket_id, channel, recipient, purpose, message, now()))


def notifications(ticket_id):
    with connect() as db:
        rows = db.execute('''SELECT channel,recipient,purpose,message,status,created_at
                             FROM notification_preview WHERE ticket_id=? ORDER BY id DESC''', (ticket_id,)).fetchall()
    return [dict(row) for row in rows]


def get_nc(ticket_id):
    with connect() as db:
        row = db.execute('SELECT * FROM demo_nc WHERE ticket_id=?', (ticket_id,)).fetchone()
    return dict(row) if row else None


def create_nc(ticket_id, reason, cause, actor):
    with connect() as db:
        db.execute('''INSERT OR IGNORE INTO demo_nc(ticket_id,reason,cause,created_by,created_at)
                      VALUES(?,?,?,?,?)''', (ticket_id, reason, cause, actor, now()))
        row = db.execute('SELECT * FROM demo_nc WHERE ticket_id=?', (ticket_id,)).fetchone()
    return dict(row)
