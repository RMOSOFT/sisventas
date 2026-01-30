from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from app.auth.web_deps import web_context
from app.auth.web_deps import web_require_admin
from app.auth.deps import  require_admin
from app.models.usuario import Usuario
from app.auth.deps import get_current_user
# Aqui si queremos que solo rediriga a admin con el todo el panel usamo
# la funcion de web_require_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

# ✅ Login page (pública)
@router.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})

# ✅ Login page (pública)
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})



# ✅ Home: redirige según rol (protegido)
@router.get("/", response_class=HTMLResponse)
def home(ctx = Depends(web_context)):
    if isinstance(ctx, RedirectResponse):
        return ctx

    user = ctx["user"]
    return RedirectResponse(
        url="/admin/dashboard" if user.rol == "admin" else "/admin/pos",
        status_code=302
    )


# ✅ Dashboard (solo admin)
@router.get("/admin/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, ctx = Depends(web_context)):
    if isinstance(ctx, RedirectResponse):
        return ctx
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "user": ctx["user"], "empresa": ctx["empresa"]}
    )
"""
@router.get("/admin/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, user: Usuario = Depends(web_current_user)):
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "user": user})
"""

# ✅ POS (admin o vendedor
@router.get("/admin/pos", response_class=HTMLResponse)
def pos_page(request: Request, ctx = Depends(web_context)):
    if isinstance(ctx, RedirectResponse):
        return ctx
    return templates.TemplateResponse(
        "admin/pos.html", 
        {"request": request, "user": ctx["user"], "empresa": ctx["empresa"]}
    )


@router.get("/admin/products", response_class=HTMLResponse)
def products_page(request: Request, ctx: Usuario = Depends(web_context)):
    if isinstance(ctx, RedirectResponse):
        return ctx
    return templates.TemplateResponse(
        "admin/products.html", 
        {"request": request, "user": ctx["user"], "empresa": ctx["empresa"]}
    )

@router.get("/admin/inventory", response_class=HTMLResponse)
def inventory_page(request: Request, ctx: Usuario = Depends(web_context)):
    if isinstance(ctx, RedirectResponse):
        return ctx
    return templates.TemplateResponse(
        "admin/inventory.html", 
        {"request": request, "user": ctx["user"], "empresa": ctx["empresa"]}
    )

@router.get("/admin/sales", response_class=HTMLResponse)
def sales_page(request: Request, ctx: Usuario = Depends(web_context)):
    if isinstance(ctx, RedirectResponse):
        return ctx
    return templates.TemplateResponse(
        "admin/sales.html", 
        {"request": request, "user": ctx["user"], "empresa": ctx["empresa"]})

@router.get("/admin/reports", response_class=HTMLResponse)
def reports_page(request: Request, ctx: Usuario = Depends(web_context)):
    if isinstance(ctx, RedirectResponse):
        return ctx
    return templates.TemplateResponse(
        "admin/reports.html", {"request": request, "user": ctx["user"], "empresa": ctx["empresa"]}
    )

# Funcion del router web para mostrar el templates reset.html 
@router.get("/admin/reset", response_class=HTMLResponse)
def admin_reset_page(request: Request):
    return templates.TemplateResponse("admin/reset.html", {"request": request})

# Funcion del router web para mostrar el templates users.html para bloquear paginas al usuario require_admin
"""
@router.get("/admin/users", response_class=HTMLResponse)
def users_page(request: Request, user: Usuario = Depends(web_context)):
    return templates.TemplateResponse("admin/users.html", {"request": request, "user": user})
"""

@router.get("/admin/users", response_class=HTMLResponse)
def users_page(request: Request, ctx = Depends(web_context)):
    # ctx puede ser RedirectResponse
    if isinstance(ctx, RedirectResponse):
        return ctx
    return templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "user": ctx["user"], "empresa": ctx["empresa"]}
    )
"""
@router.get("/admin/users", response_class=HTMLResponse)
def users_page(request: Request, ctx = Depends(get_current_user)):
    if isinstance(ctx, RedirectResponse):
        return ctx
    return templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "user": ctx["user"], "empresa": ctx["empresa"]}
    )
"""

# Funcion solo para mostrar la pagina en admin
@router.get("/admin/solicitudes", response_class=HTMLResponse)
def solicitudes_page(request: Request, ctx = Depends(web_require_admin)):
    if isinstance(ctx, RedirectResponse):
        return ctx
    return templates.TemplateResponse(
        "admin/solicitudes.html",
        {"request": request, "user": ctx["user"], "empresa": ctx["empresa"]}
    )

# Para que solo vea el admin su pagina de historial
@router.get("/admin/history", response_class=HTMLResponse)
def history_page(request: Request, ctx=Depends(web_context)):
    if isinstance(ctx, RedirectResponse):
        return ctx
    # solo admin
    if ctx["user"].rol != "admin":
        return RedirectResponse(url="/admin/pos?no_access=1", status_code=302)

    return templates.TemplateResponse(
        "admin/historial.html",
        {"request": request, "user": ctx["user"], "empresa": ctx["empresa"]}
    )
