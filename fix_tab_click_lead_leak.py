import re

def fix_tab_leak(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_cargar_leads_func = """    async function cargarLeadsServidor() {
      try {
        const activeUser = (typeof obtenerSherpaIdActivo === 'function') ? obtenerSherpaIdActivo() : '101';
        const userLeads = (typeof CortexStorageEngine !== 'undefined' && CortexStorageEngine.getLeadsForSherpa)
          ? await CortexStorageEngine.getLeadsForSherpa(activeUser)
          : [];
        todosLosLeads = Array.isArray(userLeads) ? userLeads : [];
        if (typeof renderizarLista === 'function') renderizarLista();
        if (typeof actualizarMetricas === 'function') actualizarMetricas();
      } catch (err) {
        console.warn('Error al cargar leads por sherpa:', err);
      }
    }"""

    # Replace cargarLeadsServidor function
    idx_start = content.find("async function cargarLeadsServidor() {")
    if idx_start != -1:
      idx_end = content.find("const PHONES_MENSAJE_ENVIADO =", idx_start)
      if idx_end != -1:
        content = content[:idx_start] + new_cargar_leads_func.strip() + "\n\n    " + content[idx_end:]

    # Update cambiarPestana agenda branch
    old_agenda_branch = """      } else if (target === 'agenda') {
        if (typeof renderizarLista === 'function') renderizarLista();
        if (typeof cargarLeadsServidor === 'function') cargarLeadsServidor();
      }"""

    new_agenda_branch = """      } else if (target === 'agenda') {
        if (typeof cargarLeadsServidor === 'function') {
          await cargarLeadsServidor();
        } else {
          if (typeof renderizarLista === 'function') renderizarLista();
          if (typeof actualizarMetricas === 'function') actualizarMetricas();
        }
      }"""

    if old_agenda_branch in content:
      content = content.replace(old_agenda_branch, new_agenda_branch)

    # Bump service worker version to v69
    content = content.replace('sw.js?v=68', 'sw.js?v=69')
    content = content.replace('sinergix-crm-v68', 'sinergix-crm-v69')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed tab click lead leak in {file_path}")

fix_tab_leak('index.html')
fix_tab_leak('static/index.html')

# Update sw.js version to v69
with open('sw.js', 'r', encoding='utf-8') as f:
    sw = f.read()

sw = sw.replace('sinergix-crm-v68', 'sinergix-crm-v69')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw)

print("Updated sw.js to v69.")
