import re

def fix_portfolio_isolation(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_get_leads = """      async getLeadsForSherpa(sherpaId = null) {
        const targetUser = String(sherpaId || obtenerSherpaIdActivo() || '101');
        let all = await this.getAllLeads();

        // Multi-Tenant Isolation: User 102 (Edgar Arturo) has 0 contacts. Purge any stray seeded leads.
        if (targetUser === '102') {
          const cleanAll = all.filter(l => String(l.sherpa_id || l.sherpa_user || '') !== '102' && !String(l.id || '').startsWith('lead_102_'));
          if (cleanAll.length !== all.length) {
            await this.saveAllLeads(cleanAll);
          }
          return [];
        }

        let userLeads = all.filter(l => {
          const owner = String(l.sherpa_user || l.sherpa_id || l.sherpa_nombre || 'demo');
          return owner === targetUser || (targetUser === '136' && owner === '101');
        });

        if (userLeads.length === 0 && (targetUser === '101' || targetUser === '136')) {
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

    # Replace getLeadsForSherpa in CortexStorageEngine
    idx_start = content.find("async getLeadsForSherpa(sherpaId = null) {")
    if idx_start != -1:
      idx_end = content.find("async saveLead(lead) {", idx_start)
      if idx_end != -1:
        content = content[:idx_start] + new_get_leads.strip() + "\n\n" + content[idx_end:]

    # Update ejecutarLoginSherpa to refresh leads for active user upon login
    old_login_leads_refresh = "todosLosLeads = [];"
    new_login_leads_refresh = """        // Cargar cartera aislada del usuario activo
        const leadsUsuario = await CortexStorageEngine.getLeadsForSherpa(custIdReal);
        todosLosLeads = Array.isArray(leadsUsuario) ? leadsUsuario : [];

        if (typeof renderizarLista === 'function') renderizarLista();
        if (typeof actualizarMetricas === 'function') actualizarMetricas();
        if (typeof renderAccionesPrioritarias === 'function') renderAccionesPrioritarias();"""

    if old_login_leads_refresh in content and "const leadsUsuario = await CortexStorageEngine.getLeadsForSherpa(custIdReal);" not in content:
      content = content.replace(old_login_leads_refresh, new_login_leads_refresh, 1)

    # Update salir() to clear UI cards
    old_salir_clear = "todosLosLeads = [];\n      if (typeof renderizarLista === 'function') renderizarLista();"
    new_salir_clear = """todosLosLeads = [];
      if (typeof renderizarLista === 'function') renderizarLista();
      if (typeof actualizarMetricas === 'function') actualizarMetricas();
      if (typeof renderAccionesPrioritarias === 'function') renderAccionesPrioritarias();"""

    if old_salir_clear in content:
      content = content.replace(old_salir_clear, new_salir_clear)

    # Update DOMContentLoaded to enforce clean array setting
    old_init = "const leadsLocales = await CortexStorageEngine.getLeadsForSherpa(activeUserInit);\n        if (leadsLocales && leadsLocales.length > 0) {\n          todosLosLeads = leadsLocales;\n        }"
    new_init = "const leadsLocales = await CortexStorageEngine.getLeadsForSherpa(activeUserInit);\n        todosLosLeads = Array.isArray(leadsLocales) ? leadsLocales : [];\n        if (typeof renderizarLista === 'function') renderizarLista();\n        if (typeof actualizarMetricas === 'function') actualizarMetricas();"

    if old_init in content:
      content = content.replace(old_init, new_init)

    # Bump service worker version to v67
    content = content.replace('sw.js?v=66', 'sw.js?v=67')
    content = content.replace('sinergix-crm-v66', 'sinergix-crm-v67')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Applied multi-tenant portfolio isolation fix to {file_path}")

fix_portfolio_isolation('index.html')
fix_portfolio_isolation('static/index.html')

# Update sw.js version to v67
with open('sw.js', 'r', encoding='utf-8') as f:
    sw = f.read()

sw = sw.replace('sinergix-crm-v66', 'sinergix-crm-v67')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw)

print("Updated sw.js to v67.")
