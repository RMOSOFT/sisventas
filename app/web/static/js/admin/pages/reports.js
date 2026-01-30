// Funcion para ver la dinamica de los reportes de ventas de los productos
async function loadReportsPage(){
  const daysSel = document.getElementById("rep_days");
  const btn = document.getElementById("rep_refresh");

  async function render(){
    const days = Number(daysSel.value);

    // ventas por dia
    const r1 = await api(`/api/v1/admin/reports/sales-by-day?days=${days}`);
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
    const r2 = await api(`/api/v1/admin/reports/top-products?days=${days}&limit=10`);
    const top = await r2.json();
    const topBox = document.getElementById("top_list");
    topBox.innerHTML = top.length ? top.map((p,i)=>`
      <div class="border rounded-lg p-2">
        <div class="font-semibold">${i+1}. ${p.nombre}</div>
        <div class="text-xs text-slate-500">Cant: ${money(p.cantidad)} • Total: S/ ${money(p.total)}</div>
      </div>
    `).join("") : `<div class="text-slate-500">Sin datos.</div>`;

    // bottom productos
    const r3 = await api(`/api/v1/admin/reports/bottom-products?days=${days}&limit=10`);
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

loadReportsPage();