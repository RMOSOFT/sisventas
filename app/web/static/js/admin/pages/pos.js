/* =========================
   POS RMOSOFT (LIMPIO)
   - 1 carrito: CART
   - 1 lista: PRODUCTS
   - 1 cliente: selectedClient
   - 1 cobro: cobrar()
========================= */

let PRODUCTS = [];
let CART = []; // {producto_id, nombre, precio, cantidad, descuento}
let selectedClient = null; // {id, tipo_doc, num_doc, razon_social, direccion}
let lastSale = null; // {id, numero, total, estado, can_cancel}
let clientPrefill = null; // ✅ global (arriba del archivo pos.js)

// Funcion para mensajes de productos
function flashMsg(text, type="info", ms=2200){
  const el = $("msg");
  if(!el) return;

  const styles = {
    success: "bg-emerald-50 border-emerald-300 text-emerald-800",
    danger:  "bg-rose-50 border-rose-300 text-rose-800",
    warning: "bg-amber-50 border-amber-300 text-amber-800",
    info:    "bg-slate-50 border-slate-300 text-slate-800",
  };

  const icon = {
    success: "✅",
    danger: "🗑️",
    warning: "⚠️",
    info: "ℹ️",
  };

  el.innerHTML = `
    <div class="border rounded-xl px-3 py-2 text-sm ${styles[type] || styles.info}">
      <span class="mr-2">${icon[type] || icon.info}</span>${text}
    </div>
  `;

  clearTimeout(window.__msgTimer);
  window.__msgTimer = setTimeout(() => { el.innerHTML = ""; }, ms);
}

//funcion para poner mensajes a la derecha del sistema principal
function toastMsg(text, type="success", ms=2500){
  const area = document.getElementById("toast-area");
  if(!area) return;

  const colors = {
    success: "✅ bg-green-600",
    info: "ℹ️ bg-blue-600",
    warning: "⚠️ bg-orange-500 text-white",//"⚠️ bg-yellow-500 text-black",
    danger: "🗑️ bg-red-600"
  };

  const el = document.createElement("div");
  el.className = `
    ${colors[type] || colors.success}
    text-white text-sm px-4 py-3 rounded-xl shadow-lg
    animate-slide-in pointer-events-auto
  `;
  el.textContent = text;

  area.appendChild(el);

  setTimeout(() => {
    el.classList.add("opacity-0");
    setTimeout(() => el.remove(), 300);
  }, ms);
}


const $ = (id) => document.getElementById(id);

function esc(s){ return (s||"").toString().replaceAll("<","&lt;").replaceAll(">","&gt;"); }
function money(x){ return Number(x || 0).toFixed(2); }

async function apiJson(url, opts = {}) {
  const r = await fetch(url, {
    ...opts,
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) }
  });
  const data = await r.json().catch(() => null);
  return { r, data };
}

/* ---------- Mensajes UI ---------- */
function setMsg(text, ok=true){
  const el = $("msg");
  if(!el) return;
  el.className = "text-sm mt-2 " + (ok ? "text-green-700" : "text-red-700");
  el.textContent = text || "";
}

/* ---------- Productos ---------- 
<div class="border rounded-xl p-3 flex items-center justify-between gap-3">
      <div>
        <div class="font-semibold">${esc(p.nombre)}</div>
        <div class="text-xs text-slate-500">Stock: ${money(p.stock_actual)} • Precio: S/ ${money(p.precio)}</div>
      </div>
      <button data-id="${p.id}" class="px-3 py-2 rounded-lg border hover:bg-slate-50 font-semibold">+</button>
    </div>

    <div class="border rounded-2xl p-3 bg-white hover:bg-slate-50 transition flex items-center justify-between gap-3">
      <div>
        <div class="font-semibold">${esc(p.nombre)}</div>
        <div class="text-xs text-slate-500">Stock: ${money(p.stock_actual)} • Precio: S/ ${money(p.precio)}</div>
      </div>
      <button data-id="${p.id}" class="h-10 w-10 rounded-xl border bg-white hover:bg-slate-100 active:scale-[0.98] font-bold">+</button>
    </div>*/
function renderProducts(list){
  const grid = $("products_grid");
  if(!grid) return;

  grid.innerHTML = list.map(p => `
    <div class="rounded-2xl border border-slate-200 bg-gradient-to-b from-white to-slate-50 p-3 hover:border-slate-300 hover:shadow-sm transition flex items-center justify-between gap-3">
        <div class="min-w-0">
            <div class="font-semibold text-slate-900 truncate">${esc(p.nombre)}</div>
            <div class="text-xs text-slate-600">Stock: ${money(p.stock_actual)} • Precio: S/ ${money(p.precio)}</div>
        </div>
        <button data-id="${p.id}" 
            class="h-10 w-10 shrink-0 rounded-xl bg-[#0B1F3A] text-white hover:opacity-95 active:scale-[0.98] font-bold shadow-sm">
            +
        </button>
    </div>
  `).join("");

  grid.querySelectorAll("button[data-id]").forEach(btn => {
    btn.addEventListener("click", () => addToCart(Number(btn.dataset.id)));
  });
}

async function loadProducts(){
  const { r, data } = await apiJson("/api/v1/admin/products");
  if(!r.ok){
    toastMsg("Error al cargar los productos", "danger", 3000);
    setMsg("Error cargando productos", false);
    return;
  }
  PRODUCTS = Array.isArray(data) ? data : [];
  renderProducts(PRODUCTS);
}

/* ---------- Carrito ---------- */
function renderCart() {
  const tbody = $("cart");
  if (!tbody) return;

  // ✅ usa tu carrito real: CART
  if (!CART || CART.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="px-3 py-6 text-center text-slate-500">
          Carrito vacío
        </td>
      </tr>
    `;
    flashMsg("Carrito vacío. Agrega productos para continuar.", "info", 2500);
    renderTotals();
    return;
  }

  tbody.innerHTML = CART.map((it, idx) => {
    const nombre = it.nombre ?? "";
    const precio = Number(it.precio || 0);
    const cantidad = Number(it.cantidad || 1);
    const descuento = Number(it.descuento || 0);
    const totalLinea = (precio * cantidad) - descuento;

    return `
      <tr class="align-top">
        <td class="px-3 py-2">
          <input
            class="w-20 border rounded-lg px-2 py-1"
            type="number" min="1" step="1"
            value="${cantidad}"
            data-idx="${idx}" data-role="qty"
          />
        </td>

        <td class="px-3 py-2">
          <div class="font-semibold text-slate-900 break-words">
            ${escapeHtml(nombre)}
          </div>
        </td>

        <td class="px-3 py-2 text-right tabular-nums">
          ${money(precio)}
        </td>

        <td class="px-3 py-2 text-right">
          <input
            class="w-24 border rounded-lg px-2 py-1 text-right tabular-nums"
            type="number" min="0" step="0.01"
            value="${descuento}"
            data-idx="${idx}" data-role="disc"
          />
        </td>

        <td class="px-3 py-2 text-right font-semibold tabular-nums">
          ${money(totalLinea)}
        </td>

        <td class="px-3 py-2 text-right">
          <button
            class="text-xs font-semibold text-red-700 hover:underline"
            data-idx="${idx}" data-role="remove"
          >
            Quitar
          </button>
        </td>
      </tr>
    `;
  }).join("");

  // ✅ delegación de eventos y mensaje de actualizacion de productos
  tbody.oninput = (e) => {
    const el = e.target;
    const idx = Number(el?.dataset?.idx);
    const role = el?.dataset?.role;
    if (!Number.isFinite(idx) || !role) return;

    if (role === "qty") {
      let v = Math.max(1, Number(el.value || 1));
      CART[idx].cantidad = v;
      toastMsg(`Cantidad actualizada (x${v})`, "info", 1800);//${qty}
      renderTotals();
      renderCart();
    }

    if (role === "disc") {
      let v = Math.max(0, Number(el.value || 0));
      CART[idx].descuento = v;
      renderTotals();
      renderCart();
    }
  };
  //Aqui mensaje al quitar el producto del carrito
  tbody.onclick = (e) => {
    const el = e.target;
    const idx = Number(el?.dataset?.idx);
    const role = el?.dataset?.role;
    if (!Number.isFinite(idx) || role !== "remove") return;

    //nuevo codigo para el mensaje
    const name = CART[idx]?.nombre || "Producto"

    CART.splice(idx, 1);

    //Mensaje al quitar productos
    toastMsg(`Producto quitado: ${name}`, "danger");
    flashMsg(`Producto quitado: ${name}`, "danger", 2000);
    //flashMsg(`Producto eliminado`, "danger", 1500);

    renderTotals();
    renderCart();
  };

  renderTotals();
}

//Nueva funcion agregada
function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

//Nuevas funciones
function clearClientPrefillUI(){
  clientPrefill = null;
  $("cli_prefill_box")?.classList.add("hidden");
  ["pf_nombres","pf_ap_pat","pf_ap_mat","pf_dir","pf_cod","pf_ec","pf_ubigeo"].forEach(id=>{
    if($(id)) $(id).value = "";
  });
}

//Nueva funciones
function renderClientPrefillUI(data){
  clientPrefill = data || {};
  $("cli_prefill_box")?.classList.remove("hidden");

  // Helpers (agarra snake_case o camelCase)
  const nombres =
    clientPrefill.nombres ||
    clientPrefill.nombre_completo ||                 // DNI
    clientPrefill.nombre_o_razon_social ||           // RUC
    clientPrefill.razon_social ||
    "";

  const apPat = clientPrefill.apellido_paterno || clientPrefill.apellidoPaterno || "";
  const apMat = clientPrefill.apellido_materno || clientPrefill.apellidoMaterno || "";

  const dir =
    clientPrefill.direccion_completa ||
    clientPrefill.direccion ||
    clientPrefill.domicilioFiscal ||
    "";

  const cod =
    clientPrefill.codigo_verificacion ??
    clientPrefill.codVerifica ??
    clientPrefill.codigoVerificacion ??
    "";

  // ubigeo puede venir como string, o ubigeo_reniec / ubigeo_sunat, o array raro
  let ubg =
    clientPrefill.ubigeo ||
    clientPrefill.ubigeo_reniec ||
    clientPrefill.ubigeo_sunat ||
    "";
  if(Array.isArray(ubg)) ubg = ubg.filter(Boolean).join("-");

  const ec = clientPrefill.estadoCivil || clientPrefill.estado_civil || "";

  // Pintar en inputs
  $("pf_nombres").value = String(nombres).trim();
  $("pf_ap_pat").value  = String(apPat).trim();
  $("pf_ap_mat").value  = String(apMat).trim();
  $("pf_dir").value     = String(dir).trim();
  $("pf_cod").value     = String(cod).trim();
  $("pf_ec").value      = String(ec).trim();
  $("pf_ubigeo").value  = String(ubg).trim();
}



function renderTotals(){
  let subtotal = 0;
  for(const it of CART){
    subtotal += (Number(it.precio)*Number(it.cantidad)) - Number(it.descuento||0);
  }

  const val = money(subtotal);

  //$("subtotal").textContent = money(subtotal);
  // ✅ principal (derecha)
  if($("subtotal")) $("subtotal").textContent = val;
  // ✅ opcional (pie del carrito)
  if($("subtotal_top")) $("subtotal_top").textContent = val;
}

function addToCart(producto_id){
  const p = PRODUCTS.find(x => x.id === producto_id);
  if(!p) return;

  //Nuevo codigo para los mensajes
  let qty = 1;

  const existing = CART.find(x => x.producto_id === producto_id);
  if(existing){
    existing.cantidad += 1;
    //Nuevo mensaje al agregar el producto
    qty = existing.cantidad;
    flashMsg(`Cantidad actualizada: ${p.nombre} (x${qty})`, "info", 1800);

  } else {
    CART.push({
      producto_id,
      nombre: p.nombre,
      precio: Number(p.precio),
      cantidad: 1,
      descuento: 0
    });
    //toastShow(`Agregado: ${prod.nombre}`, "success", 1400);
    toastMsg(`Producto agregado: ${p.nombre}`, "success");
    flashMsg(`Agregado al carrito: ${p.nombre} (x1)`, "success", 2000);
  }
  //flashMsg(`Agregado al carrito: ${prod.nombre} (x${cantidad})`, "success");
  renderCart();
  renderTotals();
}

function clearCart(){
  CART = [];
  renderCart();
  renderTotals();
}

function clearSelectedClient(){
    //mensaje para deseleccionar la cliente
    const oldName = selectedClient?.razon_social || "Cliente";
  selectedClient = null;
  renderSelectedClient();
  flashMsg(`${oldName} quitado de la venta.`, "danger", 2000);
}

/* ---------- Clientes ---------- */
function renderSelectedClient(){
  const box = $("cli_selected");
  if(!box) return;

  if(!selectedClient){
    box.innerHTML = `<span class="text-slate-500">Sin cliente seleccionado</span>`;
    return;
  }

  box.innerHTML = `
    <div class="flex items-center justify-between">
      <div>
        <div class="text-green-700 font-semibold">Cliente seleccionado ✅</div>
        <div class="mt-1">
          <span class="inline-block text-[11px] px-2 py-0.5 rounded bg-slate-100 border">${esc(selectedClient.tipo_doc||"DOC")}</span>
          <span class="ml-1 font-semibold">${esc(selectedClient.num_doc||"")}</span>
        </div>
        <div class="text-sm font-semibold mt-1">${esc(selectedClient.razon_social||"")}</div>
        <div class="text-xs text-slate-600">${esc(selectedClient.direccion||"")}</div>
      </div>
      <button id="cli_btn_clear" class="text-xs underline text-slate-600 hover:text-black">Quitar</button>
    </div>
  `;

  $("cli_btn_clear")?.addEventListener("click", clearSelectedClient);
}

function renderClientResults(list){
  const box = $("cli_results");
  if(!box) return;

  if(!list || list.length === 0){
    box.innerHTML = `<div class="text-slate-500 text-xs mt-2">No encontrado. Puedes crear cliente rápido.</div>`;
    return;
  }

  box.innerHTML = list.map(c => `
    <button data-id="${c.id}" class="w-full text-left border rounded-lg px-3 py-2 mt-2 hover:bg-slate-50">
      <div class="flex items-center justify-between">
        <div class="font-semibold">${esc(c.razon_social || "")}</div>
        <div class="text-xs text-slate-500">${esc(c.tipo_doc||"")} ${esc(c.num_doc||"")}</div>
      </div>
      <div class="text-xs text-slate-500">${esc(c.direccion||"")}</div>
    </button>
  `).join("");

  box.querySelectorAll("button[data-id]").forEach(b => {
    b.addEventListener("click", () => {
      const id = Number(b.dataset.id);
      selectedClient = list.find(x => x.id === id) || null;
      renderSelectedClient();
      //Mensaje al seleccionar cliente encontrado
      toastMsg(`Cliente seleccionado: ${selectedClient.razon_social}`, "success");
      flashMsg(`Cliente seleccionado: ${selectedClient?.razon_social || "OK"}`, "success", 2200);
      //flashMsg("Cliente listo para la venta", "info", 2000);
      //setMsg("Cliente seleccionado ✅", true);
    });
  });
}


// Nueva funcion agregada 
async function searchClient(){
  const q = $("cli_q")?.value?.trim() || "";
  if(!q){
    renderClientResults([]);
    flashMsg("Ingresa DNI/RUC/NOMBRE para buscar.", "warning", 2200);
    //setMsg("Ingresa DNI/RUC/NOMBRE", false);
    clearClientPrefillUI();
    return;
  }

  // 1) BD primero
  const { r, data } = await apiJson(`/api/v1/admin/clientes/search?q=${encodeURIComponent(q)}`);
  if(!r.ok){
    toastMsg("Error buscando cliente", "danger", 3000);
    setMsg("Error buscando cliente", false);
    clearClientPrefillUI();
    return;
  }

  const list = Array.isArray(data) ? data : [];
  renderClientResults(list);

  //Mensaje para al encontrar al cliente en la base de datos
  toastMsg("Cliente encontrado y cargado", "success", 2500);
  flashMsg(`Cliente encontrado en BD: ${list[0]?.razon_social || "OK"}`, "success", 2200);

  // Si existe en BD, ocultamos prefill proveedor
  if(list.length > 0){
    clearClientPrefillUI();
    return;
  }

  // 2) Si no existe y es doc, lookup proveedor
  if(/^\d{8,11}$/.test(q)){
    const tipo = (q.length === 11) ? "RUC" : "DNI";

    const { r: lr, data: luData } = await apiJson(
      `/api/v1/admin/clientes/lookup?tipo=${tipo}&num=${encodeURIComponent(q)}`
    );

    // Nota: tu endpoint siempre devuelve 200 con enabled true/false
    if(luData?.enabled && luData?.data){
      renderClientPrefillUI(luData.data);
      //Mensaje al encontrar datos del proveedor
      flashMsg("Datos encontrados (proveedor). Puedes guardarlo con “Crear cliente rápido”.", "success", 2600);
      //setMsg("✅ Datos encontrados (proveedor). Usa 'Crear cliente rápido' para guardar.", true);
    } else {
      clearClientPrefillUI();
      //Mensaje al no encontrar nada tanto en la base de datos o proveedor
      flashMsg("No encontrado. Puedes crear cliente rápido manual.", "warning", 2500);
      //setMsg("No encontrado. Puedes crear cliente rápido.", false);
    }
    return;
  }

  // Si no es DNI/RUC
  clearClientPrefillUI();
}



function openClientModal(prefillDoc = ""){
  $("cli_modal")?.classList.remove("hidden");
  $("cli_modal_msg").textContent = "";
  const q = prefillDoc || $("cli_q")?.value?.trim() || "";
  if(q){
    $("cli_num").value = q;
    $("cli_tipo").value = (q.length === 11 ? "RUC" : "DNI");
  }
}

function closeClientModal(){ $("cli_modal")?.classList.add("hidden"); }

async function saveQuickClient(){
  const tipo_doc = $("cli_tipo").value;
  const num_doc = $("cli_num").value.trim();
  const razon_social = $("cli_razon").value.trim();
  const direccion = $("cli_dir").value.trim();
  const telefono = $("cli_tel").value.trim();
  const email = $("cli_email").value.trim();
  const msg = $("cli_modal_msg");

  if(!num_doc || num_doc.length < 6){
    msg.className = "text-sm text-red-700";
    msg.textContent = "Documento inválido.";
    return;
  }
  if(!razon_social){
    msg.className = "text-sm text-red-700";
    msg.textContent = "Ingresa nombre / razón social.";
    return;
  }

  const payload = { tipo_doc, num_doc, razon_social, direccion, telefono, email };
  const { r, data } = await apiJson("/api/v1/admin/clientes", { method:"POST", body: JSON.stringify(payload) });

  if(!r.ok){
    msg.className = "text-sm text-red-700";
    msg.textContent = data?.detail || "No se pudo crear el cliente.";
    return;
  }

  selectedClient = data;
  renderSelectedClient();
  closeClientModal();
  //mensaje al crear cliente 
  toastMsg("Cliente creado correctamente", "success", 2500);
  flashMsg(`Cliente creado y seleccionado: ${data?.razon_social || "OK"}`, "success", 2500);
  //setMsg("Cliente creado y seleccionado ✅", true);
}

/* ---------- Modal post-venta ---------- */
function showSaleModal(sale){
  lastSale = sale;

  $("sale_modal_title").textContent = `✅ Venta #${sale.numero}`;
  $("sale_modal_sub").textContent = `• Estado: ${sale.estado || "emitida"} • Total S/ ${money(sale.total)} `;
  $("sale_modal_msg").textContent = "";

  // debajo del titulo
    if(sale.comprobante){
      $("sale_modal_sub").textContent =
        `• ${sale.comprobante} • Estado: ${sale.estado || "emitida"} • Total S/ ${money(sale.total)}`;
    }

  // Imprimir
  $("sale_btn_print").onclick = () => window.open(`/api/v1/admin/sales/${sale.id}/ticket`, "_blank");

  // Nueva venta
  $("sale_btn_new").onclick = () => {
    resetPOSForm(); // limpia carrito + cliente + mensajes
    //clearCart();
    // si quieres, no borres cliente; si quieres modo rápido: deja el cliente
    // clearSelectedClient();
    $("sale_modal")?.classList.add("hidden");
  };

  // Anular
  const btnCancel = $("sale_btn_cancel");
  const canCancel = sale.can_cancel === true;
  btnCancel.classList.toggle("hidden", !canCancel);
  btnCancel.disabled = false;

  btnCancel.onclick = async () => {
    $("sale_modal_msg").className = "text-sm mt-2 text-slate-600";
    $("sale_modal_msg").textContent = "Anulando...";

    // ✅ MENSAJE ARRIBA A LA DERECHA (igual que los demás)
    toastMsg(`Anulando venta #${sale.numero}...`, "info", 1800);
    flashMsg(`Anulando venta #${sale.numero}...`, "info", 1800);

    const { r, data } = await apiJson(`/api/v1/admin/sales/${sale.id}/cancel`, {
      method:"POST",
      body: JSON.stringify({ motivo: "Anulación desde POS" })
    });

    if(!r.ok){
      $("sale_modal_msg").className = "text-sm mt-2 text-red-700";
      $("sale_modal_msg").textContent = data?.detail || "No se pudo anular.";

      // ✅ ERROR ARRIBA A LA DERECHA
      toastMsg(`No se pudo anular • Venta #${sale.numero}`, "danger", 2600);
      flashMsg(data?.detail || `No se pudo anular • Venta #${sale.numero}`, "danger", 2600);
      return;
    }

    $("sale_modal_msg").className = "text-sm mt-2 text-green-700";
    $("sale_modal_msg").textContent = "✅ Venta anulada (stock devuelto y registrado).";
    btnCancel.disabled = true;
    // ✅ OK ARRIBA A LA DERECHA
    toastMsg(`✅ Venta anulada (stock devuelto y registrado).`, "success", 3000);
    flashMsg(`✅ Venta anulada • Ticket #${sale.numero}`, "warning", 3000);
  };

  $("sale_modal")?.classList.remove("hidden");
}


function hideSaleModal(){ $("sale_modal")?.classList.add("hidden"); }

function bindSaleModalUI(){
  $("sale_modal_close")?.addEventListener("click", hideSaleModal);
  $("sale_modal")?.addEventListener("click", (e)=>{
    if(e.target && e.target.id === "sale_modal") hideSaleModal();
  });
}

// Funcion de venta emitida
function buildResumenFromCart(){
  const items = CART.map(x => x.nombre);
  const n_items = CART.reduce((a,x)=> a + Number(x.cantidad || 0), 0);

  let subtotal = 0;
  let descuento = 0;

  for(const it of CART){
    subtotal += Number(it.precio) * Number(it.cantidad || 0);
    descuento += Number(it.descuento || 0);
  }

  const igv = 0; // luego lo activas si quieres (subtotal * 0.18)
  const total = subtotal - descuento + igv;

  return {
    n_items,
    preview: items.slice(0,3),
    subtotal,
    igv,
    descuento,
    total
  };
}

// Funcion resumen del carrito
function renderResumenVenta(resumen, venta){
  // Cantidad de ítems
  $("res_items").textContent = resumen.n_items;

  // Preview productos •
  $("res_preview").innerHTML = resumen.preview
    .map(n => `<div class="text-xs text-slate-700">Producto(s): ${n}</div>`)
    .join("");

  // Totales
  $("res_subtotal").textContent = money(resumen.subtotal);
  $("res_igv").textContent = money(resumen.igv);
  $("res_desc").textContent = money(resumen.descuento);
  $("res_total").textContent = money(resumen.total);

  /* Cliente
  if(venta.cliente){
    $("res_cliente").textContent =
      `${venta.cliente.nombre} · ${venta.cliente.tipo_doc} ${venta.cliente.num_doc}`;
  }
  */
  // Cliente (fallback: selectedClient si el backend no lo devuelve)
  const c = venta?.cliente || selectedClient || null;

  if(c){
    const nombre = c.nombre || c.razon_social || c.nombres || "";
    const tipo = c.tipo_doc || c.tipo || "";
    const num  = c.num_doc || c.numero || "";
    $("res_cliente").textContent = `Nombre: ${nombre}\n${tipo}: ${num}`.trim();
  } else {
    $("res_cliente").textContent = "";
  }

  // Efectivo / Vuelto (si backend lo devuelve)
  const cashBox = $("cash_resume");
  const isCash = (String(venta?.metodo_pago || "").toLowerCase() === "efectivo");

  if(cashBox){
    cashBox.classList.toggle("hidden", !isCash);
  }

  if(isCash){
    if($("res_efectivo")) $("res_efectivo").textContent = "S/ " + money(venta.efectivo_recibido || 0);
    if($("res_vuelto")) $("res_vuelto").textContent = "S/ " + money(venta.vuelto || 0);
  }else{
    if($("res_efectivo")) $("res_efectivo").textContent = "S/ 0.00";
    if($("res_vuelto")) $("res_vuelto").textContent = "S/ 0.00";
  }
}

/* ---------- COBRAR (ÚNICO) ---------- */
async function cobrar(){
  if(CART.length === 0){
    //mensaje al cobrar el producto
    toastMsg("Agrega productos al carrito antes de cobrar.", "warning", 2200);
    flashMsg("Agrega productos al carrito antes de cobrar.", "warning", 2200);
    //setMsg("Agrega productos al carrito.", false);
    return;
  }

  const descuentoTotal = Number($("descuento_total")?.value || 0);
  const metodoPagoRaw = $("metodo_pago")?.value || "efectivo";
  const metodoPago = metodoPagoRaw.toLowerCase();
  // 1️⃣ Construyes el resumen
  const resumen = buildResumenFromCart();

  let efectivoRecibido = 0;
  if(metodoPago === "efectivo"){
    efectivoRecibido = Number($("efectivo_recibido")?.value || 0);

    if(efectivoRecibido < Number(resumen.total || 0)){
      toastMsg("Efectivo insuficiente para completar la venta.", "warning", 2500);
      flashMsg("Efectivo insuficiente. Ingresa un monto mayor o igual al total.", "warning", 3000);
      return;
    }
  }

  const payload = {
    items: CART.map(x => ({
      producto_id: x.producto_id,
      cantidad: Number(x.cantidad),
      descuento: Number(x.descuento || 0)
    })),
    descuento_total: descuentoTotal,
    metodo_pago: metodoPagoRaw,
    cliente_id: selectedClient?.id || null,

    efectivo_recibido: (metodoPago === "efectivo") ? efectivoRecibido : 0 //efectivoRecibido, // Nuevo codigo para el vuelto
  };

  

  const btn = $("btn_cobrar");
  btn.disabled = true;
  setMsg("Procesando...", true);

  // 2️⃣ Envío al backend (fetch /api/v1/admin/sales)
  const { r, data } = await apiJson("/api/v1/admin/sales", { method:"POST", body: JSON.stringify(payload) });

  btn.disabled = false;

  if(!r.ok){
    //mensaje si falla el cobro
    toastMsg("Error al procesar la venta", "danger", 3000);
    flashMsg(data?.detail || "Error al cobrar.", "danger", 2600);
    //flashMsg("Verifique los datos", "danger", 2000);
    //setMsg(data?.detail || "Error al cobrar.", false);
    return;
  }

  // ✅ data debe traer: id, numero, total, estado, can_cancel
  showSaleModal({
    id: data.id,
    numero: data.numero,
    total: data.total,
    estado: data.estado || "emitida",
    metodo_pago: data.metodo_pago,
    efectivo_recibido: data.efectivo_recibido,
    vuelto: data.vuelto,
    can_cancel: Boolean(data.can_cancel),
  });

  // 3️⃣ Pintas el resumen en el modal "Venta emitida"
  renderResumenVenta(resumen, data);

  // limpia carrito
  clearCart();

  // recarga productos (stock actualizado)
  await loadProducts();
  //mensaje si la venta fue exitosa
  toastMsg(`Venta realizada • Ticket #${data.numero}`, "success", 3500);
  flashMsg(`Venta OK • Ticket #${data.numero} • Total S/ ${money(data.total)}`, "success", 2800);
  //flashMsg(`Total S/ ${money(data.total)}`, "success", 3000);
  //setMsg(`Venta OK • Ticket #${data.numero} • Total S/ ${money(data.total)}`, true);
}


// Funcion para el calculo del vuelto
function toggleCashBox(){
  const metodo = ($("metodo_pago")?.value || "efectivo").toLowerCase();
  const box = $("cash_box");
  if(!box) return;

  const isCash = (metodo === "efectivo");
  box.classList.toggle("hidden", !isCash);

  if(!isCash){
    if($("efectivo_recibido")) $("efectivo_recibido").value = "";
    if($("vuelto_preview")) $("vuelto_preview").textContent = "S/ 0.00";
  }else{
    calcVueltoPreview();
  }
}

function calcVueltoPreview(){
  const resumen = buildResumenFromCart(); // ya lo tienes
  const efectivo = Number($("efectivo_recibido")?.value || 0);
  const vuelto = Math.max(efectivo - Number(resumen.total || 0), 0);
  if($("vuelto_preview")) $("vuelto_preview").textContent = "S/ " + money(vuelto);
}


/* ---------- INIT ---------- */
/* ---------- INIT ---------- */
function bindUI() {
  // Buscar productos
  $("search")?.addEventListener("input", () => {
    const q = $("search").value.trim().toLowerCase();
    const filtered = q
      ? PRODUCTS.filter(p =>
          (p.nombre || "").toLowerCase().includes(q) ||
          (p.sku || "").toLowerCase().includes(q)
        )
      : PRODUCTS;
    renderProducts(filtered);
  });

  // Buscar cliente
  $("cli_btn_search")?.addEventListener("click", searchClient);
  $("cli_q")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") searchClient();
  });

    $("cli_btn_quick")?.addEventListener("click", ()=>{
      const q = $("cli_q")?.value?.trim() || "";
      openClientModal(q);

      if(clientPrefill){
        const tipo = clientPrefill.tipo_doc || (q.length===11 ? "RUC" : "DNI");
        $("cli_tipo").value = tipo;
        $("cli_num").value  = clientPrefill.num_doc || q;

        // ✅ si es RUC: razón social directa, no apellidos
        if(tipo === "RUC"){
          const rs =
            $("pf_nombres")?.value?.trim() ||
            clientPrefill.nombre_o_razon_social ||
            clientPrefill.razon_social ||
            "";
          $("cli_razon").value = rs.trim();
          $("cli_dir").value   = ($("pf_dir")?.value?.trim() || clientPrefill.direccion || "");
          return;
        }

        // ✅ si es DNI: nombres + apellidos (snake_case / camelCase)
        const nombres = $("pf_nombres")?.value?.trim() || clientPrefill.nombres || clientPrefill.nombre_completo || "";
        const apPat   = $("pf_ap_pat")?.value?.trim()  || clientPrefill.apellido_paterno || clientPrefill.apellidoPaterno || "";
        const apMat   = $("pf_ap_mat")?.value?.trim()  || clientPrefill.apellido_materno || clientPrefill.apellidoMaterno || "";

        $("cli_razon").value = `${nombres} ${apPat} ${apMat}`.replace(/\s+/g," ").trim();
        $("cli_dir").value   = ($("pf_dir")?.value?.trim() || clientPrefill.direccion || "");
        return;
      }

      // manual
      if(/^\d{8,11}$/.test(q)){
        $("cli_tipo").value = (q.length === 11 ? "RUC" : "DNI");
        $("cli_num").value  = q;
      }
    });
    

  // Modal cliente
  $("cli_modal_close")?.addEventListener("click", closeClientModal);
  $("cli_modal_cancel")?.addEventListener("click", closeClientModal);
  $("cli_modal_save")?.addEventListener("click", saveQuickClient);
  $("cli_modal")?.addEventListener("click", (e) => {
    if (e.target && e.target.id === "cli_modal") closeClientModal();
  });

  //Funcion metodo de pago y vuelto
  $("metodo_pago")?.addEventListener("change", toggleCashBox);
  $("efectivo_recibido")?.addEventListener("input", calcVueltoPreview);

  // para que al abrir la página se pinte bien desde el inicio
  toggleCashBox();

  // Cobrar
  $("btn_cobrar")?.addEventListener("click", (e) => {
    e.preventDefault();
    cobrar();
  });



  // Modal post-venta
  bindSaleModalUI();
}


function resetClientUI(){
  clientPrefill = null;
  selectedClient = null;

  if($("cli_q")) $("cli_q").value = "";
  if($("cli_results")) $("cli_results").innerHTML = "";
  if($("cli_selected")) $("cli_selected").innerHTML = "Sin cliente seleccionado";
}

function resetTotalsUI(){
  if($("subtotal")) $("subtotal").textContent = "0.00";
  if($("descuento_total")) $("descuento_total").value = "";
  if($("msg")) $("msg").textContent = "";
}

// función para resetear efectivo/vuelto
function resetCashUI(){
  // Limpia input y preview
  if($("efectivo_recibido")) $("efectivo_recibido").value = "";
  if($("vuelto_preview")) $("vuelto_preview").textContent = "S/ 0.00";

  // (Opcional) asegúrate de recalcular/ocultar según método actual
  toggleCashBox();
}

function resetPOSForm(){
    clearCart();       // tu función (vacía carrito y UI)
    resetClientUI();   // limpia cliente y búsqueda
    resetTotalsUI();   // limpia subtotal/descuento/mensajes
    resetCashUI(); // ✅ nuevo
}

async function initPOS(){
    //toggleCashBox(); // para que al cargar ya se oculte/muestre

    //$("metodo_pago")?.addEventListener("change", toggleCashBox);
    //$("efectivo_recibido")?.addEventListener("input", calcVueltoPreview);
    bindUI();
    renderCart();
    renderTotals();
    renderSelectedClient();
    await loadProducts();
}

if($("products_grid")) initPOS();