#!/usr/bin/env python3
"""Local Alella intake PoC; never exposes the Zammad token to the browser."""
import base64
import json
import mimetypes
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOKEN_FILE = ROOT.parent / '.zammad-api-token'
ZAMMAD = os.environ.get('ZAMMAD_URL', 'http://127.0.0.1:8081').rstrip('/')
ICGC = 'https://eines.icgc.cat/geocodificador'
PORT = int(os.environ.get('QE_INTAKE_PORT', '8083'))
CSRF = secrets.token_urlsafe(32)
ALELLA = '080039'
MAX_PHOTO = 8 * 1024 * 1024


def zammad(method, path, data):
    token = TOKEN_FILE.read_text().strip()
    req = urllib.request.Request(
        ZAMMAD + '/api/v1/' + path,
        data=json.dumps(data).encode() if data is not None else None,
        method=method,
        headers={
            'Authorization': 'Token token=' + token,
            'Content-Type': 'application/json',
            'X-Zammad-Suppress-Notifications': 'true',
            'From': '4',  # fictitious brigade user, local PoC only
        },
    )
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=30) as response:
        return json.load(response)


def geocode(path, params):
    url = ICGC + '/' + path + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'Qualiteasy-Alella-PoC/1.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.load(response)
    result = []
    for feature in data.get('features', []):
        p = feature.get('properties') or {}
        if str(p.get('id_municipi')) != ALELLA:
            continue
        coords = feature.get('geometry', {}).get('coordinates') or []
        result.append({'label': p.get('etiqueta') or p.get('nom') or '',
                       'lon': coords[0] if len(coords) > 1 else None,
                       'lat': coords[1] if len(coords) > 1 else None})
    return result


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path)
        if path.path in ('/', '/app.js', '/style.css'):
            filename = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}[path.path]
            body = (ROOT / filename).read_bytes()
            if filename == 'index.html':
                body = body.replace(b'__CSRF__', CSRF.encode())
            self.send_response(200)
            self.send_header('Content-Type', mimetypes.guess_type(filename)[0] + '; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' blob: data:; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(body)
            return
        if path.path == '/api/streets':
            q = urllib.parse.parse_qs(path.query).get('q', [''])[0].strip()
            if len(q) < 3 or len(q) > 100:
                return self.send_json(200, [])
            try:
                return self.send_json(200, geocode('autocompletar', {'text': q + ', Alella', 'size': 8}))
            except (OSError, ValueError) as e:
                return self.send_json(502, {'error': 'El servei de carrers no respon.'})
        if path.path == '/api/reverse':
            try:
                p = urllib.parse.parse_qs(path.query)
                lat, lon = float(p['lat'][0]), float(p['lon'][0])
                if not (41.45 <= lat <= 41.53 and 2.25 <= lon <= 2.35):
                    return self.send_json(400, {'error': 'La posició és fora de la zona d’Alella.'})
                return self.send_json(200, geocode('invers', {'lat': lat, 'lon': lon, 'layers': 'address,topo1,topo2', 'size': 5}))
            except (KeyError, ValueError, IndexError):
                return self.send_json(400, {'error': 'Coordenades incorrectes.'})
            except OSError:
                return self.send_json(502, {'error': 'El servei de carrers no respon.'})
        self.send_error(404)

    def do_POST(self):
        if self.path != '/api/incidents':
            return self.send_error(404)
        if self.headers.get('X-CSRF') != CSRF:
            return self.send_json(403, {'error': 'Sessió del formulari no vàlida.'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.send_json(415, {'error': 'Format no acceptat.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 12 * 1024 * 1024:
                return self.send_json(413, {'error': 'La foto és massa gran (màxim 8 MB).'})
            item = json.loads(self.rfile.read(length))
            what = str(item.get('what', '')).strip()
            where = str(item.get('where', '')).strip()
            photo = item.get('photo') or {}
            if not (5 <= len(what) <= 2000 and 3 <= len(where) <= 200):
                return self.send_json(400, {'error': 'Indica què passa i on passa.'})
            mime = str(photo.get('content_type', ''))
            if mime not in ('image/jpeg', 'image/png', 'image/webp'):
                return self.send_json(400, {'error': 'Cal una foto JPEG, PNG o WebP.'})
            raw = base64.b64decode(photo.get('data', ''), validate=True)
            if not 0 < len(raw) <= MAX_PHOTO:
                return self.send_json(400, {'error': 'La foto ha de tenir un màxim de 8 MB.'})
            signatures = {'image/jpeg': raw.startswith(b'\xff\xd8\xff'),
                          'image/png': raw.startswith(b'\x89PNG\r\n\x1a\n'),
                          'image/webp': raw.startswith(b'RIFF') and raw[8:12] == b'WEBP'}
            if not signatures[mime]:
                return self.send_json(400, {'error': 'El contingut de la foto no coincideix amb el format indicat.'})
            filename = Path(str(photo.get('name', 'foto'))).name[:100]
            if not filename or filename.startswith('.'):
                filename = 'foto' + {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}[mime]
            fields = {}
            gps = item.get('gps')
            if gps:
                lat, lon = float(gps['lat']), float(gps['lon'])
                if not (41.45 <= lat <= 41.53 and 2.25 <= lon <= 2.35):
                    return self.send_json(400, {'error': 'La posició GPS és fora d’Alella.'})
                fields = {'qe_latitud': str(round(lat, 7)), 'qe_longitud': str(round(lon, 7)),
                          'qe_precisio_m': str(round(float(gps.get('accuracy', 0)))),
                          'qe_ubicacio_font': 'gps_operari'}
            else:
                fields['qe_ubicacio_font'] = 'adreca_manual'
            title = what.splitlines()[0][:100]
            body = 'Observació de brigada:\n' + what + '\n\nUbicació indicada:\n' + where
            created = zammad('POST', 'tickets', {
                'title': title, 'group': 'Recepció municipal', 'customer_id': 4,
                'state': 'Pendent de revisió municipal', 'qe_origen': 'brigada',
                'qe_ubicacio': where, **fields,
                'article': {'subject': 'Avís de l’operari', 'body': body,
                            'type': 'note', 'internal': True,
                            'attachments': [{'filename': filename, 'data': base64.b64encode(raw).decode(),
                                             'mime-type': mime}]},
            })
            return self.send_json(201, {'number': created['number'], 'id': created['id']})
        except (ValueError, KeyError, TypeError):
            return self.send_json(400, {'error': 'Revisa les dades i la foto.'})
        except (OSError, urllib.error.HTTPError) as e:
            print('Error Zammad:', type(e).__name__, getattr(e, 'code', ''), flush=True)
            return self.send_json(502, {'error': 'No s’ha pogut crear l’avís. Torna-ho a provar.'})


if __name__ == '__main__':
    print(f'Formulari Alella: http://127.0.0.1:{PORT}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
