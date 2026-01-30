
// Utilidades para la pagina de dashboard y POS de ventas
window.money = (n) => (Number(n)||0).toFixed(2);

// Utilidades para la funcion de la pagina ventas donde se ve la dinamica al ver detalles y vendidas por fechas o imprimir el tickets
window.fmtDate = (iso) => {
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
};