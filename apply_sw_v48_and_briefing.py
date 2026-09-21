import os, re, shutil

work_dir = r'c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm'
git_repo = r'C:\Users\andre\.gemini\antigravity\brain\4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8\scratch\Sinergix-CRM\sinergix-crm'
escritorio_dir = r'c:\Users\andre\OneDrive\Escritorio'

src_index = os.path.join(work_dir, 'index.html')

sw_content = '''const CACHE_NAME = 'sinergix-crm-v48';
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
        console.warn('[SW v48] Cache addAll warning:', err);
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
            console.log('[SW v48] Purgando caché obsoleta:', cache);
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

# 1. Update mockStandAloneApiResponse for /api/sherpa/briefing if missing or refine
mock_briefing_code = '''      if (url.includes('/api/sherpa/briefing')) {
        const activeUser = (typeof obtenerSherpaIdActivo === 'function') ? obtenerSherpaIdActivo() : (localStorage.getItem('sherpa_id_activo') || 'sherpa_edgar');
        const userLeads = await CortexStorageEngine.getLeadsForSherpa(activeUser);
        const sherpaNom = localStorage.getItem('sherpa_nombre') || (activeUser === 'sherpa_edgar' ? 'Edgar' : activeUser);

        let resumen = '';
        let pendientes = userLeads.filter(l => !l.respondio && !l.is_cancelled).length;

        if (userLeads.length === 0) {
          resumen = `¡Buenos días, ${sherpaNom}! ☀️\\n\\nNo tienes seguimientos ni tareas pendientes para hoy. Tu base de datos está limpia y lista para la captura de leads.`;
        } else {
          resumen = `¡Buenos días, ${sherpaNom}! ☀️\\n\\nTienes ${userLeads.length} prospecto(s) en tu cartera (${pendientes} pendiente(s) por responder encuesta de 3 preguntas).`;
        }

        const acciones = [];
        if (userLeads.length > 0) {
          const sinEncuesta = userLeads.filter(l => !l.respondio && !l.is_cancelled).slice(0, 4);
          sinEncuesta.forEach(l => {
            acciones.push({
              lead_id: l.id || l._id,
              nombre: l.nombre,
              tipo: 'pendiente',
              mensaje: `Enviar invitación a la encuesta de 3 preguntas a ${l.nombre} (${l.telefono}).`,
              boton_label: 'Enviar WhatsApp'
            });
          });
        }

        return new Response(JSON.stringify({
          ok: true,
          fecha: new Date().toLocaleDateString('es-MX', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }),
          resumen_texto: resumen,
          contactos_seguimiento: pendientes,
          sprints_por_vencer: 0,
          acciones_prioritarias: acciones
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (url.startsWith('/api/leads')) {'''

if 'if (url.includes(\'/api/sherpa/briefing\')) {' not in content:
    content = content.replace('if (url.startsWith(\'/api/leads\')) {', mock_briefing_code)
    print('[FIX] Added mockStandAloneApiResponse handler for /api/sherpa/briefing!')

# 2. Update cargarBriefingMatutino function in index.html
new_cargar_briefing = '''    async function cargarBriefingMatutino() {
      try {
        const activeUser = (typeof obtenerSherpaIdActivo === 'function') ? obtenerSherpaIdActivo() : (localStorage.getItem('sherpa_id_activo') || 'sherpa_edgar');
        const sherpaNom = localStorage.getItem('sherpa_nombre') || (activeUser === 'sherpa_edgar' ? 'Edgar' : activeUser);
        const elFecha = document.getElementById('briefing-fecha-txt');
        const elResumen = document.getElementById('briefing-resumen-box');
        const elKpiPend = document.getElementById('briefing-kpi-pendientes');
        const elKpiCrit = document.getElementById('briefing-kpi-criticos');

        const fechaStr = new Date().toLocaleDateString('es-MX', { weekday: 'short', month: 'short', day: 'numeric' });
        if (elFecha) elFecha.innerText = 'Resumen de hoy (' + fechaStr + ')';

        let data = null;
        try {
          const res = await apiFetch('/api/sherpa/briefing');
          if (res && res.ok) {
            data = await res.json();
          }
        } catch (e) {
          console.warn('Briefing API fetch warning:', e);
        }

        const userLeads = (typeof CortexStorageEngine !== 'undefined' && CortexStorageEngine.getLeadsForSherpa)
          ? await CortexStorageEngine.getLeadsForSherpa(activeUser)
          : [];

        let resumenTexto = data && data.resumen_texto ? data.resumen_texto : '';
        if (!resumenTexto) {
          if (userLeads.length === 0) {
            resumenTexto = `¡Buenos días, ${sherpaNom}! ☀️\\n\\nNo tienes seguimientos ni tareas pendientes para hoy. Tu base de datos está limpia y lista para la captura de leads.`;
          } else {
            const pendCount = userLeads.filter(l => !l.respondio && !l.is_cancelled).length;
            resumenTexto = `¡Buenos días, ${sherpaNom}! ☀️\\n\\nTienes ${userLeads.length} prospecto(s) en tu cartera (${pendCount} pendiente(s) por responder encuesta).`;
          }
        }

        if (elResumen) elResumen.innerText = resumenTexto;
        if (elKpiPend) elKpiPend.innerText = userLeads.filter(l => !l.respondio && !l.is_cancelled).length;
        if (elKpiCrit) elKpiCrit.innerText = 0;

        if (data && data.acciones_prioritarias && data.acciones_prioritarias.length > 0) {
          const list = document.getElementById('briefing-acciones-list');
          if (list) {
            list.innerHTML = '';
            data.acciones_prioritarias.forEach(a => {
              const card = document.createElement('div');
              card.className = 'p-4 rounded-2xl border flex flex-col justify-between space-y-3 ' + (a.tipo === 'critico' ? 'bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800' : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 shadow-clinical-sm');
              card.innerHTML = `
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <span class="font-extrabold text-xs ${a.tipo === 'critico' ? 'text-amber-800 dark:text-amber-300' : 'text-slate-800 dark:text-slate-200'}">${a.nombre}</span>
                    <span class="text-[9px] px-2 py-0.5 rounded-md font-black uppercase ${a.tipo === 'critico' ? 'bg-amber-200 text-amber-900' : 'bg-slate-200 text-slate-800'}">${a.tipo}</span>
                  </div>
                  <p class="text-xs text-slate-600 dark:text-slate-300 font-medium leading-relaxed">${a.mensaje}</p>
                </div>
                <button onclick="abrirWaLinkDirecto('${a.lead_id}')" class="touch-target px-3.5 py-2 bg-ea-blue text-white rounded-xl text-xs font-bold self-start hover:bg-blue-700 transition shadow-clinical-sm">
                  <i class="fa-brands fa-whatsapp mr-1.5"></i> ${a.boton_label}
                </button>
              `;
              list.appendChild(card);
            });
          }
        } else {
          renderAccionesPrioritarias();
        }
      } catch (err) {
        console.warn('Briefing main catch:', err);
        renderAccionesPrioritarias();
      }
    }'''

old_cargar_briefing_pattern = r'async function cargarBriefingMatutino\(\) \{.*?\n    \}'
content = re.sub(old_cargar_briefing_pattern, new_cargar_briefing, content, flags=re.DOTALL)
print('[FIX] Updated cargarBriefingMatutino function in index.html!')

# 3. Update SW registration versions to v48
content = content.replace('sw.js?v=47', 'sw.js?v=48')

# Write back to src_index
with open(src_index, 'w', encoding='utf-8') as f:
    f.write(content)

# Copy index.html to static/index.html
src_static_index = os.path.join(work_dir, 'static', 'index.html')
os.makedirs(os.path.dirname(src_static_index), exist_ok=True)
with open(src_static_index, 'w', encoding='utf-8') as f:
    f.write(content)

# Save sw.js & static/sw.js
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

print('[SUCCESS] All files updated and synchronized across all target directories!')
