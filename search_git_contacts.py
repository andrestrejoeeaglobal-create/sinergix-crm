import subprocess
import json
import re

def run_cmd(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=r"C:\Users\andre\.gemini\antigravity\brain\4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8\scratch\Sinergix-CRM\sinergix-crm")
    return res.stdout

commits_raw = run_cmd(['git', 'log', '--oneline', '-n', '50'])
commits = [line.split()[0] for line in commits_raw.strip().split('\n') if line]

print(f"Checking {len(commits)} commits...")

all_found_leads = {}

for c in commits:
    for filename in ['index.html', 'static/index.html', 'build_germancrm.py', 'build_real_crm.py', 'app/main.py']:
        content = run_cmd(['git', 'show', f'{c}:{filename}'])
        if not content:
            continue
        
        # Look for array of objects or list of contacts
        if 'PHONES_MENSAJE_ENVIADO' in content:
            phones = re.findall(r'\'(\d{10})\'', content)
            if phones:
                all_found_leads[f"{c}:{filename}:phones"] = len(phones)
        
        # Look for names or initial leads
        lead_matches = re.findall(r'nombre["\':\s]+([^",\n\}]+)', content)
        if lead_matches:
            all_found_leads[f"{c}:{filename}:names"] = len(lead_matches)

for k, v in all_found_leads.items():
    print(f"{k} => {v}")
