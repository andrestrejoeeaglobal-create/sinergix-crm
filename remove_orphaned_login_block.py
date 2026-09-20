import re

def remove_orphaned_block(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern for the orphaned block after closing #modal-login
    pattern = r'(</div>\s*</div>\s*)\n\s*<div>\s*<label[^>]*>Contraseña</label>[\s\S]*?</form>\s*</div>\s*</div>'

    if re.search(pattern, content):
        content = re.sub(pattern, r'\1', content)
        # Bump Service Worker version to v62
        content = content.replace('sw.js?v=61', 'sw.js?v=62')
        content = content.replace('sinergix-crm-v61', 'sinergix-crm-v62')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Removed orphaned login block from {file_path}")
    else:
        print(f"Orphaned block pattern not found in {file_path}")

remove_orphaned_block('index.html')
remove_orphaned_block('static/index.html')

# Update sw.js version to v62
with open('sw.js', 'r', encoding='utf-8') as f:
    sw_content = f.read()

sw_content = sw_content.replace('sinergix-crm-v61', 'sinergix-crm-v62')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_content)

print("Updated sw.js to v62.")
