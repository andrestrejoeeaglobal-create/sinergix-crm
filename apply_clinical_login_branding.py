import os, re, shutil, subprocess

work_dir = r'c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm'
git_repo = r'C:\Users\andre\.gemini\antigravity\brain\4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8\scratch\Sinergix-CRM\sinergix-crm'
escritorio_dir = r'c:\Users\andre\OneDrive\Escritorio'

src_index = os.path.join(work_dir, 'index.html')

sw_content = '''const CACHE_NAME = 'sinergix-crm-v53';
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
        console.warn('[SW v53] Cache addAll warning:', err);
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
            console.log('[SW v53] Purgando caché obsoleta:', cache);
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

# Replace modal-login HTML block with Clinical Branding Guide standards
new_login_modal = '''  <!-- Modal Iniciar Sesión (Gobernanza de Diseño Clínico T.I.L.O. & Equipo en Acción®) -->
  <div id="modal-login" class="fixed inset-0 z-[100] bg-slate-900/90 dark:bg-slate-950/95 flex items-center justify-center p-4 overflow-y-auto hidden backdrop-blur-md">
    <!-- Canvas animado de constelaciones -->
    <canvas id="login-canvas" class="absolute inset-0 pointer-events-none z-0"></canvas>

    <div class="relative z-10 w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-clinical-lg space-y-5 transition-colors duration-200">
      
      <!-- Top Bar: Toggle de Tema Dual -->
      <div class="flex items-center justify-between">
        <span class="inline-flex items-center px-2.5 py-1 rounded-xl text-[10px] font-extrabold bg-blue-50 dark:bg-blue-950/80 text-ea-blue dark:text-blue-400 border border-blue-200 dark:border-blue-800 uppercase tracking-wider">
          <i class="fa-solid fa-user-shield mr-1.5 text-xs"></i> Acceso Sherpa
        </span>
        <button onclick="toggleTheme()" 
                class="touch-target px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 transition flex items-center gap-1.5" 
                aria-label="Cambiar Tema">
          <i class="fa-solid fa-moon dark:hidden text-xs text-slate-600" aria-hidden="true"></i>
          <i class="fa-solid fa-sun hidden dark:inline text-xs text-ea-yellow" aria-hidden="true"></i>
          <span class="dark:hidden text-[11px] font-extrabold">Oscuro</span>
          <span class="hidden dark:inline text-[11px] font-extrabold">Claro</span>
        </button>
      </div>

      <!-- Encabezado con Imagotipo Oficial Equipo en Acción® -->
      <div class="text-center space-y-1.5">
        <div class="h-12 flex items-center justify-center mb-1">
          <img src="./assets/images/logo_ea.png" 
               onerror="this.onerror=null; this.src='https://equipoenaccion.net/images/logo_ea.png';" 
               alt="Equipo en Acción®" 
               class="h-full w-auto object-contain logo-clinical-contrast" />
        </div>
        <h2 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight">
          Sinergix Negocio CRM
        </h2>
        <p class="text-xs text-slate-500 dark:text-slate-400 font-bold">
          Plataforma Gerencial — Equipo en Acción®
        </p>
      </div>

      <!-- Formulario de Autenticación -->
      <form onsubmit="ejecutarLoginSherpa(event)" class="space-y-4">
        <div>
          <label class="block text-xs font-extrabold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
            Usuario / Teléfono de 10 dígitos
          </label>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-ea-blue dark:text-blue-400">
              <i class="fa-solid fa-user text-sm"></i>
            </span>
            <input type="text" id="login-user" required placeholder="Ej. 5512345678" 
                   class="w-full pl-10 pr-4 py-3 bg-slate-50 dark:bg-slate-800/90 text-slate-900 dark:text-white rounded-2xl text-sm font-bold border border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-ea-blue focus:border-ea-blue transition placeholder-slate-400 dark:placeholder-slate-500" style="min-height: 48px;">
          </div>
        </div>

        <div>
          <label class="block text-xs font-extrabold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
            Contraseña
          </label>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-ea-blue dark:text-blue-400">
              <i class="fa-solid fa-lock text-sm"></i>
            </span>
            <input type="password" id="login-password" required placeholder="••••••••" 
                   class="w-full pl-10 pr-4 py-3 bg-slate-50 dark:bg-slate-800/90 text-slate-900 dark:text-white rounded-2xl text-sm font-bold border border-slate-300 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-ea-blue focus:border-ea-blue transition placeholder-slate-400 dark:placeholder-slate-500" style="min-height: 48px;">
          </div>
        </div>

        <!-- Mensaje de Error / Info con Triple Señal WCAG 2.2 AAA -->
        <div id="login-error-msg" class="w-full p-3.5 bg-blue-50 dark:bg-blue-950/80 border border-blue-200 dark:border-blue-800 rounded-2xl text-blue-900 dark:text-blue-200 text-xs font-bold text-center leading-relaxed backdrop-blur-md hidden flex items-center justify-center gap-2">
          <i class="fa-solid fa-circle-info text-ea-blue dark:text-blue-400 text-sm shrink-0"></i>
          <span>Sesión cerrada correctamente. Por favor ingresa tus credenciales para continuar.</span>
        </div>

        <!-- Botón Iniciar Sesión (Azul Corporativo + Target Size 48px) -->
        <button 
          type="submit" 
          id="btn-submit-login"
          class="w-full py-3.5 px-6 bg-ea-blue hover:bg-blue-700 active:bg-blue-800 text-white font-extrabold text-sm tracking-wide uppercase rounded-2xl shadow-clinical-md transition-all border border-blue-500/20 flex items-center justify-center space-x-2 touch-target cursor-pointer"
          style="min-height: 48px;"
        >
          <i class="fa-solid fa-right-to-bracket text-base"></i>
          <span>Iniciar Sesión</span>
        </button>
      </form>

      <!-- Firma Canónica de 5 Hexágonos Institucionales -->
      <div class="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2">
        <div class="flex justify-center items-center gap-1.5">
          <span><svg width="20" height="17" viewBox="0 0 576 512" aria-hidden="true"><g transform="rotate(180 288 256)"><path fill="#B70E0C" d="M441.5 39.8C432.9 25.1 417.1 16 400 16H176c-17.1 0-32.9 9.1-41.5 23.8l-112 192c-8.7 14.9-8.7 33.4 0 48.4l112 192c8.6 14.7 24.4 23.8 41.5 23.8h224c17.1 0 32.9-9.1 41.5-23.8l112-192c8.7-14.9 8.7-33.4 0-48.4l-112-192z"/></g></svg></span>
          <span><svg width="20" height="17" viewBox="0 0 576 512" aria-hidden="true"><g transform="rotate(180 288 256)"><path fill="#F29FC5" d="M441.5 39.8C432.9 25.1 417.1 16 400 16H176c-17.1 0-32.9 9.1-41.5 23.8l-112 192c-8.7 14.9-8.7 33.4 0 48.4l112 192c8.6 14.7 24.4 23.8 41.5 23.8h224c17.1 0 32.9-9.1 41.5-23.8l112-192c8.7-14.9 8.7-33.4 0-48.4l-112-192z"/></g></svg></span>
          <span><svg width="20" height="17" viewBox="0 0 576 512" aria-hidden="true"><g transform="rotate(90 288 256)"><path fill="#1C75BC" d="M441.5 39.8C432.9 25.1 417.1 16 400 16H176c-17.1 0-32.9 9.1-41.5 23.8l-112 192c-8.7 14.9-8.7 33.4 0 48.4l112 192c8.6 14.7 24.4 23.8 41.5 23.8h224c17.1 0 32.9-9.1 41.5-23.8l112-192c8.7-14.9 8.7-33.4 0-48.4l-112-192z"/></g></svg></span>
          <span><svg width="20" height="17" viewBox="0 0 576 512" aria-hidden="true"><g transform="rotate(180 288 256)"><path fill="#3AAA35" d="M441.5 39.8C432.9 25.1 417.1 16 400 16H176c-17.1 0-32.9 9.1-41.5 23.8l-112 192c-8.7 14.9-8.7 33.4 0 48.4l112 192c8.6 14.7 24.4 23.8 41.5 23.8h224c17.1 0 32.9-9.1 41.5-23.8l112-192c8.7-14.9 8.7-33.4 0-48.4l-112-192z"/></g></svg></span>
          <span><svg width="20" height="17" viewBox="0 0 576 512" aria-hidden="true"><g transform="rotate(180 288 256)"><path fill="#FFCC00" d="M441.5 39.8C432.9 25.1 417.1 16 400 16H176c-17.1 0-32.9 9.1-41.5 23.8l-112 192c-8.7 14.9-8.7 33.4 0 48.4l112 192c8.6 14.7 24.4 23.8 41.5 23.8h224c17.1 0 32.9-9.1 41.5-23.8l112-192c8.7-14.9 8.7-33.4 0-48.4l-112-192z"/></g></svg></span>
        </div>
        <p class="text-[10px] text-slate-500 dark:text-slate-400 font-extrabold text-center tracking-tight">
          © 2026 Equipo en Acción® • Gobernanza Omnicanal T.I.L.O.
        </p>
      </div>

    </div>
  </div>'''

old_login_modal_pattern = r'<!-- Modal Iniciar Sesión.*?<div id="modal-login".*?</div>\s*</div>'
content = re.sub(old_login_modal_pattern, new_login_modal, content, flags=re.DOTALL)
print('[FIX] Redesigned login modal with clinical-branding-guide standards!')

# Update error box styling in ejecutarLoginSherpa JS function
old_error_style = 'errorBox.className = "w-full max-w-md p-3.5 bg-red-950/90 border border-red-500 rounded text-red-100 text-xs font-bold text-center backdrop-blur-md mb-4";'
new_error_style = 'errorBox.className = "w-full p-3.5 bg-red-50 dark:bg-red-950/80 border border-red-300 dark:border-red-800 rounded-2xl text-red-800 dark:text-red-200 text-xs font-bold text-center backdrop-blur-md mb-4 flex items-center justify-center gap-2";'
content = content.replace(old_error_style, new_error_style)

# Bump SW version to v53
content = content.replace('sw.js?v=52', 'sw.js?v=53')
print('[FIX] Bumped Service Worker reference to sw.js?v=53!')

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

print('[SUCCESS] Applied clinical-branding-guide to login screen and synchronized all target files!')
