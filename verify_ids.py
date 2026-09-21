with open(r"c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm\index.html", "r", encoding="utf-8") as f:
    text = f.read()

ids_to_check = [
    'vista-briefing', 'vista-agenda', 'vista-cartera', 'vista-radar', 'vista-biometria', 'vista-simulador',
    'tab-btn-briefing', 'tab-btn-agenda', 'tab-btn-cartera', 'tab-btn-radar', 'tab-btn-biometria', 'tab-btn-simulador'
]

for id_name in ids_to_check:
    found = f'id="{id_name}"' in text or f"id='{id_name}'" in text
    print(f"{id_name}: {'FOUND' if found else 'MISSING'}")
