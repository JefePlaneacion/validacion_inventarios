import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import shutil

# URLs
login_url = "https://tg.toscanagroup.com.co/index.php"
ruta_archivo = r"C:/Users/JORGE CONTRERAS/OneDrive - 900208659-2 DAMIS SAS/Escritorio/PLANEACION/PLANEACION/INDICADORES PLANEACION/analisis_pedidos.xlsx"
hoja_objetivo = "Pedidos_clientes"

# Lista de pedidos a consultar
pedidos_list = [106371,106259,106573,106511,104022,102697,102599,106335,102445,105899,106584,106153,106011,105970,106430,105268,100234,106120,106049,106139,106148,104830,106419,106395,106326,100150,104417,104253,104357,106094,106114,105671,105398,102253,106103,100249,103091,101262,105093,105672,105189,105171,105552]

# Crear copia de seguridad del archivo si existe
if os.path.exists(ruta_archivo):
    ruta_backup = ruta_archivo.replace(".xlsx", "_backup.xlsx")
    shutil.copy(ruta_archivo, ruta_backup)

try:
    # Crear sesión persistente
    session = requests.Session()

    # Obtener la página de login
    login_page = session.get(login_url, timeout=10)
    login_page.raise_for_status()

    # Autenticación
    payload = {
        'usuario': 'jorge.contreras',
        'contrasena': 'EstebanGrey1704*'
    }

    login_response = session.post(login_url, data=payload, timeout=10)
    login_response.raise_for_status()

    if "Ingresar" in login_response.text:
        print("Login fallido.")
        exit()

    print("Login exitoso!")

    # Leer archivo Excel si existe
    if os.path.exists(ruta_archivo):
        df_pedidos_existente = pd.read_excel(ruta_archivo, sheet_name=hoja_objetivo, dtype={"Numero de Pedido": str})
    else:
        df_pedidos_existente = pd.DataFrame()

    # Convertir la columna de pedidos en un set para búsqueda rápida
    pedidos_existentes = set(df_pedidos_existente["Numero de Pedido"].astype(str)) if not df_pedidos_existente.empty else set()

    # Lista para almacenar nuevos pedidos
    nuevos_pedidos = []

    # Iterar sobre cada pedido
    for pedido_sel in pedidos_list:
        pedido_sel_str = str(pedido_sel)

        # Si el pedido ya está en la base de datos, lo ignoramos
        if pedido_sel_str in pedidos_existentes:
            print(f"El pedido {pedido_sel} ya existe en la base de datos. Se omitirá.")
            continue

        protected_url = f"https://tg.toscanagroup.com.co/ver_cotizacion.php?id={pedido_sel}"
        protected_response = session.get(protected_url, timeout=10)
        protected_response.raise_for_status()

        print(f"Accediendo a pedido {pedido_sel}...")

        soup = BeautifulSoup(protected_response.text, 'html.parser')
        table_element = soup.find("div", class_="container-fluid")
        datos_cliente = str(table_element.find("h3"))

        texto_dividido = r"Pedido\s+(.*?)\s+-\s+No\.(\d+)\s+-\s+Fecha Entrega:(\d{4}/\d{2}/\d{2})"
        texto_dividido_final = re.search(texto_dividido, datos_cliente)

        if texto_dividido_final:
            cliente = texto_dividido_final.group(1).strip()
            pedido_exist = texto_dividido_final.group(2).strip()
            fecha_entrega = texto_dividido_final.group(3).strip()
        else:
            cliente = "Desconocido"
            pedido_exist = "00000"
            fecha_entrega = "0000/00/00"

        # Extraer tabla de pedidos
        tabla_pedido = table_element.find_all("div", class_="row-fluid")
        table_pedido = tabla_pedido[-4]
        tabla_items = table_pedido.find("table")

        tabla_campos_final = tabla_items.find("thead")
        if not tabla_campos_final:
            print(f"Error: No se encontraron los campos de la tabla para el pedido {pedido_sel}")
            continue

        columnas = [th.get_text(strip=True) for th in tabla_campos_final.find_all("th")[1:-1]]
        columnas.extend(["fecha de entrega", "cliente", "Numero de Pedido"])

        tabla_items_final = tabla_items.find("tbody")
        filas = tabla_items_final.find_all("tr")

        for fil in filas:
            celdas = [td.get_text(strip=True) for td in fil.find_all("td")[1:-2]]
            if not celdas:
                continue

            celdas.extend([fecha_entrega, cliente, int(pedido_exist)])
            nuevos_pedidos.append(dict(zip(columnas, celdas)))

    # Si hay nuevos pedidos, agregarlos al archivo
    if nuevos_pedidos:
        df_nuevos_pedidos = pd.DataFrame(nuevos_pedidos)

        # Verificar duplicados antes de agregar
        if not df_pedidos_existente.empty:
            df_pedidos_final = pd.concat([df_pedidos_existente, df_nuevos_pedidos], ignore_index=True)
        else:
            df_pedidos_final = df_nuevos_pedidos

        # Guardar en Excel
        with pd.ExcelWriter(ruta_archivo, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
            df_pedidos_final.to_excel(writer, sheet_name=hoja_objetivo, index=False)

        print(f"Se guardaron {len(nuevos_pedidos)} nuevos pedidos.")
    else:
        print("No hay nuevos pedidos para guardar.")

except requests.exceptions.RequestException as e:
    print(f"Error de red o solicitud: {e}")
except Exception as e:
    print(f"Error inesperado: {e}")

