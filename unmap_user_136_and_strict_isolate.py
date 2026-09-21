import re

def update_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_get_leads = """      async getLeadsForSherpa(sherpaId = null) {
        const targetUser = String(sherpaId || obtenerSherpaIdActivo() || '101');
        let all = await this.getAllLeads();

        // STRICT ISOLATION RULE:
        // ONLY User 101 owns the 126 seed contacts.
        // User 136 (Luis Fernando), User 102 (Edgar Arturo), and all other users start with 0 contacts.
        if (targetUser !== '101') {
          const userLeads = all.filter(l => String(l.sherpa_user || l.sherpa_id || l.sherpa_nombre || '') === targetUser);
          const cleanAll = all.filter(l => {
            const isStray101 = String(l.id || '').startsWith('lead_101_') && String(l.sherpa_id || l.sherpa_user || '') !== '101';
            const isStrayUser = String(l.sherpa_id || l.sherpa_user || '') === targetUser && String(l.id || '').startsWith('lead_101_');
            return !isStray101 && !isStrayUser;
          });
          if (cleanAll.length !== all.length) {
            await this.saveAllLeads(cleanAll);
          }
          return userLeads;
        }

        let userLeads = all.filter(l => {
          const owner = String(l.sherpa_user || l.sherpa_id || l.sherpa_nombre || 'demo');
          return owner === '101';
        });

        if (userLeads.length === 0) {
          const seeded = CARTERA_USER_101_SEED.map((l, idx) => ({
            ...l,
            id: `lead_101_${idx + 1}`,
            _id: `lead_101_${idx + 1}`,
            sherpa_id: '101',
            sherpa_user: '101'
          }));
          const cleanOther101 = all.filter(l => String(l.sherpa_id || l.sherpa_user || '') !== '101' && !String(l.id || '').startsWith('lead_101_'));
          await this.saveAllLeads([...cleanOther101, ...seeded]);
          userLeads = seeded;
        }

        return userLeads;
      }"""

    # Replace getLeadsForSherpa
    idx_start = content.find("async getLeadsForSherpa(sherpaId = null) {")
    if idx_start != -1:
      idx_end = content.find("async saveLead(lead) {", idx_start)
      if idx_end != -1:
        content = content[:idx_start] + new_get_leads.strip() + "\n\n" + content[idx_end:]

    # Bump Service Worker to v68
    content = content.replace('sw.js?v=67', 'sw.js?v=68')
    content = content.replace('sinergix-crm-v67', 'sinergix-crm-v68')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Unmapped User 136 from 101 seed in {file_path}")

update_file('index.html')
update_file('static/index.html')

# Update sw.js version to v68
with open('sw.js', 'r', encoding='utf-8') as f:
    sw = f.read()

sw = sw.replace('sinergix-crm-v67', 'sinergix-crm-v68')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw)

print("Updated sw.js to v68.")
