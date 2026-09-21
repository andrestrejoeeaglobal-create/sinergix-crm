import re
import subprocess
import os

def update_label(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update label text
    content = content.replace("Usuario / Teléfono de 10 dígitos", "Usuario")
    content = content.replace('placeholder="Ej. 5512345678"', 'placeholder="Ingresa tu usuario"')

    # Bump service worker version to v72
    content = content.replace('sw.js?v=71', 'sw.js?v=72')
    content = content.replace('sinergix-crm-v71', 'sinergix-crm-v72')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated login label in {file_path}")

update_label('index.html')
update_label('static/index.html')

# Update sw.js version to v72
with open('sw.js', 'r', encoding='utf-8') as f:
    sw = f.read()

sw = sw.replace('sinergix-crm-v71', 'sinergix-crm-v72')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw)

print("Updated sw.js to v72.")

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
