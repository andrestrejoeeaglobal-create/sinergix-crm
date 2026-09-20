import re

def remove_tab_toast(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern for showToast active tab notification inside cambiarPestana
    pattern = r'\s*if\s*\(\s*typeof\s+showToast\s*===\s*[\'"]function[\'"]\s*\)\s*\{\s*showToast\(\s*`Pestaña activa:[^`]*`,\s*[\'"]info[\'"]\s*\);\s*\}'

    if re.search(pattern, content):
        content = re.sub(pattern, '', content)
        # Bump Service Worker version to v63
        content = content.replace('sw.js?v=62', 'sw.js?v=63')
        content = content.replace('sinergix-crm-v62', 'sinergix-crm-v63')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Removed tab alert popup from {file_path}")
    else:
        print(f"Pattern not found in {file_path}")

remove_tab_toast('index.html')
remove_tab_toast('static/index.html')

# Update sw.js version to v63
with open('sw.js', 'r', encoding='utf-8') as f:
    sw_content = f.read()

sw_content = sw_content.replace('sinergix-crm-v62', 'sinergix-crm-v63')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_content)

print("Updated sw.js to v63.")
