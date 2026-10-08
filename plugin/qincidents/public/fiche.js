const map = document.querySelector('#qe-map');
if (map) {
  const lat = Number(map.dataset.lat), lon = Number(map.dataset.lon);
  const z = 16, n = 2 ** z, w = map.clientWidth, h = map.clientHeight;
  const cx = (lon + 180) / 360 * n * 256;
  const sin = Math.sin(lat * Math.PI / 180);
  const cy = (0.5 - Math.log((1 + sin) / (1 - sin)) / (4 * Math.PI)) * n * 256;
  const minX = Math.floor((cx - w / 2) / 256), maxX = Math.floor((cx + w / 2) / 256);
  const minY = Math.floor((cy - h / 2) / 256), maxY = Math.floor((cy + h / 2) / 256);
  for (let x = minX; x <= maxX; x++) for (let y = minY; y <= maxY; y++) {
    const tile = document.createElement('img');
    tile.className = 'qe-tile';
    tile.src = `https://tile.openstreetmap.org/${z}/${x}/${y}.png`;
    tile.alt = '';
    tile.style.left = `${Math.round(x * 256 - cx + w / 2)}px`;
    tile.style.top = `${Math.round(y * 256 - cy + h / 2)}px`;
    map.append(tile);
  }
  const marker = document.createElement('span'); marker.className = 'qe-marker'; map.append(marker);
  const credit = document.createElement('a'); credit.className = 'qe-credit'; credit.href = 'https://www.openstreetmap.org/copyright'; credit.target = '_blank'; credit.rel = 'noopener noreferrer'; credit.textContent = '© OpenStreetMap contributors'; map.append(credit);
}
const photoDialog = document.querySelector('#qe-photo-dialog');
document.querySelectorAll('.qe-zoom').forEach(button => button.addEventListener('click', () => {
  photoDialog.querySelector('img').src = button.dataset.photo;
  photoDialog.showModal();
}));
document.querySelector('#qe-photo-close')?.addEventListener('click', () => photoDialog.close());
document.querySelector('#qe-print')?.addEventListener('click', () => window.print());
