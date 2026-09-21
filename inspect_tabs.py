import re

with open(r"c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm\index.html", "r", encoding="utf-8") as f:
    text = f.read()

print("=== VISTA SECTIONS ===")
vistas = re.findall(r'id=["\'](vista-[^"\']+)["\']', text)
print("Found vista IDs:", sorted(list(set(vistas))))

print("\n=== ALL SECTION / CONTAINER IDs ===")
all_ids = re.findall(r'id=["\']([^"\']+)["\']', text)
print("IDs starting with vista/tab/agenda/chat/cartera/radar/bio/sim:", [i for i in set(all_ids) if any(k in i.lower() for k in ['vista', 'agenda', 'cartera', 'salud', 'radar', 'bio', 'sim', 'briefing', 'chat'])])

print("\n=== TAB BUTTON ONCLICK CALLS ===")
for line in text.splitlines():
    if 'cambiarPestana' in line or 'switchTab' in line:
        print(line.strip())

print("\n=== FUNCTION DEFINITIONS ===")
for i, line in enumerate(text.splitlines()):
    if 'function cambiarPestana' in line or 'function switchTab' in line:
        print("\n".join(text.splitlines()[i:i+30]))
