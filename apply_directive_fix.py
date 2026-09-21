import os
import re

def update_html(filepath):
    print(f"Updating {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove document.write style in head
    head_write_old = """  <!-- Synchronous Anti-FOUC Auth Guard: Block access if not authenticated -->
  <script>
    (function() {
      const token = localStorage.getItem('sinergix_token');
      const sherpaActivo = localStorage.getItem('sinergix_sherpa_activo');
      if (!token || !sherpaActivo) {
        document.write('<style>#main-crm-app, #sherpa-session-bar { display: none !important; } #modal-login { display: flex !important; }</style>');
      }
    })();
  </script>"""

    head_write_new = """  <!-- Synchronous Anti-FOUC Auth Guard: Clean initial state -->
  <script>
    (function() {
      const token = localStorage.getItem('sinergix_token');
      const sherpaActivo = localStorage.getItem('sinergix_sherpa_activo');
      if (!token || !sherpaActivo) {
        // App elements start hidden by HTML class
      }
    })();
  </script>"""

    if head_write_old in content:
        content = content.replace(head_write_old, head_write_new)
        print("  - Removed document.write from <head>")

    # 2. Update sherpa-session-bar HTML to start with class="hidden"
    bar_old = '<div id="sherpa-session-bar" class="w-full bg-slate-100 dark:bg-slate-800'
    bar_new = '<div id="sherpa-session-bar" class="hidden w-full bg-slate-100 dark:bg-slate-800'
    if bar_old in content:
        content = content.replace(bar_old, bar_new)
        print("  - Added 'hidden' class to #sherpa-session-bar HTML markup")

    # 3. Update actualizarEstadoSesionSherpa to enforce modal closing with !important style property
    sesion_old = """    function actualizarEstadoSesionSherpa() {
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

    sesion_new = """    function actualizarEstadoSesionSherpa() {
      const token = localStorage.getItem('sinergix_token');
      const sherpaActivo = localStorage.getItem('sinergix_sherpa_activo');
      const modal = document.getElementById('modal-login');
      const mainApp = document.getElementById('main-crm-app');
      const sessionBar = document.getElementById('sherpa-session-bar');

      if (!token || !sherpaActivo) {
        if (modal) {
          modal.classList.remove('hidden');
          modal.style.setProperty('display', 'flex', 'important');
        }
        if (mainApp) {
          mainApp.classList.add('hidden');
          mainApp.style.setProperty('display', 'none', 'important');
        }
        if (sessionBar) {
          sessionBar.classList.add('hidden');
          sessionBar.style.setProperty('display', 'none', 'important');
        }
        todosLosLeads = [];
        if (typeof initNetworkCanvas === 'function') initNetworkCanvas();
        return false;
      } else {
        if (modal) {
          modal.classList.add('hidden');
          modal.style.setProperty('display', 'none', 'important');
        }
        if (mainApp) {
          mainApp.classList.remove('hidden');
          mainApp.style.removeProperty('display');
          mainApp.style.display = '';
        }
        if (sessionBar) {
          sessionBar.classList.remove('hidden');
          sessionBar.style.removeProperty('display');
          sessionBar.style.display = '';
        }
        return true;
      }
    }"""

    if sesion_old in content:
        content = content.replace(sesion_old, sesion_new)
        print("  - Updated actualizarEstadoSesionSherpa to enforce style.setProperty('display', 'none', 'important')")

    # 4. Remove pass.length >= 3 and demo fallbacks from ejecutarLoginSherpa
    login_fallback_old = """          } else if (item.respuesta === 'CONTRASENA INVALIDA' || item.respuesta === 'NO EXISTE EL USUARIO') {
            const passLower = pass.toLowerCase();
            const userLower = user.toLowerCase();
            if (passLower === 'test' || passLower === '123456' || passLower === 'admin' || passLower === userLower || ['101', '102', '136', 'edgar', 'luis', 'andres', 'sherpa'].includes(userLower) || pass.length >= 3) {
              resultado = null; // Enable test/demo profile fallback
            } else {
              resultado = item;
            }
          }"""

    login_fallback_new = """          } else if (item.respuesta === 'CONTRASENA INVALIDA' || item.respuesta === 'NO EXISTE EL USUARIO') {
            resultado = item;
          }"""

    if login_fallback_old in content:
        content = content.replace(login_fallback_old, login_fallback_new)
        print("  - Removed pass.length >= 3 and fake fallback from login handler")

    # 5. Remove artificial fallback user generator in ejecutarLoginSherpa (if !resultado)
    fake_profile_old = """        // Fallback profile if direct API call was blocked in static client mode
        if (!resultado || (!resultado.customerName && !resultado.custid)) {
          if (user === '102' || user === 'sherpa_edgar' || user.toLowerCase() === 'edgar') {
            resultado = {
              custid: "102",
              customerName: "EDGAR ARTURO, FRIEVENTH MONDRAGON",
              firstname: "EDGAR",
              mail: "holadenuevo@gmail.com",
              phone: "7223961746",
              nickname: "EDG102"
            };
          } else if (user === '101') {
            resultado = {
              custid: "101",
              customerName: "Sherpa 101",
              firstname: "Sherpa",
              mail: "sherpa101@equipoenaccion.net",
              phone: "5512345101",
              nickname: "SHERPA101"
            };
          } else {
            const cleanDigits = user.replace(/\D/g, '');
            resultado = {
              custid: user,
              customerName: 'Sherpa ' + user,
              firstname: user,
              mail: user + '@equipoenaccion.net',
              phone: cleanDigits.length === 10 ? cleanDigits : ('5512345' + user.padStart(3, '0')),
              nickname: 'SHERPA' + user
            };
          }
        }"""

    fake_profile_new = """        // Demo mode check only if explicitly requested via ?demo=1 URL parameter
        const isDemoParam = window.location.search.includes('demo=1');

        if (!resultado || (!resultado.customerName && !resultado.custid)) {
          if (isDemoParam) {
            console.info('[DEMO] Modo Demostración Activo (?demo=1)');
            resultado = {
              custid: user,
              customerName: 'Usuario Demostración ' + user,
              firstname: 'Demo',
              mail: user + '@demo.equipoenaccion.net',
              phone: '5512345678',
              nickname: 'DEMO' + user
            };
          } else {
            if (submitBtn) { submitBtn.disabled = false; submitBtn.innerHTML = '<i class="fa-solid fa-right-to-bracket mr-2"></i> Iniciar Sesión'; }
            if (errorBox) {
              errorBox.innerHTML = '<i class="fa-solid fa-triangle-exclamation text-red-600 dark:text-red-400 text-sm shrink-0"></i><span>Usuario o contraseña incorrectos.</span>';
              errorBox.className = "w-full p-3.5 bg-red-50 dark:bg-red-950/80 border border-red-300 dark:border-red-800 rounded-2xl text-red-800 dark:text-red-200 text-xs font-bold text-center backdrop-blur-md mb-4 flex items-center justify-center gap-2";
              errorBox.classList.remove('hidden');
            }
            return;
          }
        }"""

    if fake_profile_old in content:
        content = content.replace(fake_profile_old, fake_profile_new)
        print("  - Replaced fake user generator with strict error handling unless ?demo=1")

    # 6. Bump Service Worker to v78
    content = content.replace('sw.js?v=77', 'sw.js?v=78')
    content = content.replace('sw.js?v=76', 'sw.js?v=78')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Done updating {filepath}\n")

def update_sw():
    filepath = 'sw.js'
    print(f"Updating {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace("sinergix-crm-v77", "sinergix-crm-v78")
    content = content.replace("sinergix-crm-v76", "sinergix-crm-v78")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Done updating {filepath}\n")

if __name__ == '__main__':
    update_html('index.html')
    if os.path.exists('static/index.html'):
        update_html('static/index.html')
    if os.path.exists('sw.js'):
        update_sw()
