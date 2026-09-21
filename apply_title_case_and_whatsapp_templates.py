import re

def update_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_helpers = """    function formatearNombreNatural(str) {
      if (!str) return '';
      let s = str.trim();
      if (s.includes(',')) {
        const parts = s.split(',').map(p => p.trim()).filter(Boolean);
        const firstName = parts[0] || '';
        const lastNamePart = parts[1] || '';
        const lastNames = lastNamePart.split(/\\s+/).filter(Boolean);
        const firstLastName = lastNames[0] || '';

        const fnWords = firstName.split(/\\s+/).filter(Boolean);
        if (fnWords.length === 1 && firstLastName) {
          s = `${firstName} ${firstLastName}`;
        } else {
          s = firstName;
        }
      }

      let clean = s.replace(/\\s+/g, ' ').trim();
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
      const customNombre = localStorage.getItem('sinergix_sherpa_nombre');
      if (customNombre && customNombre.trim()) {
        return formatearNombreNatural(customNombre);
      }
      let nombreRaw = sesion.firstname || sesion.primer_nombre || sesion.nombre || sesion.customerName || 'Sherpa';
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

    # Replace name helpers
    idx_pila = content.find("function obtenerNombrePila(lead) {")
    if idx_pila != -1:
      # find start of helper block or function formatearNombreNatural
      idx_formatear = content.rfind("function formatearNombreNatural", 0, idx_pila)
      if idx_formatear != -1:
        idx_end_pila = content.find("return formatearNombreNatural(resultado);\n    }", idx_pila) + len("return formatearNombreNatural(resultado);\n    }")
        content = content[:idx_formatear] + new_helpers.strip() + content[idx_end_pila:]
      else:
        idx_end_pila = content.find("return partes[0];\n    }", idx_pila) + len("return partes[0];\n    }")
        content = content[:idx_pila] + new_helpers.strip() + content[idx_end_pila:]

    new_guion = """    function renderGuionGira2026(lead, tipoGuion = 'paso1_apertura', horarioMesa = '3:30 PM', sedeKey = null) {
      const sesion = obtenerSherpaSesion();
      const sherpaNombreNorm = obtenerNombreSherpaFormateado(sesion);
      const keySede = sedeKey || localStorage.getItem('sinergix_sede_activa') || obtenerSedeSegunFechaSistema();
      const objSede = SEDES_GIRA_2026[keySede] || SEDES_GIRA_2026.puebla;

      let plantillaRaw = '';

      if (tipoGuion === 'paso1_apertura') {
        plantillaRaw = `Hola, {nombre}, espero que estés muy bien. Soy ${sherpaNombreNorm}.\\n\\n` +
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
        plantillaRaw = `Hola, {nombre}, espero que estés muy bien. Soy ${sherpaNombreNorm}.\\n\\n` +
          `Imagino que andas con la agenda súper apretada hoy, ¡no te preocupes en absoluto, entiendo perfecto!\\n\\n` +
          `Te escribo rápido solo para saber si prefieres que libere tu turno de las ${horarioMesa} para asignárselo a alguien en lista de espera de la gira, o si mantenemos tu espacio reservado.\\n\\n` +
          `Dime con toda confianza. ¡Un saludo!`;
      } else if (tipoGuion === 'reactivacion_b') {
        plantillaRaw = `Hola, {nombre}, buenas tardes. Soy ${sherpaNombreNorm}.\\n\\n` +
          `Te busco porque sé lo importante que es para ti el cuidado y el rendimiento de tu familia.\\n\\n` +
          `Seguimos coordinando la jornada de diagnóstico aquí en ${objSede.nombre} y me gustaría asegurar que no te quedes fuera de esta sesión preventiva de salud celular.\\n\\n` +
          `¿Crees que logremos vernos hoy a las ${horarioMesa} o prefieres que agendemos un espacio especial más adelante?`;
      } else if (tipoGuion === 'reactivacion_c') {
        plantillaRaw = `Hola, {nombre}, buenas tardes. Soy ${sherpaNombreNorm}.\\n\\n` +
          `¿Confirmamos tu asistencia para las ${horarioMesa} en ${objSede.nombre}? Quedo al pendiente para enviarte el pase.`;
      } else {
        plantillaRaw = `Hola, {nombre}, soy ${sherpaNombreNorm}. Te escribo para la Jornada Especial de la Gira de Poder 2026 en ${objSede.nombre}. ¿Confirmamos tu lugar?`;
      }

      return formatearSaludoPila(lead, plantillaRaw);
    }"""

    # Replace renderGuionGira2026
    idx_guion = content.find("function renderGuionGira2026")
    if idx_guion != -1:
      idx_end_guion = content.find("return formatearSaludoPila(lead, plantillaRaw);\n    }", idx_guion) + len("return formatearSaludoPila(lead, plantillaRaw);\n    }")
      content = content[:idx_guion] + new_guion.strip() + content[idx_end_guion:]

    # Format header Sherpa name in actualizarHeaderSherpa
    content = content.replace("if (elNom) {\n          elNom.textContent = sherpaSesion.nombre;", "if (elNom) {\n          elNom.textContent = formatearNombreNatural(sherpaSesion.nombre);")
    content = content.replace("if (elNom) elNom.textContent = sherpaSesion.nombre;", "if (elNom) elNom.textContent = formatearNombreNatural(sherpaSesion.nombre);")

    # Service worker version bump to v66
    content = content.replace('sw.js?v=65', 'sw.js?v=66')
    content = content.replace('sinergix-crm-v65', 'sinergix-crm-v66')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {file_path}")

update_file('index.html')
update_file('static/index.html')

# Update sw.js version
with open('sw.js', 'r', encoding='utf-8') as f:
    sw = f.read()

sw = sw.replace('sinergix-crm-v65', 'sinergix-crm-v66')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw)

print("Updated sw.js to v66")
