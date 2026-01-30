// Funciones para la pagina de dashboard y POS de ventas
const api = (path, opts={}) => fetch(path, {headers: {"Content-Type":"application/json"}, ...opts});

function money(n){ return (Number(n)||0).toFixed(2); }


async function loadDashboard(){
  const r = await api("/api/v1/dashboard/summary");
  const d = await r.json();

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


// Seccion para pagina del POS.js
let products = [];
let cart = []; // {producto_id, nombre, precio, cantidad, descuento}

function renderProducts(filter=""){
  const grid = document.getElementById("products_grid");
  const f = filter.trim().toLowerCase();
  const list = products.filter(p => !f || (p.nombre||"").toLowerCase().includes(f) || (p.sku||"").toLowerCase().includes(f));
  grid.innerHTML = list.map(p => `
    <div class="border rounded-xl p-3 flex items-center justify-between">
      <div>
        <div class="font-semibold">${p.nombre}</div>
        <div class="text-xs text-slate-500">Stock: ${money(p.stock_actual)} • Precio: S/ ${money(p.precio)}</div>
      </div>
      <button class="px-3 py-2 rounded-lg border" onclick="addToCart(${p.id})">+</button>
    </div>
  `).join("");
}

function renderCart(){
  const box = document.getElementById("cart");
  box.innerHTML = cart.map((c, idx) => `
    <div class="border rounded-lg p-2">
      <div class="flex justify-between">
        <strong>${c.nombre}</strong>
        <button class="text-xs underline" onclick="removeItem(${idx})">Quitar</button>
      </div>
      <div class="flex gap-2 mt-2">
        <input class="border rounded px-2 py-1 w-20" type="number" min="1" value="${c.cantidad}"
          onchange="setQty(${idx}, this.value)" />
        <input class="border rounded px-2 py-1 w-28" type="number" min="0" value="${c.descuento||0}"
          onchange="setDesc(${idx}, this.value)" placeholder="Desc" />
        <div class="ml-auto">S/ ${money((c.precio*c.cantidad) - (c.descuento||0))}</div>
      </div>
    </div>
  `).join("");

  const subtotal = cart.reduce((acc,c)=> acc + (c.precio*c.cantidad) - (c.descuento||0), 0);
  document.getElementById("subtotal").textContent = money(subtotal);
}

window.addToCart = (id) => {
  const p = products.find(x=>x.id===id);
  if(!p) return;
  const found = cart.find(x=>x.producto_id===id);
  if(found){ found.cantidad += 1; }
  else cart.push({producto_id:id, nombre:p.nombre, precio:Number(p.precio), cantidad:1, descuento:0});
  renderCart();
};
window.removeItem = (idx)=>{ cart.splice(idx,1); renderCart(); };
window.setQty = (idx, v)=>{ cart[idx].cantidad = Math.max(1, Number(v)||1); renderCart(); };
window.setDesc = (idx, v)=>{ cart[idx].descuento = Math.max(0, Number(v)||0); renderCart(); };

async function loadPos(){
  const r = await api("/api/v1/products");
  products = await r.json();
  renderProducts("");

  document.getElementById("search").addEventListener("input", (e)=>renderProducts(e.target.value));

  document.getElementById("btn_cobrar").addEventListener("click", async ()=>{
    const msg = document.getElementById("msg");
    msg.textContent = "";
    if(cart.length===0){ msg.textContent="Carrito vacío."; return; }

    const descuento_total = Math.max(0, Number(document.getElementById("descuento_total").value)||0);
    const metodo_pago = document.getElementById("metodo_pago").value;

    const payload = {
      items: cart.map(c=>({producto_id:c.producto_id, cantidad:c.cantidad, descuento:(c.descuento||0)})),
      descuento_total,
      metodo_pago
    };

    const res = await api("/api/v1/sales", {method:"POST", body: JSON.stringify(payload)});
    const data = await res.json();
    if(!res.ok){
      msg.textContent = data.detail || "Error al vender";
      return;
    }
    msg.textContent = `✅ Venta OK • Ticket #${data.numero} • Total S/ ${money(data.total)}`;
    cart = [];
    renderCart();
    // recargar productos (stock actualizado)
    const rr = await api("/api/v1/products");
    products = await rr.json();
    renderProducts(document.getElementById("search").value || "");
  });
}

//Funcion para la pagina de Products + Inventory
async function loadProductsPage(){
  const list = document.getElementById("products_list");
  const msg = document.getElementById("p_msg");

  const modal = document.getElementById("modal");
  const open = document.getElementById("btn_open_modal");
  const close = document.getElementById("btn_close_modal");
  // cerrar al hacer click fuera (productos)
    document.getElementById("modal").addEventListener("click", (e) => {
      if (e.target.id === "modal") {
        document.getElementById("modal").classList.add("hidden");
      }
    });

  open.addEventListener("click", ()=> modal.classList.remove("hidden"), {once:false});
  close.addEventListener("click", ()=> modal.classList.add("hidden"), {once:false});

  async function refresh(search=""){
    const r = await api("/api/v1/products" + (search ? `?search=${encodeURIComponent(search)}` : ""));
    const data = await r.json();
    list.innerHTML = data.map(p => `
      <div class="p-3 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div>
          <div class="font-semibold">${p.nombre}</div>
          <div class="text-xs text-slate-500">
            SKU: ${p.sku || "—"} • Precio: S/ ${money(p.precio)} • Costo: S/ ${money(p.costo)}
          </div>
        </div>
        <div class="text-sm">
          <span class="inline-block border rounded-lg px-3 py-1">
            Stock: <b>${money(p.stock_actual)}</b> (min ${money(p.stock_minimo)})
          </span>
        </div>
      </div>
    `).join("");
  }

  document.getElementById("p_search").addEventListener("input", (e)=> refresh(e.target.value));
  await refresh("");

  document.getElementById("btn_save_product").addEventListener("click", async ()=>{
    msg.textContent = "";
    const nombre = document.getElementById("f_nombre").value.trim();
    const sku = document.getElementById("f_sku").value.trim() || null;

    const precio = Number(document.getElementById("f_precio").value || 0);
    const costo  = Number(document.getElementById("f_costo").value || 0);

    const stock_actual = Number(document.getElementById("f_stock").value || 0);
    const stock_minimo = Number(document.getElementById("f_min").value || 0);

    if(!nombre){ msg.textContent="❌ Falta nombre"; return; }
    if(precio < 0 || costo < 0 || stock_actual < 0 || stock_minimo < 0){
      msg.textContent="❌ Valores inválidos"; return;
    }

    const payload = {nombre, sku, precio, costo, stock_actual, stock_minimo, activo:true};

    const res = await api("/api/v1/products", {method:"POST", body: JSON.stringify(payload)});
    const data = await res.json();
    if(!res.ok){ msg.textContent = data.detail || "❌ Error al guardar"; return; }

    msg.textContent = "✅ Producto creado";
    document.getElementById("modal").classList.add("hidden");

    // limpiar
    ["f_nombre","f_sku","f_precio","f_costo","f_stock","f_min"].forEach(id=>document.getElementById(id).value="");
    await refresh(document.getElementById("p_search").value || "");
  });
}

async function loadInventoryPage(){
  const sel = document.getElementById("m_producto");
  const msg = document.getElementById("m_msg");

  async function loadProductsToSelect(){
    const r = await api("/api/v1/products");
    const data = await r.json();
    sel.innerHTML = data.map(p=>`<option value="${p.id}">${p.nombre} (stock ${money(p.stock_actual)})</option>`).join("");
  }

  async function refreshLow(){
    const r = await api("/api/v1/inventory/low-stock");
    const data = await r.json();
    const box = document.getElementById("low_list");
    if(data.length===0){
      box.innerHTML = `<div class="text-slate-500">Sin alertas ✅</div>`;
      return;
    }
    box.innerHTML = data.map(x=>`
      <div class="border rounded-lg p-2">
        <div class="font-semibold">${x.nombre}</div>
        <div class="text-xs text-slate-500">Stock: ${money(x.stock)} • Mínimo: ${money(x.min)}</div>
      </div>
    `).join("");
  }

  document.getElementById("btn_refresh_low").addEventListener("click", refreshLow);

  document.getElementById("btn_move").addEventListener("click", async ()=>{
    msg.textContent = "";
    const producto_id = Number(sel.value);
    const tipo = document.getElementById("m_tipo").value;
    const cantidad = Number(document.getElementById("m_cantidad").value || 0);
    const referencia = document.getElementById("m_ref").value.trim() || null;

    if(!producto_id){ msg.textContent="❌ Selecciona producto"; return; }
    if(cantidad <= 0){ msg.textContent="❌ Cantidad debe ser > 0"; return; }

    const payload = {producto_id, tipo, cantidad, referencia};

    const res = await api("/api/v1/inventory/movements", {method:"POST", body: JSON.stringify(payload)});
    const data = await res.json();
    if(!res.ok){ msg.textContent = data.detail || "❌ Error en movimiento"; return; }

    msg.textContent = "✅ Movimiento registrado";
    document.getElementById("m_cantidad").value = "";
    document.getElementById("m_ref").value = "";

    // recargar select y alertas
    await loadProductsToSelect();
    await refreshLow();
  });

  await loadProductsToSelect();
  await refreshLow();
}


// Funciones para la pagina ventas donde se ve la dinamica al ver detalles y vendidas por fechas o imprimir el tickets
function fmtDate(iso){
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

async function loadSalesPage(){
  const list = document.getElementById("sales_list");
  const modal = document.getElementById("sale_modal");

  document.getElementById("btn_close_sale_modal").addEventListener("click", ()=> modal.classList.add("hidden"));
  //document.getElementById("btn_refresh_sales").addEventListener("click", refresh);

  // cerrar al hacer click fuera
    document.getElementById("sale_modal").addEventListener("click", (e) => {
      if (e.target.id === "sale_modal") {
        document.getElementById("sale_modal").classList.add("hidden");
      }
    });

    // cerrar con ESC
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        document.getElementById("sale_modal").classList.add("hidden");
      }
    });

  async function refresh(){
    const r = await api("/api/v1/sales?limit=50");
    const data = await r.json();

    if(data.length === 0){
      list.innerHTML = `<div class="p-3 text-slate-500">Aún no hay ventas.</div>`;
      return;
    }

    list.innerHTML = data.map(v => `
      <button class="w-full text-left p-3 hover:bg-slate-50 flex items-center justify-between gap-3"
              onclick="openSale(${v.id})">
        <div>
          <div class="font-semibold">Ticket #${v.numero}</div>
          <div class="text-xs text-slate-500">${fmtDate(v.fecha)} • ${v.metodo_pago} • ${v.estado}</div>
        </div>
        <div class="font-bold">S/ ${money(v.total)}</div>
      </button>
    `).join("");
  }

  document.getElementById("btn_refresh_sales").addEventListener("click", refresh);

  window.refreshSales = refresh;

  window.openSale = async (id) => {
    const r = await api(`/api/v1/sales/${id}`);
    const d = await r.json();

    document.getElementById("sale_title").textContent = `Ticket #${d.numero}`;
    document.getElementById("d_fecha").textContent = fmtDate(d.fecha);
    document.getElementById("d_pago").textContent = d.metodo_pago;
    document.getElementById("d_estado").textContent = d.estado;
    document.getElementById("d_total").textContent = "S/ " + money(d.total);

    // Funcion al rellenar todos los datos imprimimos 
    document.getElementById("btn_print_placeholder").onclick = () => {
      window.open(`/api/v1/sales/${id}/ticket`, "_blank");
    };

    // Funcion para anular los productos en ventas antes de imprimir
     // Abrir modal anulación
    document.getElementById("btn_cancel_sale").onclick = () => {
      document.getElementById("cancel_ticket_label").textContent = `Ticket #${d.numero}`;
      document.getElementById("cancel_motivo").value = "";
      document.getElementById("cancel_msg").textContent = "";
      document.getElementById("cancel_modal").classList.remove("hidden");

      // guardamos el id actual
      window._cancel_sale_id = id;
      window._cancel_sale_num = d.numero;
    };

    // Cerrar modal anulación
    const closeCancel = () => document.getElementById("cancel_modal").classList.add("hidden");
    document.getElementById("btn_cancel_close").onclick = closeCancel;
    document.getElementById("btn_cancel_back").onclick = closeCancel;

    // Confirmar anulación
    document.getElementById("btn_cancel_confirm").onclick = async () => {
      const saleId = window._cancel_sale_id;
      const motivo = document.getElementById("cancel_motivo").value.trim() || null;
      const msg = document.getElementById("cancel_msg");

      msg.textContent = "Procesando...";
      msg.className = "text-sm mt-2 text-slate-600";

      const res = await api(`/api/v1/sales/${saleId}/cancel`, {
        method: "POST",
        body: JSON.stringify({ motivo })
      });
      const data = await res.json();

      if(!res.ok){
        msg.textContent = data.detail || "Error al anular";
        msg.className = "text-sm mt-2 text-red-600";
        return;
      }

      msg.textContent = "✅ Venta anulada y stock devuelto.";
      msg.className = "text-sm mt-2 text-green-700";

      // cerrar en 800ms y refrescar vistas
      setTimeout(async () => {
        closeCancel();
        document.getElementById("sale_modal").classList.add("hidden");

        // refrescar lista de ventas si existe helper global
        if (window.refreshSales) await window.refreshSales();

        // refrescar dashboard/reportes si estás en esas páginas
        if (window.page === "dashboard" && window.refreshDashboard) await window.refreshDashboard();
        if (window.page === "reports" && window.refreshReports) await window.refreshReports();
      }, 800);
    };   



    //document.getElementById("btn_cancel_sale").onclick = async () => {
    //  if(!confirm("¿Seguro que deseas ANULAR esta venta? Se devolverá el stock.")) return;

    //  const motivo = prompt("Motivo (opcional):") || null;

    //  const res = await api(`/api/v1/sales/${id}/cancel`, {
    //    method: "POST",
    //    body: JSON.stringify({ motivo })
    //  });

    //  const data = await res.json();
    //  if(!res.ok){
    //    alert(data.detail || "Error al anular");
    //    return;
    //  }

    //  alert("✅ Venta anulada y stock devuelto.");
      // refrescar lista y volver a cargar detalle
    //  await loadSalesPage(); // si no te funciona por scope, dime y lo ajustamos
    //};

    const box = document.getElementById("d_items");
    box.innerHTML = d.items.map(it => `
      <div class="p-2 flex items-center justify-between">
        <div>
          <div class="font-semibold">${it.nombre}</div>
          <div class="text-xs text-slate-500">
            ${money(it.cantidad)} x S/ ${money(it.precio_unitario)} • desc ${money(it.descuento)}
          </div>
        </div>
        <div class="font-semibold">S/ ${money(it.total_linea)}</div>
      </div>
    `).join("");

    modal.classList.remove("hidden");
  };

  await refresh();
}


// Funcion para ver la dinamica de los reportes de ventas de los productos
async function loadReportsPage(){
  const daysSel = document.getElementById("rep_days");
  const btn = document.getElementById("rep_refresh");

  async function render(){
    const days = Number(daysSel.value);

    // ventas por dia
    const r1 = await api(`/api/v1/reports/sales-by-day?days=${days}`);
    const byDay = await r1.json();

    const boxDay = document.getElementById("by_day");
    if(byDay.length === 0){
      boxDay.innerHTML = `<div class="text-slate-500">Aún no hay ventas en este periodo.</div>`;
    } else {
      boxDay.innerHTML = `
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-slate-500">
              <th class="py-2">Día</th>
              <th class="py-2">Tickets</th>
              <th class="py-2">Total</th>
            </tr>
          </thead>
          <tbody>
            ${byDay.map(x=>`
              <tr class="border-t">
                <td class="py-2">${x.dia}</td>
                <td class="py-2">${x.tickets}</td>
                <td class="py-2 font-semibold">S/ ${money(x.total)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }

    // top productos
    const r2 = await api(`/api/v1/reports/top-products?days=${days}&limit=10`);
    const top = await r2.json();
    const topBox = document.getElementById("top_list");
    topBox.innerHTML = top.length ? top.map((p,i)=>`
      <div class="border rounded-lg p-2">
        <div class="font-semibold">${i+1}. ${p.nombre}</div>
        <div class="text-xs text-slate-500">Cant: ${money(p.cantidad)} • Total: S/ ${money(p.total)}</div>
      </div>
    `).join("") : `<div class="text-slate-500">Sin datos.</div>`;

    // bottom productos
    const r3 = await api(`/api/v1/reports/bottom-products?days=${days}&limit=10`);
    const bottom = await r3.json();
    const bottomBox = document.getElementById("bottom_list");
    bottomBox.innerHTML = bottom.length ? bottom.map((p,i)=>`
      <div class="border rounded-lg p-2">
        <div class="font-semibold">${i+1}. ${p.nombre}</div>
        <div class="text-xs text-slate-500">Cant: ${money(p.cantidad)} • Total: S/ ${money(p.total)}</div>
      </div>
    `).join("") : `<div class="text-slate-500">Sin datos.</div>`;
  }

  window.refreshReports = render;

  btn.addEventListener("click", render);
  daysSel.addEventListener("change", render);

  await render();
}

// Funciones para la pagina de dashboard y POS de ventas
if(window.page==="dashboard") loadDashboard();
if(window.page==="pos") loadPos();

// Funciones de dinamica para la pagina de inventarios
if(window.page==="products") loadProductsPage();
if(window.page==="inventory") loadInventoryPage();

// Funciones para la pagina ventas
if(window.page==="sales") loadSalesPage();

// Funcion para ver la dinamica de los reportes de ventas
if(window.page==="reports") loadReportsPage();