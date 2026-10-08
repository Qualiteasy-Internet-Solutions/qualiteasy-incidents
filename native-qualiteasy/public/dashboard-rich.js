(() => {
  'use strict';
  const demoGroups = ['Recepció municipal', 'Brigada', 'Validació municipal'];
  const origins = { brigada: 'Operari de brigada', ajuntament: 'Ajuntament', telefon: 'Trucada rebuda', correu: 'Correu rebut', whatsapp: 'WhatsApp', web_municipal: 'Web municipal', intern: 'Gestió interna', altres: 'Altres' };
  const title = value => String(value || '').replace(/^\[MOSTRA ALELLA · NC \d+\]\s*/, '').replace(/^\[DEMO\]\s*/, '');
  const isClosed = name => /^(closed|tancat|tancada)$/i.test(name || '');
  const displayStage = name => ({ closed: 'Tancada', new: 'Nova', open: 'En curs' })[String(name || '').toLowerCase()] || name || 'Pendent';
  const stageClass = name => {
    const text = (name || '').toLowerCase();
    if (text.includes('revisió') || text === 'new' || text === 'nou') return 'review';
    if (text.includes('execució') || text === 'open' || text === 'obert') return 'work';
    if (text.includes('validació')) return 'validation';
    if (isClosed(text)) return 'closed';
    return 'other';
  };
  function node(tag, className, value) {
    const result = document.createElement(tag);
    if (className) result.className = className;
    if (value !== undefined) result.textContent = value;
    return result;
  }
  function label(name) {
    const key = stageClass(name);
    return node('span', `qe-stage qe-stage-${key}`, displayStage(name));
  }
  function info(name, value) {
    const box = node('div', 'qe-detail-info');
    box.append(node('small', '', name), node('strong', '', value || 'Pendent'));
    return box;
  }
  function mount(host, helpers) {
    const shell = node('section', 'qe-dashboard');
    shell.innerHTML = `
      <div class="qe-dash-hero">
        <div class="qe-dash-hero-main">
          <div class="qe-dash-eyebrow">QUALITEASY <span>·</span> ALELLA</div>
          <h1>Incidències sota control.</h1>
          <p>De l’avís inicial a la feina de la brigada, la validació i la no conformitat quan calgui.</p>
          <div class="qe-dash-actions"><a class="qe-dash-primary" href="#ticket/create">+ Nova incidència</a><a class="qe-dash-outline" href="http://127.0.0.1:8083/demo?role=municipal" target="_blank" rel="noopener noreferrer">Provar el flux per perfils ↗</a></div>
        </div>
        <div class="qe-dash-flow" aria-label="Cicle de la incidència"><div class="qe-dash-flow-label">CICLE DE RESOLUCIÓ</div><div><span>01</span> Recepció i revisió</div><div><span>02</span> Assignació a brigada</div><div><span>03</span> Execució i pretancament</div><div><span>04</span> Validació municipal</div></div>
      </div>
      <div class="qe-dash-section-title"><div><span>AVUI AL SERVEI</span><h2>Una visió de tot el treball</h2></div><a href="#ticket/view">Veure totes les incidències →</a></div>
      <div class="qe-kpis">
        <div class="qe-kpi qe-kpi-active"><span>En curs</span><b data-count="active">—</b><small>Tots els grups municipals</small></div>
        <div class="qe-kpi qe-kpi-review"><span>Pendents de revisió</span><b data-count="review">—</b><small>Ajuntament</small></div>
        <div class="qe-kpi qe-kpi-work"><span>En execució</span><b data-count="work">—</b><small>Brigada</small></div>
        <div class="qe-kpi qe-kpi-validation"><span>Pendents de validació</span><b data-count="validation">—</b><small>Tancament municipal</small></div>
      </div>
      <div class="qe-workspace">
        <section class="qe-list-panel"><div class="qe-panel-heading"><div><span>SEGUIMENT</span><h2>Incidències</h2><p>Mostres reconstruïdes de l’històric d’Alella</p></div><span class="qe-panel-count" data-visible-count>—</span></div><div class="qe-list-filters"><button type="button" class="selected" data-filter="showcase">Mostra Alella</button><button type="button" data-filter="active">En curs</button><button type="button" data-filter="all">Totes</button></div><div class="qe-case-list"><p class="qe-loading">Carregant incidències…</p></div></section>
        <section class="qe-detail-panel"><div class="qe-empty">Selecciona una incidència per veure’n la fotografia, la ubicació i el seguiment.</div></section>
      </div>
      <p class="qe-dashboard-footnote">Prototip amb casos basats en registres reals. Les fotografies i les fases reconstruïdes són de demostració.</p>`;
    host.prepend(shell);
    let records = [], chosen = 0, view = 'showcase', sequence = 0;
    const list = shell.querySelector('.qe-case-list');
    const detail = shell.querySelector('.qe-detail-panel');
    const visible = () => {
      let result = records.slice();
      if (view === 'showcase') result = result.filter(item => item.title.startsWith('[MOSTRA ALELLA'));
      if (view === 'active') result = result.filter(item => !isClosed(item.stage));
      result.sort((a, b) => view === 'showcase' ? a.id - b.id : b.id - a.id);
      return result;
    };
    const showList = () => {
      const rows = visible();
      shell.querySelector('[data-visible-count]').textContent = String(rows.length);
      list.replaceChildren();
      if (!rows.length) { list.append(node('p', 'qe-loading', 'No hi ha incidències en aquesta vista.')); return; }
      for (const item of rows) {
        const button = node('button', `qe-case${item.id === chosen ? ' selected' : ''}`);
        button.type = 'button';
        const image = node('span', 'qe-case-image', '●');
        if (item.thumb) { const photo = node('img'); photo.src = item.thumb; photo.alt = ''; image.replaceChildren(photo); }
        const copy = node('span', 'qe-case-copy');
        const meta = node('span', 'qe-case-meta');
        meta.append(node('span', '', `#${item.number}`), label(item.stage));
        copy.append(meta, node('strong', 'qe-case-title', title(item.title)), node('span', 'qe-case-location', item.qe_ubicacio || 'Ubicació pendent'));
        button.append(image, copy);
        button.addEventListener('click', () => { chosen = item.id; showList(); showDetail(item); });
        list.append(button);
      }
    };
    const loadPhotos = async item => {
      if (Array.isArray(item.photos)) return item.photos;
      const articles = await helpers.json(`/ticket_articles/by_ticket/${item.id}`);
      item.photos = articles.flatMap(article => (article.attachments || []).filter(file => /\.(png|jpe?g|webp|gif)$/i.test(file.filename || '')).map(file => ({
        name: file.filename,
        url: `/api/v1/ticket_attachment/${item.id}/${article.id}/${file.id}?view=inline`,
      })));
      item.thumb = item.photos[0]?.url || '';
      return item.photos;
    };
    const showDetail = async item => {
      const call = ++sequence;
      detail.replaceChildren(node('p', 'qe-loading', 'Carregant evidències…'));
      let photos = [];
      try { photos = await loadPhotos(item); } catch { /* The case remains usable without its media. */ }
      if (call !== sequence || !detail.isConnected) return;
      const head = node('div', 'qe-detail-head');
      const heading = node('div');
      heading.append(node('span', 'qe-detail-eyebrow', `INCIDÈNCIA #${item.number}`), node('h2', '', title(item.title)));
      const historical = item.title.match(/NC (\d+)/);
      heading.append(node('p', '', historical ? `Basada en la NC històrica ${historical[1]} · Flux de demostració` : 'Seguiment municipal'));
      head.append(heading, label(item.stage));
      detail.replaceChildren(head);
      const photoBox = node('div', 'qe-detail-photo');
      if (photos.length) {
        const img = node('img'); img.src = photos[0].url; img.alt = `Fotografia de la incidència ${item.number}`;
        img.addEventListener('click', () => {
          const dialog = node('dialog', 'qe-photo-dialog');
          const close = node('button', '', 'Tanca ×'); close.type = 'button'; close.addEventListener('click', () => dialog.close());
          const full = node('img'); full.src = photos[0].url; full.alt = img.alt;
          dialog.append(close, full); document.body.append(dialog); dialog.showModal(); dialog.addEventListener('close', () => dialog.remove());
        });
        photoBox.append(img);
        if (/sintetica/i.test(photos[0].name)) photoBox.append(node('span', 'qe-photo-label', 'IMATGE SINTÈTICA · DEMO'));
      } else photoBox.append(node('div', 'qe-no-photo', 'Sense fotografia adjunta'));
      detail.append(photoBox);
      const body = node('div', 'qe-detail-content');
      const grid = node('div', 'qe-detail-info-grid');
      grid.append(info('Canal d’entrada', origins[item.qe_origen] || item.qe_origen), info('Ubicació', item.qe_ubicacio), info('Àrea responsable', item.group_name), info('Fase', displayStage(item.stage)));
      body.append(grid);
      const location = node('div', 'qe-detail-location');
      const mapTitle = node('div', 'qe-map-heading');
      mapTitle.append(node('h3', '', 'Ubicació'));
      const lat = Number(item.qe_latitud), lon = Number(item.qe_longitud);
      const valid = Number.isFinite(lat) && Number.isFinite(lon) && lat > 41.45 && lat < 41.53 && lon > 2.25 && lon < 2.35;
      if (valid) {
        const link = node('a', '', 'Obre el mapa ↗');
        link.href = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=17/${lat}/${lon}`;
        link.target = '_blank'; link.rel = 'noopener noreferrer'; mapTitle.append(link);
      }
      location.append(mapTitle);
      if (valid) {
        const canvas = node('div', 'qe-map');
        location.append(canvas, node('p', 'qe-map-hint', 'Punt aproximat del carrer; l’Ajuntament ha de verificar la ubicació exacta.'));
        requestAnimationFrame(() => helpers.map(canvas, lat, lon));
      } else location.append(node('div', 'qe-map-unknown', 'Ubicació pendent de validació per part de l’Ajuntament.'));
      body.append(location);
      const actions = node('div', 'qe-detail-actions');
      const open = node('a', 'qe-dash-primary', 'Obre la fitxa operativa →'); open.href = `#ticket/zoom/${item.id}`;
      const workflow = node('a', 'qe-dash-text', 'Assignació · brigada · NC ↗');
      workflow.href = `http://127.0.0.1:8083/demo?role=municipal&incident=${item.id}`;
      workflow.target = '_blank'; workflow.rel = 'noopener noreferrer';
      actions.append(open, workflow); body.append(actions);
      detail.append(body);
      showList();
    };
    for (const button of shell.querySelectorAll('[data-filter]')) button.addEventListener('click', () => {
      view = button.dataset.filter;
      shell.querySelectorAll('[data-filter]').forEach(other => other.classList.toggle('selected', other === button));
      const rows = visible(); chosen = rows[0]?.id || 0;
      showList();
      if (rows.length) showDetail(rows[0]); else detail.replaceChildren(node('div', 'qe-empty', 'No hi ha incidències en aquesta vista.'));
    });
    Promise.all([helpers.json('/tickets?per_page=500'), helpers.json('/ticket_states'), helpers.json('/groups')]).then(([tickets, states, groups]) => {
      if (!shell.isConnected) return;
      const stateNames = Object.fromEntries(states.map(value => [value.id, value.name]));
      const groupNames = Object.fromEntries(groups.map(value => [value.id, value.name]));
      records = tickets.filter(value => demoGroups.includes(groupNames[value.group_id])).map(value => ({ ...value, stage: stateNames[value.state_id] || 'Pendent', group_name: groupNames[value.group_id] || '—' }));
      const active = records.filter(value => !isClosed(value.stage));
      const counts = { active: active.length, review: active.filter(value => stageClass(value.stage) === 'review').length, work: active.filter(value => stageClass(value.stage) === 'work').length, validation: active.filter(value => stageClass(value.stage) === 'validation').length };
      for (const [key, number] of Object.entries(counts)) shell.querySelector(`[data-count="${key}"]`).textContent = String(number);
      const rows = visible(); chosen = rows[0]?.id || 0;
      showList();
      if (rows.length) showDetail(rows[0]);
      Promise.allSettled(records.filter(item => item.title.startsWith('[MOSTRA ALELLA')).map(async item => {
        await loadPhotos(item);
        if (shell.isConnected) showList();
      }));
    }).catch(() => { list.replaceChildren(node('p', 'qe-loading', 'No s’han pogut carregar les incidències.')); });
  }
  window.QualiteasyDashboard = { mount };
})();
