#!/usr/bin/env python3
"""Prova repetible de la configuració municipal de Zammad via REST API.

Només usa dades fictícies. Llegeix el token d'un fitxer privat i no l'imprimeix.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


class ApiError(RuntimeError):
    pass


class ZammadApi:
    def __init__(self, base_url: str, token_file: Path):
        self.base_url = base_url.rstrip('/') + '/api/v1'
        self.token = token_file.read_text().strip()
        if not self.token:
            raise ApiError('El fitxer de token és buit')

    def call(self, method: str, path: str, payload=None, timeout=30):
        body = None if payload is None else json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(
            self.base_url + '/' + path.lstrip('/'),
            data=body,
            method=method,
            headers={
                'Authorization': 'Token token=' + self.token,
                'Content-Type': 'application/json',
                'X-Zammad-Suppress-Notifications': 'true',
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            detail = error.read().decode('utf-8', 'replace')[:500]
            raise ApiError(f'{method} {path}: HTTP {error.code}: {detail}') from error


def ensure(api: ZammadApi, path: str, name: str, payload: dict):
    existing = next((row for row in api.call('GET', path) if row.get('name') == name), None)
    if existing:
        print(f'ja existeix: {path} / {name} (id={existing["id"]})')
        return existing, False
    created = api.call('POST', path, payload)
    print(f'creat: {path} / {name} (id={created["id"]})')
    return created, True


def field_screens():
    return {
        'create_middle': {'ticket.agent': {'shown': True, 'required': False, 'item_class': 'column'}},
        'edit': {'ticket.agent': {'shown': True, 'required': False}},
    }


def configure(api: ZammadApi):
    groups = {}
    for name in ('Recepció municipal', 'Brigada', 'Validació municipal'):
        groups[name], _ = ensure(api, 'groups', name, {
            'name': name,
            'active': True,
            'follow_up_possible': 'yes',
            'follow_up_assignment': True,
            'note': 'Qualiteasy: prova municipal amb dades fictícies',
        })

    state_list = api.call('GET', 'ticket_states')
    open_state = next(row for row in state_list if row['name'] == 'open')
    for name in ('En execució', 'Pendent de validació'):
        ensure(api, 'ticket_states', name, {
            'name': name,
            'state_type_id': open_state['state_type_id'],
            'ignore_escalation': False,
            'active': True,
        })

    agent = next(row for row in api.call('GET', 'roles') if row['name'] == 'Agent')
    expanded_agent = api.call('GET', f'roles/{agent["id"]}?expand=true')
    permission_map = dict(zip(expanded_agent['permissions'], expanded_agent['permission_ids']))
    ticket_agent_id = permission_map['ticket.agent']
    roles = (
        ('Operari de brigada', {
            str(groups['Brigada']['id']): 'full',
            str(groups['Validació municipal']['id']): ['create', 'read'],
        }),
        ('Validador municipal', {
            str(groups['Brigada']['id']): 'read',
            str(groups['Validació municipal']['id']): 'full',
        }),
    )
    for name, group_ids in roles:
        ensure(api, 'roles', name, {
            'name': name,
            'active': True,
            'default_at_signup': False,
            'note': 'Qualiteasy: rol de prova municipal',
            'permission_ids': [ticket_agent_id],
            'group_ids': group_ids,
        })

    fields = (
        ('qe_origen', 'Origen municipal', 'select', {
            'options': {'whatsapp': 'WhatsApp', 'intern': 'Intern', 'altres': 'Altres'},
            'default': '',
            'linktemplate': '',
        }),
        ('qe_ambit', 'Àmbit', 'select', {
            'options': {'via_publica': 'Via pública', 'edificis': 'Edificis', 'actes': 'Actes', 'altres': 'Altres'},
            'default': '',
            'linktemplate': '',
        }),
        ('qe_ubicacio', 'Ubicació', 'input', {'type': 'text', 'maxlength': 200}),
    )
    created_fields = False
    for position, (name, display, data_type, data_option) in enumerate(fields, start=1500):
        _, created = ensure(api, 'object_manager_attributes', name, {
            'name': name,
            'object': 'Ticket',
            'display': display,
            'active': True,
            'position': position,
            'data_type': data_type,
            'data_option': data_option,
            'screens': field_screens(),
        })
        created_fields |= created
    if created_fields:
        api.call('POST', 'object_manager_attributes_execute_migrations', {}, timeout=120)
        print('migracions dels camps executades; cal reiniciar els serveis Zammad')


def inspect(api: ZammadApi):
    for label, path in (
        ('grups', 'groups'),
        ('estats', 'ticket_states'),
        ('rols', 'roles'),
        ('camps qe_', 'object_manager_attributes'),
    ):
        rows = api.call('GET', path)
        if path == 'object_manager_attributes':
            rows = [row for row in rows if row.get('name', '').startswith('qe_')]
        print(label, [(row['id'], row['name']) for row in rows])


def ticket(api: ZammadApi):
    title = 'POC Qualiteasy - avís fictici de via pública'
    existing = next((row for row in api.call('GET', 'tickets') if row.get('title') == title), None)
    if existing:
        print(f'ja existeix: ticket id={existing["id"]} número={existing.get("number")}')
        return
    me = api.call('GET', 'users/me')
    created = api.call('POST', 'tickets', {
        'title': title,
        'group': 'Brigada',
        'customer_id': me['id'],
        'state': 'En execució',
        'qe_origen': 'whatsapp',
        'qe_ambit': 'via_publica',
        'qe_ubicacio': 'Ubicació fictícia de prova',
        'article': {
            'subject': 'Avís de prova',
            'body': 'Desperfecte fictici per provar assignació, fotografies i pretancament.',
            'type': 'note',
            'internal': True,
        },
    })
    print(f'creat: ticket id={created["id"]} número={created.get("number")}')


def isolation(api: ZammadApi, other_base: str):
    other = ZammadApi(other_base, args.token_file)
    try:
        other.call('GET', 'groups')
    except ApiError as error:
        if 'HTTP 401' in str(error) or 'HTTP 403' in str(error):
            print('aïllament autenticació: correcte; el token del primer client és rebutjat pel segon')
            return
        raise
    raise ApiError('El segon client ha acceptat el token del primer')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'configure', 'ticket', 'isolation'))
    parser.add_argument('--base-url', default='http://127.0.0.1:8081')
    parser.add_argument('--other-base-url', default='http://127.0.0.1:8082')
    parser.add_argument('--token-file', type=Path, default=Path(__file__).with_name('.zammad-api-token'))
    args = parser.parse_args()
    try:
        client = ZammadApi(args.base_url, args.token_file)
        {'inspect': inspect, 'configure': configure, 'ticket': ticket}.get(args.command, lambda _: isolation(client, args.other_base_url))(client)
    except (ApiError, OSError, KeyError, ValueError) as failure:
        print(f'error: {failure}', file=sys.stderr)
        raise SystemExit(1)
