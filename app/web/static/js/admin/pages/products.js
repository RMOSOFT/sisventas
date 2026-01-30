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
    const r = await api("/api/v1/admin/products" + (search ? `?search=${encodeURIComponent(search)}` : ""));
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

    const res = await api("/api/v1/admin/products", {method:"POST", body: JSON.stringify(payload)});
    const data = await res.json();
    if(!res.ok){ msg.textContent = data.detail || "❌ Error al guardar"; return; }

    msg.textContent = "✅ Producto creado";
    document.getElementById("modal").classList.add("hidden");

    // limpiar
    ["f_nombre","f_sku","f_precio","f_costo","f_stock","f_min"].forEach(id=>document.getElementById(id).value="");
    await refresh(document.getElementById("p_search").value || "");
  });

}

loadProductsPage();

