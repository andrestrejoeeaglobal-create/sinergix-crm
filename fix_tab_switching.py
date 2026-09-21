import os
import re

# We read from index.html
src_file = r"c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm\index.html"
with open(src_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Define canonical cambiarPestana function
new_cambiar_pestana = '''    function cambiarPestana(nombrePestana) {
      console.log('Ejecutando cambiarPestana:', nombrePestana);
      
      // Normalizar alias de pestañas
      let target = nombrePestana;
      if (nombrePestana === 'chat') target = 'briefing';
      if (nombrePestana === 'salud') target = 'cartera';
      if (nombrePestana === 'h7') target = 'biometria';
      if (nombrePestana === 'sim') target = 'simulador';

      const pestanas = ['briefing', 'agenda', 'cartera', 'radar', 'biometria', 'simulador'];
      
      pestanas.forEach(p => {
        const contenedor = document.getElementById(`vista-${p}`);
        const boton = document.getElementById(`tab-btn-${p}`);
        
        if (contenedor) {
          if (p === target) {
            contenedor.classList.remove('hidden');
          } else {
            contenedor.classList.add('hidden');
          }
        }
        
        if (boton) {
          if (p === target) {
            boton.className = 'py-2.5 px-3 rounded-xl text-slate-900 dark:text-white bg-white dark:bg-slate-700 shadow-clinical-sm flex items-center justify-center space-x-2 touch-target';
          } else {
            boton.className = 'py-2.5 px-3 rounded-xl text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center justify-center space-x-2 touch-target';
          }
        }
      });

      // Ejecutar rutinas de carga de datos según la pestaña activa
      if (target === 'briefing' && typeof cargarBriefingMatutino === 'function') {
        cargarBriefingMatutino();
      } else if (target === 'agenda') {
        if (typeof renderizarLista === 'function') renderizarLista();
        if (typeof cargarLeadsServidor === 'function') cargarLeadsServidor();
      } else if (target === 'cartera' && typeof cargarSaludCartera === 'function') {
        cargarSaludCartera();
      } else if (target === 'radar' && typeof cargarRadarYBono === 'function') {
        cargarRadarYBono();
      } else if (target === 'simulador' && typeof cargarSimuladorFinanciero === 'function') {
        cargarSimuladorFinanciero();
      }

      if (typeof showToast === 'function') {
        showToast(`Pestaña activa: ${target.toUpperCase()}`, 'info');
      }
    }'''

# Replace original function cambiarPestana(pestana) { ... }
pattern_orig = r'function cambiarPestana\(pestana\)\s*\{.*?\n    \}'
content = re.sub(pattern_orig, new_cambiar_pestana, content, flags=re.DOTALL)

# Remove any trailing stub function cambiarPestana(nombrePestana) { ... }
stub_pattern = r'function cambiarPestana\(nombrePestana\)\s*\{\s*console\.log\([^\)]+\);\s*showToast\([^\)]+\);\s*\}'
content = re.sub(stub_pattern, '', content)

targets = [
    r"c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm\index.html",
    r"c:\Users\andre\OneDrive\Escritorio\Archivos de prueba\sinergix-crm\static\index.html",
    r"c:\Users\andre\OneDrive\Escritorio\index.html",
    r"c:\Users\andre\OneDrive\Escritorio\static\index.html"
]

for t in targets:
    os.makedirs(os.path.dirname(t), exist_ok=True)
    with open(t, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully updated tab logic in {t} ({len(content)} chars)")
