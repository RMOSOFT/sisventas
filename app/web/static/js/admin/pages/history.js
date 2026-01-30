// history.js (PRO)
(() => {
  // ✅ Guard robusto: si no existe la tabla del historial, no hagas nada
  const rowsEl = document.getElementById("his_rows");
  if (!rowsEl) return;

  let LAST_REQ = 0;

  const FILTERS = { actor_id: "", target_id: "" }; // ✅ declarar ANTES

  function esc(s){
    return (s||"").toString().replaceAll("<","&lt;").replaceAll(">","&gt;");
  }

  async function apiJson(url, opts = {}) {
    const r = await fetch(url, {
      ...opts,
      headers: { "Content-Type":"application/json", ...(opts.headers||{}) }
    });
    const data = await r.json().catch(()=>null);
    return { r, data };
  }

  function fmtDate(x){
    if(!x) return "—";
    try { return new Date(x).toLocaleString(); } catch { return String(x); }
  }

  function buildUrl(){
    const params = new URLSearchParams();

    const q = document.getElementById("q")?.value?.trim();
    const event = document.getElementById("event")?.value?.trim();

    if (q) params.set("q", q);
    if (event) params.set("event", event);

    if (FILTERS.actor_id) params.set("actor_id", FILTERS.actor_id);
    if (FILTERS.target_id) params.set("target_id", FILTERS.target_id);

    const s = params.toString();
    return "/api/v1/admin/history" + (s ? `?${s}` : "");
  }

  function toggle(el, show){
    if(!el) return;
    el.classList.toggle("hidden", !show);
  }

  function setBtnLabel(btn, prefix, user){
    if(!btn) return;
    if(!user) btn.textContent = `${prefix}: Todos`;
    else btn.textContent = `${prefix}: ${user.nombre} ${user.apellido} • ${user.rol}`;
  }

  async function loadUsers(q){
    const { r, data } = await apiJson(`/api/v1/admin/users/min?q=${encodeURIComponent(q||"")}`);
    if(!r.ok) return [];
    return Array.isArray(data) ? data : [];
  }

  function renderUserList(listEl, users, onPick){
    if(!listEl) return;

    listEl.innerHTML = `
      <button class="w-full text-left px-3 py-2 hover:bg-slate-50" data-id="">
        ✅ Todos
      </button>
      ${users.map(u => `
        <button class="w-full text-left px-3 py-2 hover:bg-slate-50" data-id="${u.id}">
          <div class="font-semibold">${esc(u.nombre)} ${esc(u.apellido)}</div>
          <div class="text-xs text-slate-500">${esc(u.email||"")} • ${esc(u.rol||"")}</div>
        </button>
      `).join("")}
    `;

    listEl.querySelectorAll("button").forEach(b=>{
      b.addEventListener("click", ()=>{
        const id = b.dataset.id || "";
        const user = users.find(x => String(x.id) === String(id)) || null;
        onPick(id, user);
      });
    });
  }

  async function setupUserDropdown({ btnId, ddId, qId, listId, prefix, onSelect }){
    const btn = document.getElementById(btnId);
    const dd  = document.getElementById(ddId);
    const qIn = document.getElementById(qId);
    const list= document.getElementById(listId);
    if(!btn || !dd || !qIn || !list) return;

    btn.addEventListener("click", async ()=>{
      const isOpen = !dd.classList.contains("hidden");
      toggle(dd, !isOpen);

      if(!isOpen){
        qIn.value = "";
        const users = await loadUsers("");
        renderUserList(list, users, (id, user)=>{
          onSelect(id, user);
          toggle(dd, false);
          loadHistory(); // refresca
        });
        qIn.focus();
      }
    });

    qIn.addEventListener("input", async ()=>{
      const users = await loadUsers(qIn.value);
      renderUserList(list, users, (id, user)=>{
        onSelect(id, user);
        toggle(dd, false);
        loadHistory();
      });
    });

    document.addEventListener("click", (e)=>{
      if(!dd.contains(e.target) && !btn.contains(e.target)){
        toggle(dd, false);
      }
    });
  }

  async function loadHistory(){
    const reqId = ++LAST_REQ;

    const err   = document.getElementById("his_err");
    const emptyRow = document.getElementById("his_emptyRow");

    err?.classList.add("hidden");
    emptyRow?.classList.add("hidden");
    rowsEl.innerHTML = `<tr><td class="p-3 text-slate-500" colspan="4">Cargando...</td></tr>`;

    const { r, data } = await apiJson(buildUrl());

    if (reqId !== LAST_REQ) return;

    if (r.status === 401) { location.href = "/admin/login?expired=1"; return; }
    if (r.status === 403) {
      rowsEl.innerHTML = "";
      if(err){ err.textContent = "🔒 Solo el Administrador puede ver el historial."; err.classList.remove("hidden"); }
      return;
    }
    if (!r.ok) {
      rowsEl.innerHTML = "";
      if(err){ err.textContent = (data && data.detail) ? data.detail : "Error cargando historial."; err.classList.remove("hidden"); }
      return;
    }

    const arr = Array.isArray(data) ? data : [];
    if (arr.length === 0) {
      rowsEl.innerHTML = "";
      emptyRow?.classList.remove("hidden");
      return;
    }

    rowsEl.innerHTML = arr.map(x => {
      const actor  = x.actor_name || (x.actor_user_id ? `Usuario #${x.actor_user_id}` : "—Sin destinatario");
      const target = x.target_name || (x.target_user_id ? `Usuario #${x.target_user_id}` : "—Sin destinatario");

      return `
        <tr class="border-t">
          <td class="p-3 text-slate-500 whitespace-nowrap">${esc(fmtDate(x.created_at))}</td>
          <td class="p-3">
            <div class="font-semibold">${esc(x.event_label || x.event || "Evento")}</div>
            <div class="text-xs text-slate-400">${esc(actor)} • ${esc(target)}</div>
          </td>
          <td class="p-3 text-slate-700">${esc(x.title || "—")}</td>
          <td class="p-3 text-slate-600">${esc(x.message || "—")}</td>
        </tr>
      `;
    }).join("");
  }

  // ✅ Botón exportar PDF
  document.getElementById("btn_export_pdf")?.addEventListener("click", ()=>{
    const url = buildUrl().replace("/api/v1/admin/history", "/api/v1/admin/history/pdf");
    window.open(url, "_blank");
  });

  // ✅ Dropdowns Actor/Target
  setupUserDropdown({
    btnId:"actor_btn", ddId:"actor_dd", qId:"actor_q", listId:"actor_list",
    prefix:"👤 Actor",
    onSelect:(id, user)=>{
      FILTERS.actor_id = id;
      setBtnLabel(document.getElementById("actor_btn"), "👤 Actor", user);
    }
  });

  setupUserDropdown({
    btnId:"target_btn", ddId:"target_dd", qId:"target_q", listId:"target_list",
    prefix:"🎯 Target",
    onSelect:(id, user)=>{
      FILTERS.target_id = id;
      setBtnLabel(document.getElementById("target_btn"), "🎯 Target", user);
    }
  });

  // ✅ eventos UI
  document.getElementById("his_btn_refresh")?.addEventListener("click", loadHistory);
  document.getElementById("q")?.addEventListener("keydown", (e)=>{ if(e.key==="Enter") loadHistory(); });
  document.getElementById("event")?.addEventListener("change", loadHistory);

  // ✅ refresco
  const timer = setInterval(loadHistory, 10000);
  window.addEventListener("beforeunload", () => clearInterval(timer));

  loadHistory();
})();
/*-------------------------------------------*/





/* Codigo de mejor funcion
let LAST_REQ = 0;

function esc(s){
  return (s||"").toString().replaceAll("<","&lt;").replaceAll(">","&gt;");
}

async function apiJson(url, opts = {}) {
  const r = await fetch(url, {
    ...opts,
    headers: { "Content-Type":"application/json", ...(opts.headers||{}) }
  });
  const data = await r.json().catch(()=>null);
  return { r, data };
}

function fmtDate(x){
  if(!x) return "—";
  try { return new Date(x).toLocaleString(); } catch { return String(x); }
}

function buildUrl(){
  const q = document.getElementById("q")?.value?.trim() || "";
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  const s = params.toString();
  return "/api/v1/admin/history" + (s ? `?${s}` : "");
}

async function loadHistory(){
  const reqId = ++LAST_REQ;

  const rows  = document.getElementById("rows");
  const err   = document.getElementById("err");
  const emptyRow = document.getElementById("emptyRow");

  err?.classList.add("hidden");
  emptyRow?.classList.add("hidden");

  if(rows){
    rows.innerHTML = `<tr><td class="p-3 text-slate-500" colspan="4">Cargando...</td></tr>`;
  }

  const { r, data } = await apiJson(buildUrl());

  // ✅ anti-race: si llegó una respuesta vieja, no renderices
  if (reqId !== LAST_REQ) return;

  if (r.status === 401) { location.href = "/admin/login?expired=1"; return; }
  if (r.status === 403) {
    if(rows) rows.innerHTML = "";
    if(err){ err.textContent = "🔒 Solo el Administrador puede ver el historial."; err.classList.remove("hidden"); }
    return;
  }
  if (!r.ok) {
    if(rows) rows.innerHTML = "";
    if(err){ err.textContent = (data && data.detail) ? data.detail : "Error cargando historial."; err.classList.remove("hidden"); }
    return;
  }

  const arr = Array.isArray(data) ? data : [];
  if (arr.length === 0) {
    if(rows) rows.innerHTML = "";
    emptyRow?.classList.remove("hidden");
    return;
  }

  if (rows) {
    rows.innerHTML = arr.map(x => {
      const actor  = x.actor_user_id ? `actor #${esc(x.actor_user_id)}` : "—";
      const target = x.target_user_id ? `target #${esc(x.target_user_id)}` : "—";

      return `
        <tr class="border-t">
          <td class="p-3 text-slate-500 whitespace-nowrap">${esc(fmtDate(x.created_at))}</td>
          <td class="p-3">
            <div class="font-semibold">${esc(x.event || "evento")}</div>
            <div class="text-xs text-slate-400">${actor} • ${target}</div>
          </td>
          <td class="p-3 text-slate-700">${esc(x.title || "—")}</td>
          <td class="p-3 text-slate-600">${esc(x.message || "—")}</td>
        </tr>
      `;
    }).join("");
  }
}

document.getElementById("btn_refresh")?.addEventListener("click", loadHistory);
document.getElementById("q")?.addEventListener("keydown", (e)=>{ if(e.key==="Enter") loadHistory(); });

loadHistory();

// Si quieres “permanente” sin que parpadee, sube a 30s o quítalo:
setInterval(loadHistory, 30000);
*/






/* Funciono con este codigo
function esc(s){
  return (s||"").toString().replaceAll("<","&lt;").replaceAll(">","&gt;");
}

async function apiJson(url, opts = {}) {
  const r = await fetch(url, {
    ...opts,
    headers: { "Content-Type":"application/json", ...(opts.headers||{}) }
  });
  const data = await r.json().catch(()=>null);
  return { r, data };
}

function fmtDate(x){
  if(!x) return "—";
  try { return new Date(x).toLocaleString(); } catch { return String(x); }
}

function buildUrl(){
  const q = document.getElementById("q")?.value?.trim() || "";
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  const s = params.toString();
  return "/api/v1/admin/history" + (s ? `?${s}` : "");
}

async function loadHistory(){
  const rows  = document.getElementById("rows");
  const err   = document.getElementById("err");
  const empty = document.getElementById("empty");

  err.classList.add("hidden");
  empty.classList.add("hidden");
  rows.innerHTML = `<tr><td class="p-3 text-slate-500" colspan="4">Cargando...</td></tr>`;

  const { r, data } = await apiJson(buildUrl());

  if (r.status === 401) { location.href = "/admin/login?expired=1"; return; }

  if (r.status === 403) {
    rows.innerHTML = "";
    err.textContent = "🔒 Solo el Administrador puede ver el historial.";
    err.classList.remove("hidden");
    return;
  }

  if (!r.ok) {
    rows.innerHTML = "";
    err.textContent = (data && data.detail) ? data.detail : "Error cargando historial.";
    err.classList.remove("hidden");
    return;
  }

  const arr = Array.isArray(data) ? data : [];
  if (arr.length === 0) { rows.innerHTML = ""; empty.classList.remove("hidden"); return; }

  rows.innerHTML = arr.map(x => {
    const actor  = x.actor_user_id ? `actor #${esc(x.actor_user_id)}` : "—";
    const target = x.target_user_id ? `target #${esc(x.target_user_id)}` : "—";

    return `
      <tr class="border-t">
        <td class="p-3 text-slate-500 whitespace-nowrap">${esc(fmtDate(x.created_at))}</td>
        <td class="p-3">
          <div class="font-semibold">${esc(x.event || "evento")}</div>
          <div class="text-xs text-slate-400">${actor} • ${target}</div>
        </td>
        <td class="p-3 text-slate-700">${esc(x.title || "—")}</td>
        <td class="p-3 text-slate-600">${esc(x.message || "—")}</td>
      </tr>
    `;
  }).join("");
}

document.getElementById("btn_refresh")?.addEventListener("click", loadHistory);
document.getElementById("q")?.addEventListener("keydown", (e)=>{ if(e.key==="Enter") loadHistory(); });

loadHistory();
setInterval(loadHistory, 10000);
*/




