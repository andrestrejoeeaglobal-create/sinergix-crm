import re
import subprocess
import os

def apply_auth_lockdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Inject synchronous Anti-FOUC Auth Guard in <head>
    head_auth_guard = """  <!-- Synchronous Anti-FOUC Auth Guard: Block access if not authenticated -->
  <script>
    (function() {
      const token = localStorage.getItem('sinergix_token');
      const sherpaActivo = localStorage.getItem('sinergix_sherpa_activo');
      if (!token || !sherpaActivo) {
        document.write('<style>#main-crm-app, #sherpa-session-bar { display: none !important; } #modal-login { display: flex !important; }</style>');
      }
    })();
  </script>"""

    if 'Synchronous Anti-FOUC Auth Guard' not in content:
        content = content.replace('</head>', head_auth_guard + '\n</head>')

    # 2. Update initial HTML classes on main-crm-app and modal-login
    # Ensure #main-crm-app has class hidden by default
    content = re.sub(
        r'<main\s+id="main-crm-app"\s+class="([^"]*)"',
        lambda m: f'<main id="main-crm-app" class="{m.group(1)} hidden"' if 'hidden' not in m.group(1) else m.group(0),
        content
    )

    # Ensure #modal-login does NOT have class hidden by default in initial markup
    content = re.sub(
        r'<div\s+id="modal-login"\s+class="([^"]*)"',
        lambda m: f'<div id="modal-login" class="{m.group(1).replace("hidden", "").strip()}"',
        content
    )

    # 3. Update actualizarEstadoSesionSherpa
    new_actualizar_sesion = """    function actualizarEstadoSesionSherpa() {
      const token = localStorage.getItem('sinergix_token');
      const sherpaActivo = localStorage.getItem('sinergix_sherpa_activo');
      const modal = document.getElementById('modal-login');
      const mainApp = document.getElementById('main-crm-app');
      const sessionBar = document.getElementById('sherpa-session-bar');

      if (!token || !sherpaActivo) {
        if (modal) {
          modal.classList.remove('hidden');
          modal.style.display = 'flex';
        }
        if (mainApp) {
          mainApp.classList.add('hidden');
          mainApp.style.display = 'none';
        }
        if (sessionBar) {
          sessionBar.classList.add('hidden');
          sessionBar.style.display = 'none';
        }
        todosLosLeads = [];
        if (typeof initNetworkCanvas === 'function') initNetworkCanvas();
        return false;
      } else {
        if (modal) {
          modal.classList.add('hidden');
          modal.style.display = 'none';
        }
        if (mainApp) {
          mainApp.classList.remove('hidden');
          mainApp.style.display = '';
        }
        if (sessionBar) {
          sessionBar.classList.remove('hidden');
          sessionBar.style.display = '';
        }
        return true;
      }
    }"""

    idx_act = content.find("function actualizarEstadoSesionSherpa() {")
    if idx_act != -1:
        idx_end_act = content.find("async function ejecutarLoginSherpa", idx_act)
        if idx_end_act == -1:
            idx_end_act = content.find("function ejecutarLoginSherpa", idx_act)
        if idx_end_act != -1:
            content = content[:idx_act] + new_actualizar_sesion.strip() + "\n\n        " + content[idx_end_act:]

    # 4. Update DOMContentLoaded to enforce auth check first
    old_dom_load_start = "document.addEventListener('DOMContentLoaded', async () => {\n      try {"
    new_dom_load_start = """document.addEventListener('DOMContentLoaded', async () => {
      try {
        const isAuthenticated = actualizarEstadoSesionSherpa();
        if (!isAuthenticated) {
          todosLosLeads = [];
          return;
        }"""

    if old_dom_load_start in content and "const isAuthenticated = actualizarEstadoSesionSherpa();" not in content:
        content = content.replace(old_dom_load_start, new_dom_load_start)

    # 5. Bump service worker to v71
    content = content.replace('sw.js?v=70', 'sw.js?v=71')
    content = content.replace('sinergix-crm-v70', 'sinergix-crm-v71')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Applied strict auth lockdown to {file_path}")

apply_auth_lockdown('index.html')
apply_auth_lockdown('static/index.html')

# Update sw.js version to v71
with open('sw.js', 'r', encoding='utf-8') as f:
    sw = f.read()

sw = sw.replace('sinergix-crm-v70', 'sinergix-crm-v71')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw)

print("Updated sw.js to v71.")

# Validate JS syntax in index.html and static/index.html using node --check
for fname in ['index.html', 'static/index.html']:
    with open(fname, 'r', encoding='utf-8') as f:
        html = f.read()

    scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
    print(f"\n--- Validating {fname} ({len(scripts)} script blocks) ---")

    temp_js = '_temp_test_check.js'
    all_ok = True
    for idx, script in enumerate(scripts):
        with open(temp_js, 'w', encoding='utf-8') as tf:
            tf.write(script)
        res = subprocess.run(['node', '--check', temp_js], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[ERROR] Syntax Error in {fname} script block {idx+1}: {res.stderr}")
            all_ok = False
        else:
            print(f"[OK] {fname} script block {idx+1}: OK")

    if os.path.exists(temp_js):
        os.remove(temp_js)

    if not all_ok:
        raise Exception(f"Syntax validation failed for {fname}!")
    else:
        print(f"ALL SCRIPT BLOCKS PASSED SYNTAX CHECK IN {fname}!")
