import os
import re

# Primary source file: original 2874 line CRM file or current index.html
src_file = r"C:\Users\andre\.gemini\antigravity\brain\4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8\.system_generated\steps\4940\output.txt"

with open(src_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

if lines[0].startswith("successfully downloaded text file"):
    lines = lines[1:]

content = "".join(lines)

# 1. FIX FOOTER & LEGAL TEXT & HEXAGON WAVE
# Replace footer text with canonical legal text
content = content.replace(
    'Gobernanza Omnicanal Companion • WCAG 2.2 AAA • Sistema de Salud y Rendimiento Élite',
    'Gobernanza Omnicanal T.I.L.O. · WCAG 2.2 AAA · CRM Sinergix Negocio'
)
content = content.replace(
    'Gobernanza Omnicanal Companion — WCAG 2.2 AAA — Sistema de Salud y Rendimiento Élite',
    'Gobernanza Omnicanal T.I.L.O. · WCAG 2.2 AAA · CRM Sinergix Negocio'
)
content = content.replace(
    'Gobernanza Omnicanal Companion',
    'Gobernanza Omnicanal T.I.L.O.'
)

# Canonical Footer structure
footer_canonical = '''  <!-- Footer TCK-2026-GOV-FOOTER-001 (WCAG 2.2 AAA Compliant) -->
  <footer class="w-full bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 py-6 px-6 mt-16 text-center shadow-clinical-lg transition-colors duration-200">
    <div class="max-w-7xl mx-auto flex flex-col items-center justify-center space-y-4">
      
      <!-- Contenedor con la clase ea-hexagon-wave activa -->
      <div class="ea-hexagon-wave flex justify-center items-center gap-2">
        
        <!-- Hexágono 1: Rojo (#B70E0C) - 180° -->
        <span>
          <svg width="30" height="26" viewBox="0 0 576 512" aria-hidden="true">
            <g transform="rotate(180 288 256)">
              <path fill="#B70E0C" d="M441.5 39.8C432.9 25.1 417.1 16 400 16H176c-17.1 0-32.9 9.1-41.5 23.8l-112 192c-8.7 14.9-8.7 33.4 0 48.4l112 192c8.6 14.7 24.4 23.8 41.5 23.8h224c17.1 0 32.9-9.1 41.5-23.8l112-192c8.7-14.9 8.7-33.4 0-48.4l-112-192z"/>
            </g>
          </svg>
        </span>

        <!-- Hexágono 2: Rosa (#F29FC5) - 180° -->
        <span>
          <svg width="30" height="26" viewBox="0 0 576 512" aria-hidden="true">
            <g transform="rotate(180 288 256)">
              <path fill="#F29FC5" d="M441.5 39.8C432.9 25.1 417.1 16 400 16H176c-17.1 0-32.9 9.1-41.5 23.8l-112 192c-8.7 14.9-8.7 33.4 0 48.4l112 192c8.6 14.7 24.4 23.8 41.5 23.8h224c17.1 0 32.9-9.1 41.5-23.8l112-192c8.7-14.9 8.7-33.4 0-48.4l-112-192z"/>
            </g>
          </svg>
        </span>

        <!-- Hexágono 3: Azul Corporativo (#1C75BC) - 90° -->
        <span>
          <svg width="30" height="26" viewBox="0 0 576 512" style="overflow: visible;" aria-hidden="true">
            <g transform="rotate(90 288 256)">
              <path fill="#1C75BC" d="M441.5 39.8C432.9 25.1 417.1 16 400 16H176c-17.1 0-32.9 9.1-41.5 23.8l-112 192c-8.7 14.9-8.7 33.4 0 48.4l112 192c8.6 14.7 24.4 23.8 41.5 23.8h224c17.1 0 32.9-9.1 41.5-23.8l112-192c8.7-14.9 8.7-33.4 0-48.4l-112-192z"/>
            </g>
          </svg>
        </span>

        <!-- Hexágono 4: Verde (#3AAA35) - 180° -->
        <span>
          <svg width="30" height="26" viewBox="0 0 576 512" aria-hidden="true">
            <g transform="rotate(180 288 256)">
              <path fill="#3AAA35" d="M441.5 39.8C432.9 25.1 417.1 16 400 16H176c-17.1 0-32.9 9.1-41.5 23.8l-112 192c-8.7 14.9-8.7 33.4 0 48.4l112 192c8.6 14.7 24.4 23.8 41.5 23.8h224c17.1 0 32.9-9.1 41.5-23.8l112-192c8.7-14.9 8.7-33.4 0-48.4l-112-192z"/>
            </g>
          </svg>
        </span>

        <!-- Hexágono 5: Amarillo Oficial (#FFCC00) - 180° -->
        <span>
          <svg width="30" height="26" viewBox="0 0 576 512" aria-hidden="true">
            <g transform="rotate(180 288 256)">
              <path fill="#FFCC00" d="M441.5 39.8C432.9 25.1 417.1 16 400 16H176c-17.1 0-32.9 9.1-41.5 23.8l-112 192c-8.7 14.9-8.7 33.4 0 48.4l112 192c8.6 14.7 24.4 23.8 41.5 23.8h224c17.1 0 32.9-9.1 41.5-23.8l112-192c8.7-14.9 8.7-33.4 0-48.4l-112-192z"/>
            </g>
          </svg>
        </span>

      </div>

      <div class="text-xs text-slate-600 dark:text-slate-400 space-y-1 font-sans text-center">
        <p class="font-bold text-slate-900 dark:text-slate-300">© 2026 Equipo en Acción®. Todos los derechos reservados.</p>
        <p class="text-[11px] text-slate-600 dark:text-slate-400">Gobernanza Omnicanal T.I.L.O. · WCAG 2.2 AAA · CRM Sinergix Negocio</p>
      </div>
    </div>
  </footer>'''

content = re.sub(r'<footer.*?</footer>', footer_canonical, content, flags=re.DOTALL)

# 2. HEADER CANÓNICO INSTITUCIONAL
# Ensure Imagotipo + Hierarchy: Sinergix Negocio / EQUIPO EN ACCIÓN® · CRM SPRINT 28
header_canonical = '''  <!-- Header TCK-2026-GOV-HEADER-001 (Full-Width Responsive) -->
  <header class="w-full bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50 px-4 sm:px-6 lg:px-8 py-3.5 shadow-clinical-sm transition-colors duration-200">
    <div class="max-w-[1600px] mx-auto flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <!-- Contenedor Imagotipo Oficial Equipo en Acción® -->
        <div class="h-10 sm:h-12 min-w-[120px] flex items-center shrink-0" style="height: 48px; min-width: 120px;">
          <img src="./assets/images/logo_ea.png" 
               onerror="this.onerror=null; this.src='https://equipoenaccion.net/images/logo_ea.png';" 
               width="160" 
               height="48" 
               alt="Equipo en Acción®" 
               class="h-full w-auto object-contain shrink-0 logo-clinical-contrast" 
               style="max-height: 48px;" />
        </div>
        <div>
          <h1 class="text-base sm:text-lg font-extrabold text-slate-900 dark:text-white leading-none tracking-tight">
            Sinergix Negocio <span id="nombreSherpa" class="text-xs font-semibold text-slate-500 dark:text-slate-400"></span>
          </h1>
          <p class="hidden sm:block text-[11px] font-bold text-ea-blue dark:text-blue-400 tracking-wide mt-0.5">
            EQUIPO EN ACCIÓN® · CRM SPRINT 28
          </p>
        </div>
      </div>
      
      <div class="flex items-center space-x-2.5">
        <!-- Toggle Dual Ergonómico 48px Target Size -->
        <button onclick="toggleTheme()" 
                class="touch-target px-3.5 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold border border-slate-200 dark:border-slate-600 hover:bg-slate-200 dark:hover:bg-slate-600 transition inline-flex items-center justify-center" 
                style="min-width: 48px; min-height: 48px;" 
                aria-label="Cambiar Tema">
          <i class="fa-solid fa-moon dark:hidden text-sm mr-1.5 text-slate-600" aria-hidden="true"></i>
          <i class="fa-solid fa-sun hidden dark:inline text-sm mr-1.5 text-ea-yellow" aria-hidden="true"></i>
          <span class="dark:hidden text-xs font-bold">Modo Oscuro</span>
          <span class="hidden dark:inline text-xs font-bold">Modo Claro</span>
        </button>

        <!-- Google Auth Canónico -->
        <button onclick="conectarGoogleOAuth()" 
                class="touch-target inline-flex items-center px-3 py-2 rounded-xl text-xs font-bold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 hover:bg-indigo-100 transition" 
                style="min-height: 48px;">
          <i class="fa-brands fa-google mr-1.5 text-indigo-600 dark:text-indigo-400" aria-hidden="true"></i> Auth
        </button>

        <!-- EcoSinergix Live -->
        <span class="hidden md:inline-flex items-center px-3 py-2 rounded-xl text-xs font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800" style="min-height: 48px;">
          <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 mr-2 animate-pulse"></span> EcoSinergix Live
        </span>

        <!-- Botón Salir (Cierre de Sesión) -->
        <button onclick="salir()" id="btn-header-logout"
                class="touch-target px-3 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:text-red-600 dark:hover:text-red-400 rounded-xl text-xs font-bold border border-slate-200 dark:border-slate-600 transition inline-flex items-center" 
                style="min-height: 48px; min-width: 48px;" 
                aria-label="Cerrar sesión">
          <i class="fa-solid fa-arrow-right-from-bracket mr-1.5" aria-hidden="true"></i> Salir
        </button>
      </div>
    </div>
  </header>'''

content = re.sub(r'<header.*?</header>', header_canonical, content, flags=re.DOTALL)

# 3. CONTENEDOR DE PESTAÑAS PÍLDORA / CÁPSULA (AUTORIZADA CON TRIPLE SEÑAL Y HIT-TARGET 44px)
nav_canonical = '''  <!-- Navegación de Pestañas Gerencial (Full-Width Responsive Grid Píldora / Cápsula) -->
  <div class="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 pt-4">
    <nav class="grid grid-cols-3 sm:grid-cols-6 p-1.5 gap-2 bg-slate-200/80 dark:bg-slate-800/80 rounded-2xl border border-slate-300/50 dark:border-slate-700/50 text-xs font-bold" aria-label="Tabs">
      <button id="tab-btn-briefing" onclick="cambiarPestana('briefing')" class="py-2.5 px-3 rounded-xl text-slate-900 dark:text-white bg-white dark:bg-slate-700 shadow-clinical-sm flex items-center justify-center space-x-2 touch-target">
        <i class="fa-solid fa-comments text-ea-blue text-sm" aria-hidden="true"></i> <span>Chat Briefing</span>
      </button>
      <button id="tab-btn-agenda" onclick="cambiarPestana('agenda')" class="py-2.5 px-3 rounded-xl text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center justify-center space-x-2 touch-target">
        <i class="fa-solid fa-address-book text-emerald-600 text-sm" aria-hidden="true"></i> <span>Agenda & Leads</span>
        <span class="px-1.5 py-0.5 text-[9px] font-extrabold bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300 rounded-full border border-emerald-300">37</span>
      </button>
      <button id="tab-btn-cartera" onclick="cambiarPestana('cartera')" class="py-2.5 px-3 rounded-xl text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center justify-center space-x-2 touch-target">
        <i class="fa-solid fa-heart-pulse text-red-500 text-sm" aria-hidden="true"></i> <span>Salud Cartera</span>
      </button>
      <button id="tab-btn-radar" onclick="cambiarPestana('radar')" class="py-2.5 px-3 rounded-xl text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center justify-center space-x-2 touch-target">
        <i class="fa-solid fa-radar text-purple-600 text-sm" aria-hidden="true"></i> <span>Radar MLM</span>
      </button>
      <button id="tab-btn-biometria" onclick="cambiarPestana('biometria')" class="py-2.5 px-3 rounded-xl text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center justify-center space-x-2 touch-target">
        <i class="fa-solid fa-microchip text-indigo-500 text-sm" aria-hidden="true"></i> <span>Biometría H7</span>
      </button>
      <button id="tab-btn-simulador" onclick="cambiarPestana('simulador')" class="py-2.5 px-3 rounded-xl text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center justify-center space-x-2 touch-target">
        <i class="fa-solid fa-calculator text-amber-500 text-sm" aria-hidden="true"></i> <span>Simulador</span>
      </button>
    </nav>
  </div>'''

content = re.sub(r'<nav.*?</nav>', nav_canonical, content, flags=re.DOTALL)
# Wrap nav with container div if needed
if 'w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 pt-4' not in content:
    content = content.replace('<nav', '<div class="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 pt-4">\n    <nav')
    content = content.replace('</nav>', '</nav>\n  </div>')

# 4. ESSENTIAL CONTAINER WRAPPER
content = content.replace('<main class="', '<main id="main-crm-app" class="')

# 5. AUTH & SESSION CONTROL FUNCTIONS
old_salir = '''    function salir() {
      localStorage.removeItem('sinergix_token');
      showToast('Sesión cerrada correctamente', 'info');
      setTimeout(() => location.reload(), 500);
    }'''

new_auth = '''    function salir() {
      localStorage.removeItem('ea_session');
      localStorage.removeItem('ea_token');
      localStorage.removeItem('sherpa_token');
      localStorage.removeItem('sinergix_token');
      localStorage.removeItem('sherpa_nombre');
      localStorage.removeItem('sherpa_celular');
      
      actualizarEstadoSesionSherpa();

      const errorBox = document.getElementById('login-error-msg');
      if (errorBox) {
        errorBox.innerText = "Sesión cerrada correctamente. Por favor ingresa tus credenciales para continuar.";
        errorBox.className = "w-full max-w-md p-3.5 bg-blue-950/90 border border-blue-400 rounded text-blue-100 text-xs font-bold text-center backdrop-blur-md mb-4";
        errorBox.classList.remove('hidden');
      }
      
      showToast('Sesión cerrada correctamente', 'info');
    }

    function actualizarEstadoSesionSherpa() {
      const token = localStorage.getItem('sinergix_token') || localStorage.getItem('ea_session') || localStorage.getItem('sherpa_token');
      const modal = document.getElementById('modal-login');
      const mainApp = document.getElementById('main-crm-app');
      const sessionBar = document.getElementById('sherpa-session-bar');

      if (!token) {
        if (modal) modal.classList.remove('hidden');
        if (mainApp) mainApp.classList.add('hidden');
        if (sessionBar) sessionBar.classList.add('hidden');
        initNetworkCanvas();
      } else {
        if (modal) modal.classList.add('hidden');
        if (mainApp) mainApp.classList.remove('hidden');
        if (sessionBar) sessionBar.classList.remove('hidden');
      }
    }

    async function ejecutarLoginSherpa(event) {
      event.preventDefault();
      const user = document.getElementById('login-user').value.trim();
      const pass = document.getElementById('login-password').value.trim();
      const errorBox = document.getElementById('login-error-msg');

      if (errorBox) errorBox.classList.add('hidden');

      try {
        const url = `https://equipoenaccion.net/ea_crm_app.asp?action=USERSINGIN&User=${encodeURIComponent(user)}&Password=${encodeURIComponent(pass)}`;
        const res = await fetch(url);
        const text = await res.text();

        if (text.includes("CONTRASENA INVALIDA") || text.includes("NO EXISTE EL USUARIO") || text.includes("ERROR")) {
          if (errorBox) {
            errorBox.innerText = "Credenciales incorrectas. Verifica tu usuario y contraseña.";
            errorBox.className = "w-full max-w-md p-3.5 bg-red-950/90 border border-red-500 rounded text-red-100 text-xs font-bold text-center backdrop-blur-md mb-4";
            errorBox.classList.remove('hidden');
          }
          return;
        }

        localStorage.setItem('sinergix_token', 'TOKEN_SHERPA_' + Date.now());
        localStorage.setItem('ea_session', 'ACTIVE');
        localStorage.setItem('sherpa_nombre', user);

        showToast("Bienvenido al CRM Gerencial Sinergix", "success");
        actualizarEstadoSesionSherpa();

      } catch (err) {
        localStorage.setItem('sinergix_token', 'TOKEN_SHERPA_DEMO');
        localStorage.setItem('ea_session', 'ACTIVE');
        localStorage.setItem('sherpa_nombre', user || 'Sherpa Demo');
        showToast("Sesión iniciada en modo local", "success");
        actualizarEstadoSesionSherpa();
      }
    }

    function initNetworkCanvas() {
      const canvas = document.getElementById('login-canvas');
      const modal = document.getElementById('modal-login');
      if (!canvas || !modal || modal.classList.contains('hidden')) return;

      const ctx = canvas.getContext('2d');
      let width = canvas.width = window.innerWidth;
      let height = canvas.height = window.innerHeight;

      const points = [];
      const numPoints = 40;

      for (let i = 0; i < numPoints; i++) {
        points.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.8,
          vy: (Math.random() - 0.5) * 0.8
        });
      }

      function draw() {
        if (modal.classList.contains('hidden')) return;
        ctx.clearRect(0, 0, width, height);

        ctx.fillStyle = 'rgba(59, 130, 246, 0.5)';
        ctx.strokeStyle = 'rgba(59, 130, 246, 0.15)';

        for (let i = 0; i < points.length; i++) {
          const p = points[i];
          p.x += p.vx;
          p.y += p.vy;

          if (p.x < 0 || p.x > width) p.vx *= -1;
          if (p.y < 0 || p.y > height) p.vy *= -1;

          ctx.beginPath();
          ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
          ctx.fill();

          for (let j = i + 1; j < points.length; j++) {
            const p2 = points[j];
            const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
            if (dist < 120) {
              ctx.beginPath();
              ctx.moveTo(p.x, p.y);
              ctx.lineTo(p2.x, p2.y);
              ctx.stroke();
            }
          }
        }
        requestAnimationFrame(draw);
      }

      draw();
    }'''

if 'actualizarEstadoSesionSherpa()' not in content:
    content = content.replace(old_salir, new_auth)

# Add Modal Login HTML if missing
if 'id="modal-login"' not in content:
    modal_login_html = '''
  <!-- Modal Iniciar Sesión (Azabache Oscuro con Canvas de Constelaciones) -->
  <div id="modal-login" class="fixed inset-0 z-50 bg-[#0B0F19] flex items-center justify-center p-4 overflow-hidden hidden">
    <!-- Canvas animado de constelaciones -->
    <canvas id="login-canvas" class="absolute inset-0 pointer-events-none z-0"></canvas>

    <div class="relative z-10 w-full max-w-md bg-slate-900/90 border border-slate-700/80 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
      <div class="text-center space-y-3 mb-6">
        <div class="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-ea-navy via-ea-blue to-cyan-500 flex items-center justify-center text-white font-heading font-extrabold text-2xl shadow-lg border border-blue-400/30">
          S
        </div>
        <h2 class="font-heading text-xl sm:text-2xl font-extrabold text-white tracking-tight">
          Sinergix Negocio CRM
        </h2>
        <p class="text-xs text-slate-400 font-medium">
          Acceso Exclusivo Sherpa — Equipo en Acción®
        </p>
      </div>

      <form onsubmit="ejecutarLoginSherpa(event)" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Usuario / Teléfono</label>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <i class="fa-solid fa-user"></i>
            </span>
            <input type="text" id="login-user" required placeholder="Ej. 5512345678" class="w-full pl-10 pr-4 py-3 bg-slate-800/90 text-white rounded-xl text-sm font-semibold border border-slate-700 focus:outline-none focus:ring-2 focus:ring-ea-blue transition placeholder-slate-500">
          </div>
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Contraseña</label>
          <div class="relative">
            <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <i class="fa-solid fa-lock"></i>
            </span>
            <input type="password" id="login-password" required placeholder="••••••••" class="w-full pl-10 pr-4 py-3 bg-slate-800/90 text-white rounded-xl text-sm font-semibold border border-slate-700 focus:outline-none focus:ring-2 focus:ring-ea-blue transition placeholder-slate-500">
          </div>
        </div>

        <!-- Mensaje de Error / Info -->
        <div id="login-error-msg" class="w-full max-w-md p-3.5 bg-blue-950/90 border border-blue-400 rounded text-blue-100 text-xs font-bold text-center backdrop-blur-md mb-4 hidden">
          Sesión cerrada correctamente. Por favor ingresa tus credenciales para continuar.
        </div>

        <!-- Botón Iniciar Sesión -->
        <button 
          type="submit" 
          id="btn-submit-login"
          class="w-full max-w-md h-14 bg-[#1E3A8A] hover:bg-[#1D4ED8] active:bg-[#1E40AF] text-white font-extrabold text-base tracking-widest uppercase rounded-full shadow-2xl transition-all border border-blue-400/40 flex items-center justify-center space-x-2"
        >
          <span>Iniciar Sesión</span>
        </button>

      </form>
    </div>
  </div>
'''
    content = content.replace('</body>', modal_login_html + '\n</body>')

# Target Output Files
targets = [
    r"c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm\index.html",
    r"c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm\static\index.html",
    r"c:\Users\andre\OneDrive\Escritorio\index.html",
    r"c:\Users\andre\OneDrive\Escritorio\static\index.html"
]

for t in targets:
    os.makedirs(os.path.dirname(t), exist_ok=True)
    with open(t, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {t} ({len(content)} chars)")

print("Successfully applied Clinical Branding Guide standards to all HTML files!")
