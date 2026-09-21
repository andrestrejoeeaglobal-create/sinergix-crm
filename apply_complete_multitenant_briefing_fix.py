import os
import re

def update_file(filepath):
    print(f"Updating {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update obtenerSherpaIdActivo
    old_obtener = r'function obtenerSherpaIdActivo\(\)\s*\{[\s\S]*?return localStorage\.getItem\(\'sinergix_active_user\'\) \|\|[\s\S]*?\'\';\s*\}'
    new_obtener = '''function obtenerSherpaIdActivo() {
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
    }'''

    content = re.sub(old_obtener, new_obtener, content)

    # 2. Update CortexStorageEngine.getLeadsForSherpa targetUser check
    old_target = r'const targetUser = String\(sherpaId \|\| obtenerSherpaIdActivo\(\) \|\| \'101\'\);'
    new_target = "const targetUser = String(sherpaId !== null && sherpaId !== undefined && String(sherpaId).trim() !== '' ? sherpaId : (obtenerSherpaIdActivo() || '')).trim();\n        if (!targetUser) return [];"
    content = content.replace(old_target, new_target)

    # 3. Update cargarLeadsServidor fallback
    old_cls = r'const activeUser = \(typeof obtenerSherpaIdActivo === \'function\'\) \? obtenerSherpaIdActivo\(\) : \'101\';'
    new_cls = "const activeUser = (typeof obtenerSherpaIdActivo === 'function') ? obtenerSherpaIdActivo() : '';"
    content = content.replace(old_cls, new_cls)

    # 4. Update cargarBriefingMatutino fallback
    old_cbm = r'const activeUser = \(typeof obtenerSherpaIdActivo === \'function\'\) \? obtenerSherpaIdActivo\(\) : \(localStorage\.getItem\(\'sherpa_id_activo\'\) \|\| \'sherpa_edgar\'\);'
    new_cbm = "const activeUser = (typeof obtenerSherpaIdActivo === 'function') ? obtenerSherpaIdActivo() : '';"
    content = content.replace(old_cbm, new_cbm)

    # 5. Update renderAccionesPrioritarias logic
    old_rap = r'function renderAccionesPrioritarias\(\)\s*\{[\s\S]*?if \(leads\.length === 0\) \{'
    new_rap = '''function renderAccionesPrioritarias() {
      const list = document.getElementById('briefing-acciones-list');
      if (!list) return;
      const activeUser = (typeof obtenerSherpaIdActivo === 'function') ? obtenerSherpaIdActivo() : '';
      const leads = (Array.isArray(todosLosLeads) && activeUser === '101') ? todosLosLeads : [];
      
      if (leads.length === 0 || activeUser !== '101') {'''
    content = re.sub(old_rap, new_rap, content)

    # 6. Bump sw.js version in html
    content = content.replace('sw.js?v=74', 'sw.js?v=75')
    content = content.replace('sw.js?v=73', 'sw.js?v=75')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Done updating {filepath}")

def update_sw():
    filepath = 'sw.js'
    print(f"Updating {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r"const CACHE_NAME = 'sinergix-crm-v\d+';", "const CACHE_NAME = 'sinergix-crm-v75';", content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Done updating {filepath}")

if __name__ == '__main__':
    update_file('index.html')
    if os.path.exists('static/index.html'):
        update_file('static/index.html')
    if os.path.exists('sw.js'):
        update_sw()
