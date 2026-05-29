# app/services/lookup.py  (tu lookup.py)
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
        raise LookupNotConfigured("Falta APISPERU_TOKEN o APISPERU_BASE_URL")

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

        # =======================
        # NORMALIZACIÓN PARA UI POS
        # =======================
        if tipo == "DNI":
            # El proveedor devuelve esto:
            # numero, nombre_completo, nombres, apellido_paterno, apellido_materno,
            # codigo_verificacion, direccion, ubigeo_reniec/ubigeo_sunat/ubigeo...
            return {
                "tipo_doc": "DNI",
                "num_doc": data.get("numero") or num,

                # Para mostrar en UI (y también te sirve para cliente rápido)
                "nombre_completo": (data.get("nombre_completo") or "").strip(),
                "nombres": (data.get("nombres") or "").strip(),
                "apellido_paterno": (data.get("apellido_paterno") or "").strip(),
                "apellido_materno": (data.get("apellido_materno") or "").strip(),

                # Extras
                "codigo_verificacion": data.get("codigo_verificacion") or data.get("codVerifica") or "",
                "direccion": (data.get("direccion") or data.get("direccion_completa") or "").strip(),
                "ubigeo": (
                    data.get("ubigeo_reniec")
                    or data.get("ubigeo_sunat")
                    or (data.get("ubigeo") if isinstance(data.get("ubigeo"), str) else "")
                    or ""
                ),
                "estado_civil": (data.get("estadoCivil") or data.get("estado_civil") or "").strip(),


                #"razon_social": (data.get("nombre_completo") or "").strip(),
                #"direccion": "",  # DNI normalmente no trae dirección
            }

        # RUC (tu proveedor devuelve: nombre_o_razon_social, direccion, direccion_completa, etc.)
        razon = (
            data.get("nombre_o_razon_social")
            or data.get("razonSocial")
            or data.get("razon_social")
            or ""
        )
        direccion = data.get("direccion") or data.get("direccion_completa") or ""


        return {
            "tipo_doc": "RUC",
            "num_doc": data.get("ruc") or num,
            "razon_social": razon.strip(),
            #"razon_social": (data.get("razonSocial") or data.get("razon_social") or "").strip(),
            "direccion": direccion.strip(),
            #"direccion": (data.get("direccion_completa") or data.get("direccion") or "").strip(),
            # extras opcionales si luego quieres mostrarlos:
            "estado": (data.get("estado") or "").strip(),
            "condicion": (data.get("condicion") or data.get("condicio") or "").strip(),
        }

    except httpx.RequestError:
        raise LookupError("No se pudo conectar al proveedor")


"""
def _pick_ubigeo(data: dict) -> str:
    # apiperu a veces trae ubigeo como string, a veces lista [dep,prov,dist]
    u = data.get("ubigeo")
    if isinstance(u, str):
        return u.strip()
    if isinstance(u, (list, tuple)):
        parts = [str(x).strip() for x in u if x]
        return "-".join(parts) if parts else ""
    return (data.get("ubigeo_reniec") or data.get("ubigeo_sunat") or "").strip()

if tipo == "DNI":
    nombres = (data.get("nombres") or "").strip()
    ap_pat  = (data.get("apellido_paterno") or data.get("apellidoPaterno") or "").strip()
    ap_mat  = (data.get("apellido_materno") or data.get("apellidoMaterno") or "").strip()

    # apiperu: codigo_verificacion (int) o a veces codigoVerificacion
    codver = data.get("codigo_verificacion")
    if codver is None:
        codver = data.get("codigoVerificacion")
    codver = "" if codver is None else str(codver)

    direccion = (data.get("direccion") or data.get("direccion_completa") or "").strip()
    estado_civil = (data.get("estado_civil") or data.get("estadoCivil") or "").strip()
    ubigeo = _pick_ubigeo(data)

    # nombre_completo ya viene “APELLIDOS, NOMBRES”
    razon = (data.get("nombre_completo") or "").strip()
    if not razon:
        razon = f"{ap_pat} {ap_mat} {nombres}".strip()

    return {
        "tipo_doc": "DNI",
        "num_doc": (data.get("numero") or num),
        "razon_social": razon,
        "direccion": direccion,

        # ✅ campos extra para tu panel
        "nombres": nombres,
        "apellido_paterno": ap_pat,
        "apellido_materno": ap_mat,
        "codigo_verificacion": codver,
        "estado_civil": estado_civil,
        "ubigeo": ubigeo,
    }

# RUC
razon = (
    data.get("nombre_o_razon_social")
    or data.get("nombreOrazonSocial")
    or data.get("razonSocial")
    or data.get("razon_social")
    or ""
).strip()

direccion = (data.get("direccion_completa") or data.get("direccion") or "").strip()
ubigeo = _pick_ubigeo(data)

return {
    "tipo_doc": "RUC",
    "num_doc": (data.get("ruc") or num),
    "razon_social": razon,
    "direccion": direccion,

    # ✅ para panel (en RUC varios quedan vacíos, normal)
    "nombres": razon,                 # para que se vea algo en “Nombres”
    "apellido_paterno": "",
    "apellido_materno": "",
    "codigo_verificacion": "",
    "estado_civil": "",
    "ubigeo": ubigeo,
}
"""
