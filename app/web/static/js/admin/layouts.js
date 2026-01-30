document.addEventListener("DOMContentLoaded", () => {
  // LOGOUT
  const btn = document.getElementById("btn_logout");
  btn?.addEventListener("click", async () => {
    try { await fetch("/api/v1/admin/auth/logout", { method: "POST" }); } catch {}
    window.location.href = "/login";
  });

  // ACTIVE LINK
  const path = window.location.pathname;
  document.querySelectorAll(".navlink").forEach(a => {
    const p = a.getAttribute("data-path");
    if (!p) return;

    // activo exacto o cuando estás dentro (ej: /admin/products/xxx)
    const active = (path === p) || (path.startsWith(p + "/"));
    if (active) {
      a.classList.add("font-semibold");
      a.classList.add("text-blue-700");
      a.classList.add("underline");
    } else {
      a.classList.add("text-slate-700");
    }
  });
});