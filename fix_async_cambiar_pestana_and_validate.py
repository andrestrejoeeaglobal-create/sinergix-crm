import re
import subprocess
import os

def fix_and_validate(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Make cambiarPestana async
    old_func = "function cambiarPestana(nombrePestana) {"
    new_func = "async function cambiarPestana(nombrePestana) {"

    if old_func in content:
        content = content.replace(old_func, new_func)

    # Bump service worker version to v70
    content = content.replace('sw.js?v=69', 'sw.js?v=70')
    content = content.replace('sinergix-crm-v69', 'sinergix-crm-v70')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed cambiarPestana async signature in {file_path}")

fix_and_validate('index.html')
fix_and_validate('static/index.html')

# Update sw.js version to v70
with open('sw.js', 'r', encoding='utf-8') as f:
    sw = f.read()

sw = sw.replace('sinergix-crm-v69', 'sinergix-crm-v70')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw)

print("Updated sw.js to v70.")

# Validate JS syntax in index.html by extracting <script> contents
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
print(f"Found {len(scripts)} script blocks in index.html")

temp_js = '_temp_test_check.js'
for idx, script in enumerate(scripts):
    with open(temp_js, 'w', encoding='utf-8') as tf:
        tf.write(script)
    res = subprocess.run(['node', '--check', temp_js], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Syntax Error in script block {idx+1}: {res.stderr}")
    else:
        print(f"Script block {idx+1}: OK")

if os.path.exists(temp_js):
    os.remove(temp_js)
