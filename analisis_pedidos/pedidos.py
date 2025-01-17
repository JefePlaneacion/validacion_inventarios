import requests
from bs4 import BeautifulSoup
import re
import openpyxl
from openpyxl import load_workbook
import pandas as pd
import os

# URLs
pedido_sel=99296
login_url = "https://tg.toscanagroup.com.co/index.php"
protected_url = f"https://tg.toscanagroup.com.co/ver_cotizacion.php?id={pedido_sel}"

# Crear una sesión
session = requests.Session()

# 
login_page = session.get(login_url)
soup = BeautifulSoup(login_page.text, 'html.parser')


# 2. Configura los datos de autenticación
payload = {
    'usuario': 'jorge.contreras',                # Nombre de usuario
    'contrasena': 'EstebanGrey1704*',          # Contraseña
    'url': f'/ver_cotizacion.php?id={pedido_sel}'   # Redirección
}


# 3. Realizar el POST al formulario de login con la sesión
login_response = session.post(login_url, data=payload)

# Verificar si el login fue exitoso
if login_response.ok and "Ingresar" not in login_response.text:
    print("Login exitoso!")

    # Acceder a la URL protegida
    protected_response = session.get(protected_url)

    if protected_response.ok:
        print("Acceso a la URL protegida exitoso!")
        # Parsear el contenido con BeautifulSoup
        soup = BeautifulSoup(protected_response.text, 'html.parser')
        table_element= soup.find("div",class_="container-fluid" )
        
        datos_cliente= str(table_element.find("h3"))
        texto_dividido = r"Pedido\s+(.*?)\s+-\s+(No\.\d+)\s+-\s+Fecha Entrega:(\d{4}/\d{2}/\d{2})"
        texto_dividido_final = re.search(texto_dividido,datos_cliente)

        if texto_dividido_final:
            cliente= texto_dividido_final.group(1).strip()
            pedido_exist= texto_dividido_final.group(2).strip()
            fecha_entrega= texto_dividido_final.group(3).strip()



        tabla_pedido= table_element.find_all("div",class_="row-fluid")
        table_pedido=tabla_pedido[-4] #tabla donde estan todos los items de los pedidos
        tabla_items = table_pedido.find("table")

        tabla_campos_final=tabla_items.find("thead")
        columnas= [th.get_text(strip=True) for th in tabla_campos_final.find_all("th")]
        columnas.append("fecha de entrega")
        columnas.append("cliente")
        
       
        
        columnas[0]="Numero de pedido"
        
        
        
        tabla_items_final=tabla_items.find("tbody")
        filas = tabla_items_final.find_all("tr")
        

        
        datos_pedido =[]

        for fil in filas:
            celdas = [td.get_text(strip=True) for td in fil.find_all("td")]
            if not celdas:  # Si la lista está vacía, salta esta iteración
                continue
            celdas[0]=pedido_exist
            celdas.remove("")
            celdas.append(fecha_entrega)
            celdas.append(cliente)
            
            
            print(celdas)
            fila_dict = dict(zip(columnas,celdas))
            datos_pedido.append(fila_dict)
        
        df = pd.DataFrame(datos_pedido)

        ruta_archivo = r"C:\Users\JORGE CONTRERAS\OneDrive - 900208659-2 DAMIS SAS\Escritorio\PLANEACION\consumos\INDICADORES PLANEACION\analisis_pedidos.xlsx"
        hoja_objetivo ="Pedidos_clientes"

        

        if os.path.exists(ruta_archivo):
            df_pedidos = pd.read_excel(ruta_archivo)
            df_pedidos_comb = pd.concat([df_pedidos,df], ignore_index=True)

            df_final_pedido = df_pedidos_comb.drop_duplicates(subset=['Numero de pedido', 'Producto', 'Color', 'Cant', 'Descripcion', 'Largo(mm)', 'Altura(mm)', 'Proy.(mm)', 'Valor Unidad', 'Descuento', 'Precio Final', 'Total', '', 'fecha de entrega', 'cliente'], keep="last")
        else:
            df_final_pedido=df

        with pd.ExcelWriter(ruta_archivo, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
    # Guarda el DataFrame en una nueva hoja
            df_final_pedido.to_excel(writer, sheet_name=hoja_objetivo, index=False)


        
    else:
        print("No se pudo acceder a la URL protegida.")
else:
    print("Login fallido.")