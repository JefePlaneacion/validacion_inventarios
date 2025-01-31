import aiohttp
import asyncio
import pandas as pd
import os
from openpyxl import load_workbook
from urllib.parse import quote


#parametros = "f150_id=''MP002''"
#parametros_codificados=quote(parametros)
# Configuración de la API
url = "http://201.234.74.137:82/v3/ejecutarconsultaestandar"
headers = {
    'conniKey': 'Connikey-parasolestropicalesdamis-VJDSNLE1',
    'conniToken': 'VJDSNLE1UDVAOFG4SZNFMU40SDJYOFG4SZNAOESZWTHPNFO4VTDZOA'
}
params = {
    "idCompania": 6631,
    "descripcion": "API_v2_Compras_Ordenes",
    
    #"parametros": parametros_codificados#"f150_id='MP002' and f420_fecha%3E%3D%27%272024-05-01T00:00:00%27%27"
}
num_pag = 1  # Número de página
tam_pag = 100  # Tamaño de página
max_concurrent_tasks = 10  # Máximo de tareas concurrentes


ruta_archivo = r"C:\Users\JORGE CONTRERAS\OneDrive - 900208659-2 DAMIS SAS\Escritorio\PLANEACION\consumos\INDICADORES PLANEACION\analisis_pedidos.xlsx"
hoja_objetivo = "ordenes_compra"

async def fetch_page(session, num_pag):
    """
    Función para obtener una página de datos.
    """
    # Hacemos una copia de los parámetros para evitar modificar el global `params`
    params_with_paging = {**params,'paginacion': f'numPag={num_pag}|tamPag={tam_pag}','parametros':"f420_fecha>=''2024-11-01T00:00:00'' and f150_id=''MP002''"}

    
    try:
        async with session.get(url, headers=headers, params=params_with_paging) as response:
            #print(response)

            #raise SystemError('aca termina')

    
            print(f"Consultando página {num_pag} con parámetros: {params_with_paging}")  # Depuración: Imprimir parámetros de la solicitud
            if response.status != 200:
                print(f"Error al obtener la página {num_pag}: {response.status} - {await response.text()}")
                return []
            data = await response.json()
            print(f"Respuesta de la página {num_pag}: {data}")  # Depuración: Imprimir respuesta de la API
            
            # Verifica si los datos están en la clave 'data'
            if 'detalle' not in data or 'Table' not in data['detalle']:
                print(f"Respuesta inesperada en la página {num_pag}: {data}")
                return []
                
            return data['detalle']['Table']  # Extrae la lista de datos de la respuesta

    except Exception as e:
        print(f"Excepción al obtener la página {num_pag}: {e}")
        return []

async def fetch_all_data():
    """
    Función principal para obtener todos los datos de forma concurrente.
    """
    base_inventario = []  # Lista para almacenar todos los datos
    async with aiohttp.ClientSession() as session:
        page = 1
        while True:
            # Crear tareas para las páginas actuales
            tasks = [
                asyncio.create_task(fetch_page(session, page + i))
                for i in range(max_concurrent_tasks)
            ]
            
            
            # Esperar a que todas las tareas se completen
            results = await asyncio.gather(*tasks)
            print(f'resltados en {page}:{results}')
            
            # Agregar los datos obtenidos a la lista principal
            for result in results:
                if not result:  # Si una página no tiene datos, hemos llegado al final
                    print("No se encontraron más datos en las páginas.")
                    return base_inventario
                base_inventario.extend(result)

            # Avanzar al siguiente bloque de páginas
            page += max_concurrent_tasks
    return base_inventario

def obtener_dataframe():
    """
    Función para obtener los datos como un DataFrame y guardarlos en un archivo Excel.
    """
    # Ejecutar el bucle de eventos asíncronos
    datos = asyncio.run(fetch_all_data())
    print(datos)
    
    
    # Verificar si los datos están vacíos antes de intentar crear el DataFrame
    if not datos:
        print("No se obtuvieron datos.")
        return pd.DataFrame()  # Retorna un DataFrame vacío si no hay datos

    # Convertir la lista de datos en un DataFrame de pandas
    df = pd.DataFrame(datos)
    
    # Verificar el contenido del DataFrame antes de guardar
    print(f"Datos obtenidos: {len(df)} filas.")
    print(df.head())  # Imprimir las primeras filas del DataFrame para depuración
    
    df =df[['f420_ts','f420_id_tipo_docto','f420_fecha','f420_id_clase_docto','f420_desc_estado','f120_referencia','f120_descripcion','f150_id','f421_cant_pedida','f421_cant_entrada']]
    
    df.columns=['Fecha Modificación','Tipo Doc','Fecha Occ','Clase Doc','Estado','Cod Ref','Desc Item','Bodega','Cant Pedida','Cant Entrada']
    
    # Guardar el DataFrame en un archivo Excel


    with pd.ExcelWriter(ruta_archivo, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=hoja_objetivo, index=False)
    print("Datos guardados exitosamente.")
    

    return df




# Uso del código
if __name__ == "__main__":
    df = obtener_dataframe()