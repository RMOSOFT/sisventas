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
    const r = await api("/api/v1/admin/sales?limit=50");
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
    const r = await api(`/api/v1/admin/sales/${id}`);
    const d = await r.json();

    document.getElementById("sale_title").textContent = `Ticket #${d.numero}`;
    document.getElementById("d_fecha").textContent = fmtDate(d.fecha);
    document.getElementById("d_pago").textContent = d.metodo_pago;
    document.getElementById("d_estado").textContent = d.estado;
    document.getElementById("d_total").textContent = "S/ " + money(d.total);

    // Funcion al rellenar todos los datos imprimimos 
    document.getElementById("btn_print_placeholder").onclick = () => {
      window.open(`/api/v1/admin/sales/${id}/ticket`, "_blank");
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

      const res = await api(`/api/v1/admin/sales/${saleId}/cancel`, {
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

loadSalesPage();