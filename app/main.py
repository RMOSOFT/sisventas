from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import Request
from fastapi.responses import HTMLResponse

# Importaciones de los routeres de superadmin y admin
from app.routers import admin, superadmin

# Web routes (páginas) también por módulo
from app.web import ad_routes, sa_routes

from dotenv import load_dotenv

load_dotenv()


app = FastAPI(title="RMOSOFT Ventas MVP")

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

templates = Jinja2Templates(directory="app/web/templates")

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Solo interceptamos errores web del admin
    if exc.status_code == 403 and request.url.path.startswith("/admin"):
        return templates.TemplateResponse(
            "admin/forbidden.html",
            {
                "request": request,
                "message": exc.detail or "Acceso restringido"
            },
            status_code=403
        )

    # Para API y otros errores, respuesta normal
    return HTMLResponse(
        content=exc.detail if isinstance(exc.detail, str) else "Error",
        status_code=exc.status_code
    )

# Admin API
app.include_router(admin.ad_auth_router, prefix="/api/v1/admin")
app.include_router(admin.ad_dashboard_router, prefix="/api/v1/admin")
app.include_router(admin.ad_products_router, prefix="/api/v1/admin")
app.include_router(admin.ad_inventory_router, prefix="/api/v1/admin")
app.include_router(admin.ad_sales_router, prefix="/api/v1/admin")
app.include_router(admin.ad_reports_router, prefix="/api/v1/admin")
app.include_router(admin.ad_users_router, prefix="/api/v1/admin")
app.include_router(admin.ad_access_router, prefix="/api/v1/admin")
app.include_router(admin.ad_history_router, prefix="/api/v1/admin")
app.include_router(admin.ad_history_pdf_router, prefix="/api/v1/admin")
app.include_router(admin.ad_kardex_router, prefix="/api/v1/admin")
app.include_router(admin.ad_clientes_router, prefix="/api/v1/admin")

# SuperAdmin API 
app.include_router(superadmin.sa_auth_router, prefix="/api/v1/superadmin")
app.include_router(superadmin.sa_empresas_router, prefix="/api/v1/superadmin")

# Para las paginas de redireccion routes
app.include_router(ad_routes.router)
app.include_router(sa_routes.router)

