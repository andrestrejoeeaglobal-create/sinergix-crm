import re
import subprocess
import os

def update_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_helper_and_get_leads = """    function esContactoSemilla101(lead) {
      if (!lead) return false;
      const idStr = String(lead.id || lead._id || '');
      if (idStr.startsWith('lead_101_')) return true;
      const owner = String(lead.sherpa_id || lead.sherpa_user || '');
      if (owner === '101') return true;
      const nom = (lead.nombre || '').toLowerCase().trim();
      const seedNames = ['aldair', 'angelina', 'gonzalo', 'martha', 'jose luis', 'margarito', 'javier', 'mauricio', 'ramon', 'elia', 'adela', 'jeronimo', 'alejandro', 'guadalupe', 'yoselin', 'ana velia', 'angela', 'cristina', 'antonio', 'brenda', 'gertrudis', 'fidela', 'carmen', 'enrique', 'fernando', 'dionicio', 'arely', 'emanuel', 'estela', 'catalina', 'maribel', 'fatima', 'felipa', 'emma', 'rosa', 'hermila', 'ignacia', 'crisanta', 'abraham', 'rufina', 'aida', 'amalia', 'balvina', 'juan', 'claudia', 'elena', 'elvia', 'eusebia', 'fidencio', 'laurentino', 'leoba', 'leticia', 'lilian', 'gema', 'jose', 'josefa', 'luz', 'rosario', 'evelia', 'margarito', 'marina', 'ocotlan', 'rene', 'virginia', 'yolanda', 'olga', 'saray', 'soledad', 'yamilet'];
      if (seedNames.some(sn => nom.includes(sn))) return true;
      return false;
    }

    const CortexStorageEngine = {
      dbName: 'SinergixCRMDB',
      dbVersion: 1,
      db: null,

      async init() {
        return new Promise((resolve) => {
          const request = indexedDB.open(this.dbName, this.dbVersion);
          request.onupgradeneeded = (evt) => {
            const db = evt.target.result;
            if (!db.objectStoreNames.contains('leads')) {
              db.createObjectStore('leads', { keyPath: 'id' });
            }
          };
          request.onsuccess = (evt) => {
            this.db = evt.target.result;
            resolve(true);
          };
          request.onerror = () => {
            resolve(false);
          };
        });
      },

      async getAllLeads() {
        let allLeads = [];
        if (this.db) {
          allLeads = await new Promise((resolve) => {
            const tx = this.db.transaction('leads', 'readonly');
            const store = tx.objectStore('leads');
            const req = store.getAll();
            req.onsuccess = () => resolve(req.result || []);
            req.onerror = () => resolve(this._getLocalStorageLeads());
          });
        } else {
          allLeads = this._getLocalStorageLeads();
        }
        return allLeads;
      },

      async getLeadsForSherpa(sherpaId = null) {
        const targetUser = String(sherpaId || obtenerSherpaIdActivo() || '101');
        let all = await this.getAllLeads();

        // Sanitize IndexedDB records: ensure 101 seed contacts are tagged strictly as sherpa_id = '101'
        let changed = false;
        all.forEach(l => {
          if (esContactoSemilla101(l)) {
            if (l.sherpa_id !== '101' || l.sherpa_user !== '101') {
              l.sherpa_id = '101';
              l.sherpa_user = '101';
              changed = true;
            }
          }
        });
        if (changed && typeof this.saveAllLeads === 'function') {
          await this.saveAllLeads(all);
        }

        // STRICT ISOLATION RULE:
        // ONLY User 101 owns the 126 seed contacts.
        // User 102 (Edgar Arturo), User 136 (Luis Fernando), and all other users start with 0 contacts.
        if (targetUser !== '101') {
          const userLeads = all.filter(l => !esContactoSemilla101(l) && (String(l.sherpa_id) === targetUser || String(l.sherpa_user) === targetUser));
          return userLeads;
        }

        let userLeads = all.filter(l => esContactoSemilla101(l) || String(l.sherpa_id) === '101' || String(l.sherpa_user) === '101');

        if (userLeads.length === 0) {
          const seeded = CARTERA_USER_101_SEED.map((l, idx) => ({
            ...l,
            id: `lead_101_${idx + 1}`,
            _id: `lead_101_${idx + 1}`,
            sherpa_id: '101',
            sherpa_user: '101'
          }));
          const non101Leads = all.filter(l => !esContactoSemilla101(l));
          await this.saveAllLeads([...non101Leads, ...seeded]);
          userLeads = seeded;
        }

        return userLeads;
      },"""

    idx_start = content.find("const CortexStorageEngine = {")
    if idx_start != -1:
        # Check if esContactoSemilla101 is already present before
        idx_pila = content.rfind("function formatearNombreNatural", 0, idx_start)
        idx_end_get = content.find("async saveLead(lead) {", idx_start)
        if idx_end_get != -1:
            content = content[:idx_start] + new_helper_and_get_leads.strip() + "\n\n      " + content[idx_end_get:]

    # Bump service worker version to v74
    content = content.replace('sw.js?v=73', 'sw.js?v=74')
    content = content.replace('sinergix-crm-v73', 'sinergix-crm-v74')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Applied bulletproof multi-tenant sanitization to {file_path}")

update_file('index.html')
update_file('static/index.html')

# Update sw.js version to v74
with open('sw.js', 'r', encoding='utf-8') as f:
    sw = f.read()

sw = sw.replace('sinergix-crm-v73', 'sinergix-crm-v74')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw)

print("Updated sw.js to v74.")

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
