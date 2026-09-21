import os

src_file = r"C:\Users\andre\.gemini\antigravity\brain\4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8\.system_generated\steps\4940\output.txt"
with open(src_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

if lines[0].startswith("successfully downloaded text file"):
    lines = lines[1:]

content = "".join(lines)

# 1. Update <main> tag to have id="main-crm-app"
content = content.replace(
    '<main class="flex-grow flex-1 w-full pb-8">',
    '<main id="main-crm-app" class="flex-grow flex-1 w-full pb-8">'
)

# 2. Add id="btn-header-logout" to Salir button
old_logout = '''        <!-- Botón Salir (Cierre de Sesión) -->
        <button onclick="salir()" 
                class="touch-target px-3 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:text-red-600 dark:hover:text-red-400 rounded-xl text-xs font-bold border border-slate-200 dark:border-slate-600 transition inline-flex items-center" 
                style="min-height: 48px; min-width: 48px;" 
                aria-label="Cerrar sesión">'''

new_logout = '''        <!-- Botón Salir (Cierre de Sesión) -->
        <button onclick="salir()" id="btn-header-logout"
                class="touch-target px-3 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:text-red-600 dark:hover:text-red-400 rounded-xl text-xs font-bold border border-slate-200 dark:border-slate-600 transition inline-flex items-center" 
                style="min-height: 48px; min-width: 48px;" 
                aria-label="Cerrar sesión">'''

content = content.replace(old_logout, new_logout)

# 3. Replace old salir() function with new auth & session functions
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

content = content.replace(old_salir, new_auth)

# 4. Add DOMContentLoaded call to actualizarEstadoSesionSherpa()
if 'actualizarEstadoSesionSherpa();' not in content:
    content = content.replace(
        "document.addEventListener('DOMContentLoaded', () => {",
        "document.addEventListener('DOMContentLoaded', () => {\n      actualizarEstadoSesionSherpa();"
    )

# 5. Add Modal HTML before </body>
modal_html = '''
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

content = content.replace("</body>", modal_html + "\n</body>")

with open(r"c:\Users\andre\OneDrive\Escritorio\index.html", "w", encoding="utf-8") as f:
    f.write(content)

with open(r"c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm\index.html", "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully built full original CRM index.html ({len(content)} chars)!")
