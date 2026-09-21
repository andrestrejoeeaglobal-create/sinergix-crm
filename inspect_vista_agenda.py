import re

with open(r"c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm\index.html", "r", encoding="utf-8") as f:
    text = f.read()

m = re.search(r'<div id="vista-agenda".*?</div>\s*<!-- VISTA', text, re.DOTALL)
if not m:
    m = re.search(r'<section id="vista-agenda".*?</section>', text, re.DOTALL)
if not m:
    m = re.search(r'<div id="vista-agenda".*?(?=<div id="vista-)', text, re.DOTALL)

if m:
    print("Found vista-agenda length:", len(m.group(0)))
    print("First 500 chars of vista-agenda:")
    print(m.group(0)[:500])
else:
    print("Could not isolate vista-agenda block")
