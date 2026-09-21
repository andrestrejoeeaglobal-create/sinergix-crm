import os, re, shutil

work_dir = r'c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm'
git_repo = r'C:\Users\andre\.gemini\antigravity\brain\4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8\scratch\Sinergix-CRM\sinergix-crm'
escritorio_dir = r'c:\Users\andre\OneDrive\Escritorio'

src_index = os.path.join(work_dir, 'index.html')

sw_content = '''const CACHE_NAME = 'sinergix-crm-v49';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.json'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => {
        console.warn('[SW v49] Cache addAll warning:', err);
      });
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[SW v49] Purgando caché obsoleta:', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  
  const url = event.request.url;

  // Network-First Strategy for HTML documents & navigation requests
  if (event.request.mode === 'navigate' || url.includes('index.html') || url.endsWith('/sinergix-crm/') || url.endsWith('/')) {
    event.respondWith(
      fetch(event.request, { cache: 'no-store' })
        .then((response) => {
          if (response && response.status === 200) {
            const responseToCache = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
          }
          return response;
        })
        .catch(() => {
          return caches.match(event.request).then(res => res || caches.match('./index.html'));
        })
    );
    return;
  }

  // Handle external assets gracefully
  if (!url.startsWith(self.location.origin)) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((response) => {
        if (!response || response.status !== 200) {
          return response;
        }
        const responseToCache = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });
        return response;
      }).catch(() => {
        return caches.match('./index.html');
      });
    })
  );
});
'''

with open(src_index, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Nav grid adjustment (sm:grid-cols-5 -> sm:grid-cols-4)
content = content.replace('sm:grid-cols-5', 'sm:grid-cols-4')
print('[FIX] Updated nav grid to sm:grid-cols-4!')

# 2. Add 'hidden' class to #tab-btn-radar button
old_tab_radar = '<button id="tab-btn-radar" onclick="cambiarPestana(\'radar\')" class="'
new_tab_radar = '<button id="tab-btn-radar" onclick="cambiarPestana(\'radar\')" class="hidden '
if old_tab_radar in content and 'class="hidden' not in content.split('id="tab-btn-radar"')[1][:50]:
    content = content.replace(old_tab_radar, new_tab_radar)
    print('[FIX] Added hidden class to tab-btn-radar button!')

# 3. Ensure #vista-radar has 'hidden' class
if '<div id="vista-radar" class="' in content and 'class="hidden' not in content.split('id="vista-radar"')[1][:30]:
    content = content.replace('<div id="vista-radar" class="', '<div id="vista-radar" class="hidden ')
    print('[FIX] Ensured vista-radar container is hidden!')

# 4. Update cambiarPestana active tabs list & remove radar tab trigger
old_pestanas = "const pestanas = ['briefing', 'agenda', 'cartera', 'radar', 'simulador'];"
new_pestanas = "const pestanas = ['briefing', 'agenda', 'cartera', 'simulador'];"
content = content.replace(old_pestanas, new_pestanas)

old_radar_trigger = "} else if (target === 'radar' && typeof cargarRadarYBono === 'function') {\n        cargarRadarYBono();\n      }"
if old_radar_trigger in content:
    content = content.replace(old_radar_trigger, "/* else if (target === 'radar') { ... } */")
    print('[FIX] Removed radar tab trigger from cambiarPestana!')

# 5. Add null checks in cargarRadarYBono
new_cargar_radar_y_bono = '''    async function cargarRadarYBono() {
      try {
        const resBono = await apiFetch('/api/reports/bono-retiro');
        if (resBono.ok) {
          const b = await resBono.json();
          const elTxtBono = document.getElementById('txt-bono-personal');
          const elBarBono = document.getElementById('bar-bono-personal');
          const elBadgeBono = document.getElementById('bono-faltantes-badge');
          if (elTxtBono) elTxtBono.innerText = (b.avance_personal || 0) + ' / 50';
          if (elBarBono) elBarBono.style.width = (b.porcentaje_personal || 0) + '%';
          if (elBadgeBono) elBadgeBono.innerText = 'Faltan ' + (b.faltantes || 50);

          const list = document.getElementById('bono-lideres-list');
          if (list) {
            list.innerHTML = '';
            if (!b.lideres_directos || b.lideres_directos.length === 0) {
              list.innerHTML = `<p class="text-xs text-slate-400 dark:text-slate-500 font-medium">A la espera de registros para generar analítica.</p>`;
            } else {
              b.lideres_directos.forEach(l => {
                const item = document.createElement('div');
                item.innerHTML = `
                  <div class="flex justify-between text-xs font-bold">
                    <span class="text-slate-600 dark:text-slate-400">${l.nombre}</span>
                    <span class="tabular-nums font-extrabold text-slate-800 dark:text-slate-200">${l.activos_actuales} / 50</span>
                  </div>
                  <div class="w-full bg-slate-100 dark:bg-slate-700 h-2.5 rounded-full overflow-hidden mt-1">
                    <div class="bg-indigo-500 h-full rounded-full" style="width: ${l.porcentaje}%;"></div>
                  </div>
                `;
                list.appendChild(item);
              });
            }
          }
        }

        const resRadar = await apiFetch('/api/reports/radar-multiplicadores');
        if (resRadar.ok) {
          const r = await resRadar.json();
          const list = document.getElementById('radar-lideres-list');
          if (list) {
            list.innerHTML = '';
            if (!r.lideres_emergentes || r.lideres_emergentes.length === 0) {
              list.innerHTML = `<div class="p-6 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/60 text-slate-400 dark:text-slate-500 font-medium text-xs text-center">A la espera de registros para generar analítica de multiplicadores.</div>`;
            } else {
              r.lideres_emergentes.forEach(l => {
                const card = document.createElement('div');
                card.className = 'p-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/60 flex items-center justify-between shadow-clinical-sm';
                card.innerHTML = `
                  <div>
                    <h4 class="font-bold text-slate-900 dark:text-white text-sm">${l.nombre} <span class="text-xs text-slate-400 font-normal">(Nivel ${l.nivel})</span></h4>
                    <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">${l.reclutas_ultimos_14_dias} reclutas en 14 días</p>
                  </div>
                  <span class="px-3 py-1 rounded-xl text-xs font-black bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                    ${l.insignia}
                  </span>
                `;
                list.appendChild(card);
              });
            }
          }
        }
      } catch (err) {
        console.warn('Radar error:', err);
      }
    }'''

old_cargar_radar_pattern = r'async function cargarRadarYBono\(\) \{.*?\n    \}'
content = re.sub(old_cargar_radar_pattern, new_cargar_radar_y_bono, content, flags=re.DOTALL)
print('[FIX] Added null-checks to cargarRadarYBono function!')

# 6. Update SW version from v48 to v49
content = content.replace('sw.js?v=48', 'sw.js?v=49')
print('[FIX] Updated Service Worker reference to sw.js?v=49!')

# Save index.html and static/index.html
with open(src_index, 'w', encoding='utf-8') as f:
    f.write(content)

src_static_index = os.path.join(work_dir, 'static', 'index.html')
os.makedirs(os.path.dirname(src_static_index), exist_ok=True)
with open(src_static_index, 'w', encoding='utf-8') as f:
    f.write(content)

# Save sw.js and static/sw.js
with open(os.path.join(work_dir, 'sw.js'), 'w', encoding='utf-8') as f:
    f.write(sw_content)
with open(os.path.join(work_dir, 'static', 'sw.js'), 'w', encoding='utf-8') as f:
    f.write(sw_content)

# Sync to git_repo
os.makedirs(os.path.join(git_repo, 'static'), exist_ok=True)
shutil.copy2(src_index, os.path.join(git_repo, 'index.html'))
shutil.copy2(src_index, os.path.join(git_repo, 'static', 'index.html'))
with open(os.path.join(git_repo, 'sw.js'), 'w', encoding='utf-8') as f:
    f.write(sw_content)
with open(os.path.join(git_repo, 'static', 'sw.js'), 'w', encoding='utf-8') as f:
    f.write(sw_content)

# Sync to escritorio_dir
os.makedirs(os.path.join(escritorio_dir, 'static'), exist_ok=True)
shutil.copy2(src_index, os.path.join(escritorio_dir, 'index.html'))
shutil.copy2(src_index, os.path.join(escritorio_dir, 'static', 'index.html'))
with open(os.path.join(escritorio_dir, 'sw.js'), 'w', encoding='utf-8') as f:
    f.write(sw_content)

print('[SUCCESS] Radar MLM tab successfully decoupled and hidden across all target directories!')
