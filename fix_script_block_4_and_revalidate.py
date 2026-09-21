import re
import subprocess
import os

def clean_script_block_4(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Target broken pattern at line 878-886
    broken_pattern = r'let\s*// Cargar cartera aislada del usuario activo\s*const leadsUsuario = await CortexStorageEngine\.getLeadsForSherpa\(custIdReal\);\s*todosLosLeads = Array\.isArray\(leadsUsuario\) \? leadsUsuario : \[\];\s*if \(typeof renderizarLista === \'function\'\) renderizarLista\(\);\s*if \(typeof actualizarMetricas === \'function\'\) actualizarMetricas\(\);\s*if \(typeof renderAccionesPrioritarias === \'function\'\) renderAccionesPrioritarias\(\);'
    
    clean_replacement = "let todosLosLeads = [];"

    content = re.sub(broken_pattern, clean_replacement, content)

    # Make sure ejecutarLoginSherpa contains the user refresh logic cleanly
    login_replacement = """const leadsUsuario = await CortexStorageEngine.getLeadsForSherpa(custIdReal);
        todosLosLeads = Array.isArray(leadsUsuario) ? leadsUsuario : [];
        if (typeof renderizarLista === 'function') renderizarLista();
        if (typeof actualizarMetricas === 'function') actualizarMetricas();
        if (typeof renderAccionesPrioritarias === 'function') renderAccionesPrioritarias();"""

    # Check if login_replacement already exists in content
    if "const leadsUsuario = await CortexStorageEngine.getLeadsForSherpa(custIdReal);" not in content:
        content = content.replace("todosLosLeads = [];\n\n        actualizarEstadoSesionSherpa();", login_replacement + "\n\n        actualizarEstadoSesionSherpa();")

    # Ensure cambiarPestana is async
    content = content.replace("function cambiarPestana(nombrePestana) {", "async function cambiarPestana(nombrePestana) {")

    # Bump service worker to v70
    content = content.replace('sw.js?v=69', 'sw.js?v=70')
    content = content.replace('sinergix-crm-v69', 'sinergix-crm-v70')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Cleaned script block 4 in {file_path}")

clean_script_block_4('index.html')
clean_script_block_4('static/index.html')

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
