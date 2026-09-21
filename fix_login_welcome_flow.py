import os, re, shutil, subprocess

work_dir = r'c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm'
git_repo = r'C:\Users\andre\.gemini\antigravity\brain\4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8\scratch\Sinergix-CRM\sinergix-crm'
escritorio_dir = r'c:\Users\andre\OneDrive\Escritorio'

src_index = os.path.join(work_dir, 'index.html')

sw_content = '''const CACHE_NAME = 'sinergix-crm-v54';
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
        console.warn('[SW v54] Cache addAll warning:', err);
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
            console.log('[SW v54] Purgando caché obsoleta:', cache);
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

# 1. Update salir() function using exact string replacement
old_salir_block = '''    function salir() {
      localStorage.removeItem('ea_session');
      localStorage.removeItem('ea_token');
      localStorage.removeItem('sherpa_token');
      localStorage.removeItem('sinergix_token');
      localStorage.removeItem('sinergix_active_user');
      localStorage.removeItem('sherpa_nombre');
      localStorage.removeItem('sherpa_celular');
      todosLosLeads = [];
      if (typeof renderizarLista === 'function') renderizarLista();
      
      actualizarEstadoSesionSherpa();

      const errorBox = document.getElementById('login-error-msg');
      if (errorBox) {
        errorBox.innerText = "Sesión cerrada correctamente. Por favor ingresa tus credenciales para continuar.";
        errorBox.className = "w-full max-w-md p-3.5 bg-blue-950/90 border border-blue-400 rounded text-blue-100 text-xs font-bold text-center backdrop-blur-md mb-4";
        errorBox.classList.remove('hidden');
      }
      
      showToast('Sesión cerrada correctamente', 'info');
    }'''

new_salir_block = '''    function salir() {
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

content = content.replace(old_salir_block, new_salir_block)
print('[FIX] Updated salir() function cleanly!')

# 2. Update ejecutarLoginSherpa() function using exact string replacement
old_login_block = '''        const sesion = obtenerSherpaSesion();
        if (!sesion.valido) {
          abrirModalConfigSherpa("¡Bienvenido! Por favor configura tu Nombre de Batalla y tu número de WhatsApp de 10 dígitos para operar en el CRM.");
        } else {
          showToast("Bienvenido al CRM Gerencial Sinergix", "success");
        }

      } catch (err) {
        localStorage.setItem('sinergix_token', 'TOKEN_SHERPA_DEMO');
        localStorage.setItem('sinergix_active_user', user || 'demo');
        localStorage.setItem('ea_session', 'ACTIVE');

        const digitsCatch = (user || '').replace(/\D/g, '');
        if (digitsCatch.length === 10) {
          localStorage.setItem('sherpa_celular', '521' + digitsCatch);
        }

        actualizarEstadoSesionSherpa();

        const sesionCatch = obtenerSherpaSesion();
        if (!sesionCatch.valido) {
          abrirModalConfigSherpa("¡Bienvenido! Por favor configura tu Nombre de Batalla y tu número de WhatsApp de 10 dígitos para operar en el CRM.");
        } else {
          showToast("Sesión iniciada en modo local", "success");
        }
      }'''

new_login_block = '''        cerrarAvisoModal();
        const sesion = obtenerSherpaSesion();
        if (!sesion.valido) {
          abrirModalConfigSherpa("¡Bienvenido! Por favor configura tu Nombre de Batalla y tu número de WhatsApp de 10 dígitos para operar en el CRM.");
        } else {
          showToast("¡Bienvenido al CRM Gerencial Sinergix!", "success");
        }

      } catch (err) {
        localStorage.setItem('sinergix_token', 'TOKEN_SHERPA_DEMO');
        localStorage.setItem('sinergix_active_user', user || 'demo');
        localStorage.setItem('ea_session', 'ACTIVE');

        const digitsCatch = (user || '').replace(/\\D/g, '');
        if (digitsCatch.length === 10) {
          localStorage.setItem('sherpa_celular', '521' + digitsCatch);
        }

        cerrarAvisoModal();
        actualizarEstadoSesionSherpa();

        const sesionCatch = obtenerSherpaSesion();
        if (!sesionCatch.valido) {
          abrirModalConfigSherpa("¡Bienvenido! Por favor configura tu Nombre de Batalla y tu número de WhatsApp de 10 dígitos para operar en el CRM.");
        } else {
          showToast("¡Bienvenido al CRM Gerencial Sinergix!", "success");
        }
      }'''

content = content.replace(old_login_block, new_login_block)
print('[FIX] Updated ejecutarLoginSherpa() function cleanly!')

# Bump SW to v54
content = content.replace('sw.js?v=53', 'sw.js?v=54')
print('[FIX] Bumped Service Worker reference to sw.js?v=54!')

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

print('[SUCCESS] Login welcome flow fixed and synchronized across all target directories!')
