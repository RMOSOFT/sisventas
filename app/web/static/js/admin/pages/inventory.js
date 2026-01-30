// Funcion para la pagina de inventarios de los productos.
async function loadInventoryPage(){
  const sel = document.getElementById("m_producto");
  const msg = document.getElementById("m_msg");

  async function loadProductsToSelect(){
    const r = await api("/api/v1/admin/products");
    const data = await r.json();
    sel.innerHTML = data.map(p=>`<option value="${p.id}">${p.nombre} (stock ${money(p.stock_actual)})</option>`).join("");
  }

  async function refreshLow(){
    const r = await api("/api/v1/admin/inventory/low-stock");
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

    const res = await api("/api/v1/admin/inventory/movements", {method:"POST", body: JSON.stringify(payload)});
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

loadInventoryPage();