import os, re, shutil

work_dir = r'c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm'
git_repo = r'C:\Users\andre\.gemini\antigravity\brain\4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8\scratch\Sinergix-CRM\sinergix-crm'
escritorio_dir = r'c:\Users\andre\OneDrive\Escritorio'

src_index = os.path.join(work_dir, 'index.html')

sw_content = '''const CACHE_NAME = 'sinergix-crm-v51';
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
        console.warn('[SW v51] Cache addAll warning:', err);
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
            console.log('[SW v51] Purgando caché obsoleta:', cache);
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

# Update EcoSinergix Live badge styling with cursor-default select-none pointer-events-none
old_live_badge = '<span class="hidden md:inline-flex items-center px-3 py-2 rounded-xl text-xs font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800" style="min-height: 48px;">'

new_live_badge = '<span id="badge-ecosinergix-live" class="hidden md:inline-flex items-center px-3 py-2 rounded-xl text-xs font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 cursor-default select-none pointer-events-none" style="min-height: 48px;" title="Estado del Sistema: En Línea">'

if old_live_badge in content:
    content = content.replace(old_live_badge, new_live_badge)
    print('[FIX] EcoSinergix Live badge updated to non-clickable visual indicator!')

# Bump SW to v51
content = content.replace('sw.js?v=50', 'sw.js?v=51')
print('[FIX] Bumped Service Worker reference to sw.js?v=51!')

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

print('[SUCCESS] Applied EcoSinergix Live badge fix and synchronized all target files!')
