from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth_sa.sa_deps import get_current_superadmin
from app.auth_sa.sa_web_deps import web_current_superadmin
from app.models.super_admin import SuperAdmin

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

@router.get("/superadmin/login", response_class=HTMLResponse)
def sa_login_page(request: Request):
    return templates.TemplateResponse("superadmin/login.html", {"request": request})


@router.get("/superadmin/empresas", response_class=HTMLResponse)
def sa_empresas_page(request: Request, sa = Depends(web_current_superadmin)):
    return templates.TemplateResponse("superadmin/empresas.html", {"request": request, "sa": sa})


@router.get("/superadmin", response_class=HTMLResponse)
def sa_home(sa: SuperAdmin = Depends(get_current_superadmin)):
    return RedirectResponse("/superadmin/empresas")


# Funcion para poner la nueva contraseña que viene del router de superadmin para el panel
@router.get("/superadmin/reset", response_class=HTMLResponse)
def sa_reset_page(request: Request, token: str):
    return templates.TemplateResponse("superadmin/reset.html", {"request": request, "token": token})