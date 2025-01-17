from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from fastapi.responses import HTMLResponse

app = FastAPI()

class Credentials(BaseModel):
    usuario: str
    contrasena: str

@app.post("/", response_class=HTMLResponse)
async def get_protected_content(credentials: Credentials):
    # URLs
    login_url = "https://tg.toscanagroup.com.co/index.php"
    protected_url = "https://tg.toscanagroup.com.co/ver_cotizacion.php?id=99002"

    # Crear una sesión
    session = requests.Session()

    # 1. Obtener la página de login primero para extraer el token CSRF
    login_page = session.get(login_url)
    soup = BeautifulSoup(login_page.text, 'html.parser')

    # Buscar token CSRF (ajusta el nombre si es necesario)
    csrf_token = soup.find('input', {'name': 'csrf_token_name'})
    token_value = csrf_token.get('value') if csrf_token else None

    # Configurar los datos de autenticación
    payload = {
        'usuario': "jorge.contreras",
        'contrasena': "EstebanGrey1704*",
        'url': '/ver_cotizacion.php?id=99002'
    }
    if token_value:
        payload['csrf_token_name'] = token_value  # Usa el nombre exacto del token

    # 2. Realizar el POST al formulario de login
    login_response = session.post(login_url, data=payload)

    # Verificar si el login fue exitoso
    if login_response.ok and "Ingresar" not in login_response.text:
        # Acceder a la URL protegida
        protected_response = session.get(protected_url)
        
        if protected_response.ok:
            # Parsear el contenido de la página protegida y devolverlo como HTML
            return HTMLResponse(content=protected_response.text)
        else:
            raise HTTPException(status_code=403, detail="No se pudo acceder a la URL protegida.")
    else:
        raise HTTPException(status_code=401, detail="Login fallido.")

