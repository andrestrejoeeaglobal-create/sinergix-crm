import re
import subprocess
import os

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix missing comma after getLeadsForSherpa method end
    pattern = r'(return userLeads;\s*\})\s*(async saveLead\(lead\))'
    replacement = r'\1,\n\n      \2'

    content = re.sub(pattern, replacement, content)

    # Also check if any other object methods miss commas
    content = content.replace("return userLeads;\n      }\n\nasync saveLead(lead) {", "return userLeads;\n      },\n\n      async saveLead(lead) {")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed comma in {file_path}")

fix_file('index.html')
fix_file('static/index.html')

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
