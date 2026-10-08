#!/usr/bin/env python3
"""Local municipal workflow facade over Zammad for the Alella demonstration.

Role switching and notification previews are deliberately simulated. This server binds
only to loopback and is not a production authorization or messaging service.
"""
import base64
import html
import json
import mimetypes
import os
import secrets
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from http.server import ThreadingHTTPServer
from pathlib import Path

import server as intake
import workflow_store as store

ROOT = Path(__file__).resolve().parent
AUTH_FILE = os.environ.get('QE_DEMO_PASSWORD_FILE')
AUTH_PASSWORD = Path(AUTH_FILE).read_text().strip() if AUTH_FILE else None
ALLOWED_GROUPS = {2, 3, 4}
ORIGINS = {'telefon', 'correu', 'whatsapp', 'web_municipal', 'ajuntament'}
ORIGIN_LABELS = {'telefon': 'Trucada rebuda', 'correu': 'Correu rebut', 'whatsapp': 'WhatsApp',
                 'web_municipal': 'Web municipal', 'ajuntament': 'Detecció interna',
                 'brigada': 'Operari de brigada', 'intern': 'Gestió interna'}
CATEGORIES = {'via_publica', 'edificis', 'actes', 'altres'}
ROLES = {'municipal', 'brigada', 'brigada_suport', 'cap_brigada', 'responsable_servei', 'validador'}
ASSIGNEES = {4: 'Operari Prova', 6: 'Operari Suport Prova'}
STAGES = {1: 'Nova', 2: 'Oberta', 3: 'Pendent', 4: 'Tancada',
          7: 'En execució', 8: 'Pendent de validació', 9: 'Pendent de revisió'}
NC_PENDING_TAG = 'qe-pendent-nc'
NC_LINKED_TAG = 'qe-nc-demo'
DEMO_PEOPLE = {
    'municipal': {'id': 3, 'name': 'Ajuntament · usuari de prova', 'position': 'Gestió municipal'},
    'brigada': {'id': 4, 'name': 'Operari Prova', 'position': 'Operari de brigada'},
    'brigada_suport': {'id': 6, 'name': 'Operari Suport Prova', 'position': 'Operari de brigada'},
    'validador': {'id': 5, 'name': 'Validador Prova', 'position': 'Responsable de tancament'},
    'cap_brigada': {'id': None, 'name': 'Cap de Brigada (prova)', 'position': 'Coordinació de brigada'},
    'responsable_servei': {'id': None, 'name': 'Responsable del servei (prova)', 'position': 'Seguiment del servei'},
}


def request_zammad(method, path, payload=None, raw=False):
    token = intake.TOKEN_FILE.read_text().strip()
    req = urllib.request.Request(
        intake.ZAMMAD + '/api/v1/' + path,
        data=json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None,
        method=method,
        headers={'Authorization': 'Token token=' + token,
                 'Content-Type': 'application/json',
                 'X-Zammad-Suppress-Notifications': 'true'},
    )
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=45) as response:
        return (response.read(), response.headers.get('Content-Type', 'application/octet-stream')) if raw else json.load(response)


def json_body(handler):
    if handler.headers.get('X-CSRF') != intake.CSRF:
        raise PermissionError('Sessió caducada. Torna a carregar la pàgina.')
    if handler.headers.get('Content-Type', '').split(';')[0] != 'application/json':
        raise ValueError('Format no acceptat.')
    size = int(handler.headers.get('Content-Length', '0'))
    if not 0 < size <= 48 * 1024 * 1024:
        raise ValueError('La petició és massa gran.')
    return json.loads(handler.rfile.read(size))


def image_attachment(photo):
    mime = str(photo.get('content_type', ''))
    if mime not in ('image/jpeg', 'image/png', 'image/webp'):
        raise ValueError('Cal una imatge JPEG, PNG o WebP.')
    raw = base64.b64decode(photo.get('data', ''), validate=True)
    if not 0 < len(raw) <= intake.MAX_PHOTO:
        raise ValueError('Cada foto ha de tenir un màxim de 8 MB.')
    signatures = {'image/jpeg': raw.startswith(b'\xff\xd8\xff'),
                  'image/png': raw.startswith(b'\x89PNG\r\n\x1a\n'),
                  'image/webp': raw.startswith(b'RIFF') and raw[8:12] == b'WEBP'}
    if not signatures[mime]:
        raise ValueError('El contingut de la foto no coincideix amb el format indicat.')
    filename = Path(str(photo.get('name', 'foto'))).name[:100]
    if not filename or filename.startswith('.'):
        filename = 'foto' + {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}[mime]
    return {'filename': filename, 'data': base64.b64encode(raw).decode(), 'mime-type': mime}


def document_attachment(file):
    mime = str(file.get('content_type', ''))
    if mime != 'application/pdf':
        return image_attachment(file)
    raw = base64.b64decode(file.get('data', ''), validate=True)
    if not 0 < len(raw) <= intake.MAX_PHOTO or not raw.startswith(b'%PDF-'):
        raise ValueError('Cada PDF ha de ser vàlid i tenir un màxim de 8 MB.')
    filename = Path(str(file.get('name', 'document.pdf'))).name[:100]
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    return {'filename': filename, 'data': base64.b64encode(raw).decode(), 'mime-type': mime}


def field(item, key, limit=200, required=False):
    value = str(item.get(key, '')).strip()
    if len(value) > limit or (required and not value):
        raise ValueError('Revisa el camp «' + key + '».')
    return value


def actor(item, allowed):
    role = item.get('actor_role')
    if role not in allowed:
        raise ValueError('Aquesta acció no correspon al perfil de demostració seleccionat.')
    return DEMO_PEOPLE[role]


def ticket_in_demo(ticket_id):
    ticket = request_zammad('GET', f'tickets/{ticket_id}')
    if ticket.get('group_id') not in ALLOWED_GROUPS:
        raise LookupError('La incidència no pertany als grups de la demostració.')
    return ticket


def ticket_media(ticket_id):
    articles = request_zammad('GET', f'ticket_articles/by_ticket/{ticket_id}')
    media = []
    for article in articles:
        for attachment in article.get('attachments', []):
            mime = (attachment.get('preferences') or {}).get('Mime-Type', '') or attachment.get('content_type', '')
            filename = attachment.get('filename', 'Adjunt')
            media.append({'name': filename, 'image': mime.startswith('image/') or
                          bool(re.search(r'\.(png|jpe?g|webp|gif)$', filename, re.I)),
                          'url': f'/api/attachment/{ticket_id}/{article["id"]}/{attachment["id"]}',
                          'phase': ('Pretancament' if 'pretancament' in (article.get('subject') or '').lower() else
                                    'Tancament' if 'tancament' in (article.get('subject') or '').lower() else 'Avís')})
    return media


def preview_payload(ticket, media=None):
    ticket_id = ticket['id']
    metadata = store.meta(ticket_id)
    if ticket.get('qe_origen') == 'brigada' and not metadata.get('reporter_name'):
        metadata = {**metadata, 'reporter_name': 'Operari Prova', 'reporter_position': 'Operari de brigada',
                    'origin_department': 'Brigada municipal'}
    linked_nc = store.get_nc(ticket_id)
    tags = request_zammad('GET', f'tags?object=Ticket&o_id={ticket_id}').get('tags', [])
    if media is None:
        media = ticket_media(ticket_id)
    photos = [m for m in media if m['image']]
    return {'id': ticket_id, 'number': ticket['number'], 'title': ticket['title'],
            'stage': STAGES.get(ticket.get('state_id'), 'Altres'),
            'state_id': ticket.get('state_id'), 'group_id': ticket.get('group_id'),
            'owner_id': ticket.get('owner_id'), 'origin': ticket.get('qe_origen') or 'altres',
            'category': ticket.get('qe_ambit') or metadata.get('category', ''),
            'location': ticket.get('qe_ubicacio') or '',
            'lat': ticket.get('qe_latitud'), 'lon': ticket.get('qe_longitud'),
            'location_source': ticket.get('qe_ubicacio_font') or '',
            'photo': photos[0]['url'] if photos else None,
            'photos': photos, 'attachments': media,
            'synthetic_photo': bool(photos and 'sintetica' in photos[0]['name'].lower()),
            'nc_pending': NC_PENDING_TAG in tags and not linked_nc,
            'nc': {**linked_nc, 'reference': f'NC-DEMO-{linked_nc["id"]:04d}'} if linked_nc else None,
            'created_at': ticket.get('created_at'), 'metadata': metadata,
            'events': store.events(ticket_id), 'notifications': store.notifications(ticket_id)}


def visible_to_role(item, role):
    if role in ('brigada', 'brigada_suport'):
        user_id = DEMO_PEOPLE[role]['id']
        return item['owner_id'] == user_id or item['metadata'].get('assignee_id') == user_id
    if role == 'validador':
        return item['group_id'] == 4
    if role == 'cap_brigada':
        return bool(item['metadata'].get('brigade_lead'))
    if role == 'responsable_servei':
        return bool(item['metadata'].get('service_lead'))
    return True


def work_order_html(item):
    m = item['metadata']
    esc = lambda value: html.escape(str(value or '—'))
    case_title = re.sub(r'^\[MOSTRA ALELLA · NC \d+\]\s*', '', item['title'])
    photo_rows = ''.join('<figure><img src="' + esc(p['url']) + '" alt="Fotografia adjunta"><figcaption>' +
                         esc(p['phase'] + ' · ' + p['name']) + '</figcaption></figure>' for p in item['photos'][:4])
    generated = datetime.now().astimezone().strftime('%d/%m/%Y %H:%M')
    return f'''<!doctype html><html lang="ca"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ordre de treball · {esc(item['number'])}</title><link rel="stylesheet" href="/work-order.css"></head><body>
    <header><div><small>QUALITEASY · ALELLA · DEMOSTRACIÓ</small><h1>Ordre de treball</h1><p>Incidència #{esc(item['number'])} · Generada el {esc(generated)}</p></div><button id="print" type="button">Imprimeix / Desa en PDF</button></header>
    <main><section class="intro"><strong>{esc(case_title)}</strong><span class="state">{esc(item['stage'])}</span></section>
    <div class="grid"><div><small>Data de l’avís</small><b>{esc(str(item["created_at"] or "")[:10])}</b></div><div><small>Canal d’entrada</small><b>{esc(ORIGIN_LABELS.get(item["origin"], item["origin"]))}</b></div><div><small>Autor / càrrec</small><b>{esc(m.get("reporter_name"))} · {esc(m.get("reporter_position"))}</b></div><div><small>Ubicació</small><b>{esc(item['location'])}</b></div><div><small>Àmbit</small><b>{esc(m.get('category') or item['category'])}</b></div><div><small>Prioritat</small><b>{esc(m.get('priority'))}</b></div><div><small>Data límit</small><b>{esc(m.get('due_date'))}</b></div><div><small>Departament d’origen</small><b>{esc(m.get('origin_department'))}</b></div><div><small>Departament destí</small><b>{esc(m.get('target_department') or 'Serveis municipals')}</b></div><div><small>Executor / càrrec</small><b>{esc(m.get('assignee_name'))} · {esc(m.get('assignee_position'))}</b></div><div><small>Coordinació</small><b>{esc(m.get('brigade_lead'))} / {esc(m.get('service_lead'))}</b></div></div>
    <section><h2>Problema comunicat</h2><p>{esc(case_title)}</p></section>
    <section><h2>Acció encomanada</h2><p>{esc(m.get('action_instruction'))}</p></section>
    <section><h2>Observacions de l’execució i pretancament</h2><p>{esc(m.get('work_done'))}</p><div class="photo-grid">{photo_rows}</div></section>
    <section class="signoff"><div><h2>Pretancament de brigada</h2><p>{esc(m.get('preclosed_by'))} · {esc(m.get('preclosed_at'))}</p></div><div><h2>Validació municipal</h2><p>{esc(m.get('closed_by'))} · {esc(m.get('closed_at'))}</p></div></section>
    <footer>Document de la prova local. La fitxa digital és l’original operatiu. Fotos sintètiques identificades quan corresponen. <a href="/demo?role=municipal">Torna al panell</a>.</footer></main><script src="/work-order.js" defer></script></body></html>'''.encode()


class Handler(intake.Handler):
    def authenticated(self):
        if not AUTH_PASSWORD:
            return True
        header = self.headers.get('Authorization', '')
        try:
            scheme, value = header.split(' ', 1)
            user, password = base64.b64decode(value, validate=True).decode().split(':', 1)
            valid = scheme.lower() == 'basic' and secrets.compare_digest(user, 'demo') and secrets.compare_digest(password, AUTH_PASSWORD)
        except (ValueError, UnicodeError):
            valid = False
        if valid:
            return True
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Qualiteasy demo", charset="UTF-8"')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', '0')
        self.end_headers()
        return False
    def serve_file(self, filename):
        body = (ROOT / filename).read_bytes()
        if filename == 'dashboard.html':
            body = body.replace(b'__CSRF__', intake.CSRF.encode())
        self.send_response(200)
        media_type = mimetypes.guess_type(filename)[0] or 'text/plain'
        self.send_header('Content-Type', media_type + ('; charset=utf-8' if media_type.startswith(('text/', 'application/javascript')) else ''))
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' https://tile.openstreetmap.org data: blob:; connect-src 'self'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.authenticated():
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        static = {'/demo': 'dashboard.html', '/qualiteasy-logo.png': 'assets/qualiteasy-logo.png', '/dashboard.js': 'dashboard.js',
                  '/dashboard.css': 'dashboard.css', '/work-order.css': 'work-order.css',
                  '/work-order.js': 'work-order.js'}
        if path in static:
            return self.serve_file(static[path])
        if path == '/api/incidents':
            try:
                role = urllib.parse.parse_qs(parsed.query).get('role', ['municipal'])[0]
                if role not in ROLES:
                    raise ValueError('Perfil desconegut.')
                tickets = request_zammad('GET', 'tickets?per_page=500')
                result = [preview_payload(t) for t in tickets if t.get('group_id') in ALLOWED_GROUPS]
                return self.send_json(200, {'incidents': [item for item in result if visible_to_role(item, role)],
                                            'role': role, 'persona': DEMO_PEOPLE[role],
                                            'role_preview': True})
            except (OSError, ValueError, KeyError) as exc:
                print('List error:', type(exc).__name__, flush=True)
                return self.send_json(502, {'error': 'No es poden carregar les incidències.'})
        order_match = re.fullmatch(r'/ordre/(\d+)', path)
        if order_match:
            try:
                ticket = ticket_in_demo(int(order_match.group(1)))
                body = work_order_html(preview_payload(ticket))
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; base-uri 'none'")
                self.end_headers()
                return self.wfile.write(body)
            except (OSError, ValueError, LookupError):
                return self.send_error(404)
        photo_match = re.fullmatch(r'/api/attachment/(\d+)/(\d+)/(\d+)', path)
        if photo_match:
            try:
                ticket, article, attachment = photo_match.groups()
                details = ticket_in_demo(int(ticket))
                body, mime = request_zammad('GET', f'ticket_attachment/{ticket}/{article}/{attachment}', raw=True)
                if not (mime.startswith('image/') or mime.startswith('application/pdf')):
                    return self.send_error(415)
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'private, max-age=60')
                self.send_header('X-Content-Type-Options', 'nosniff')
                if mime.startswith('application/pdf'):
                    self.send_header('Content-Disposition', 'attachment; filename=\"document.pdf\"')
                self.end_headers()
                return self.wfile.write(body)
            except (OSError, ValueError, LookupError):
                return self.send_error(502)
        return super().do_GET()

    def do_POST(self):
        if not self.authenticated():
            return
        path = urllib.parse.urlparse(self.path).path
        if path == '/api/municipal-incidents':
            try:
                item = json_body(self)
                what, where = field(item, 'what', 2000, True), field(item, 'where', 200, True)
                origin = item.get('origin')
                if origin not in ORIGINS or len(what) < 5 or len(where) < 3:
                    raise ValueError('Indica el canal, què passa i on passa.')
                source = field(item, 'origin_department', 100, True)
                category = item.get('category', '')
                if category and category not in CATEGORIES:
                    raise ValueError('Àmbit desconegut.')
                point = item.get('point')
                fields = {'qe_ubicacio_font': 'adreca_manual'}
                if point:
                    lat, lon = float(point['lat']), float(point['lon'])
                    if not (41.45 <= lat <= 41.53 and 2.25 <= lon <= 2.35):
                        raise ValueError('El punt queda fora de la zona d’Alella.')
                    fields = {'qe_latitud': str(round(lat, 7)),
                              'qe_longitud': str(round(lon, 7)),
                              'qe_ubicacio_font': 'geocodificacio_carrer_aproximada'}
                article = {'subject': 'Entrada municipal',
                           'body': f'Canal: {origin}\n\nIncidència: {what}\n\nUbicació: {where}',
                           'type': 'note', 'internal': True}
                files = item.get('files') or ([item['photo']] if item.get('photo') else [])
                if not isinstance(files, list) or len(files) > 4:
                    raise ValueError('Pots adjuntar fins a quatre fitxers.')
                if files:
                    article['attachments'] = [document_attachment(file) for file in files]
                t = request_zammad('POST', 'tickets', {
                    'title': what.splitlines()[0][:100], 'group': 'Recepció municipal',
                    'state': 'Pendent de revisió municipal', 'customer_id': 3,
                    'qe_origen': origin, 'qe_ubicacio': where,
                    **({'qe_ambit': category} if category else {}), **fields,
                    'article': article,
                })
                store.save_meta(t['id'], {'origin_department': source, 'category': category,
                                          'reporter_name': DEMO_PEOPLE['municipal']['name'],
                                          'reporter_position': DEMO_PEOPLE['municipal']['position'],
                                          'target_department': 'Serveis municipals'})
                store.add_event(t['id'], 'Alta', DEMO_PEOPLE['municipal']['name'], 'Avís registrat i pendent de revisió.')
                return self.send_json(201, {'number': t['number'], 'id': t['id']})
            except PermissionError as exc:
                return self.send_json(403, {'error': str(exc)})
            except (ValueError, KeyError, TypeError) as exc:
                return self.send_json(400, {'error': str(exc) or 'Revisa les dades.'})
            except OSError as exc:
                print('Create error:', type(exc).__name__, flush=True)
                return self.send_json(502, {'error': 'No s’ha pogut crear la incidència.'})
        action_match = re.fullmatch(r'/api/incidents/(\d+)/(assign|preclose|close|return|nc)', path)
        if action_match:
            try:
                ticket_id = int(action_match.group(1))
                action = action_match.group(2)
                item = json_body(self)
                t = ticket_in_demo(ticket_id)
                current = store.meta(ticket_id)
                if action == 'assign':
                    who = actor(item, {'municipal'})
                    if t.get('state_id') != 9:
                        raise ValueError('Només es pot assignar una incidència pendent de revisió.')
                    category = item.get('category')
                    if category not in CATEGORIES:
                        raise ValueError('Selecciona un àmbit.')
                    due = field(item, 'due_date', 10, True)
                    if date.fromisoformat(due) < date.today():
                        raise ValueError('La data límit ha de ser avui o posterior.')
                    action_text = field(item, 'action_instruction', 2000, True)
                    assignee_id = int(item.get('assignee_id', 0))
                    if assignee_id not in ASSIGNEES:
                        raise ValueError('Selecciona un operari disponible.')
                    changes = {
                        'origin_department': field(item, 'origin_department', 100, True),
                        'target_department': field(item, 'target_department', 100, True),
                        'category': category, 'cause': field(item, 'cause', 1000),
                        'priority': item.get('priority') if item.get('priority') in ('normal', 'urgent') else 'normal',
                        'action_instruction': action_text, 'due_date': due,
                        'assignee_id': assignee_id, 'assignee_name': ASSIGNEES[assignee_id],
                        'assignee_position': DEMO_PEOPLE['brigada']['position'],
                        'brigade_lead': field(item, 'brigade_lead', 100, True),
                        'service_lead': field(item, 'service_lead', 100, True),
                        'validator_id': 5, 'validator_name': DEMO_PEOPLE['validador']['name'],
                    }
                    request_zammad('PUT', f'tickets/{ticket_id}', {
                        'group': 'Brigada', 'owner_id': assignee_id, 'state': 'En execució',
                        'qe_ambit': category,
                        'article': {'subject': 'Ordre de treball assignada', 'body':
                                    f'Acció encomanada: {action_text}\nData límit: {due}\nExecutor: {changes["assignee_name"]}',
                                    'type': 'note', 'internal': True},
                    })
                    store.save_meta(ticket_id, changes)
                    store.add_event(ticket_id, 'Assignació', who['name'],
                                    f'Feina assignada a {changes["assignee_name"]}. Data límit {due}.')
                    title = re.sub(r'^\[MOSTRA ALELLA · NC \d+\]\s*', '', t['title'])
                    for channel, recipient, purpose in (
                        ('correu', changes['brigade_lead'], 'Activació a Serveis Municipals'),
                        ('WhatsApp', changes['service_lead'], 'Activació a Serveis Municipals'),
                        ('WhatsApp', changes['assignee_name'], 'Assignació de l’execució')):
                        store.add_notification(ticket_id, channel, recipient, purpose,
                                               f'Incidència #{t["number"]}: {title}. Ubicació: {t.get("qe_ubicacio") or "pendent"}. Data límit: {due}.')
                    return self.send_json(200, {'status': 'assignada', 'number': t['number']})
                if action == 'preclose':
                    who = actor(item, {'brigada', 'brigada_suport'})
                    if t.get('group_id') != 3 or t.get('owner_id') != who['id'] or t.get('state_id') != 7:
                        raise ValueError('Aquesta incidència no està assignada a l’operari de prova.')
                    done = field(item, 'work_done', 2000, True)
                    photos = item.get('photos') or []
                    if not isinstance(photos, list) or len(photos) > 3:
                        raise ValueError('Pots afegir fins a tres fotografies.')
                    article = {'subject': 'Pretancament de la brigada',
                               'body': 'Feina executada: ' + done + '\nPendent de validació municipal.',
                               'type': 'note', 'internal': True}
                    if photos:
                        article['attachments'] = [image_attachment(photo) for photo in photos]
                    request_zammad('PUT', f'tickets/{ticket_id}', {
                        'group': 'Validació municipal', 'owner_id': 5,
                        'state': 'Pendent de validació', 'article': article,
                    })
                    stamp = store.now()
                    store.save_meta(ticket_id, {'work_done': done, 'preclosed_by': who['name'],
                                                 'preclosed_position': who['position'], 'preclosed_at': stamp,
                                                 'validator_id': 5, 'validator_name': DEMO_PEOPLE['validador']['name']})
                    store.add_event(ticket_id, 'Pretancament', who['name'],
                                    'Feina acabada; l’Ajuntament ha de validar-la.' +
                                    (f' {len(photos)} foto(s) adjuntada(es).' if photos else ''))
                    store.add_notification(ticket_id, 'correu', DEMO_PEOPLE['validador']['name'],
                                           'Pendent de validació',
                                           f'Incidència #{t["number"]} pretancada per la brigada. Revisa les evidències.')
                    return self.send_json(200, {'status': 'pendent_validacio'})
                if action == 'close':
                    who = actor(item, {'municipal', 'validador'})
                    if t.get('group_id') != 4 or t.get('state_id') != 8:
                        raise ValueError('Només es pot tancar una incidència pretancada.')
                    reason = field(item, 'closure_reason', 2000, True)
                    files = item.get('files') or []
                    if not isinstance(files, list) or len(files) > 4:
                        raise ValueError('Pots adjuntar fins a quatre fitxers.')
                    article = {'subject': 'Tancament municipal validat',
                               'body': 'Validació i motiu de tancament: ' + reason,
                               'type': 'note', 'internal': True}
                    if files:
                        article['attachments'] = [document_attachment(file) for file in files]
                    request_zammad('PUT', f'tickets/{ticket_id}', {'state': 'closed', 'article': article})
                    stamp = store.now()
                    store.save_meta(ticket_id, {'closure_reason': reason, 'closed_by': who['name'],
                                                 'closed_position': who['position'], 'closed_at': stamp})
                    store.add_event(ticket_id, 'Tancament', who['name'], reason)
                    return self.send_json(200, {'status': 'tancada'})
                if action == 'return':
                    who = actor(item, {'municipal', 'validador'})
                    if t.get('group_id') != 4 or t.get('state_id') != 8:
                        raise ValueError('Només es pot retornar una incidència pendent de validació.')
                    reason = field(item, 'return_reason', 2000, True)
                    assignee_id = int(current.get('assignee_id') or 4)
                    if assignee_id not in ASSIGNEES:
                        assignee_id = 4
                    request_zammad('PUT', f'tickets/{ticket_id}', {
                        'group': 'Brigada', 'owner_id': assignee_id, 'state': 'En execució',
                        'article': {'subject': 'Retorn a brigada', 'body': reason,
                                    'type': 'note', 'internal': True},
                    })
                    store.save_meta(ticket_id, {'return_reason': reason, 'work_done': '',
                                                 'preclosed_by': '', 'preclosed_position': '',
                                                 'preclosed_at': ''})
                    store.add_event(ticket_id, 'Retorn', who['name'], reason)
                    store.add_notification(ticket_id, 'WhatsApp', ASSIGNEES[assignee_id],
                                           'Correcció pendent', f'Incidència #{t["number"]} retornada: {reason}')
                    return self.send_json(200, {'status': 'retornada'})
                who = actor(item, {'municipal', 'validador'})
                reason = field(item, 'reason', 500, True)
                if len(reason) < 3:
                    raise ValueError('Indica per què aquest cas requereix una NC formal.')
                existing = store.get_nc(ticket_id)
                if existing:
                    return self.send_json(200, {'status': 'ja_vinculada', 'reference': f'NC-DEMO-{existing["id"]:04d}'})
                cause = field(item, 'cause', 1000)
                nc = store.create_nc(ticket_id, reason, cause, who['name'])
                reference = f'NC-DEMO-{nc["id"]:04d}'
                request_zammad('POST', 'ticket_articles', {
                    'ticket_id': ticket_id, 'subject': 'Derivació a no conformitat de prova',
                    'body': f'Qualiteasy demo: {reference}. Motiu: {reason}. La NC és un registre local de la prova, no una NC del sistema de producció.',
                    'content_type': 'text/plain', 'type': 'note', 'internal': True,
                })
                request_zammad('POST', 'tags/add', {'item': NC_LINKED_TAG, 'object': 'Ticket', 'o_id': ticket_id})
                store.add_event(ticket_id, 'Derivació a NC', who['name'], f'{reference}: {reason}')
                return self.send_json(201, {'status': 'vinculada', 'reference': reference})
            except PermissionError as exc:
                return self.send_json(403, {'error': str(exc)})
            except LookupError:
                return self.send_json(404, {'error': 'Incidència no trobada.'})
            except (ValueError, KeyError, TypeError) as exc:
                return self.send_json(400, {'error': str(exc) or 'Revisa les dades.'})
            except (OSError, sqlite3.Error) as exc:
                print('Workflow error:', type(exc).__name__, getattr(exc, 'code', ''), flush=True)
                return self.send_json(502, {'error': 'No s’ha pogut completar l’acció. Revisa l’estat abans de repetir-la.'})
        return super().do_POST()


if __name__ == '__main__':
    store.initialize()
    print(f'Qualiteasy demo: http://127.0.0.1:{intake.PORT}/demo', flush=True)
    ThreadingHTTPServer(('127.0.0.1', intake.PORT), Handler).serve_forever()
