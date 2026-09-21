import os

def update_file(filepath):
    print(f"Updating {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace esContactoSemilla101 function block
    old_es_semilla = """function esContactoSemilla101(lead) {
      if (!lead) return false;
      const idStr = String(lead.id || lead._id || '');
      if (idStr.startsWith('lead_101_')) return true;
      const owner = String(lead.sherpa_id || lead.sherpa_user || '');
      if (owner === '101') return true;
      const nom = (lead.nombre || '').toLowerCase().trim();
      const seedNames = ['aldair', 'angelina', 'gonzalo', 'martha', 'jose luis', 'margarito', 'javier', 'mauricio', 'ramon', 'elia', 'adela', 'jeronimo', 'alejandro', 'guadalupe', 'yoselin', 'ana velia', 'angela', 'cristina', 'antonio', 'brenda', 'gertrudis', 'fidela', 'carmen', 'enrique', 'fernando', 'dionicio', 'arely', 'emanuel', 'estela', 'catalina', 'maribel', 'fatima', 'felipa', 'emma', 'rosa', 'hermila', 'ignacia', 'crisanta', 'abraham', 'rufina', 'aida', 'amalia', 'balvina', 'juan', 'claudia', 'elena', 'elvia', 'eusebia', 'fidencio', 'laurentino', 'leoba', 'leticia', 'lilian', 'gema', 'jose', 'josefa', 'luz', 'rosario', 'evelia', 'margarito', 'marina', 'ocotlan', 'rene', 'virginia', 'yolanda', 'olga', 'saray', 'soledad', 'yamilet'];
      if (seedNames.some(sn => nom.includes(sn))) return true;
      return false;
    }"""

    new_es_semilla = """// Set de teléfonos y nombres semilla del Usuario 101 para desinfección total de IndexedDB
    const SEED_101_PHONES_SET = new Set((typeof CARTERA_USER_101_SEED !== 'undefined' ? CARTERA_USER_101_SEED : []).map(l => String(l.telefono || '').replace(/\\D/g, '').slice(-10)).filter(Boolean));
    const SEED_101_NAMES_SET = new Set((typeof CARTERA_USER_101_SEED !== 'undefined' ? CARTERA_USER_101_SEED : []).map(l => String(l.nombre || '').toLowerCase().trim()).filter(Boolean));

    function esContactoSemilla101(lead) {
      if (!lead) return false;
      const idStr = String(lead.id || lead._id || '');
      if (idStr.startsWith('lead_101_')) return true;
      const owner = String(lead.sherpa_id || lead.sherpa_user || '');
      if (owner === '101') return true;
      const tel10 = String(lead.telefono || '').replace(/\\D/g, '').slice(-10);
      if (tel10 && SEED_101_PHONES_SET.has(tel10)) return true;
      const nomNorm = (lead.nombre || '').toLowerCase().trim();
      if (nomNorm && SEED_101_NAMES_SET.has(nomNorm)) return true;
      const seedNames = ['aldair', 'angelina', 'gonzalo', 'martha', 'jose luis', 'margarito', 'javier', 'mauricio', 'ramon', 'elia', 'adela', 'jeronimo', 'alejandro', 'guadalupe', 'yoselin', 'ana velia', 'angela', 'cristina', 'antonio', 'brenda', 'gertrudis', 'fidela', 'carmen', 'enrique', 'fernando', 'dionicio', 'arely', 'emanuel', 'estela', 'catalina', 'maribel', 'fatima', 'felipa', 'emma', 'rosa', 'hermila', 'ignacia', 'crisanta', 'abraham', 'rufina', 'aida', 'amalia', 'balvina', 'juan', 'claudia', 'elena', 'elvia', 'eusebia', 'fidencio', 'laurentino', 'leoba', 'leticia', 'lilian', 'gema', 'jose', 'josefa', 'luz', 'rosario', 'evelia', 'margarito', 'marina', 'ocotlan', 'rene', 'virginia', 'yolanda', 'olga', 'saray', 'soledad', 'yamilet', 'tania', 'margarita', 'lourdez', 'lourdes', 'adriana', 'candelaria', 'martina', 'honorina', 'alba', 'maria', 'ana lilia'];
      if (seedNames.some(sn => nomNorm.includes(sn))) return true;
      return false;
    }"""

    if old_es_semilla in content:
        content = content.replace(old_es_semilla, new_es_semilla)
        print("  - Updated esContactoSemilla101 with dynamic phone & name Sets")
    else:
        print("  - esContactoSemilla101 pattern not found or already updated")

    # 2. Update filter condition in getLeadsForSherpa
    old_filter = "const userLeads = all.filter(l => !esContactoSemilla101(l) && (String(l.sherpa_id) === targetUser || String(l.sherpa_user) === targetUser));"
    new_filter = "const userLeads = all.filter(l => !esContactoSemilla101(l) && String(l.sherpa_id) === targetUser);"
    if old_filter in content:
        content = content.replace(old_filter, new_filter)
        print("  - Updated getLeadsForSherpa filter")

    # 3. Bump Service Worker version to v77
    content = content.replace('sw.js?v=76', 'sw.js?v=77')
    content = content.replace('sw.js?v=75', 'sw.js?v=77')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Finished {filepath}\n")

def update_sw():
    filepath = 'sw.js'
    print(f"Updating {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace("sinergix-crm-v76", "sinergix-crm-v77")
    content = content.replace("sinergix-crm-v75", "sinergix-crm-v77")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Finished {filepath}\n")

if __name__ == '__main__':
    update_file('index.html')
    if os.path.exists('static/index.html'):
        update_file('static/index.html')
    if os.path.exists('sw.js'):
        update_sw()
