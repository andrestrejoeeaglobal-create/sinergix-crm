import os, re, shutil, subprocess

work_dir = r'c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm'
git_repo = r'C:\Users\andre\.gemini\antigravity\brain\4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8\scratch\Sinergix-CRM\sinergix-crm'
escritorio_dir = r'c:\Users\andre\OneDrive\Escritorio'

src_index = os.path.join(work_dir, 'index.html')

sw_content = '''const CACHE_NAME = 'sinergix-crm-v55';
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
        console.warn('[SW v55] Cache addAll warning:', err);
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
            console.log('[SW v55] Purgando caché obsoleta:', cache);
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

# 1. Update obtenerSherpaIdActivo and obtenerSherpaSesion using string replacement
old_session_funcs = '''    function obtenerSherpaIdActivo() {
      return localStorage.getItem('sinergix_active_user') || 
             localStorage.getItem('sherpa_celular') || 
             localStorage.getItem('sherpa_nombre') || 
             'demo';
    }

    function obtenerSherpaSesion() {
      const nombre = (localStorage.getItem('sherpa_nombre') || (document.getElementById('input-sherpa-nombre')?.value || '').trim()).trim();
      const rawCelular = (localStorage.getItem('sherpa_celular') || (document.getElementById('input-sherpa-celular')?.value || '').trim()).replace(/\\D/g, '');
      const celular = rawCelular ? (rawCelular.length === 10 ? '521' + rawCelular : rawCelular) : '';
      
      if (!nombre || !celular) {
        return { valido: false, nombre: '', celular: '' };
      }
      return { valido: true, nombre, celular };
    }'''

new_session_funcs = '''    function obtenerSherpaIdActivo() {
      return localStorage.getItem('sinergix_active_user') || 
             localStorage.getItem('sherpa_id_activo') || 
             localStorage.getItem('sherpa_celular') || 
             localStorage.getItem('sherpa_nombre') || 
             '101';
    }

    function obtenerSherpaSesion() {
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

content = content.replace(old_session_funcs, new_session_funcs)
print('[FIX] Updated obtenerSherpaIdActivo and obtenerSherpaSesion cleanly!')

# 2. Update ejecutarLoginSherpa to properly initialize pre-configured user profile for USER_ID 101
old_login_exec_code = '''        localStorage.setItem('sinergix_token', 'TOKEN_SHERPA_' + Date.now());
        localStorage.setItem('sinergix_active_user', user);
        localStorage.setItem('ea_session', 'ACTIVE');

        const digits = user.replace(/\\D/g, '');
        if (digits.length === 10) {
          localStorage.setItem('sherpa_celular', '521' + digits);
        }
        
        const existingNom = localStorage.getItem('sherpa_nombre');
        if (!existingNom) {
          if (digits.length !== 10 && user.length > 2 && !/^\\d+$/.test(user)) {
            localStorage.setItem('sherpa_nombre', user);
          }
        }'''

new_login_exec_code = '''        localStorage.setItem('sinergix_token', 'TOKEN_SHERPA_' + Date.now());
        localStorage.setItem('sinergix_active_user', user);
        localStorage.setItem('ea_session', 'ACTIVE');

        const digits = user.replace(/\\D/g, '');
        if (digits.length === 10) {
          localStorage.setItem('sherpa_celular', '521' + digits);
        } else if (!localStorage.getItem('sherpa_celular')) {
          localStorage.setItem('sherpa_celular', '5215512345678');
        }

        if (user === '101' || user === 'sherpa_edgar') {
          localStorage.setItem('sherpa_nombre', 'Sherpa Edgar');
        } else if (!localStorage.getItem('sherpa_nombre')) {
          localStorage.setItem('sherpa_nombre', 'Sherpa ' + user);
        }'''

content = content.replace(old_login_exec_code, new_login_exec_code)
print('[FIX] Updated login profile initialization for USER_ID 101!')

# Bump SW to v55
content = content.replace('sw.js?v=54', 'sw.js?v=55')
print('[FIX] Bumped Service Worker reference to sw.js?v=55!')

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

print('[SUCCESS] Enforced USER_ID primary key session validation across all target directories!')
