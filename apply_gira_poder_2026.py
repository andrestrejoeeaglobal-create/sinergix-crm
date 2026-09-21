import re
import json

def patch_index_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add SEDES_GIRA_2026, helper functions, name extractor, phone sanitizer, and renderGuionGira2026
    gira_engine_code = """
    // ── MOTOR DE PROSPECCIÓN "GIRA DE PODER 2026" (Flujo 2 Pasos + Reactivación Táctica) ──
    const SEDES_GIRA_2026 = {
      puebla: {
        key: 'puebla',
        nombre: 'Puebla',
        fechaCompleta: 'Lunes 21 de Septiembre',
        labelOption: 'Puebla (Lun 21 sep)',
        direccion: 'Centro de Experiencia Sinergix, Av. Juárez #2104, Col. La Paz, Puebla, Pue.'
      },
      izucar: {
        key: 'izucar',
        nombre: 'Izúcar de Matamoros',
        fechaCompleta: 'Martes 22 de Septiembre',
        labelOption: 'Izúcar de Matamoros (Mar 22 sep)',
        direccion: 'Hotel & Centro de Convenciones Matamoros, Calle Hidalgo #12, Centro, Izúcar, Pue.'
      },
      tecamachalco: {
        key: 'tecamachalco',
        nombre: 'Tecamachalco',
        fechaCompleta: 'Miércoles 23 de Septiembre',
        labelOption: 'Tecamachalco (Mié 23 sep)',
        direccion: 'Salón Empresarial Tecamachalco, Av. Guerrero #504, Centro, Tecamachalco, Pue.'
      },
      huamantla: {
        key: 'huamantla',
        nombre: 'Huamantla',
        fechaCompleta: 'Jueves 24 de Septiembre',
        labelOption: 'Huamantla (Jue 24 sep)',
        direccion: 'Cámara de Comercio Huamantla, Calle Juárez Norte #201, Centro, Huamantla, Tlax.'
      }
    };

    function obtenerFechaLocalMexico() {
      try {
        const formatter = new Intl.DateTimeFormat('en-CA', {
          timeZone: 'America/Mexico_City',
          year: 'numeric',
          month: '2-digit',
          day: '2-digit'
        });
        return formatter.format(new Date());
      } catch (e) {
        return new Date().toISOString().split('T')[0];
      }
    }

    function obtenerSedeSegunFechaSistema() {
      const fechaHoy = obtenerFechaLocalMexico();
      if (fechaHoy === '2026-09-21') return 'puebla';
      if (fechaHoy === '2026-09-22') return 'izucar';
      if (fechaHoy === '2026-09-23') return 'tecamachalco';
      if (fechaHoy === '2026-09-24') return 'huamantla';
      return 'puebla';
    }

    function sanitizarTelefonoWhatsAppMX(phoneRaw) {
      let digits = String(phoneRaw || '').replace(/\\D/g, '');
      if (digits.startsWith('521') && digits.length === 13) {
        digits = '52' + digits.slice(3);
      }
      if (digits.length === 12 && digits.startsWith('52')) {
        return digits;
      }
      if (digits.length === 10) {
        digits = '52' + digits;
      }
      return digits;
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

      if (compuestosValidos.includes(primerosDos)) {
        return partes[0] + ' ' + partes[1];
      }

      return partes[0];
    }

    function formatearSaludoPila(lead, textoPlantilla) {
      const nombrePila = obtenerNombrePila(lead);
      if (!nombrePila) {
        return textoPlantilla
          .replace(/Hola\\s*,\\s*\\{nombre\\}\\s*,?/gi, 'Hola,')
          .replace(/Hola\\s*\\{nombre\\}\\s*,?/gi, 'Hola,')
          .replace(/\\{nombre\\}/gi, '')
          .replace(/\\s+,\\s*/g, ', ')
          .replace(/\\s+/g, ' ')
          .trim();
      }
      return textoPlantilla.replace(/\\{nombre\\}/gi, nombrePila);
    }

    function renderGuionGira2026(lead, tipoGuion = 'paso1_apertura', horarioMesa = '3:30 PM', sedeKey = null) {
      const sesion = obtenerSherpaSesion();
      const sherpaNom = sesion.nombre || 'Sherpa';
      const keySede = sedeKey || localStorage.getItem('sinergix_sede_activa') || obtenerSedeSegunFechaSistema();
      const objSede = SEDES_GIRA_2026[keySede] || SEDES_GIRA_2026.puebla;

      const soyTexto = sherpaNom ? ` Soy ${sherpaNom}.` : '';

      let plantillaRaw = '';

      if (tipoGuion === 'paso1_apertura') {
        plantillaRaw = `Hola {nombre}, te escribo personalmente porque este ${objSede.fechaCompleta} tenemos la Jornada Especial de la Gira de Poder 2026 aquí en ${objSede.nombre}.\\n\\n` +
          `Estamos abordando la causa raíz del desgaste biológico y celular frente a la industria del malestar, ayudando a las personas a descartar que el cansancio, la inflamación o la falta de energía sean "síntomas normales".\\n\\n` +
          `Voy a estar coordinando las mesas de trabajo y diagnóstico. Tengo asignados solo 2 turnos para mi equipo cercano: a las 3:30 PM y a las 4:30 PM.\\n\\n` +
          `¿Cuál de estos dos horarios te queda mejor para apartar tu lugar?`;
      } else if (tipoGuion === 'paso2_confirmacion') {
        plantillaRaw = `Excelente, {nombre}. Queda reservado tu espacio a las ${horarioMesa} en ${objSede.nombre}.\\n\\n` +
          `📍 Dirección: ${objSede.direccion}\\n\\n` +
          `Te pido llegar 5 minutos antes para iniciar puntualmente con tu valoración. Recuerda que si por alguna razón no puedes asistir, me avises con tiempo para liberar el turno a alguien en lista de espera.\\n\\n` +
          `Nos vemos allá. ¡Un saludo!`;
      } else if (tipoGuion === 'reactivacion_a') {
        plantillaRaw = `Hola {nombre}, espero que estés muy bien.${soyTexto} Veo que andas con la agenda súper apretada hoy. No te preocupes en absoluto, entiendo perfecto.\\n\\n` +
          `Te escribo rápido solo para saber si prefieres que libere tu lugar a las ${horarioMesa} para asignárselo a alguien en lista de espera de la gira, o si mantenemos tu espacio reservado.\\n\\n` +
          `¡Dime con toda confianza!`;
      } else if (tipoGuion === 'reactivacion_b') {
        plantillaRaw = `Hola {nombre}, buenas tardes.${soyTexto} Te busco porque sé lo importante que es para ti el cuidado y rendimiento de tu familia.\\n\\n` +
          `Seguimos coordinando la jornada de diagnóstico en ${objSede.nombre} y me gustaría asegurar que no te quedes fuera de esta sesión preventiva.\\n\\n` +
          `¿Crees que logremos vernos hoy a las ${horarioMesa} o me avisas si agendamos un espacio especial?`;
      } else if (tipoGuion === 'reactivacion_c') {
        plantillaRaw = `Hola {nombre}, ¿confirmamos tu asistencia para las ${horarioMesa} en ${objSede.nombre}? Quedo al pendiente para enviarte el pase.`;
      } else {
        plantillaRaw = `Hola {nombre}, ${soyTexto} te escribo para la Jornada Especial de la Gira de Poder 2026 en ${objSede.nombre}. ¿Confirmamos tu lugar?`;
      }

      return formatearSaludoPila(lead, plantillaRaw);
    }
"""

    if "const SEDES_GIRA_2026 =" not in content:
        target_pos = "// ── CORTEX STORAGE ENGINE"
        content = content.replace(target_pos, gira_engine_code + "\n\n    " + target_pos, 1)

    # 2. Update registrarEnvioEnUnClic with mobile persistence (sessionStorage & anti-false positive)
    old_registrar_envio = """    function registrarEnvioEnUnClic(leadId, tipoGuion = 'encuesta') {
      const lead = todosLosLeads.find(l => String(l._id || l.id) === String(leadId));
      if (!lead) return;

      const urlWa = obtenerEnlaceWhatsAppLead(lead, tipoGuion);
      if (!urlWa) return;

      window.open(urlWa, '_blank');

      if (!lead.mensaje_enviado || lead.etapa_pipeline === 'Lead') {
        lead.mensaje_enviado = true;
        lead.contactado = true;
        lead.etapa_pipeline = 'Bio-Auditoría';
        lead.actualizado_en = new Date().toISOString();

        if (typeof CortexStorageEngine !== 'undefined' && CortexStorageEngine.saveLead) {
          CortexStorageEngine.saveLead(lead);
        }

        renderizarLista();
        actualizarMetricas();
        showToast(`Envío registrado para ${lead.nombre}`, 'success');
      }
    }"""

    new_registrar_envio = """    function registrarEnvioEnUnClic(leadId, tipoGuion = 'paso1_apertura') {
      const lead = todosLosLeads.find(l => String(l._id || l.id) === String(leadId) || String(l.telefono || '').endsWith(String(leadId).replace(/\\D/g, '')));
      if (!lead) return;

      const selGuion = document.getElementById('select-guion-paso')?.value || tipoGuion || 'paso1_apertura';
      const selHorario = document.getElementById('select-horario-mesa')?.value || '3:30 PM';
      const selSede = document.getElementById('select-sede-global')?.value || 'puebla';

      const texto = renderGuionGira2026(lead, selGuion, selHorario, selSede);
      const telClean = sanitizarTelefonoWhatsAppMX(lead.telefono);
      const urlWa = `https://api.whatsapp.com/send?phone=${telClean}&text=${encodeURIComponent(texto)}`;

      // Save pending confirmation in sessionStorage for mobile focus return
      try {
        sessionStorage.setItem('sinergix_pending_wa_confirm', JSON.stringify({
          leadId: lead._id || lead.id,
          leadNombre: lead.nombre,
          tipoGuion: selGuion,
          horarioMesa: selHorario,
          timestamp: Date.now()
        }));
      } catch (e) {}

      window.open(urlWa, '_blank');

      // Trigger interactive confirmation modal
      abrirModalConfirmacionEnvio(lead._id || lead.id, selGuion, selHorario);
    }

    function abrirModalConfirmacionEnvio(leadId, tipoGuion, horarioMesa) {
      const lead = todosLosLeads.find(l => String(l._id || l.id) === String(leadId));
      if (!lead) return;

      let modalConfirm = document.getElementById('modal-confirmacion-envio-wa');
      if (!modalConfirm) {
        modalConfirm = document.createElement('div');
        modalConfirm.id = 'modal-confirmacion-envio-wa';
        modalConfirm.className = 'fixed inset-0 z-[110] bg-slate-900/80 backdrop-blur-sm flex items-center justify-center p-4 fade-in';
        document.body.appendChild(modalConfirm);
      }

      const nombrePila = obtenerNombrePila(lead) || lead.nombre;

      modalConfirm.innerHTML = `
        <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 max-w-sm w-full shadow-clinical-lg space-y-4 text-center">
          <div class="w-14 h-14 mx-auto rounded-2xl bg-emerald-100 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-2xl shadow-clinical-sm">
            <i class="fa-brands fa-whatsapp"></i>
          </div>
          <div class="space-y-1">
            <h3 class="text-base font-black text-slate-900 dark:text-white">¿Se envió el mensaje a ${nombrePila}?</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 font-medium">Confirma para actualizar el pipeline y registrar la traza en la Agenda.</p>
          </div>
          <div class="flex flex-col gap-2 pt-2">
            <button onclick="confirmarEnvioProspeccion('${lead._id || lead.id}', '${tipoGuion}', '${horarioMesa}')" class="touch-target w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold rounded-2xl text-xs shadow-clinical-sm transition cursor-pointer">
              <i class="fa-solid fa-check mr-1.5"></i> Confirmar y Registrar Estado
            </button>
            <button onclick="cerrarModalConfirmacionEnvio()" class="touch-target w-full py-2.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold rounded-2xl text-xs transition cursor-pointer">
              Cancelar / Reintentar
            </button>
          </div>
        </div>
      `;
      modalConfirm.classList.remove('hidden');
    }

    function cerrarModalConfirmacionEnvio() {
      const modalConfirm = document.getElementById('modal-confirmacion-envio-wa');
      if (modalConfirm) modalConfirm.classList.add('hidden');
      try { sessionStorage.removeItem('sinergix_pending_wa_confirm'); } catch (e) {}
    }

    async function confirmarEnvioProspeccion(leadId, tipoGuion, horarioMesa) {
      const lead = todosLosLeads.find(l => String(l._id || l.id) === String(leadId));
      if (!lead) {
        cerrarModalConfirmacionEnvio();
        return;
      }

      lead.mensaje_enviado = true;
      lead.contactado = true;

      if (tipoGuion === 'paso1_apertura') {
        lead.etapa_pipeline = 'Mensaje Enviado (Paso 1)';
      } else if (tipoGuion === 'paso2_confirmacion') {
        lead.etapa_pipeline = 'Mesa Reservada (Paso 2)';
        lead.respondio = true;
        lead.horario_mesa = horarioMesa;
      } else if (tipoGuion.startsWith('reactivacion')) {
        lead.etapa_pipeline = 'Reactivación Enviada';
      } else {
        lead.etapa_pipeline = 'Bio-Auditoría';
      }

      if (!Array.isArray(lead.historial_seguimiento)) {
        lead.historial_seguimiento = [];
      }

      const sesion = obtenerSherpaSesion();
      lead.historial_seguimiento.push({
        evento: `Envío ${tipoGuion}`,
        etapa: lead.etapa_pipeline,
        horario_mesa: horarioMesa || '',
        fecha: new Date().toISOString(),
        sherpa_id: sesion.userId || '101'
      });

      lead.actualizado_en = new Date().toISOString();

      if (typeof CortexStorageEngine !== 'undefined' && CortexStorageEngine.saveLead) {
        await CortexStorageEngine.saveLead(lead);
      }

      cerrarModalConfirmacionEnvio();
      renderizarLista();
      actualizarMetricas();
      showToast(`¡Estado actualizado: ${lead.etapa_pipeline} para ${lead.nombre}!`, 'success');
    }

    // Listener global para reactivar confirmación al regresar de WhatsApp nativo en móviles
    function checkPendingWaConfirmationOnFocus() {
      try {
        const raw = sessionStorage.getItem('sinergix_pending_wa_confirm');
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed && parsed.leadId && (Date.now() - parsed.timestamp < 600000)) {
            abrirModalConfirmacionEnvio(parsed.leadId, parsed.tipoGuion, parsed.horarioMesa);
          }
        }
      } catch (e) {}
    }

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        checkPendingWaConfirmationOnFocus();
      }
    });
    window.addEventListener('focus', checkPendingWaConfirmationOnFocus);"""

    if old_registrar_envio in content:
        content = content.replace(old_registrar_envio, new_registrar_envio)

    # 3. Update Grouped State Families in actualizarMetricas and filtrarPorEstado
    old_filtrar_estado = """        if (filtroEstadoActual === 'todos') return true;
        if (filtroEstadoActual === 'enviados') return !l.is_cancelled && Boolean(l.mensaje_enviado);
        if (filtroEstadoActual === 'no_enviados' || filtroEstadoActual === 'pendientes') return !l.is_cancelled && !l.mensaje_enviado;
        if (filtroEstadoActual === 'respondieron') return !l.is_cancelled && Boolean(l.respondio);
        if (filtroEstadoActual === 'cancelados') return Boolean(l.is_cancelled);
        return true;"""

    new_filtrar_estado = """        if (filtroEstadoActual === 'todos') return !l.is_cancelled;
        if (filtroEstadoActual === 'enviados') {
          return !l.is_cancelled && (Boolean(l.mensaje_enviado) || ['Bio-Auditoría', 'Mensaje Enviado (Paso 1)', 'Reactivación Enviada', 'Mesa Reservada (Paso 2)', 'Datos Enviados', 'Plan Vendido', 'Sprint Activo'].includes(l.etapa_pipeline));
        }
        if (filtroEstadoActual === 'no_enviados' || filtroEstadoActual === 'pendientes') {
          return !l.is_cancelled && (!l.mensaje_enviado && (l.etapa_pipeline === 'Lead' || !l.etapa_pipeline));
        }
        if (filtroEstadoActual === 'respondieron') {
          return !l.is_cancelled && (Boolean(l.respondio) || l.etapa_pipeline === 'Mesa Reservada (Paso 2)');
        }
        if (filtroEstadoActual === 'cancelados') return Boolean(l.is_cancelled);
        return true;"""

    if old_filtrar_estado in content:
        content = content.replace(old_filtrar_estado, new_filtrar_estado)

    # 4. Update Campaign Active Control Bar HTML in Agenda tab with 3 selectors (Paso/Guion, Horario, Sede)
    old_campaign_bar = """        <!-- BARRA DE CONTROL DE CAMPAÑA ACTIVA DE DIFUSIÓN -->
        <div class="bg-white dark:bg-slate-800 p-4 rounded-2xl border border-slate-200 dark:border-slate-700 mb-4 flex flex-col md:flex-row items-center justify-between gap-4 shadow-clinical-sm">
          <div class="flex items-center gap-3 w-full md:w-auto">
            <div class="w-10 h-10 rounded-xl bg-indigo-100 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold shrink-0">
              <i class="fa-solid fa-bullhorn text-lg"></i>
            </div>
            <div>
              <h3 class="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 dark:text-slate-400">Campaña Activa de Difusión</h3>
              <p class="text-sm font-extrabold text-slate-900 dark:text-white flex items-center gap-2" id="label-campana-activa">
                Gira de Campo (21-24 Sep)
              </p>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-3 w-full md:w-auto">
            <!-- Configuración del Nombre de Batalla del Sherpa -->
            <div class="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl px-2.5 py-1.5 shadow-clinical-sm">
              <i class="fa-solid fa-user-ninja text-indigo-500 text-sm"></i>
              <input type="text" id="input-sherpa-nombre" onchange="guardarNombreSherpa(this.value)" placeholder="Tu Nombre de Batalla..." class="bg-transparent border-none text-xs font-sans font-bold text-slate-800 dark:text-slate-200 focus:outline-none w-36" title="Ingresa tu Nombre de Batalla para personalizar las invitaciones" />
            </div>

            <!-- Configuración del Teléfono Celular WhatsApp del Sherpa -->
            <div class="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl px-2.5 py-1.5 shadow-clinical-sm">
              <i class="fa-brands fa-whatsapp text-emerald-500 text-sm"></i>
              <input type="tel" id="input-sherpa-celular" onchange="guardarCelularSherpa(this.value)" placeholder="Tu Celular WhatsApp (10 dígitos)..." class="bg-transparent border-none text-xs font-mono font-bold text-slate-800 dark:text-slate-200 focus:outline-none w-44" title="Ingresa tu número celular personal de WhatsApp a 10 dígitos para recibir respuestas" />
            </div>

            <!-- Selector de Mensaje -->
            <select id="select-campana-global" onchange="actualizarCampanaActiva(this.value)" class="bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl px-3 py-2 text-xs font-bold text-slate-800 dark:text-slate-200 focus:outline-none focus:border-ea-blue">
              <option value="gira_terreno">1. Convocatoria Gira de Campo (21-24 Sep)</option>
              <option value="diagnostico_metabolico">2. Diagnóstico Metabólico (Bio-Auditoría)</option>
            </select>

            <!-- Selector de Sede Predeterminada -->
            <select id="select-sede-global" onchange="actualizarSedeGlobal(this.value)" class="bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl px-3 py-2 text-xs font-bold text-slate-800 dark:text-slate-200 focus:outline-none focus:border-ea-blue">
              <option value="Puebla (Lun 21 sep)">Puebla (Lun 21 sep)</option>
              <option value="Izúcar de Matamoros (Mar 22 sep)">Izúcar de Matamoros (Mar 22 sep)</option>
              <option value="Tecamachalco (Mié 23 sep)">Tecamachalco (Mié 23 sep)</option>
              <option value="Huamantla (Jue 24 sep)">Huamantla (Jue 24 sep)</option>
            </select>

            <!-- Botón para Previsualizar Plantilla -->
            <button onclick="abrirModalPrevisualizacion()" class="touch-target bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-bold px-3 py-2 rounded-xl text-xs border border-slate-300 dark:border-slate-600 flex items-center gap-1.5 transition">
              <i class="fa-solid fa-eye text-sm text-ea-blue"></i>
              <span>Vista Previa</span>
            </button>
          </div>
        </div>"""

    new_campaign_bar = """        <!-- BARRA DE CONTROL DE CAMPAÑA ACTIVA DE DIFUSIÓN (GIRA DE PODER 2026) -->
        <div class="bg-white dark:bg-slate-800 p-4 rounded-2xl border border-slate-200 dark:border-slate-700 mb-4 flex flex-col xl:flex-row items-center justify-between gap-4 shadow-clinical-sm">
          <div class="flex items-center gap-3 w-full xl:w-auto">
            <div class="w-10 h-10 rounded-xl bg-indigo-100 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold shrink-0">
              <i class="fa-solid fa-bullhorn text-lg"></i>
            </div>
            <div>
              <h3 class="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 dark:text-slate-400">Motor de Prospección Canónico</h3>
              <p class="text-sm font-extrabold text-slate-900 dark:text-white flex items-center gap-2" id="label-campana-activa">
                Gira de Poder 2026 (Flujo 2 Pasos)
              </p>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-2.5 w-full xl:w-auto">
            <!-- Configuración del Nombre de Batalla del Sherpa -->
            <div class="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl px-2.5 py-1.5 shadow-clinical-sm">
              <i class="fa-solid fa-user-ninja text-indigo-500 text-xs"></i>
              <input type="text" id="input-sherpa-nombre" onchange="guardarNombreSherpa(this.value)" placeholder="Tu Nombre de Batalla..." class="bg-transparent border-none text-xs font-sans font-bold text-slate-800 dark:text-slate-200 focus:outline-none w-32" title="Ingresa tu Nombre de Batalla para personalizar las invitaciones" />
            </div>

            <!-- Configuración del Teléfono Celular WhatsApp del Sherpa -->
            <div class="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl px-2.5 py-1.5 shadow-clinical-sm">
              <i class="fa-brands fa-whatsapp text-emerald-500 text-xs"></i>
              <input type="tel" id="input-sherpa-celular" onchange="guardarCelularSherpa(this.value)" placeholder="Tu Celular WhatsApp (10 dígitos)..." class="bg-transparent border-none text-xs font-mono font-bold text-slate-800 dark:text-slate-200 focus:outline-none w-36" title="Ingresa tu número celular personal de WhatsApp a 10 dígitos para recibir respuestas" />
            </div>

            <!-- Selector de Guion / Paso (Flujo 2 Pasos + Reactivaciones) -->
            <select id="select-guion-paso" onchange="localStorage.setItem('sinergix_guion_paso_activo', this.value)" class="bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl px-2.5 py-1.5 text-xs font-bold text-slate-800 dark:text-slate-200 focus:outline-none focus:border-ea-blue shadow-clinical-sm">
              <option value="paso1_apertura">Paso 1: Apertura y Presuasión (12:00 - 13:00)</option>
              <option value="paso2_confirmacion">Paso 2: Confirmación y Compromiso de Mesa</option>
              <option value="reactivacion_a">Reactivación A: Despresurización & Cupo</option>
              <option value="reactivacion_b">Reactivación B: Causa & Familia</option>
              <option value="reactivacion_c">Reactivación C: Ejecutiva 1 Línea</option>
            </select>

            <!-- Selector de Horario de Mesa -->
            <select id="select-horario-mesa" onchange="localStorage.setItem('sinergix_horario_mesa_activo', this.value)" class="bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl px-2.5 py-1.5 text-xs font-bold text-slate-800 dark:text-slate-200 focus:outline-none focus:border-ea-blue shadow-clinical-sm">
              <option value="3:30 PM">Mesa 3:30 PM</option>
              <option value="4:00 PM">Mesa 4:00 PM</option>
              <option value="4:30 PM">Mesa 4:30 PM</option>
              <option value="5:00 PM">Mesa 5:00 PM</option>
              <option value="5:30 PM">Mesa 5:30 PM</option>
            </select>

            <!-- Selector de Sede de la Gira (Auto-Detección por Fecha) -->
            <select id="select-sede-global" onchange="actualizarSedeGlobal(this.value)" class="bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-xl px-2.5 py-1.5 text-xs font-bold text-slate-800 dark:text-slate-200 focus:outline-none focus:border-ea-blue shadow-clinical-sm">
              <option value="puebla">Puebla (Lun 21 sep)</option>
              <option value="izucar">Izúcar de Matamoros (Mar 22 sep)</option>
              <option value="tecamachalco">Tecamachalco (Mié 23 sep)</option>
              <option value="huamantla">Huamantla (Jue 24 sep)</option>
            </select>

            <!-- Botón Previsualización -->
            <button onclick="abrirModalPrevisualizacion()" class="touch-target bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-bold px-2.5 py-1.5 rounded-xl text-xs border border-slate-300 dark:border-slate-600 flex items-center gap-1.5 transition shadow-clinical-sm">
              <i class="fa-solid fa-eye text-xs text-ea-blue"></i>
              <span>Vista Previa</span>
            </button>
          </div>
        </div>"""

    if old_campaign_bar in content:
        content = content.replace(old_campaign_bar, new_campaign_bar)

    # 5. Auto-select Sede according to system date in DOMContentLoaded
    old_dom_content = """        const sedeSaved = localStorage.getItem('sinergix_sede_activa') || 'Puebla (Lun 21 sep)';"""
    new_dom_content = """        const sedeAutoDetected = obtenerSedeSegunFechaSistema();
        const sedeSaved = localStorage.getItem('sinergix_sede_activa') || sedeAutoDetected;
        localStorage.setItem('sinergix_sede_activa', sedeSaved);"""

    if old_dom_content in content:
        content = content.replace(old_dom_content, new_dom_content)

    # Auto-set dropdown values in DOMContentLoaded
    old_dropdown_sync = """        if (selectCamp) selectCamp.value = campanaSaved;
        if (selectSede) selectSede.value = sedeSaved;"""

    new_dropdown_sync = """        if (selectSede) selectSede.value = sedeSaved;
        const selGuion = document.getElementById('select-guion-paso');
        const selHorario = document.getElementById('select-horario-mesa');
        if (selGuion) selGuion.value = localStorage.getItem('sinergix_guion_paso_activo') || 'paso1_apertura';
        if (selHorario) selHorario.value = localStorage.getItem('sinergix_horario_mesa_activo') || '3:30 PM';"""

    if old_dropdown_sync in content:
        content = content.replace(old_dropdown_sync, new_dropdown_sync)

    # 6. Bump Service Worker to v64
    content = content.replace('sw.js?v=63', 'sw.js?v=64')
    content = content.replace('sinergix-crm-v63', 'sinergix-crm-v64')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched Gira 2026 engine in {file_path}")

patch_index_html('index.html')
patch_index_html('static/index.html')

# Update sw.js version to v64
with open('sw.js', 'r', encoding='utf-8') as f:
    sw_content = f.read()

sw_content = sw_content.replace('sinergix-crm-v63', 'sinergix-crm-v64')
with open('sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_content)

print("Updated sw.js to v64.")
