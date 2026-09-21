import os

def update_file(filepath):
    print(f"Updating script templates in {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    old_func_start = "function renderGuionGira2026(lead, tipoGuion = 'paso1_apertura', horarioMesa = '3:30 PM', sedeKey = null) {"
    old_func_end = "return formatearSaludoPila(lead, plantillaRaw);\n    }"

    idx_start = content.find(old_func_start)
    if idx_start == -1:
        print(f"  - Error: could not find renderGuionGira2026 in {filepath}")
        return

    idx_end = content.find(old_func_end, idx_start)
    if idx_end == -1:
        print(f"  - Error: could not find end of renderGuionGira2026 in {filepath}")
        return

    new_func = """function renderGuionGira2026(lead, tipoGuion = 'paso1_apertura', horarioMesa = '3:30 PM', sedeKey = null) {
      const sesion = obtenerSherpaSesion();
      const sherpaNombreNorm = obtenerNombreSherpaFormateado(sesion);
      const keySede = sedeKey || localStorage.getItem('sinergix_sede_activa') || obtenerSedeSegunFechaSistema();
      const objSede = SEDES_GIRA_2026[keySede] || SEDES_GIRA_2026.puebla;

      let plantillaRaw = '';

      if (tipoGuion === 'paso1_apertura') {
        plantillaRaw = `Hola, {nombre}, espero que estés muy bien.\\n\\n` +
          `Te escribo porque este ${objSede.fechaCompleta} tenemos una Jornada Especial aquí en ${objSede.nombre} donde estamos abordando la causa raíz del desgaste biológico y celular frente a la industria del malestar.\\n\\n` +
          `Estarán nutriólogos apoyándonos para realizar consultas clínicas ayudando a las personas a conocer la situación actual de su salud a través de un estudio con resultados en tiempo real y evaluando sus resultados.\\n\\n` +
          `Voy a estar coordinando las mesas de trabajo y diagnóstico. Tengo asignados solo 2 turnos para mis contactos cercanos: a las 3:30 PM y a las 4:30 PM.\\n\\n` +
          `¿Cuál de estos dos horarios te queda mejor para apartarte tu lugar?`;
      } else if (tipoGuion === 'paso2_confirmacion') {
        plantillaRaw = `Excelente, {nombre}. Queda reservado tu espacio a las ${horarioMesa} en ${objSede.nombre}.\\n\\n` +
          `Te comparto la Dirección: ${objSede.direccion}\\n\\n` +
          `Te pido llegar 5 minutos antes para iniciar puntualmente con tu valoración. Recuerda que, si por alguna razón no puedes asistir, me avises con tiempo para liberar el turno a alguien en lista de espera.\\n\\n` +
          `Nos vemos allá. Saludos!`;
      } else if (tipoGuion === 'reactivacion_a') {
        plantillaRaw = `Hola de nuevo {nombre}, espero que estés muy bien.\\n\\n` +
          `Me imagino que andas con un montón de cosas hoy, si es así, no te preocupes, entiendo perfectamente.\\n\\n` +
          `Te escribo rápido solo para saber si prefieres que mejor libere tu turno de las ${horarioMesa} para asignárselo a alguien de la lista de espera, o si alcanzas a llegar y mantenemos tu espacio reservado.\\n\\n` +
          `Dime con toda confianza. Saludos!`;
      } else if (tipoGuion === 'reactivacion_b') {
        plantillaRaw = `Hola, {nombre}, buenas tardes.\\n\\n` +
          `Te busco porque me has comentado que para ti es importante el cuidado y la salud de tu familia.\\n\\n` +
          `Seguimos coordinando la jornada de diagnóstico aquí en ${objSede.nombre} y me gustaría asegurar que no te quedes fuera de esta sesión preventiva de salud celular.\\n\\n` +
          `¿Crees que logremos vernos hoy a las ${horarioMesa} o prefieres que agendemos un espacio más adelante?`;
      } else if (tipoGuion === 'reactivacion_c') {
        plantillaRaw = `Hola, {nombre}, buenas tardes!\\n\\n` +
          `Solo para saber si confirmamos tu asistencia a las ${horarioMesa}? Quedo al pendiente para enviarte el pase. Saludos!`;
      } else {
        plantillaRaw = `Hola, {nombre}, soy ${sherpaNombreNorm}. Te escribo para la Jornada Especial de la Gira de Poder 2026 en ${objSede.nombre}. ¿Confirmamos tu lugar?`;
      }

      return formatearSaludoPila(lead, plantillaRaw);
    }"""

    content = content[:idx_start] + new_func + content[idx_end + len(old_func_end):]

    # Bump Service Worker to v79
    content = content.replace('sw.js?v=78', 'sw.js?v=79')
    content = content.replace('sw.js?v=77', 'sw.js?v=79')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Done updating {filepath}\n")

def update_sw():
    filepath = 'sw.js'
    print(f"Updating {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace("sinergix-crm-v78", "sinergix-crm-v79")
    content = content.replace("sinergix-crm-v77", "sinergix-crm-v79")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Done updating {filepath}\n")

if __name__ == '__main__':
    update_file('index.html')
    if os.path.exists('static/index.html'):
        update_file('static/index.html')
    if os.path.exists('sw.js'):
        update_sw()
