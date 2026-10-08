(() => {
  'use strict';
  const api = '/api/v1';
  const $ = (s, root = document) => root.querySelector(s);
  const make = (tag, className, text) => { const e = document.createElement(tag); if (className) e.className = className; if (text) e.textContent = text; return e; };
  const encode = encodeURIComponent;
  let currentTicket = 0;
  async function json(path) { const r = await fetch(api + path, { credentials: 'same-origin' }); if (!r.ok) throw Error(String(r.status)); return r.json(); }

  function login() {
    const root = $('.login .fullscreen-center');
    if (!root || $('.qe-login-brand', root)) return;
    const brand = make('section', 'qe-login-brand');
    brand.innerHTML = '<div class="qe-login-wordmark"><img src="/assets/qualiteasy/qualiteasy-logo.png" alt="Qualiteasy"></div><div><div class="qe-login-eyebrow">Qualitat i servei públic</div><h1>Incidències que es resolen.</h1><p>Una visió clara de cada avís, de la brigada fins a la validació municipal.</p></div><small>QUALITEASY · ÀREA D’INCIDÈNCIES</small>';
    root.prepend(brand);
    const body = $('.fullscreen-body', root);
    const hero = $('.hero-unit', body);
    if (hero) { hero.prepend(make('p', 'qe-login-form-intro', 'Accedeix al teu espai de treball')); hero.prepend(make('h2', 'qe-login-form-title', 'Benvingut/da')); }
    const username = $('.login label[for="username"]'); if (username) username.textContent = 'Usuari o correu electrònic';
    const password = $('.login label[for="password"]'); if (password) password.textContent = 'Contrasenya';
    const submit = $('.login #login button[type="submit"]'); if (submit) submit.textContent = 'Entra';
    const remember = $('.login .checkbox-replacement .label-text'); if (remember) remember.textContent = 'Recorda’m';
    const forgot = $('.login a[href="#password_reset"]'); if (forgot) forgot.textContent = 'Has oblidat la contrasenya?';
  }

  function dashboard() {
    if (location.hash !== '#dashboard') return;
    const host = $('.dashboard.main');
    if (!host || $('.qe-dashboard', host) || !window.QualiteasyDashboard) return;
    window.QualiteasyDashboard.mount(host, { json, map, make });
  }

  function brandNavigation() {
    const logo = $('.navigation .search .logo');
    if (!logo || logo.dataset.qeBrand) return;
    logo.dataset.qeBrand = '1';
    logo.classList.remove('js-toggleNotifications');
    logo.querySelector('.icon-logo')?.remove();
    logo.insertAdjacentHTML('afterbegin', '<img class="qe-brand-original" src="/assets/qualiteasy/qualiteasy-logo.png" alt="Qualiteasy">');
    logo.title = 'Torna al panell d’incidències';
    logo.setAttribute('role', 'link');
    logo.setAttribute('tabindex', '0');
    logo.setAttribute('aria-label', 'Qualiteasy: panell d’incidències');
    logo.addEventListener('click', event => { event.preventDefault(); event.stopPropagation(); location.hash = '#dashboard'; });
    logo.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); location.hash = '#dashboard'; } });
  }

  function map(container, lat, lon) {
    const zoom = 16, size = 256, scale = 2 ** zoom;
    const clamped = Math.max(-85, Math.min(85, lat));
    const x = (lon + 180) / 360 * scale;
    const y = (1 - Math.asinh(Math.tan(clamped * Math.PI / 180)) / Math.PI) / 2 * scale;
    const width = container.clientWidth || 700, height = 260;
    for (let dx = -2; dx <= 2; dx++) for (let dy = -1; dy <= 1; dy++) {
      const tileX = Math.floor(x) + dx, tileY = Math.floor(y) + dy;
      if (tileY < 0 || tileY >= scale) continue;
      const img = make('img');
      img.src = `https://tile.openstreetmap.org/${zoom}/${(tileX + scale) % scale}/${tileY}.png`;
      img.alt = '';
      img.loading = 'lazy';
      img.style.left = `${width / 2 + (tileX - x) * size}px`;
      img.style.top = `${height / 2 + (tileY - y) * size}px`;
      container.append(img);
    }
    container.append(make('span', 'qe-map-pin'));
    const credit = make('a', 'qe-map-credit', '© OpenStreetMap');
    credit.href = 'https://www.openstreetmap.org/copyright'; credit.target = '_blank'; credit.rel = 'noopener';
    container.append(credit);
  }

  async function ticket() {
    const id = Number((location.hash.match(/^#ticket\/zoom\/(\d+)/) || [])[1]);
    if (!id || id === currentTicket) return;
    const host = $('.ticketZoom');
    if (!host) return;
    currentTicket = id;
    $('.qe-evidence', host)?.remove();
    try {
      const [data, articles] = await Promise.all([json(`/tickets/${id}`), json(`/ticket_articles/by_ticket/${id}`)]);
      if (currentTicket !== id) return;
      if (!host.isConnected) { currentTicket = 0; return; }
      const evidence = make('section', 'qe-evidence');
      const photos = articles.flatMap(a => (a.attachments || []).filter(f => /^image\/(jpeg|png|webp|gif)$/i.test(f.preferences?.ContentType || f.content_type || '') || /\.(png|jpe?g|webp|gif)$/i.test(f.filename || '')).map(f => ({ article: a.id, file: f })));
      if (photos.length) {
        evidence.append(make('h2', '', 'Fotografies de la incidència'));
        const grid = make('div', 'qe-photos');
        for (const { article, file } of photos) {
          const src = `${api}/ticket_attachment/${id}/${article}/${file.id}?view=inline`;
          const button = make('button'); button.type = 'button'; button.setAttribute('aria-label', `Ampliar ${file.filename}`);
          const img = make('img'); img.src = src; img.alt = file.filename || 'Fotografia adjunta'; img.loading = 'lazy';
          button.append(img, make('small', '', file.filename || 'Fotografia'));
          button.addEventListener('click', () => {
            const dialog = make('dialog', 'qe-photo-dialog');
            const close = make('button', '', 'Tanca ×'); close.type = 'button'; close.onclick = () => dialog.close();
            const full = make('img'); full.src = src; full.alt = img.alt;
            dialog.append(close, full); document.body.append(dialog); dialog.showModal(); dialog.addEventListener('close', () => dialog.remove());
          });
          grid.append(button);
        }
        evidence.append(grid);
        if (photos.some(p => /sintetica/i.test(p.file.filename || ''))) evidence.append(make('p', 'qe-caption', 'Fotografies sintètiques per a la demostració. No són els adjunts originals d’Alella.'));
      }
      const lat = Number(data.qe_latitud), lon = Number(data.qe_longitud);
      if (Number.isFinite(lat) && Number.isFinite(lon) && lat && lon) {
        evidence.append(make('h2', '', 'Ubicació de la incidència'));
        if (data.qe_ubicacio) evidence.append(make('p', 'qe-caption', data.qe_ubicacio));
        const canvas = make('div', 'qe-map'); evidence.append(canvas);
        requestAnimationFrame(() => map(canvas, lat, lon));
        evidence.append(make('p', 'qe-caption', 'Punt aproximat de demostració. Cal confirmar el carrer i la posició sobre el terreny.'));
      }
      if (evidence.childNodes.length) {
        const header = $('.ticketZoom-header', host);
        if (header) header.after(evidence); else currentTicket = 0;
      }
    } catch (err) { currentTicket = 0; console.warn('Qualiteasy evidence unavailable', err); }
  }

  function creation() {
    if (window.App?.TicketCreate?.prototype?.articleSenderTypeMap?.['phone-in']) {
      const intake = App.TicketCreate.prototype.articleSenderTypeMap['phone-in'];
      intake.article = 'note'; intake.sender = 'Agent'; intake.title = 'Incidència';
    }
    if (!location.hash.startsWith('#ticket/create')) return;
    const h = $('.newTicket .page-header h1'); if (h) h.textContent = 'Nova incidència';
    const submit = $('.newTicket .js-submit'); if (submit) submit.textContent = 'Crea la incidència';
  }

  let timer;
  function refresh() { clearTimeout(timer); timer = setTimeout(() => { login(); brandNavigation(); dashboard(); ticket(); creation(); }, 120); }
  document.addEventListener('DOMContentLoaded', () => { refresh(); new MutationObserver(refresh).observe(document.body, { childList: true, subtree: true }); window.addEventListener('hashchange', () => { currentTicket = 0; refresh(); }); });
})();
