import re

def patch_sidebar(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the sidebar container pattern in vista-agenda
    pattern_sidebar = r'(<!-- Columna Lateral: Filtros & Acciones \(3 Cols\) -->[\s\S]*?<!-- Columna Principal: Grilla de Tarjetas de Prospectos)'

    new_sidebar_html = """<!-- Columna Lateral: Filtros & Acciones (3 Cols) -->
      <div class="lg:col-span-3 space-y-6">
        <section class="bg-white dark:bg-slate-800 rounded-3xl p-5 border border-slate-200 dark:border-slate-700 shadow-clinical-md space-y-4">
          <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-700 pb-3">
            <div>
              <h2 class="text-base font-black text-slate-900 dark:text-white" id="sherpa-name-title">Agenda del Sherpa</h2>
              <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium">Prospección & Encuestas</p>
            </div>
            <span class="text-[10px] font-extrabold uppercase px-2.5 py-1 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 tabular-nums border border-slate-200 dark:border-slate-600 shadow-clinical-sm" id="count-total-leads">Total: 0</span>
          </div>

          <!-- Buscador Primero -->
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
              <i class="fa-solid fa-magnifying-glass text-xs"></i>
            </span>
            <input type="text" id="search-input" oninput="filtrarContactos()" class="w-full pl-9 pr-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-xs font-semibold text-slate-900 dark:text-white focus:outline-none focus:border-ea-blue shadow-clinical-sm transition" placeholder="Buscar por nombre o teléfono...">
          </div>

          <!-- Botones de Acción Principal -->
          <div class="grid grid-cols-1 gap-2">
            <button id="btn-nuevo-prospecto-main" onclick="abrirModalAgregar()" class="touch-target w-full bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold py-2.5 rounded-xl shadow-clinical-sm text-xs flex items-center justify-center transition cursor-pointer">
              <i class="fa-solid fa-user-plus text-xs mr-2"></i> + Nuevo Prospecto
            </button>
            <button id="btn-importar-prospectos-main" onclick="openImportModal()" class="touch-target w-full bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center cursor-pointer hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition">
              <i class="fa-solid fa-cloud-arrow-up text-xs mr-2 text-indigo-600 dark:text-indigo-400"></i> Importar (Google / CSV)
            </button>
          </div>

          <!-- Filtros de Estado Compactos -->
          <div class="space-y-1.5 pt-2 border-t border-slate-100 dark:border-slate-700">
            <p class="text-[10px] font-extrabold uppercase text-slate-400 mb-1">Filtrar por Estado</p>
            <div class="space-y-1 text-xs font-bold">
              <button id="btn-filtro-todos" onclick="filtrarPorEstado('todos')" class="w-full px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-xl border border-slate-200 dark:border-slate-700 flex justify-between items-center transition hover:scale-[1.01]">
                <span class="truncate"><i class="fa-solid fa-list mr-1.5 text-ea-blue"></i> Mostrar Todos</span>
                <span class="text-xs font-black tabular-nums bg-slate-200 dark:bg-slate-700 px-2 py-0.5 rounded-md" id="count-todos">0</span>
              </button>

              <button id="btn-filtro-enviados" onclick="filtrarPorEstado('enviados')" class="w-full px-3 py-1.5 bg-blue-50 dark:bg-blue-950/40 text-ea-blue dark:text-blue-300 rounded-xl border border-blue-200 dark:border-blue-800 flex justify-between items-center transition hover:scale-[1.01]">
                <span class="truncate"><i class="fa-solid fa-paper-plane mr-1.5 text-blue-600 dark:text-blue-400"></i> Mensaje Enviado</span>
                <span class="text-xs font-black tabular-nums bg-blue-100 dark:bg-blue-900/60 px-2 py-0.5 rounded-md" id="count-enviados">0</span>
              </button>

              <button id="btn-filtro-no-enviados" onclick="filtrarPorEstado('no_enviados')" class="w-full px-3 py-1.5 bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 rounded-xl border border-amber-200 dark:border-amber-800 flex justify-between items-center transition hover:scale-[1.01]">
                <span class="truncate"><i class="fa-solid fa-clock mr-1.5 text-amber-600 dark:text-amber-400"></i> Sin Mensaje Enviado</span>
                <span class="text-xs font-black tabular-nums bg-amber-100 dark:bg-amber-900/60 px-2 py-0.5 rounded-md" id="count-no-enviados">0</span>
              </button>

              <button id="btn-filtro-respondieron" onclick="filtrarPorEstado('respondieron')" class="w-full px-3 py-1.5 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 rounded-xl border border-emerald-200 dark:border-emerald-800 flex justify-between items-center transition hover:scale-[1.01]">
                <span class="truncate"><i class="fa-solid fa-circle-check mr-1.5 text-emerald-600 dark:text-emerald-400"></i> Ya Respondieron</span>
                <span class="text-xs font-black tabular-nums bg-emerald-100 dark:bg-emerald-900/60 px-2 py-0.5 rounded-md" id="count-responded">0</span>
              </button>

              <button id="btn-filtro-cancelados" onclick="filtrarPorEstado('cancelados')" class="w-full px-3 py-1.5 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 rounded-xl border border-slate-200 dark:border-slate-600 flex justify-between items-center transition hover:scale-[1.01]">
                <span class="truncate"><i class="fa-solid fa-ban mr-1.5"></i> Cancelados</span>
                <span class="text-xs font-black tabular-nums bg-slate-200 dark:bg-slate-600 px-2 py-0.5 rounded-md" id="count-cancelled">0</span>
              </button>
            </div>
          </div>
        </section>
      </div>

      <!-- Columna Principal: Grilla de Tarjetas de Prospectos"""

    if re.search(pattern_sidebar, content):
        content = re.sub(pattern_sidebar, new_sidebar_html, content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Compact sidebar applied to {file_path}")
    else:
        print(f"Pattern not found in {file_path}")

patch_sidebar('index.html')
patch_sidebar('static/index.html')
