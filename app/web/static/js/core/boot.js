
(function(){
  const page = window.page;
  if(!page) return;

  const map = {
    dashboard: "/static/js/admin/pages/dashboard.js",
    pos: "/static/js/admin/pages/pos.js",
    products: "/static/js/admin/pages/products.js",
    inventory: "/static/js/admin/pages/inventory.js",
    sales: "/static/js/admin/pages/sales.js",
    reports: "/static/js/admin/pages/reports.js",
    users: "/static/js/admin/pages/users.js",
    solicitudes: "/static/js/admin/pages/solicitudes.js",
    history: "/static/js/admin/pages/history.js",
  };

  const src = map[page];
  if(!src){
    console.warn("No JS mapped for page:", page);
    return;
  }

  const s = document.createElement("script");
  s.src = src;
  s.defer = true;
  document.body.appendChild(s);
})();