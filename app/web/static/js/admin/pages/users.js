
const USER_ROLE = document.body?.dataset?.rol || "";

// Nueva funcion para restringir al crear usuario
function showAccessDenied(customText){
  const modal = document.getElementById("access_modal");
  const overlay = document.getElementById("access_overlay");
  const card = document.getElementById("access_card");
  const ok = document.getElementById("access_ok");
  const txt = document.getElementById("access_text");

  if (customText) txt.textContent = customText;

  // mostrar
  modal.classList.remove("hidden");

  // animar (next tick)
  requestAnimationFrame(() => {
    overlay.classList.remove("opacity-0");
    overlay.classList.add("opacity-100");

    card.classList.remove("opacity-0","translate-y-2");
    card.classList.add("opacity-100","translate-y-0");
  });

  function close(){
    overlay.classList.remove("opacity-100");
    overlay.classList.add("opacity-0");

    card.classList.remove("opacity-100","translate-y-0");
    card.classList.add("opacity-0","translate-y-2");

    setTimeout(() => modal.classList.add("hidden"), 200);
  }

  ok.onclick = close;
  overlay.onclick = close;
}
//function showAccessDenied() {
//  alert(
//    "🔒 Acceso restringido\n\n" +
//    "Esta acción requiere autorización del Administrador.\n" +
//    "Solicita permisos para continuar."
//  );
//}

async function api(url, opts={}){
  const r = await fetch(url, {
    ...opts,
    headers: { "Content-Type":"application/json", ...(opts.headers||{}) }
  });

  // nueva funcion para la pagina expirada 
  // ✅ Sesión expirada
  if (r.status === 401) {
    window.location.href = "/admin/login?expired=1";
    return r;
  }
  return r;
}

function esc(s){ return (s||"").toString().replaceAll("<","&lt;").replaceAll(">","&gt;"); }

async function loadUsers(){
  const list = document.getElementById("list");
  list.innerHTML = `<div class="p-3 text-slate-500">Cargando...</div>`;

  const r = await api("/api/v1/admin/users");
  const data = await r.json().catch(()=>[]);
  if(!r.ok){
    list.innerHTML = `<div class="p-3 text-red-600">Error cargando usuarios</div>`;
    return;
  }

  if(!Array.isArray(data) || data.length === 0){
    list.innerHTML = `<div class="p-3 text-slate-500">Aún no hay usuarios.</div>`;
    return;
  }

  list.innerHTML = data.map(u => `
    <div class="p-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
      <div>
        <div class="font-semibold">${esc(u.nombre)} ${esc(u.apellido||"")}</div>
        <div class="text-xs text-slate-500">
          ${esc(u.email)} ${u.username ? "• @" + esc(u.username) : ""} • Rol: <b>${esc(u.rol)}</b>
        </div>
      </div>
      <div class="text-xs text-slate-500">
        Último login: ${u.last_login_at ? esc(u.last_login_at) : "—"}
      </div>
    </div>
  `).join("");
}

function openModal(){ document.getElementById("modal").classList.remove("hidden"); }
function closeModal(){ document.getElementById("modal").classList.add("hidden"); }

// document.getElementById("btn_open").onclick = openModal;
//document.getElementById("btn_open").onclick = () => {
//  if (USER_ROLE !== "admin") return showAccessDenied();
//  openModal();
//};
document.getElementById("btn_open").onclick = () => {
  if (USER_ROLE !== "admin") {
    showAccessDenied("Solo el Administrador puede crear usuarios. Solicita permisos para continuar.");
    return;
  }
  openModal();
};


document.getElementById("btn_close").onclick = closeModal;

document.getElementById("modal").addEventListener("click", (e)=>{
  if(e.target.id === "modal") closeModal();
});


document.getElementById("btn_save").onclick = async () => {
    if (USER_ROLE !== "admin") {
    showAccessDenied();
    return;
  }
  // ... sigue normal
  const msg = document.getElementById("msg");
  msg.textContent = "";

  const payload = {
    nombre: document.getElementById("f_nombre").value.trim(),
    apellido: document.getElementById("f_apellido").value.trim() || null,
    email: document.getElementById("f_email").value.trim(),
    username: document.getElementById("f_username").value.trim() || null,
    telefono: document.getElementById("f_telefono").value.trim() || null,
    rol: document.getElementById("f_rol").value,
  };

  if(!payload.nombre || !payload.email){
    msg.textContent = "Falta nombre o email.";
    return;
  }

  const r = await api("/api/v1/admin/users", {
    method:"POST",
    body: JSON.stringify(payload)
  });

  const data = await r.json().catch(()=> ({}));
  if(!r.ok){
    msg.textContent = data.detail || "Error creando usuario";
    return;
  }

  msg.className = "text-sm mt-3 text-green-600";
  msg.textContent = "✅ Usuario creado. Se envió el link para crear contraseña.";

  // limpiar
  ["f_nombre","f_apellido","f_email","f_username","f_telefono"].forEach(id=>document.getElementById(id).value="");
  document.getElementById("f_rol").value = "vendedor";

  await loadUsers();
  setTimeout(()=> closeModal(), 800);
};

loadUsers();