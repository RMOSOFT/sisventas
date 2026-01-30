
if (document.body?.dataset?.page !== "solicitudes") {
  // NO estamos en solicitudes => no ejecutar nada
  // Esto evita que se meta en otras páginas
  console.debug("solicitudes.js skipped");
} else {
  // ... TODO tu código acá adentro
  function esc(s){ return (s||"").toString().replaceAll("<","&lt;").replaceAll(">","&gt;"); }

    async function apiJson(url, opts = {}) {
      const r = await fetch(url, {
        ...opts,
        headers: { "Content-Type": "application/json", ...(opts.headers || {}) }
      });
      const data = await r.json().catch(() => null);
      return { r, data };
    }

    function recursoLabel(x){
      if (x === "dashboard") return "Dashboard";
      return x;
    }

    async function loadRequests(){
      const tbody = document.getElementById("req_rows");
      const empty = document.getElementById("req_empty");
      const err   = document.getElementById("req_err");

      err.classList.add("hidden");
      empty.classList.add("hidden");
      tbody.innerHTML = `<tr><td class="p-3 text-slate-500" colspan="5">Cargando...</td></tr>`;

      const { r, data } = await apiJson("/api/v1/admin/access/requests");

      // ✅ sesión expirada
      if (r.status === 401) {
        location.href = "/admin/login?expired=1";
        return;
      }

      // ✅ no es admin
      if (r.status === 403) {
        tbody.innerHTML = "";
        err.textContent = "🔒 Solo el Administrador puede ver solicitudes.";
        err.classList.remove("hidden");
        return;
      }

      if(!r.ok){
        tbody.innerHTML = "";
        err.textContent = (data && data.detail) ? data.detail : "Error cargando solicitudes.";
        err.classList.remove("hidden");
        return;
      }

      const rows = Array.isArray(data) ? data : [];
      if(rows.length === 0){
        tbody.innerHTML = "";
        empty.classList.remove("hidden");
        return;
      }

      tbody.innerHTML = rows.map(x => `
        <tr>
          <td class="p-3">
            <div class="font-semibold">${esc(x.user?.nombre || "")} ${esc(x.user?.apellido || "")}</div>
            <div class="text-xs text-slate-500">${esc(x.user?.email || "")} • ${esc(x.user?.rol || "")}</div>
          </td>
          <td class="p-3">${esc(recursoLabel(x.recurso))}</td>
          <td class="p-3 text-slate-600">${esc(x.motivo || "—")}</td>
          <td class="p-3 text-slate-500">${esc(x.created_at || "")}</td>
          <td class="p-3">
            <div class="flex justify-end gap-2">
              <button data-id="${x.id}" class="btn-deny rounded-lg px-3 py-1.5 border border-slate-200 hover:bg-slate-50">
                Denegar
              </button>
              <button data-id="${x.id}" class="btn-approve rounded-lg px-3 py-1.5 bg-blue-700 text-white hover:bg-blue-600">
                Aprobar
              </button>
            </div>
          </td>
        </tr>
      `).join("");

      document.querySelectorAll(".btn-approve").forEach(btn => {
        btn.addEventListener("click", async () => {
          const id = Number(btn.dataset.id);
          btn.disabled = true;
          await apiJson("/api/v1/admin/access/approve", { method:"POST", body: JSON.stringify({ id }) });
          await loadRequests();
        });
      });

      document.querySelectorAll(".btn-deny").forEach(btn => {
        btn.addEventListener("click", async () => {
          const id = Number(btn.dataset.id);
          btn.disabled = true;
          await apiJson("/api/v1/admin/access/deny", { method:"POST", body: JSON.stringify({ id }) });
          await loadRequests();
        });
      });
    }

    /*
    // ✅ GUARD PRO: solo corre si existe la tabla de solicitudes
    if (document.getElementById("req_rows")) {
        document.getElementById("req_btn_refresh")?.addEventListener("click", loadRequests);
      
        let reqTimer = setInterval(loadRequests, 10000);
        window.addEventListener("beforeunload", () => clearInterval(reqTimer));
        loadRequests();

        //setInterval(loadRequests, 10000);
        //loadRequests();
    }
    */

    document.getElementById("req_btn_refresh")?.addEventListener("click", loadRequests);

    let reqTimer = setInterval(loadRequests, 10000);
    window.addEventListener("beforeunload", () => clearInterval(reqTimer));
    loadRequests();
}



/*
function esc(s){ return (s||"").toString().replaceAll("<","&lt;").replaceAll(">","&gt;"); }

async function apiJson(url, opts = {}) {
  const r = await fetch(url, {
    ...opts,
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) }
  });
  const data = await r.json().catch(() => null);
  return { r, data };
}

function recursoLabel(x){
  if (x === "dashboard") return "Dashboard";
  return x;
}

async function loadRequests(){
  const tbody = document.getElementById("req_rows");
  const empty = document.getElementById("req_empty");
  const err   = document.getElementById("req_err");

  err.classList.add("hidden");
  empty.classList.add("hidden");
  tbody.innerHTML = `<tr><td class="p-3 text-slate-500" colspan="5">Cargando...</td></tr>`;

  const { r, data } = await apiJson("/api/v1/admin/access/requests");

  // ✅ sesión expirada
  if (r.status === 401) {
    location.href = "/admin/login?expired=1";
    return;
  }

  // ✅ no es admin
  if (r.status === 403) {
    tbody.innerHTML = "";
    err.textContent = "🔒 Solo el Administrador puede ver solicitudes.";
    err.classList.remove("hidden");
    return;
  }

  if(!r.ok){
    tbody.innerHTML = "";
    err.textContent = (data && data.detail) ? data.detail : "Error cargando solicitudes.";
    err.classList.remove("hidden");
    return;
  }

  const rows = Array.isArray(data) ? data : [];
  if(rows.length === 0){
    tbody.innerHTML = "";
    empty.classList.remove("hidden");
    return;
  }

  tbody.innerHTML = rows.map(x => `
    <tr>
      <td class="p-3">
        <div class="font-semibold">${esc(x.user?.nombre || "")} ${esc(x.user?.apellido || "")}</div>
        <div class="text-xs text-slate-500">${esc(x.user?.email || "")} • ${esc(x.user?.rol || "")}</div>
      </td>
      <td class="p-3">${esc(recursoLabel(x.recurso))}</td>
      <td class="p-3 text-slate-600">${esc(x.motivo || "—")}</td>
      <td class="p-3 text-slate-500">${esc(x.created_at || "")}</td>
      <td class="p-3">
        <div class="flex justify-end gap-2">
          <button data-id="${x.id}" class="btn-deny rounded-lg px-3 py-1.5 border border-slate-200 hover:bg-slate-50">
            Denegar
          </button>
          <button data-id="${x.id}" class="btn-approve rounded-lg px-3 py-1.5 bg-blue-700 text-white hover:bg-blue-600">
            Aprobar
          </button>
        </div>
      </td>
    </tr>
  `).join("");

  document.querySelectorAll(".btn-approve").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = Number(btn.dataset.id);
      btn.disabled = true;
      await apiJson("/api/v1/admin/access/approve", { method:"POST", body: JSON.stringify({ id }) });
      await loadRequests();
    });
  });

  document.querySelectorAll(".btn-deny").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = Number(btn.dataset.id);
      btn.disabled = true;
      await apiJson("/api/v1/admin/access/deny", { method:"POST", body: JSON.stringify({ id }) });
      await loadRequests();
    });
  });
}

// ✅ GUARD PRO: solo corre si existe la tabla de solicitudes
if (document.getElementById("req_rows")) {
  document.getElementById("req_btn_refresh")?.addEventListener("click", loadRequests);
  setInterval(loadRequests, 10000);
  loadRequests();
}

*/