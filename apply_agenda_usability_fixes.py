import re

def update_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update obtenerSherpaSesion to check sinergix_sherpa_activo first
    old_obtener_sesion = """    function obtenerSherpaSesion() {
      const activeUser = obtenerSherpaIdActivo();
      const token = localStorage.getItem('sinergix_token') || localStorage.getItem('ea_session') || localStorage.getItem('sherpa_token');
      
      if (!activeUser || !token) {
        return { valido: false, userId: null, nombre: '', celular: '' };
      }

      let nombre = (localStorage.getItem('sherpa_nombre') || '').trim();
      let rawCelular = (localStorage.getItem('sherpa_celular') || '').replace(/\D/g, '');"""

    new_obtener_sesion = """    function obtenerSherpaSesion() {
      const activeUser = obtenerSherpaIdActivo();
      const token = localStorage.getItem('sinergix_token') || localStorage.getItem('ea_session') || localStorage.getItem('sherpa_token');
      
      if (!activeUser || !token) {
        return { valido: false, userId: null, nombre: '', celular: '' };
      }

      let nombre = '';
      let rawCelular = '';

      try {
        const rawActive = localStorage.getItem('sinergix_sherpa_activo');
        if (rawActive) {
          const parsed = JSON.parse(rawActive);
          if (parsed.nombre) nombre = parsed.nombre;
          if (parsed.phone || parsed.telefono || parsed.celular) {
            rawCelular = (parsed.phone || parsed.telefono || parsed.celular).replace(/\\D/g, '');
          }
        }
      } catch(e) {}

      if (!nombre) nombre = (localStorage.getItem('sherpa_nombre') || '').trim();
      if (!rawCelular) rawCelular = (localStorage.getItem('sherpa_celular') || '').replace(/\\D/g, '');"""

    if old_obtener_sesion in content:
        content = content.replace(old_obtener_sesion, new_obtener_sesion)

    # 2. Update actualizarHeaderSherpa to auto-populate input-sherpa-nombre and input-sherpa-celular
    old_header_sherpa = """      if (sherpaSesion && sherpaSesion.nombre) {
        if (elNom) {
          elNom.textContent = sherpaSesion.nombre;
          elNom.className = 'text-emerald-600 dark:text-emerald-400 font-extrabold';
        }
        if (elTel) {
          elTel.textContent = sherpaSesion.telefono ? `(${sherpaSesion.telefono})` : '';
          elTel.className = 'text-slate-600 dark:text-slate-300 font-mono text-xs font-bold';
        }
        if (elSpanHeader) {
          const pNombre = sherpaSesion.primer_nombre || sherpaSesion.nombre.split(',')[0].trim().split(' ')[0];
          elSpanHeader.textContent = `• Sherpa ${pNombre} (ID: ${sherpaSesion.custid || sherpaSesion.id})`;
        }
      }"""

    new_header_sherpa = """      if (sherpaSesion && sherpaSesion.nombre) {
        if (elNom) {
          elNom.textContent = sherpaSesion.nombre;
          elNom.className = 'text-emerald-600 dark:text-emerald-400 font-extrabold';
        }
        if (elTel) {
          elTel.textContent = sherpaSesion.telefono ? `(${sherpaSesion.telefono})` : '';
          elTel.className = 'text-slate-600 dark:text-slate-300 font-mono text-xs font-bold';
        }
        if (elSpanHeader) {
          const pNombre = sherpaSesion.primer_nombre || sherpaSesion.nombre.split(',')[0].trim().split(' ')[0];
          elSpanHeader.textContent = `• Sherpa ${pNombre} (ID: ${sherpaSesion.custid || sherpaSesion.id})`;
        }

        const inpNom = document.getElementById('input-sherpa-nombre');
        const inpCel = document.getElementById('input-sherpa-celular');
        const modalInpNom = document.getElementById('modal-input-sherpa-nombre');
        const modalInpCel = document.getElementById('modal-input-sherpa-celular');

        const cleanPhone = (sherpaSesion.phone || sherpaSesion.telefono || sherpaSesion.celular || '').replace(/\\D/g, '').replace(/^521/, '').replace(/^52/, '');

        if (inpNom) inpNom.value = sherpaSesion.nombre;
        if (inpCel && cleanPhone) inpCel.value = cleanPhone;
        if (modalInpNom) modalInpNom.value = sherpaSesion.nombre;
        if (modalInpCel && cleanPhone) modalInpCel.value = cleanPhone;

        localStorage.setItem('sherpa_nombre', sherpaSesion.nombre);
        if (cleanPhone) localStorage.setItem('sherpa_celular', '521' + cleanPhone);
      }"""

    if old_header_sherpa in content:
        content = content.replace(old_header_sherpa, new_header_sherpa)

    # 3. Add helper functions destacarYabrirModalAgregar & destacarYabrirImportar
    if "function destacarYabrirModalAgregar" not in content:
        target_add = "function abrirModalAgregar() {"
        helper_code = """    function destacarYabrirModalAgregar() {
      const btn = document.getElementById('btn-nuevo-prospecto-main');
      if (btn) {
        btn.classList.add('ring-4', 'ring-emerald-400', 'animate-pulse');
        setTimeout(() => btn.classList.remove('ring-4', 'ring-emerald-400', 'animate-pulse'), 1500);
      }
      abrirModalAgregar();
    }

    function destacarYabrirImportar() {
      const btn = document.getElementById('btn-importar-prospectos-main');
      if (btn) {
        btn.classList.add('ring-4', 'ring-indigo-400', 'animate-pulse');
        setTimeout(() => btn.classList.remove('ring-4', 'ring-indigo-400', 'animate-pulse'), 1500);
      }
      openImportModal();
    }\n\n    """
        content = content.replace(target_add, helper_code + target_add, 1)

    # 4. Enhance empty state HTML in renderizarLista
    old_empty = "contenedor.innerHTML = `<div class=\"col-span-full p-12 text-center text-slate-400 dark:text-slate-500 font-medium text-xs bg-white dark:bg-slate-800 rounded-3xl border border-slate-200 dark:border-slate-700 shadow-clinical-sm\">No hay contactos registrados. Captura tu primer lead o importa un archivo.</div>`;"
    
    new_empty = """contenedor.innerHTML = `
        <div class="col-span-full p-8 sm:p-12 text-center bg-white dark:bg-slate-800 rounded-3xl border border-slate-200 dark:border-slate-700 shadow-clinical-md space-y-5 fade-in">
          <div class="w-16 h-16 mx-auto rounded-3xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-3xl shadow-clinical-sm animate-bounce">
            <i class="fa-solid fa-user-plus"></i>
          </div>
          <div class="max-w-md mx-auto space-y-1.5">
            <h4 class="text-base font-extrabold text-slate-900 dark:text-white">Tu Agenda de Prospectos está Lista</h4>
            <p class="text-xs text-slate-500 dark:text-slate-400 font-medium leading-relaxed">No hay contactos registrados en esta vista. Comienza a construir tu red capturando tu primer prospecto manualmente o importando tu lista de contactos.</p>
          </div>
          <div class="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button onclick="destacarYabrirModalAgregar()" class="touch-target px-5 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold rounded-2xl text-xs shadow-clinical-md flex items-center gap-2 transition transform hover:scale-105 cursor-pointer animate-pulse">
              <i class="fa-solid fa-plus text-sm"></i>
              <span>+ Nuevo Prospecto</span>
            </button>
            <button onclick="destacarYabrirImportar()" class="touch-target px-5 py-3 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-800 dark:text-slate-200 font-bold rounded-2xl text-xs border border-slate-300 dark:border-slate-600 flex items-center gap-2 transition cursor-pointer">
              <i class="fa-solid fa-file-import text-sm text-ea-blue"></i>
              <span>Importar (Google / CSV / VCF)</span>
            </button>
          </div>
        </div>
      `;"""

    if old_empty in content:
        content = content.replace(old_empty, new_empty)

    # 5. Bump SW to v61
    content = content.replace('sw.js?v=60', 'sw.js?v=61')
    content = content.replace('sinergix-crm-v60', 'sinergix-crm-v61')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched {file_path}")

update_html('index.html')
update_html('static/index.html')

# Update sw.js version to v61
with open('sw.js', 'r', encoding='utf-8') as f:
    sw_content = f.read()

sw_content = sw_content.replace('sinergix-crm-v60', 'sinergix-crm-v61')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_content)

print("Updated sw.js to v61.")
