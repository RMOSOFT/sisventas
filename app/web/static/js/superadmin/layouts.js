
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn_sa_logout");
  if (!btn) return;

  btn.addEventListener("click", async (e) => {
    e.preventDefault();

    try {
      await fetch("/api/v1/superadmin/auth/logout", { method: "POST" });
    } catch (err) {
      // incluso si falla, igual redirigimos para “cerrar sesión” visualmente
    }

    window.location.href = "/superadmin/login";
  });
});
