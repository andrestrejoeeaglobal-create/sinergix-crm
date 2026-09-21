import os, re, shutil, subprocess

work_dir = r'c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm'
git_repo = r'C:\Users\andre\.gemini\antigravity\brain\4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8\scratch\Sinergix-CRM\sinergix-crm'
escritorio_dir = r'c:\Users\andre\OneDrive\Escritorio'

src_index = os.path.join(work_dir, 'index.html')

sw_content = '''const CACHE_NAME = 'sinergix-crm-v56';
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
        console.warn('[SW v56] Cache addAll warning:', err);
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
            console.log('[SW v56] Purgando caché obsoleta:', cache);
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

# 1. Update obtenerSherpaSesion mapping
old_sesion_func = '''    function obtenerSherpaSesion() {
      const activeUser = obtenerSherpaIdActivo();
      const token = localStorage.getItem('sinergix_token') || localStorage.getItem('ea_session') || localStorage.getItem('sherpa_token');
      
      let nombre = (localStorage.getItem('sherpa_nombre') || '').trim();
      let rawCelular = (localStorage.getItem('sherpa_celular') || '').replace(/\\D/g, '');

      if (!nombre && activeUser) {
        if (activeUser === '101' || activeUser === 'sherpa_edgar') {
          nombre = 'Sherpa Edgar';
        } else if (activeUser === '102') {
          nombre = 'Sherpa 102';
        } else {
          nombre = 'Sherpa ' + activeUser;
        }
        localStorage.setItem('sherpa_nombre', nombre);
      }

      if (!rawCelular && activeUser) {
        rawCelular = activeUser.length === 10 ? activeUser : '5512345678';
        localStorage.setItem('sherpa_celular', '521' + rawCelular);
      }

      const celular = rawCelular ? (rawCelular.length === 10 ? '521' + rawCelular : rawCelular) : '5215512345678';
      const valido = Boolean(activeUser && activeUser !== 'demo');

      return { 
        valido: valido, 
        userId: activeUser, 
        nombre: nombre || ('Sherpa ' + activeUser), 
        celular: celular 
      };
    }'''

new_sesion_func = '''    function obtenerSherpaSesion() {
      const activeUser = obtenerSherpaIdActivo();
      const token = localStorage.getItem('sinergix_token') || localStorage.getItem('ea_session') || localStorage.getItem('sherpa_token');
      
      let nombre = (localStorage.getItem('sherpa_nombre') || '').trim();
      let rawCelular = (localStorage.getItem('sherpa_celular') || '').replace(/\\D/g, '');

      if (!nombre && activeUser) {
        if (activeUser === '101') {
          nombre = 'Sherpa 101';
        } else if (activeUser === '102' || activeUser === 'sherpa_edgar') {
          nombre = 'Sherpa Edgar';
        } else {
          nombre = 'Sherpa ' + activeUser;
        }
        localStorage.setItem('sherpa_nombre', nombre);
      }

      if (!rawCelular && activeUser) {
        rawCelular = activeUser.length === 10 ? activeUser : ('5512345' + activeUser.padStart(3, '0'));
        localStorage.setItem('sherpa_celular', '521' + rawCelular);
      }

      const celular = rawCelular ? (rawCelular.length === 10 ? '521' + rawCelular : rawCelular) : '5215512345678';
      const valido = Boolean(activeUser && activeUser !== 'demo');

      return { 
        valido: valido, 
        userId: activeUser, 
        nombre: nombre || ('Sherpa ' + activeUser), 
        celular: celular 
      };
    }'''

content = content.replace(old_sesion_func, new_sesion_func)

# 2. Update actualizarIndicadorSherpa header label (fix double 'Sherpa Sherpa')
old_indicador = '''      if (sesion.valido) {
        if (elNom) {
          elNom.textContent = sesion.nombre;
          elNom.className = 'text-emerald-600 dark:text-emerald-400 font-extrabold';
        }
        if (elTel) {
          const celDisplay = sesion.celular.replace(/^521/, '').replace(/^52/, '');
          elTel.textContent = `(+52 1 ${celDisplay})`;
          elTel.className = 'text-slate-600 dark:text-slate-300 font-mono text-xs font-bold';
        }
        if (elSpanHeader) elSpanHeader.textContent = `• Sherpa ${sesion.nombre}`;
      }'''

new_indicador = '''      if (sesion.valido) {
        if (elNom) {
          elNom.textContent = sesion.nombre + ' (ID: ' + sesion.userId + ')';
          elNom.className = 'text-emerald-600 dark:text-emerald-400 font-extrabold';
        }
        if (elTel) {
          const celDisplay = sesion.celular.replace(/^521/, '').replace(/^52/, '');
          elTel.textContent = `(+52 1 ${celDisplay})`;
          elTel.className = 'text-slate-600 dark:text-slate-300 font-mono text-xs font-bold';
        }
        const labelHeader = sesion.nombre.startsWith('Sherpa') ? sesion.nombre : ('Sherpa ' + sesion.nombre);
        if (elSpanHeader) elSpanHeader.textContent = `• ${labelHeader} (ID: ${sesion.userId})`;
      }'''

content = content.replace(old_indicador, new_indicador)

# 3. Update ejecutarLoginSherpa profile assignment
old_login_exec = '''        if (user === '101' || user === 'sherpa_edgar') {
          localStorage.setItem('sherpa_nombre', 'Sherpa Edgar');
        } else if (!localStorage.getItem('sherpa_nombre')) {
          localStorage.setItem('sherpa_nombre', 'Sherpa ' + user);
        }'''

new_login_exec = '''        if (user === '101') {
          localStorage.setItem('sherpa_nombre', 'Sherpa 101');
        } else if (user === '102' || user === 'sherpa_edgar') {
          localStorage.setItem('sherpa_nombre', 'Sherpa Edgar');
        } else {
          localStorage.setItem('sherpa_nombre', 'Sherpa ' + user);
        }'''

content = content.replace(old_login_exec, new_login_exec)

# 4. Update cargarBriefingMatutino sherpaNom fallback
old_briefing_nom = "const sherpaNom = localStorage.getItem('sherpa_nombre') || (activeUser === 'sherpa_edgar' ? 'Edgar' : activeUser);"
new_briefing_nom = "const sherpaNom = localStorage.getItem('sherpa_nombre') || (activeUser === '101' ? 'Sherpa 101' : (activeUser === '102' || activeUser === 'sherpa_edgar' ? 'Edgar' : ('Sherpa ' + activeUser)));"
content = content.replace(old_briefing_nom, new_briefing_nom)

# Bump SW to v56
content = content.replace('sw.js?v=55', 'sw.js?v=56')
print('[FIX] Corrected USER_ID 101 vs 102 mapping across session functions!')

# Validate JS syntax in index.html with node --check
scripts = re.findall(r'<script>(.*?)</script>', content, flags=re.DOTALL)
temp_js_path = os.path.join(work_dir, '_temp_validate.js')

has_error = False
for idx, s in enumerate(scripts):
    with open(temp_js_path, 'w', encoding='utf-8') as tf:
        tf.write(s)
    proc = subprocess.run(['node', '--check', temp_js_path], capture_output=True, text=True)
    if proc.returncode != 0:
        print(f'[SYNTAX ERROR in script tag #{idx+1}]:', proc.stderr)
        has_error = True
    else:
        print(f'[VALIDATED] Script tag #{idx+1} passed Node syntax check cleanly!')

if os.path.exists(temp_js_path):
    os.remove(temp_js_path)

if has_error:
    raise RuntimeError('JavaScript syntax check failed!')

# Save index.html & static/index.html
with open(src_index, 'w', encoding='utf-8') as f:
    f.write(content)

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

print('[SUCCESS] USER_ID 101 vs 102 mapping fixed and synchronized across all target directories!')
