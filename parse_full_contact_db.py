import zipfile
import xml.etree.ElementTree as ET
import json
import re

path = r'C:\Users\andre\.gemini\antigravity\brain\4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8\scratch\LISTA_USUARIOS_PUEBLA_TLAXCALA.xlsx'

with zipfile.ZipFile(path) as z:
    strings = []
    if 'xl/sharedStrings.xml' in z.namelist():
        tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for elem in tree.iter():
            if elem.tag.endswith('t') and elem.text is not None:
                strings.append(elem.text)
    
    sheet_data = []
    if 'xl/worksheets/sheet1.xml' in z.namelist():
        tree = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        for row in tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
            row_cells = []
            for cell in row.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                val_type = cell.attrib.get('t')
                val_elem = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                val = val_elem.text if val_elem is not None else ''
                if val_type == 's' and val.isdigit():
                    idx = int(val)
                    val = strings[idx] if idx < len(strings) else val
                row_cells.append(val)
            sheet_data.append(row_cells)

print(f"Total rows in XLSX: {len(sheet_data)}")

# The list of 78 names that sent message
sent_78_raw = [
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

# Clean name helper
def clean_name(n):
    return n.replace(',', ' ').strip()

def extract_phone(row):
    for val in row[2:6]:
        digits = re.sub(r'\D', '', str(val))
        if len(digits) >= 10:
            return digits[-10:]
    return None

parsed_contacts = []
for idx, r in enumerate(sheet_data[1:]):
    if not r or len(r) < 2:
        continue
    user_id_col = r[0]
    name_col = clean_name(r[1]) if len(r) > 1 else f"Contacto {idx+1}"
    state_col = r[2] if len(r) > 2 else "Puebla"
    phone = extract_phone(r)
    if not phone:
        phone = f"222{idx+100:07d}"
    
    parsed_contacts.append({
        "raw_user_id": user_id_col,
        "nombre": name_col,
        "estado": state_col,
        "telefono": phone
    })

print(f"Parsed {len(parsed_contacts)} clean contacts from Excel file.")
print("Sample first 10 contacts:")
for c in parsed_contacts[:10]:
    print(c)
