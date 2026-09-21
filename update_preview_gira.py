import re

def update_preview(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_enlace_func = """    function obtenerEnlaceWhatsAppLead(lead, tipoGuion = 'encuesta') {
      if (!lead) return '';
      const sesion = obtenerSherpaSesion();
      if (!sesion.valido) {
        abrirModalConfigSherpa("Configura tu nombre y número de WhatsApp para que las confirmaciones lleguen a tu cuenta personal.");
        return '';
      }

      let linkRef = '';
      try {
        linkRef = generarLinkCaptura(lead, sesion.nombre, sesion.celular);
      } catch (err) {
        console.warn("Error generando link de captura:", err);
        abrirModalConfigSherpa("Configura tu nombre y número de WhatsApp para que las confirmaciones lleguen a tu cuenta personal.");
        return '';
      }

      const primerNombre = (lead.nombre || '').trim().split(' ')[0] || 'Hola';

      if (tipoGuion === 'recordatorio') {
        const soyTexto = ` Soy ${sesion.nombre}.`;
        return `Hola ${primerNombre}.${soyTexto}\\n¿Pudiste responder la encuesta? 😃\\nTe agradecería mucho! 🙏\\n${linkRef}`;
      }

      const campanaKey = localStorage.getItem('sinergix_campana_activa') || 'gira_terreno';
      const sedeFinal = lead.sede || lead.ciudad || localStorage.getItem('sinergix_sede_activa') || 'Puebla (Lunes 21 sep)';
      const campana = CAMPANAS_SINERGIX[campanaKey] || CAMPANAS_SINERGIX.gira_terreno;

      return campana.render(lead.nombre, sedeFinal, linkRef, sesion.nombre);
    }"""

    new_enlace_func = """    function obtenerEnlaceWhatsAppLead(lead, tipoGuion = 'paso1_apertura') {
      if (!lead) return '';
      const selGuion = document.getElementById('select-guion-paso')?.value || tipoGuion || 'paso1_apertura';
      const selHorario = document.getElementById('select-horario-mesa')?.value || '3:30 PM';
      const selSede = document.getElementById('select-sede-global')?.value || 'puebla';

      return renderGuionGira2026(lead, selGuion, selHorario, selSede);
    }"""

    if old_enlace_func in content:
        content = content.replace(old_enlace_func, new_enlace_func)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated preview functions in {file_path}")

update_preview('index.html')
update_preview('static/index.html')
