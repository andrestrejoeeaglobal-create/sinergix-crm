import re
import subprocess
import os

def clean_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Clean multiple async prefixes
    content = re.sub(r'(?:async\s+)+function cambiarPestana', 'async function cambiarPestana', content)

    # Clean broken script block 4 header if present
    content = re.sub(
        r'let\s*// Cargar cartera aislada del usuario activo\s*const leadsUsuario = await CortexStorageEngine\.getLeadsForSherpa\(custIdReal\);\s*todosLosLeads = Array\.isArray\(leadsUsuario\) \? leadsUsuario : \[\];\s*if \(typeof renderizarLista === \'function\'\) renderizarLista\(\);\s*if \(typeof actualizarMetricas === \'function\'\) actualizarMetricas\(\);\s*if \(typeof renderAccionesPrioritarias === \'function\'\) renderAccionesPrioritarias\(\);',
        'let todosLosLeads = [];',
        content
    )

    # Bump service worker to v70
    content = content.replace('sw.js?v=69', 'sw.js?v=70')
    content = content.replace('sinergix-crm-v69', 'sinergix-crm-v70')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Cleaned {file_path}")

clean_file('index.html')
clean_file('static/index.html')

# Update sw.js version to v70
with open('sw.js', 'r', encoding='utf-8') as f:
    sw = f.read()

sw = sw.replace('sinergix-crm-v69', 'sinergix-crm-v70')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw)

print("Updated sw.js to v70.")

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
        print(f"🎉 ALL SCRIPT BLOCKS PASSED SYNTAX CHECK IN {fname}!")
