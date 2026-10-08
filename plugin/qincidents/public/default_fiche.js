// Només els tres registres de la demostració tenen una fitxa Qualiteasy pròpia.
// El paràmetre qe_native permet obrir GLPI explícitament per editar-los.
(() => {
  const url = new URL(window.location.href);
  if (!url.pathname.endsWith('/front/ticket.form.php')) return;

  const id = url.searchParams.get('id');
  if (!['4', '5', '6'].includes(id)) return;

  if (url.searchParams.get('qe_native') === '1') {
    const expand = () => {
      const section = document.querySelector('#item-main');
      if (section && !section.classList.contains('show') && !section.classList.contains('collapsing')) {
        document.querySelector('[data-bs-target="#item-main"]')?.click();
      }
      const lat = document.querySelector('[name="qlatitud"]');
      const lon = document.querySelector('[name="qlongitud"]');
      if (lat && lon && !document.querySelector('#qe-use-gps')) {
        const button = document.createElement('button');
        button.type = 'button';
        button.id = 'qe-use-gps';
        button.className = 'btn btn-sm btn-outline-primary mt-2';
        button.textContent = 'Usar la ubicació d’aquest dispositiu';
        button.addEventListener('click', () => {
          if (!navigator.geolocation) {
            button.textContent = 'Aquest dispositiu no ofereix geolocalització';
            return;
          }
          navigator.geolocation.getCurrentPosition(({coords}) => {
            lat.value = coords.latitude.toFixed(7);
            lon.value = coords.longitude.toFixed(7);
            for (const field of [lat, lon]) {
              field.dispatchEvent(new Event('input', {bubbles: true}));
              field.dispatchEvent(new Event('change', {bubbles: true}));
            }
            button.textContent = 'Coordenades obtingudes · desa la incidència';
          }, () => { button.textContent = 'No s’ha pogut obtenir la ubicació'; },
          {enableHighAccuracy: true, timeout: 15000, maximumAge: 0});
        });
        lat.closest('.field-container')?.append(button);
      }
      for (const name of ['users_id_qverificadorid', 'users_id_qtancadorid']) {
        const select = document.querySelector(`[name="${name}"]`);
        if (!select || select.dataset.qeFiltered) continue;
        select.dataset.qeFiltered = '1';
        window.jQuery(select).on('select2:open', () => {
          const allowed = new Set(['-----', 'alella_municipal_demo', 'alella_operari_demo']);
          const filter = () => {
            const list = document.querySelector(`[id$="${select.id}-results"]`);
            list?.querySelectorAll('.select2-results__option').forEach(option => {
              if (option.getAttribute('role') === 'option') {
                option.style.display = allowed.has(option.textContent.trim()) ? '' : 'none';
              }
            });
          };
          filter();
          const observer = new MutationObserver(filter);
          const dropdown = document.querySelector('.select2-container--open .select2-results');
          if (dropdown) observer.observe(dropdown, {childList: true, subtree: true});
          window.jQuery(select).one('select2:close', () => observer.disconnect());
        });
      }
    };
    const start = () => {
      expand();
      let checks = 0;
      const timer = window.setInterval(() => {
        expand();
        if (document.querySelector('#qe-use-gps') || ++checks >= 20) window.clearInterval(timer);
      }, 250);
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true});
    else start();
    return;
  }

  window.location.replace(`/plugins/qincidents/front/fiche.php?id=${id}`);
})();
