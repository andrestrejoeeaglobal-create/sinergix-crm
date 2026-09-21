import re

def update_name_and_templates(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    name_helpers_code = """    function formatearNombreNatural(str) {
      if (!str) return '';
      let clean = str.replace(/,/g, ' ').replace(/\\s+/g, ' ').trim();
      return clean.split(' ').map((word, idx) => {
        if (!word) return '';
        const lower = word.toLowerCase();
        if (idx > 0 && ['de', 'del', 'la', 'los', 'las', 'y'].includes(lower)) {
          return lower;
        }
        return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
      }).join(' ');
    }

    function obtenerNombreSherpaFormateado(sesion) {
      if (!sesion) return 'Sherpa';
      let nombreRaw = sesion.firstname || sesion.primer_nombre || (sesion.nombre ? sesion.nombre.split(',')[0].trim() : '') || 'Sherpa';
      return formatearNombreNatural(nombreRaw);
    }

    function obtenerNombrePila(lead) {
      let raw = (typeof lead === 'string' ? lead : (lead?.nombre || '')).trim();
      if (!raw || /^(s\\/n|sin nombre|contacto|lead|prospecto)$/i.test(raw)) {
        return '';
      }
      raw = raw.replace(/^(dr\\.|dra\\.|ing\\.|lic\\.|prof\\.|cp\\.|mtro\\.|mtra\\.|doctora?|ingeniero?|licenciado?)\\s+/i, '');
      raw = raw.replace(/^ma\\.\\s+/i, 'María ');
      raw = raw.replace(/^j\\.\\s+/i, 'José ');

      const partes = raw.split(/\\s+/).filter(Boolean);
      if (partes.length === 0) return '';

      const primerosDos = (partes[0] + ' ' + (partes[1] || '')).toLowerCase();
      const compuestosValidos = ['maría elena', 'maria elena', 'juan carlos', 'josé luis', 'jose luis', 'ana maría', 'ana maria', 'luz maría', 'luz maria'];

      let resultado = partes[0];
      if (compuestosValidos.includes(primerosDos)) {
        resultado = partes[0] + ' ' + partes[1];
      }

      return formatearNombreNatural(resultado);
    }"""

    # Target old function by string matching
    old_pila_start = "function obtenerNombrePila(lead) {"
    old_pila_end = "return partes[0];\n    }"

    if old_pila_start in content and old_pila_end in content:
        idx_start = content.find(old_pila_start)
        idx_end = content.find(old_pila_end, idx_start) + len(old_pila_end)
        content = content[:idx_start] + name_helpers_code + content[idx_end:]

    new_guion_func = """    function renderGuionGira2026(lead, tipoGuion = 'paso1_apertura', horarioMesa = '3:30 PM', sedeKey = null) {
      const sesion = obtenerSherpaSesion();
      const sherpaNombreNorm = obtenerNombreSherpaFormateado(sesion);
      const keySede = sedeKey || localStorage.getItem('sinergix_sede_activa') || obtenerSedeSegunFechaSistema();
      const objSede = SEDES_GIRA_2026[keySede] || SEDES_GIRA_2026.puebla;

      let plantillaRaw = '';

      if (tipoGuion === 'paso1_apertura') {
        plantillaRaw = `Hola, {nombre}, espero que estés muy bien. Te saluda ${sherpaNombreNorm}.\\n\\n` +
          `Te escribo personalmente porque este ${objSede.fechaCompleta} tenemos la Jornada Especial de la Gira de Poder 2026 aquí en ${objSede.nombre}.\\n\\n` +
          `Estamos abordando la causa raíz del desgaste biológico y celular frente a la industria del malestar, ayudando a las personas a descartar que el cansancio, la inflamación o la falta de energía sean "síntomas normales".\\n\\n` +
          `Voy a estar coordinando las mesas de trabajo y diagnóstico. Tengo asignados solo 2 turnos para mi equipo cercano: a las 3:30 PM y a las 4:30 PM.\\n\\n` +
          `¿Cuál de estos dos horarios te queda mejor para apartar tu lugar?`;
      } else if (tipoGuion === 'paso2_confirmacion') {
        plantillaRaw = `Excelente, {nombre}. Queda reservado tu espacio a las ${horarioMesa} en ${objSede.nombre}.\\n\\n` +
          `📍 Dirección: ${objSede.direccion}\\n\\n` +
          `Te pido llegar 5 minutos antes para iniciar puntualmente con tu valoración. Recuerda que si por alguna razón no puedes asistir, me avises con tiempo para liberar el turno a alguien en lista de espera.\\n\\n` +
          `Nos vemos allá. ¡Un saludo!`;
      } else if (tipoGuion === 'reactivacion_a') {
        plantillaRaw = `Hola, {nombre}, espero que estés muy bien. Te saluda ${sherpaNombreNorm}.\\n\\n` +
          `Imagino que andas con la agenda súper apretada hoy, ¡no te preocupes en absoluto, entiendo perfecto!\\n\\n` +
          `Te escribo rápido solo para saber si prefieres que libere tu turno de las ${horarioMesa} para asignárselo a alguien en lista de espera de la gira, o si mantenemos tu espacio reservado.\\n\\n` +
          `Dime con toda confianza. ¡Un saludo!`;
      } else if (tipoGuion === 'reactivacion_b') {
        plantillaRaw = `Hola, {nombre}, buenas tardes. Te saluda ${sherpaNombreNorm}.\\n\\n` +
          `Te busco porque sé lo importante que es para ti el cuidado y rendimiento de tu familia.\\n\\n` +
          `Seguimos coordinando la jornada de diagnóstico en ${objSede.nombre} y me gustaría asegurar que no te quedes fuera de esta sesión preventiva.\\n\\n` +
          `¿Crees que logremos vernos hoy a las ${horarioMesa} o me avisas si agendamos un espacio especial?`;
      } else if (tipoGuion === 'reactivacion_c') {
        plantillaRaw = `Hola, {nombre}, te saluda ${sherpaNombreNorm}. ¿Confirmamos tu asistencia para las ${horarioMesa} en ${objSede.nombre}? Quedo al pendiente para enviarte el pase.`;
      } else {
        plantillaRaw = `Hola, {nombre}, te saluda ${sherpaNombreNorm}. Te escribo para la Jornada Especial de la Gira de Poder 2026 en ${objSede.nombre}. ¿Confirmamos tu lugar?`;
      }

      return formatearSaludoPila(lead, plantillaRaw);
    }"""

    old_guion_start = "function renderGuionGira2026(lead, tipoGuion = 'paso1_apertura'"
    old_guion_end = "return formatearSaludoPila(lead, plantillaRaw);\n    }"

    if old_guion_start in content and old_guion_end in content:
        idx_start = content.find(old_guion_start)
        idx_end = content.find(old_guion_end, idx_start) + len(old_guion_end)
        content = content[:idx_start] + new_guion_func.strip() + content[idx_end:]

    # Bump Service Worker to v65
    content = content.replace('sw.js?v=64', 'sw.js?v=65')
    content = content.replace('sinergix-crm-v64', 'sinergix-crm-v65')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Applied name formatting & Reactivación A updates to {file_path}")

update_name_and_templates('index.html')
update_name_and_templates('static/index.html')

# Update sw.js version to v65
with open('sw.js', 'r', encoding='utf-8') as f:
    sw_content = f.read()

sw_content = sw_content.replace('sinergix-crm-v64', 'sinergix-crm-v65')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_content)

print("Updated sw.js to v65.")
