#!/usr/bin/env python3
"""Configura de manera repetible la demo nativa Qualiteasy via REST API de Zammad."""
from pathlib import Path
import os
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from poc_api import ZammadApi

root = Path(__file__).resolve().parents[1]
api = ZammadApi('http://127.0.0.1:8084', root / '.zammad-api-token')
settings = {s['name']: s for s in api.call('GET', 'settings')}
changes = {
    'product_name': 'Qualiteasy · Incidències',
    'fqdn': 'localhost:8084',
    'ticket_hook': 'Incidència #',
    'ui_ticket_create_available_types': ['phone-in'],
    'ui_ticket_create_default_type': 'phone-in',
    'user_create_account': False,
}
for name, value in changes.items():
    entry = settings[name]
    if entry['state_current']['value'] == value:
        print('setting ja configurat:', name)
        continue
    api.call('PUT', f"settings/{entry['id']}", {'state_current': {'value': value}})
    print('setting actualitzat:', name)

translations = {
    'New Ticket': 'Nova incidència',
    'Ticket': 'Incidència',
    'Tickets': 'Incidències',
    'Ticket#': 'Incidència #',
    'Received Call': 'Nova incidència',
    'Inbound Call': 'Nova incidència',
    'Related Tickets': 'Incidències relacionades',
    'Outbound Call': 'Incidència',
    'Send Email': 'Incidència',
    'My Stats': 'Seguiment municipal',
    'Dashboard': 'Panell d’incidències',
}
for source, target in translations.items():
    api.call('POST', 'translations/upsert', {'locale': 'ca', 'source': source, 'target': target})
    print('traducció:', source, '→', target)

name = 'Alella · brigada i validació municipal'
existing = next((x for x in api.call('GET', 'checklist_templates') if x['name'] == name), None)
items = [
    'Confirmar l’origen, la ubicació i les fotografies de l’avís',
    'Ajuntament: validar i classificar la incidència',
    'Ajuntament: assignar responsable i termini a la brigada',
    'Brigada: executar l’actuació i adjuntar foto del resultat',
    'Brigada: efectuar el pretancament',
    'Ajuntament: verificar el resultat i fer el tancament definitiu',
    'Valorar si cal convertir la incidència en una no conformitat',
]
if existing:
    template = existing
    print('checklist plantilla ja existent:', template['id'])
else:
    template = api.call('POST', 'checklist_templates', {'name': name, 'active': True, 'items': items})
    print('checklist plantilla creada:', template['id'])

ticket_id = int(os.environ.get('QE_DEMO_TICKET_ID', '0'))
if ticket_id:
    incidence = api.call('GET', f'tickets/{ticket_id}')
    if incidence.get('checklist_id'):
        print('checklist ja vinculada a la incidència:', incidence['checklist_id'])
    else:
        result = api.call('POST', 'checklists', {'ticket_id': ticket_id, 'template_id': template['id']})
        print('checklist vinculada:', result['id'])
