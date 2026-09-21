import os

def fix_file(filepath):
    print(f"Fixing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Fix getLeadsForSherpa targetUser line
    target_old = "const targetUser = String(sherpaId || obtenerSherpaIdActivo() || '101');"
    target_new = "const targetUser = String(sherpaId !== null && sherpaId !== undefined && String(sherpaId).trim() !== '' ? sherpaId : (obtenerSherpaIdActivo() || '')).trim();\n        if (!targetUser) return [];"
    if target_old in content:
        content = content.replace(target_old, target_new)
        print("  - Fixed targetUser fallback in getLeadsForSherpa")
    else:
        print("  - targetUser fallback already fixed or not found")

    # 2. Fix cargarLeadsServidor activeUser line
    cls_old = "const activeUser = (typeof obtenerSherpaIdActivo === 'function') ? obtenerSherpaIdActivo() : '101';"
    cls_new = "const activeUser = (typeof obtenerSherpaIdActivo === 'function') ? obtenerSherpaIdActivo() : '';\n        if (!activeUser) { todosLosLeads = []; if (typeof renderizarLista === 'function') renderizarLista(); return; }"
    if cls_old in content:
        content = content.replace(cls_old, cls_new)
        print("  - Fixed activeUser fallback in cargarLeadsServidor")
    else:
        print("  - activeUser fallback in cargarLeadsServidor already fixed or not found")

    # 3. Fix cargarBriefingMatutino activeUser line
    cbm_old = "const activeUser = (typeof obtenerSherpaIdActivo === 'function') ? obtenerSherpaIdActivo() : (localStorage.getItem('sherpa_id_activo') || 'sherpa_edgar');"
    cbm_new = "const activeUser = (typeof obtenerSherpaIdActivo === 'function') ? obtenerSherpaIdActivo() : '';"
    if cbm_old in content:
        content = content.replace(cbm_old, cbm_new)
        print("  - Fixed activeUser fallback in cargarBriefingMatutino")
    else:
        print("  - activeUser fallback in cargarBriefingMatutino already fixed or not found")

    # 4. Ensure obtenerSherpaIdActivo is updated
    obtener_old = """function obtenerSherpaIdActivo() {
      return localStorage.getItem('sinergix_active_user') || 
             localStorage.getItem('sherpa_id_activo') || 
             '';
    }"""
    obtener_new = """function obtenerSherpaIdActivo() {
      let active = localStorage.getItem('sinergix_active_user') || 
                   localStorage.getItem('sherpa_id_activo');
      if (!active) {
        try {
          const raw = localStorage.getItem('sinergix_sherpa_activo');
          if (raw) {
            const obj = JSON.parse(raw);
            if (obj && (obj.custid || obj.id || obj.usuario || obj.sherpa_id)) {
              active = String(obj.custid || obj.id || obj.usuario || obj.sherpa_id);
            }
          }
        } catch (e) {}
      }
      return active ? String(active).trim() : '';
    }"""
    if obtener_old in content:
        content = content.replace(obtener_old, obtener_new)
        print("  - Fixed obtenerSherpaIdActivo implementation")
    else:
        print("  - obtenerSherpaIdActivo already updated or not found")

    # 5. Fix renderAccionesPrioritarias logic
    rap_old = """function renderAccionesPrioritarias() {
      const list = document.getElementById('briefing-acciones-list');
      if (!list) return;
      const leads = Array.isArray(todosLosLeads) ? todosLosLeads : [];
      
      if (leads.length === 0) {"""
    rap_new = """function renderAccionesPrioritarias() {
      const list = document.getElementById('briefing-acciones-list');
      if (!list) return;
      const activeUser = (typeof obtenerSherpaIdActivo === 'function') ? obtenerSherpaIdActivo() : '';
      const leads = (Array.isArray(todosLosLeads) && activeUser === '101') ? todosLosLeads : [];
      
      if (leads.length === 0 || activeUser !== '101') {"""
    if rap_old in content:
        content = content.replace(rap_old, rap_new)
        print("  - Fixed renderAccionesPrioritarias isolation")
    else:
        print("  - renderAccionesPrioritarias already updated or not found")

    # 6. Bump Service Worker version to v76
    content = content.replace('sw.js?v=75', 'sw.js?v=76')
    content = content.replace('sw.js?v=74', 'sw.js?v=76')
    content = content.replace('sw.js?v=73', 'sw.js?v=76')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Finished {filepath}\n")

def fix_sw():
    filepath = 'sw.js'
    print(f"Fixing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace("sinergix-crm-v75", "sinergix-crm-v76")
    content = content.replace("sinergix-crm-v74", "sinergix-crm-v76")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Finished {filepath}\n")

if __name__ == '__main__':
    fix_file('index.html')
    if os.path.exists('static/index.html'):
        fix_file('static/index.html')
    if os.path.exists('sw.js'):
        fix_sw()
