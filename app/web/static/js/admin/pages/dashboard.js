// Funcion para la pagina de solo el dashboard
// ===== Modal PRO + fade =====
//const ROLE = document.body?.dataset?.rol || "";

// ===== helpers =====
async function apiJson(url, opts = {}) {
  const r = await fetch(url, {
    ...opts,
    headers: { "Content-Type":"application/json", ...(opts.headers||{}) }
  });
  const data = await r.json().catch(()=>null);
  return { r, data };
}

function openAccessModal(msg){
  const m = document.getElementById("accessModal");
  const t = document.getElementById("accessMsg");
  if (!m) return;
  if (t) t.textContent = msg || "";
  m.classList.remove("hidden");
}

function closeAccessModal(){
  document.getElementById("accessModal")?.classList.add("hidden");
}

// ===== main =====
document.addEventListener("DOMContentLoaded", () => {
  // 1) Bind botones (ahora sí existen)
  const btnClose = document.getElementById("btnCloseAccess");
  const btnReq   = document.getElementById("btnRequestAccess");
  const modal    = document.getElementById("accessModal");

  btnClose?.addEventListener("click", closeAccessModal);

  // Cerrar haciendo click fuera del cuadro
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) closeAccessModal();
  });

  btnReq?.addEventListener("click", async () => {
    if (!btnReq) return;

    btnReq.disabled = true;
    const oldText = btnReq.textContent;
    btnReq.textContent = "Enviando...";

    try {
      const { r, data } = await apiJson("/api/v1/admin/access/request", {
        method: "POST",
        body: JSON.stringify({
          recurso: "dashboard",
          motivo: "Necesito ver métricas para operar mejor"
        })
      });

      if (r.status === 401) {
        location.href = "/admin/login?expired=1";
        return;
      }

      if (!r.ok) {
        openAccessModal((data && data.detail) ? data.detail : "No se pudo enviar la solicitud.");
        btnReq.disabled = false;
        btnReq.textContent = oldText;
        return;
      }

      if (data && data.already) {
        openAccessModal("✅ Ya existe una solicitud pendiente. El Administrador la revisará pronto.");
      } else {
        openAccessModal("✅ Solicitud enviada. Cuando el Administrador apruebe, recarga la página.");
      }

      btnReq.textContent = "Enviado ✓";
      // opcional: re-habilitar luego
      setTimeout(() => { btnReq.disabled = false; btnReq.textContent = oldText; }, 1500);

    } catch (err) {
      openAccessModal("❌ Error de conexión. Intenta nuevamente.");
      btnReq.disabled = false;
      btnReq.textContent = oldText;
    }
  });

  // 2) Cargar dashboard
  loadDashboard();
});


//document.getElementById("btn_access_close")?.addEventListener("click", closeAccessModal);
//document.getElementById("btn_access_request")?.addEventListener("click", requestAccessDashboard);


// ===== Tu Dashboard actual =====
async function loadDashboard(){
    // ✅ Guard PRO: solo corre si existe el dashboard en el DOM
  if (!document.getElementById("ventas_total")) return;
  const { r, data: d } = await apiJson("/api/v1/admin/dashboard/summary");
  //const r = await api("/api/v1/admin/dashboard/summary");
  
    if (r.status === 401) {
        location.href = "/admin/login?expired=1";
        return;
      }
      // aquí el vendedor no autorizado -> abre modal pro
      if (r.status === 403) {
        openAccessModal("Solo el Administrador puede ver estas métricas. Puedes solicitar acceso.");   // <-- NUEVO
        return;              // no llenes datos
    }
    if(!r.ok || !d){
        openAccessModal("Ocurrió un error cargando el dashboard.");
        return;
    }

    //const d = await r.json();
  

  // Emitidas
  document.getElementById("ventas_total").textContent = "S/ " + money(d.ventas_total);
  document.getElementById("tickets").textContent = d.tickets;

  // Anuladas (auditoría)
  document.getElementById("anuladas_total").textContent = "S/ " + money(d.anuladas_total || 0);
  document.getElementById("tickets_anulados").textContent = (d.tickets_anulados ?? 0);

  // Stock bajo
  document.getElementById("low_count").textContent = (d.stock_bajo || []).length;

  // Top emitidas
  const top = document.getElementById("top_list");
  const topArr = d.top_productos || [];
  top.innerHTML = topArr.length
    ? topArr.map(x => `<li>• ${x.nombre} — ${money(x.cantidad)}</li>`).join("")
    : `<li class="text-slate-500">Sin datos.</li>`;

  // Alertas stock bajo
  const low = document.getElementById("low_list");
  const lowArr = d.stock_bajo || [];
  low.innerHTML = lowArr.length
    ? lowArr.map(x => `<li>• ${x.nombre} — stock ${money(x.stock)} (min ${money(x.min)})</li>`).join("")
    : `<li class="text-slate-500">Sin alertas ✅</li>`;

  // Top anulaciones
  const ta = document.getElementById("top_anulaciones_list");
  const taArr = d.top_anulaciones || [];
  ta.innerHTML = taArr.length
    ? taArr.map(x => `<li>• ${x.nombre} — ${money(x.cantidad)}</li>`).join("")
    : `<li class="text-slate-500">Sin anulaciones.</li>`;

  // Últimas anuladas
  const ua = document.getElementById("ultimas_anuladas_list");
  const uaArr = d.ultimas_anuladas || [];
  ua.innerHTML = uaArr.length
    ? uaArr.map(x => {
        const f = new Date(x.fecha).toLocaleString();
        return `<li>• Ticket #${x.numero} — S/ ${money(x.total)} <span class="text-xs text-slate-500">(${f})</span></li>`;
      }).join("")
    : `<li class="text-slate-500">No hay anulaciones recientes.</li>`;

  // Exponer refresco (para que al anular puedas actualizar dashboard)
  window.refreshDashboard = loadDashboard;

}

loadDashboard();

// Si es vendedor, mostrar modal encima (pero deja ver la pantalla)
//if (ROLE !== "admin") {
  //openAccessModal("Este módulo requiere autorización del Administrador. Puedes solicitar acceso.");
//}