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

/* ---------- Productos ---------- */
function renderProducts(list){
  const grid = $("products_grid");
  if(!grid) return;

  grid.innerHTML = list.map(p => `
    <div class="border rounded-xl p-3 flex items-center justify-between gap-3">
      <div>
        <div class="font-semibold">${esc(p.nombre)}</div>
        <div class="text-xs text-slate-500">Stock: ${money(p.stock_actual)} • Precio: S/ ${money(p.precio)}</div>
      </div>
      <button data-id="${p.id}" class="px-3 py-2 rounded-lg border hover:bg-slate-50 font-semibold">+</button>
    </div>
  `).join("");

  grid.querySelectorAll("button[data-id]").forEach(btn => {
    btn.addEventListener("click", () => addToCart(Number(btn.dataset.id)));
  });
}

async function loadProducts(){
  const { r, data } = await apiJson("/api/v1/admin/products");
  if(!r.ok){
    setMsg("Error cargando productos", false);
    return;
  }
  PRODUCTS = Array.isArray(data) ? data : [];
  renderProducts(PRODUCTS);
}

/* ---------- Carrito ---------- */
function renderCart(){
  const box = $("cart");
  if(!box) return;

  if(CART.length === 0){
    box.innerHTML = `<div class="text-slate-500">Carrito vacío</div>`;
  } else {
    box.innerHTML = CART.map((it, idx) => `
      <div class="border rounded-xl p-2">
        <div class="flex justify-between items-center gap-2">
          <div class="font-semibold">${esc(it.nombre)}</div>
          <button data-i="${idx}" class="text-xs underline text-slate-600 hover:text-black">Quitar</button>
        </div>

        <div class="grid grid-cols-3 gap-2 mt-2">
          <input data-i="${idx}" data-k="cantidad" class="border rounded px-2 py-1 w-full" value="${it.cantidad}" />
          <input data-i="${idx}" data-k="descuento" class="border rounded px-2 py-1 w-full" value="${it.descuento}" />
          <div class="text-right font-semibold">S/ ${money((it.precio*it.cantidad)-it.descuento)}</div>
        </div>
        <div class="text-xs text-slate-500 mt-1">Cant. • Desc. • Total</div>
      </div>
    `).join("");
  }

  box.querySelectorAll("button[data-i]").forEach(b => {
    b.addEventListener("click", () => {
      CART.splice(Number(b.dataset.i), 1);
      renderCart();
      renderTotals();
    });
  });

  box.querySelectorAll("input[data-i]").forEach(inp => {
    inp.addEventListener("change", () => {
      const i = Number(inp.dataset.i);
      const k = inp.dataset.k;
      let v = Number(inp.value || 0);

      if(k === "cantidad"){
        if(v < 1) v = 1;
        CART[i].cantidad = v;
      } else {
        if(v < 0) v = 0;
        CART[i].descuento = v;
      }
      renderCart();
      renderTotals();
    });
  });
}

function renderTotals(){
  let subtotal = 0;
  for(const it of CART){
    subtotal += (Number(it.precio)*Number(it.cantidad)) - Number(it.descuento||0);
  }
  $("subtotal").textContent = money(subtotal);
}

function addToCart(producto_id){
  const p = PRODUCTS.find(x => x.id === producto_id);
  if(!p) return;

  const existing = CART.find(x => x.producto_id === producto_id);
  if(existing){
    existing.cantidad += 1;
  } else {
    CART.push({
      producto_id,
      nombre: p.nombre,
      precio: Number(p.precio),
      cantidad: 1,
      descuento: 0
    });
  }
  renderCart();
  renderTotals();
}

function clearCart(){
  CART = [];
  renderCart();
  renderTotals();
}

function clearSelectedClient(){
  selectedClient = null;
  renderSelectedClient();
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
      setMsg("Cliente seleccionado ✅", true);
    });
  });
}


async function searchClient(){
  const q = $("cli_q")?.value?.trim() || "";
  if(!q){
    renderClientResults([]);
    setMsg("Ingresa DNI/RUC/NOMBRE", false);
    return;
  }

  clientPrefill = null;

  // 1) buscar en tu BD
  const { r, data } = await apiJson(`/api/v1/admin/clientes/search?q=${encodeURIComponent(q)}`);
  if(!r.ok){
    setMsg("Error buscando cliente", false);
    return;
  }

  const list = Array.isArray(data) ? data : [];
  renderClientResults(list);

  // 2) si NO existe en BD y es DNI/RUC -> lookup proveedor
  if(list.length === 0 && /^\d{8,11}$/.test(q)){
    const tipo = (q.length === 11) ? "RUC" : "DNI";

    const { r: r2, data: luData } = await apiJson(
      `/api/v1/admin/clientes/lookup?tipo=${tipo}&num=${encodeURIComponent(q)}`
    );

    if(r2.ok && luData?.enabled && luData?.data){
      clientPrefill = luData.data;
      setMsg("✅ Datos encontrados. Clic en 'Crear cliente rápido' para guardar.", true);
    } else {
      setMsg("No encontrado. Puedes crear cliente rápido manual.", false);
    }
  } else if(list.length === 0) {
    setMsg("No encontrado. Puedes crear cliente rápido.", false);
  }
}

/*
async function searchClient(){
  const q = $("cli_q")?.value?.trim() || "";
  clientPrefill = null;

  if(!q){
    renderClientResults([]);
    setMsg("Ingresa DNI/RUC/NOMBRE", false);
    return;
  }

  // 1) Buscar en BD
  const { r, data } = await apiJson(`/api/v1/admin/clientes/search?q=${encodeURIComponent(q)}`);
  if(!r.ok){
    setMsg("Error buscando cliente", false);
    return;
  }

  const list = Array.isArray(data) ? data : [];
  renderClientResults(list);

  // Si hay resultados, NO hacemos lookup ni abrimos modal
  if(list.length > 0){
    clientPrefill = null;
    setMsg("", true);
    return;
  }

  // 2) Si NO existe en BD y es DNI/RUC -> lookup silencioso (SIN abrir modal)
  if(/^\d{8,11}$/.test(q)){
    const tipo = (q.length === 11) ? "RUC" : "DNI";

    try{
      const lu = await fetch(`/api/v1/admin/clientes/lookup?tipo=${tipo}&num=${encodeURIComponent(q)}`);
      const luData = await lu.json().catch(()=>null);

      if(luData?.enabled && luData?.data){
        clientPrefill = {
          tipo_doc: luData.data.tipo_doc || tipo,
          num_doc:  luData.data.num_doc  || q,
          razon_social: luData.data.razon_social || "",
          direccion: luData.data.direccion || "",
        };
      } else {
        clientPrefill = { tipo_doc: tipo, num_doc: q, razon_social:"", direccion:"" };
      }
    }catch(e){
      clientPrefill = { tipo_doc: tipo, num_doc: q, razon_social:"", direccion:"" };
    }

    setMsg("No encontrado. Puedes crear cliente rápido.", false);
    return;
  }

  // 3) Si no es doc (es nombre) y no hay resultados
  clientPrefill = null;
  setMsg("No encontrado.", false);
}
*/

/*
async function searchClient(){
    // si tu search no encontró nada:
    const q = $("cli_q")?.value?.trim() || ""; // ✅ 1) primero q
    if(!q){
        renderClientResults([]);
        setMsg("Ingresa DNI/RUC/NOMBRE", false);
        return;
    }

    // ✅ 2) buscar en tu BD primero
    const { r, data } = await apiJson(`/api/v1/admin/clientes/search?q=${encodeURIComponent(q)}`);
    if(!r.ok){
        setMsg("Error buscando cliente", false);
        return;
    }

    const list = Array.isArray(data) ? data : [];
    renderClientResults(list);

     // ✅ 3) si no existe en tu BD y es DNI/RUC -> lookup proveedor
    if(list.length === 0 && /^\d{8,11}$/.test(q)){
        const tipo = (q.length === 11) ? "RUC" : "DNI";

        const lu = await fetch(`/api/v1/admin/clientes/lookup?tipo=${tipo}&num=${encodeURIComponent(q)}`);
        const luData = await lu.json().catch(()=>null);

        // abre modal y prellena si hay data
        openClientModal(q);

        if(luData?.enabled && luData?.data){
          document.getElementById("cli_tipo").value = luData.data.tipo_doc || tipo;
          document.getElementById("cli_num").value  = luData.data.num_doc  || q;
          document.getElementById("cli_razon").value = luData.data.razon_social || "";
          document.getElementById("cli_dir").value   = luData.data.direccion || "";
        } else {
          // fallback manual
          document.getElementById("cli_tipo").value = tipo;
          document.getElementById("cli_num").value  = q;
        }
    }
    // ✅ 4) si es doc pero NO abre modal automáticamente, solo prefill (opcional)
    if(list.length === 0 && /^\d{8,11}$/.test(q)){
        $("cli_num").value = q;
        $("cli_tipo").value = (q.length === 11 ? "RUC" : "DNI");
    }
}
*/

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
  setMsg("Cliente creado y seleccionado ✅", true);
}

/* ---------- Modal post-venta ---------- */
function showSaleModal(sale){
  lastSale = sale;

  $("sale_modal_title").textContent = `✅ Venta #${sale.numero}`;
  $("sale_modal_sub").textContent = `Total S/ ${money(sale.total)} • Estado: ${sale.estado || "emitida"}`;
  $("sale_modal_msg").textContent = "";

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

    const { r, data } = await apiJson(`/api/v1/admin/sales/${sale.id}/cancel`, {
      method:"POST",
      body: JSON.stringify({ motivo: "Anulación desde POS" })
    });

    if(!r.ok){
      $("sale_modal_msg").className = "text-sm mt-2 text-red-700";
      $("sale_modal_msg").textContent = data?.detail || "No se pudo anular.";
      return;
    }

    $("sale_modal_msg").className = "text-sm mt-2 text-green-700";
    $("sale_modal_msg").textContent = "✅ Venta anulada (stock devuelto y registrado).";
    btnCancel.disabled = true;
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

/* ---------- COBRAR (ÚNICO) ---------- */
async function cobrar(){
  if(CART.length === 0){
    setMsg("Agrega productos al carrito.", false);
    return;
  }

  const descuentoTotal = Number($("descuento_total")?.value || 0);
  const metodoPago = $("metodo_pago")?.value || "efectivo";

  const payload = {
    items: CART.map(x => ({
      producto_id: x.producto_id,
      cantidad: Number(x.cantidad),
      descuento: Number(x.descuento || 0)
    })),
    descuento_total: descuentoTotal,
    metodo_pago: metodoPago,
    cliente_id: selectedClient?.id || null,
  };

  const btn = $("btn_cobrar");
  btn.disabled = true;
  setMsg("Procesando...", true);

  const { r, data } = await apiJson("/api/v1/admin/sales", { method:"POST", body: JSON.stringify(payload) });

  btn.disabled = false;

  if(!r.ok){
    setMsg(data?.detail || "Error al cobrar.", false);
    return;
  }

  // ✅ data debe traer: id, numero, total, estado, can_cancel
  showSaleModal({
    id: data.id,
    numero: data.numero,
    total: data.total,
    estado: data.estado || "emitida",
    can_cancel: Boolean(data.can_cancel),
  });

  // limpia carrito
  clearCart();

  // recarga productos (stock actualizado)
  await loadProducts();

  setMsg(`Venta OK • Ticket #${data.numero} • Total S/ ${money(data.total)}`, true);
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

  // Crear cliente rápido (abre modal y prefill)
  $("cli_btn_quick")?.addEventListener("click", () => {
    const q = $("cli_q")?.value?.trim() || "";
    openClientModal(q);

    if (clientPrefill) {
      $("cli_tipo").value  = clientPrefill.tipo_doc || (q.length === 11 ? "RUC" : "DNI");
      $("cli_num").value   = clientPrefill.num_doc || q;
      $("cli_razon").value = clientPrefill.razon_social || "";
      $("cli_dir").value   = clientPrefill.direccion || "";
    } else {
      if (/^\d{8,11}$/.test(q)) {
        $("cli_tipo").value = (q.length === 11 ? "RUC" : "DNI");
        $("cli_num").value = q;
      }
    }
  });

  // Modal cliente
  $("cli_modal_close")?.addEventListener("click", closeClientModal);
  $("cli_modal_cancel")?.addEventListener("click", closeClientModal);
  $("cli_modal_save")?.addEventListener("click", saveQuickClient);
  $("cli_modal")?.addEventListener("click", (e) => {
    if (e.target && e.target.id === "cli_modal") closeClientModal();
  });

  // Cobrar
  $("btn_cobrar")?.addEventListener("click", (e) => {
    e.preventDefault();
    cobrar();
  });

  // Modal post-venta
  bindSaleModalUI();
}
/*
function bindUI(){
  $("search")?.addEventListener("input", () => {
    const q = $("search").value.trim().toLowerCase();
    const filtered = q ? PRODUCTS.filter(p =>
      (p.nombre||"").toLowerCase().includes(q) ||
      (p.sku||"").toLowerCase().includes(q)
    ) : PRODUCTS;
    renderProducts(filtered);
  });

  // Clientes
  $("cli_btn_search")?.addEventListener("click", searchClient);
  $("cli_q")?.addEventListener("keydown", (e)=>{ if(e.key === "Enter") searchClient(); });
  //$("cli_btn_quick")?.addEventListener("click", ()=> openClientModal($("cli_q")?.value?.trim() || ""));
  $("cli_btn_quick")?.addEventListener("click", ()=>{
    const q = $("cli_q")?.value?.trim() || "";
    openClientModal(q);



    // ✅ usar datos del lookup si existen
    if(clientPrefill){
        $("cli_tipo").value = clientPrefill.tipo_doc || "DNI";
        $("cli_num").value  = clientPrefill.num_doc || q;
        $("cli_razon").value = clientPrefill.razon_social || "";
        $("cli_dir").value   = clientPrefill.direccion || "";
    } else {
        // fallback manual
        if(/^\d{8,11}$/.test(q)){
          $("cli_tipo").value = (q.length === 11 ? "RUC" : "DNI");
          $("cli_num").value  = q;
        }
      }
    });


  $("cli_modal_close")?.addEventListener("click", closeClientModal);
  $("cli_modal_cancel")?.addEventListener("click", closeClientModal);
  $("cli_modal_save")?.addEventListener("click", saveQuickClient);
  $("cli_modal")?.addEventListener("click", (e)=>{
    if(e.target && e.target.id === "cli_modal") closeClientModal();
  });

  // Cobrar
  $("btn_cobrar")?.addEventListener("click", (e)=>{ e.preventDefault(); cobrar(); });

  bindSaleModalUI();
}
*/

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

function resetPOSForm(){
  clearCart();       // tu función (vacía carrito y UI)
  resetClientUI();   // limpia cliente y búsqueda
  resetTotalsUI();   // limpia subtotal/descuento/mensajes
}

async function initPOS(){
  bindUI();
  renderCart();
  renderTotals();
  renderSelectedClient();
  await loadProducts();
}

if($("products_grid")) initPOS();