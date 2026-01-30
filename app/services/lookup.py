
import os
import httpx

class LookupNotConfigured(Exception):
    pass

class LookupError(Exception):
    pass

def _provider() -> str:
    return (os.getenv("LOOKUP_PROVIDER") or "none").strip().lower()

def _token() -> str:
    return (os.getenv("APISPERU_TOKEN") or "").strip()

def _base_url() -> str:
    base = (os.getenv("APISPERU_BASE_URL") or "").strip().rstrip("/")
    # limpiar si alguien lo puso como .../dni o .../ruc
    if base.endswith("/dni") or base.endswith("/ruc"):
        base = base.rsplit("/", 1)[0]
    return base
    #return (os.getenv("APISPERU_BASE_URL") or "").strip().rstrip("/")

async def lookup_document(tipo: str, num: str) -> dict:
    """
    Normaliza respuesta:
    {
      "tipo_doc": "DNI|RUC",
      "num_doc": "...",
      "razon_social": "...",
      "direccion": "..."
    }
    """
    if _provider() != "apiperu_dev":
        raise LookupNotConfigured("Lookup no configurado (provider!=apiperu_dev)")

    token = _token()
    base = _base_url()
    if not token or not base:
        raise LookupNotConfigured("Falta APIPERU_TOKEN o APIPERU_BASE_URL")

    tipo = tipo.strip().upper()
    num = num.strip()

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    if tipo == "DNI":
        url = f"{base}/dni"
        payload = {"dni": num}
    elif tipo == "RUC":
        url = f"{base}/ruc"
        payload = {"ruc": num}
    else:
        raise LookupError("Tipo no soportado (solo DNI/RUC)")

    print("[LOOKUP] provider:", _provider(), "base:", _base_url(), "token_ok:", bool(_token()))
    print("[LOOKUP] tipo:", tipo, "num:", num)
    print("[LOOKUP] POST:", url, "payload:", payload)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
            print("[LOOKUP] status:", resp.status_code)
            print("[LOOKUP] body:", resp.text[:300])

        if resp.status_code != 200:
            raise LookupError(f"Proveedor respondió {resp.status_code}")

        raw = resp.json() or {}
        if raw.get("success") is not True:
            raise LookupError(raw.get("message") or "No se encontraron resultados")

        data = raw.get("data") or {}

        if tipo == "DNI":
            return {
                "tipo_doc": "DNI",
                "num_doc": data.get("numero") or num,
                "razon_social": (data.get("nombre_completo") or "").strip(),
                "direccion": "",  # DNI normalmente no trae dirección
            }

        # RUC
        return {
            "tipo_doc": "RUC",
            "num_doc": data.get("ruc") or num,
            "razon_social": (data.get("razonSocial") or data.get("razon_social") or "").strip(),
            "direccion": (data.get("direccion_completa") or data.get("direccion") or "").strip(),
        }

    except httpx.RequestError:
        raise LookupError("No se pudo conectar al proveedor")
"""
import os
import httpx

from dotenv import load_dotenv

load_dotenv()

class LookupNotConfigured(Exception):
    pass

class LookupError(Exception):
    pass

def _provider() -> str:
    return (os.getenv("LOOKUP_PROVIDER") or "none").strip().lower()

def _token() -> str:
    return (os.getenv("APISPERU_TOKEN") or "").strip()

def _base_url() -> str:
    return (os.getenv("APISPERU_BASE_URL") or "").strip().rstrip("/")

#def get_provider_name() -> str:
#    return (os.getenv("LOOKUP_PROVIDER") or "none").strip().lower()

async def lookup_document(tipo: str, num: str) -> dict:
    
    #Retorna dict normalizado:
    #{
    #  "tipo_doc": "RUC | DNI",
    #  "num_doc": "20123456789",
    #  "razon_social": "...",
    #  "direccion": "...",
    #  "telefono": None,
    #  "email": None
    #}
    

    if _provider() != "apisperu":
        raise LookupNotConfigured("Lookup no configurado (provider=none)")

    token = _token()
    base = _base_url()
    if not token or not base:
        raise LookupNotConfigured("Falta APISPERU_TOKEN o APISPERU_BASE_URL")

    tipo = tipo.strip().upper()
    num = num.strip()


    if tipo == "RUC":
        url = f"{base}/ruc/{num}"
    elif tipo == "DNI":
        url = f"{base}/dni/{num}"
    else:
        raise LookupError("Tipo no soportado en lookup (solo DNI/RUC)")

    # ✅ DEBUG (déjalo mientras pruebas)    
    print("LOOKUP URL:", url, "TOKEN OK:", bool(token))
    # print("STATUS:", resp.status_code)
    print("BODY:", resp.text[:200])

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # según tu captura: token por querystring
            resp = await client.get(url, params={"token": token})

        print("STATUS:", resp.status_code)
        print("BODY:", resp.text[:200])

        if resp.status_code != 200:
            raise LookupError(f"Proveedor respondió {resp.status_code}")

        raw = resp.json() or {}

        # ApisPeru: cuando no existe devuelve success=false
        if raw.get("success") is False:
            # no es falla de conexión, es "no hay data"
            raise LookupError(raw.get("message") or "No se encontraron resultados.")

        # ✅ Normalización (para POS)
        if tipo == "RUC":
            razon = raw.get("razonSocial") or raw.get("razon_social") or raw.get("nombre") or ""
            direccion = raw.get("direccion") or raw.get("domicilioFiscal") or ""
            return {
                "tipo_doc": "RUC",
                "num_doc": num,
                "razon_social": razon.strip(),
                "direccion": direccion.strip(),
            }

        # DNI
        nombres = raw.get("nombres") or ""
        ape_pat = raw.get("apellidoPaterno") or raw.get("apellido_paterno") or ""
        ape_mat = raw.get("apellidoMaterno") or raw.get("apellido_materno") or ""
        razon = (f"{nombres} {ape_pat} {ape_mat}").strip()
        return {
            "tipo_doc": "DNI",
            "num_doc": num,
            "razon_social": razon,      # para tu tabla clientes sirve como "nombres"
            "direccion": "",            # normalmente DNI no trae dirección
            "nombres": nombres.strip(),
            "apellidos": (f"{ape_pat} {ape_mat}").strip(),
        }

    except httpx.RequestError:
        raise LookupError("No se pudo conectar al proveedor")
"""
