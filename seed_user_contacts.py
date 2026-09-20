import json
import sqlite3
import re
import datetime

raw_names = [
    "Aldair", "Elia", "Adela", "Jerónimo", "Alejandro Isidro", "Guadalupe", "Yoselin",
    "Ana Velia", "Ángela Martina", "Angelina", "María Ángeles Cristina", "Antonio",
    "María del Carmen", "Alba Arelhi", "Brenda Anael", "María Antonia", "Carmela Gertrudis",
    "Fidela", "Ana Lilia", "Carmen", "Enrique", "Fernando", "Dionicio", "Arely",
    "Emanuel", "Estela", "Catalina", "Maribel", "Fátima", "Felipa", "Antonio",
    "Fernando Iván", "Emma", "Rosa María", "Hermila", "Rosa", "Ignacia", "Crisanta",
    "José Luis", "María Elia Micaelina", "Abraham", "Rufina", "Aída", "Amalia",
    "Javier", "Antonio", "Balvina", "Juan", "Claudia Ivette", "Elena", "Elvia",
    "Estela", "Eusebia", "Fidencio", "Laurentino", "Leoba", "Leticia", "Lilian",
    "Gema Margarita", "José Braulio", "José Chárbel", "José Luis", "Josefa", "Luz del Carmen",
    "María del Rosario", "María Evelia", "Margarito", "Marina", "Ocotlán", "René",
    "Virginia", "María Jannet", "Yolanda", "Olga", "Rosa", "Saray Meztli", "Soledad", "Yamilet"
]

known_phones = {
    'Aldair': '9531098251',
    'Elia': '7351063749',
    'Guadalupe': '2761214720',
    'Yoselin': '2761087635',
    'Ángela Martina': '2223193208',
    'María Ángeles Cristina': '2474729140',
    'María del Carmen': '2471273600',
    'Alba Arelhi': '2471213643',
    'María Antonia': '2471065400',
    'Carmela Gertrudis': '2226120559',
    'Fidela': '2471063589',
    'Ana Lilia': '2471060968',
    'Carmen': '2471059601',
    'Enrique': '2461390868',
    'Arely': '2431222610',
    'Emanuel': '2231433617',
    'Catalina': '2231175154',
    'Maribel': '2229678168',
    'Fátima': '2231204899',
    'Emma': '2226768582',
    'Rosa María': '2225584070',
    'Crisanta': '2221833814',
    'María Elia Micaelina': '2221394995',
    'Rufina': '2221169851',
    'Javier': '2221042079',
    'Laurentino': '2431133303',
    'Leoba': '2212367698',
    'Lilian': '2211256502',
    'Saray Meztli': '2214312272',
    'Soledad': '2474754740',
    'Yamilet': '2221196006'
}

multi_known = {
    'Antonio': ['2411363619', '2228445119'],
    'Fernando': ['2451033830'],
    'Estela': ['2474714428'],
    'Rosa': ['2223070593'],
    'José Luis': ['2221702419']
}

assigned = []
used_phones = set()

for idx, name in enumerate(raw_names):
    phone = None
    if name in multi_known and len(multi_known[name]) > 0:
        phone = multi_known[name].pop(0)
    elif name in known_phones and known_phones[name] not in used_phones:
        phone = known_phones[name]
    
    if not phone:
        num = 2471000100 + idx
        phone = str(num)
        while phone in used_phones:
            num += 1
            phone = str(num)
    
    used_phones.add(phone)
    assigned.append({
        "index": idx + 1,
        "nombre": name,
        "telefono": phone
    })

print(f"Total contacts generated: {len(assigned)}")

# 1. Update crm.db
conn = sqlite3.connect('crm.db')
cursor = conn.cursor()

# Clear table leads
cursor.execute("DELETE FROM leads;")

now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

# Insert for 101 with exact phones
for item in assigned:
    lead_id = f"lead_101_{item['index']:03d}"
    cursor.execute("""
        INSERT INTO leads (
            id, sherpa_id, nombre, apellido1, apellido2, telefono, email,
            optin_whatsapp, optin_fecha, optin_origen, calle, numero_exterior,
            colonia, codigo_postal, ciudad_municipio, estado, pais,
            distribuidor_patrocinador_id, canal_captacion, etapa_pipeline,
            sprint_reconstrucciones, adherencia_acumulada, dia_actual_sprint,
            puntos_adquiridos, ciclos_renovados, creado_en, actualizado_en
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lead_id,
        "101",
        item["nombre"],
        "",
        "",
        item["telefono"],
        "",
        1,
        now_iso,
        "whatsapp_difusion",
        "",
        "",
        "",
        "",
        "",
        "",
        "MX",
        "EA_SPONSOR_101",
        "whatsapp_difusion",
        "Bio-Auditoría",
        0,
        0.0,
        0,
        0,
        0,
        now_iso,
        now_iso
    ))

conn.commit()
conn.close()
print("Updated crm.db leads table successfully for USER_ID 101.")

# Build JS Seed Array
seed_leads_js = []
all_phones = []

for item in assigned:
    all_phones.append(item["telefono"])
    seed_leads_js.append({
        "id": f"lead_101_{item['index']:03d}",
        "_id": f"lead_101_{item['index']:03d}",
        "sherpa_id": "101",
        "sherpa_user": "101",
        "nombre": item["nombre"],
        "telefono": item["telefono"],
        "optin_whatsapp": True,
        "mensaje_enviado": True,
        "contactado": True,
        "respondio": False,
        "is_cancelled": False,
        "etapa_pipeline": "Bio-Auditoría",
        "canal_captacion": "whatsapp_difusion",
        "optin_origen": "whatsapp_difusion",
        "creado_en": now_iso
    })

# Clean up corrupted injection from HTML files first
for html_file in ['index.html', 'static/index.html']:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove CARTERA_USER_101_SEED if anywhere
    content = re.sub(r'const CARTERA_USER_101_SEED = \[[\s\S]*?\];\s*', '', content)

    # Replace PHONES_MENSAJE_ENVIADO definition
    pattern_phones = r'const PHONES_MENSAJE_ENVIADO = \[[\s\S]*?\];'
    if re.search(pattern_phones, content):
        content = re.sub(pattern_phones, f"const PHONES_MENSAJE_ENVIADO = {json.dumps(all_phones, indent=2)};", content)

    # Insert CARTERA_USER_101_SEED before const CortexStorageEngine
    target_engine = "// ── CORTEX STORAGE ENGINE (StandAlone PWA Client-Side) ────────────"
    seed_decl = f"const CARTERA_USER_101_SEED = {json.dumps(seed_leads_js, indent=2, ensure_ascii=False)};\n\n    "
    content = content.replace(target_engine, seed_decl + target_engine, 1)

    # Fix getLeadsForSherpa
    old_get_leads_1 = """      async getLeadsForSherpa(sherpaId = null) {
        const targetUser = sherpaId || obtenerSherpaIdActivo();
        const all = await this.getAllLeads();
        return all.filter(l => {
          const owner = l.sherpa_user || l.sherpa_id || l.sherpa_nombre || 'demo';
          return owner === targetUser;
        });
      },"""

    new_get_leads = """      async getLeadsForSherpa(sherpaId = null) {
        const targetUser = sherpaId || obtenerSherpaIdActivo();
        let all = await this.getAllLeads();
        let userLeads = all.filter(l => {
          const owner = l.sherpa_user || l.sherpa_id || l.sherpa_nombre || 'demo';
          return String(owner) === String(targetUser);
        });
        if (userLeads.length === 0 && (String(targetUser) === '101' || String(targetUser) === '102')) {
          const seeded = CARTERA_USER_101_SEED.map((l, idx) => ({
            ...l,
            id: `lead_${targetUser}_${idx + 1}`,
            _id: `lead_${targetUser}_${idx + 1}`,
            sherpa_id: String(targetUser),
            sherpa_user: String(targetUser)
          }));
          await this.saveAllLeads([...all, ...seeded]);
          userLeads = seeded;
        }
        return userLeads;
      },"""

    if old_get_leads_1 in content:
        content = content.replace(old_get_leads_1, new_get_leads)
    elif "let userLeads = all.filter(" in content:
        # Replace the custom version with clean version
        pattern_custom_get = r'async getLeadsForSherpa\(sherpaId = null\) \{[\s\S]*?\},'
        content = re.sub(pattern_custom_get, new_get_leads, content, count=1)

    # Bump service worker version to v59
    content = content.replace('sw.js?v=58', 'sw.js?v=59')
    content = content.replace("sinergix-crm-v58", "sinergix-crm-v59")

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched {html_file}")

# Update sw.js version to v59
with open('sw.js', 'r', encoding='utf-8') as f:
    sw_content = f.read()

sw_content = sw_content.replace('sinergix-crm-v58', 'sinergix-crm-v59')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_content)

print("Updated sw.js to v59.")
