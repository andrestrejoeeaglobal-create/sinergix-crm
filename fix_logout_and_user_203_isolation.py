import os, re, shutil, subprocess

work_dir = r'c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm'
git_repo = r'C:\Users\andre\.gemini\antigravity\brain\4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8\scratch\Sinergix-CRM\sinergix-crm'
escritorio_dir = r'c:\Users\andre\OneDrive\Escritorio'

src_index = os.path.join(work_dir, 'index.html')

sw_content = '''const CACHE_NAME = 'sinergix-crm-v57';
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
        console.warn('[SW v57] Cache addAll warning:', err);
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
            console.log('[SW v57] Purgando caché obsoleta:', cache);
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

# 1. Update obtenerSherpaIdActivo and obtenerSherpaSesion to handle clean logout & session validation
old_session_funcs = '''    function obtenerSherpaIdActivo() {
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

new_session_funcs = '''    function obtenerSherpaIdActivo() {
      return localStorage.getItem('sinergix_active_user') || 
             localStorage.getItem('sherpa_id_activo') || 
             '';
    }

    function obtenerSherpaSesion() {
      const activeUser = obtenerSherpaIdActivo();
      const token = localStorage.getItem('sinergix_token') || localStorage.getItem('ea_session') || localStorage.getItem('sherpa_token');
      
      if (!activeUser || !token) {
        return { valido: false, userId: '', nombre: '', celular: '' };
      }

      let nombre = (localStorage.getItem('sherpa_nombre') || '').trim();
      let rawCelular = (localStorage.getItem('sherpa_celular') || '').replace(/\\D/g, '');

      if (!nombre) {
        if (activeUser === '101') {
          nombre = 'Sherpa 101';
        } else if (activeUser === '102' || activeUser === 'sherpa_edgar') {
          nombre = 'Sherpa Edgar';
        } else {
          nombre = 'Sherpa ' + activeUser;
        }
        localStorage.setItem('sherpa_nombre', nombre);
      }

      if (!rawCelular) {
        rawCelular = activeUser.length === 10 ? activeUser : ('5512345' + activeUser.padStart(3, '0'));
        localStorage.setItem('sherpa_celular', '521' + rawCelular);
      }

      const celular = rawCelular ? (rawCelular.length === 10 ? '521' + rawCelular : rawCelular) : '5215512345678';

      return { 
        valido: true, 
        userId: activeUser, 
        nombre: nombre || ('Sherpa ' + activeUser), 
        celular: celular 
      };
    }'''

content = content.replace(old_session_funcs, new_session_funcs)
print('[FIX] Updated obtenerSherpaSesion to return valido=false when no active user/token is in localStorage!')

# 2. Update salir() function to clear all keys, purge memory, and show explicit logout toast + inline notice
old_salir = '''    function salir() {
      localStorage.removeItem('ea_session');
      localStorage.removeItem('ea_token');
      localStorage.removeItem('sherpa_token');
      localStorage.removeItem('sinergix_token');
      localStorage.removeItem('sinergix_active_user');
      localStorage.removeItem('sherpa_nombre');
      localStorage.removeItem('sherpa_celular');
      todosLosLeads = [];
      if (typeof renderizarLista === 'function') renderizarLista();
      
      cerrarAvisoModal();
      actualizarEstadoSesionSherpa();

      const errorBox = document.getElementById('login-error-msg');
      if (errorBox) {
        errorBox.innerHTML = '<i class="fa-solid fa-circle-info text-ea-blue dark:text-blue-400 text-sm shrink-0"></i><span>Sesión cerrada correctamente. Por favor ingresa tus credenciales para continuar.</span>';
        errorBox.className = "w-full p-3.5 bg-blue-50 dark:bg-blue-950/80 border border-blue-200 dark:border-blue-800 rounded-2xl text-blue-900 dark:text-blue-200 text-xs font-bold text-center leading-relaxed backdrop-blur-md flex items-center justify-center gap-2 mb-4";
        errorBox.classList.remove('hidden');
      }
    }'''

new_salir = '''    function salir() {
      const prevUser = localStorage.getItem('sinergix_active_user') || localStorage.getItem('sherpa_nombre') || 'Sherpa';
      
      localStorage.removeItem('ea_session');
      localStorage.removeItem('ea_token');
      localStorage.removeItem('sherpa_token');
      localStorage.removeItem('sinergix_token');
      localStorage.removeItem('sinergix_active_user');
      localStorage.removeItem('sherpa_id_activo');
      localStorage.removeItem('sherpa_nombre');
      localStorage.removeItem('sherpa_celular');
      
      todosLosLeads = [];
      if (typeof renderizarLista === 'function') renderizarLista();
      
      actualizarEstadoSesionSherpa();

      const errorBox = document.getElementById('login-error-msg');
      if (errorBox) {
        errorBox.innerHTML = '<i class="fa-solid fa-circle-info text-ea-blue dark:text-blue-400 text-sm shrink-0"></i><span>La sesión de <strong>' + prevUser + '</strong> se cerró correctamente. Por favor ingresa tus credenciales para continuar.</span>';
        errorBox.className = "w-full p-3.5 bg-blue-50 dark:bg-blue-950/80 border border-blue-200 dark:border-blue-800 rounded-2xl text-blue-900 dark:text-blue-200 text-xs font-bold text-center leading-relaxed backdrop-blur-md flex items-center justify-center gap-2 mb-4";
        errorBox.classList.remove('hidden');
      }

      showToast('Sesión de ' + prevUser + ' cerrada correctamente', 'info');
    }'''

content = content.replace(old_salir, new_salir)
print('[FIX] Refactored salir() to display explicit logout toast notice + clear all storage!')

# 3. Update ejecutarLoginSherpa to purge any old user keys and initialize clean user session (e.g. 203)
old_login_exec = '''        localStorage.setItem('sinergix_token', 'TOKEN_SHERPA_' + Date.now());
        localStorage.setItem('sinergix_active_user', user);
        localStorage.setItem('ea_session', 'ACTIVE');

        const digits = user.replace(/\\D/g, '');
        if (digits.length === 10) {
          localStorage.setItem('sherpa_celular', '521' + digits);
        } else if (!localStorage.getItem('sherpa_celular')) {
          localStorage.setItem('sherpa_celular', '5215512345678');
        }

        if (user === '101') {
          localStorage.setItem('sherpa_nombre', 'Sherpa 101');
        } else if (user === '102' || user === 'sherpa_edgar') {
          localStorage.setItem('sherpa_nombre', 'Sherpa Edgar');
        } else {
          localStorage.setItem('sherpa_nombre', 'Sherpa ' + user);
        }'''

new_login_exec = '''        // Purge any stale user session variables before setting new USER_ID
        localStorage.removeItem('sherpa_nombre');
        localStorage.removeItem('sherpa_celular');

        localStorage.setItem('sinergix_token', 'TOKEN_SHERPA_' + user + '_' + Date.now());
        localStorage.setItem('sinergix_active_user', user);
        localStorage.setItem('sherpa_id_activo', user);
        localStorage.setItem('ea_session', 'ACTIVE');

        const digits = user.replace(/\\D/g, '');
        if (digits.length === 10) {
          localStorage.setItem('sherpa_celular', '521' + digits);
        } else {
          localStorage.setItem('sherpa_celular', '521551234' + user.padStart(3, '0'));
        }

        if (user === '101') {
          localStorage.setItem('sherpa_nombre', 'Sherpa 101');
        } else if (user === '102' || user === 'sherpa_edgar') {
          localStorage.setItem('sherpa_nombre', 'Sherpa Edgar');
        } else {
          localStorage.setItem('sherpa_nombre', 'Sherpa ' + user);
        }

        todosLosLeads = [];'''

content = content.replace(old_login_exec, new_login_exec)

# 4. Update login success toasts to state active USER_ID
old_success_toast = 'showToast("¡Bienvenido al CRM Gerencial Sinergix!", "success");'
new_success_toast = 'showToast("¡Bienvenido al CRM Gerencial Sinergix! Sesión activa: Sherpa " + user + " (ID: " + user + ")", "success");'
content = content.replace(old_success_toast, new_success_toast)

# Bump SW to v57
content = content.replace('sw.js?v=56', 'sw.js?v=57')
print('[FIX] Bumped Service Worker reference to sw.js?v=57!')

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

print('[SUCCESS] Refactored logout notice and multi-tenant session purging for USER_ID 203!')
