import streamlit as st
import pandas as pd
import plotly.express as px


df_final = pd.read_excel("consumoi.xlsx")
print(df_final)

# Datos simulados de inventario
data = {
    "Producto": ["A", "B", "C", "D", "E"],
    "Inventario": [100, 50, 15, 10, 5],
    "Punto_de_Reorden": [80, 40, 20, 10, 8]
}

df = pd.DataFrame(data)

# Crear columna de alerta
df["Estado"] = df.apply(lambda row: "🔴 Alerta: Inventario bajo" if row["Inventario"] <= row["Punto_de_Reorden"] else "🟢 OK", axis=1)

# Título del dashboard
st.title("📊 Cuadro de Alertas - Inventario y Punto de Reorden")

# Mostrar la tabla completa
st.write("### Tabla completa del inventario")
st.dataframe(df)

# Filtrar solo los productos en alerta
alertas = df[df["Estado"].str.contains("🔴")]
st.write("### Productos en alerta")

if not alertas.empty:
    st.warning(f"⚠️ Hay {len(alertas)} productos en alerta.")
    st.dataframe(alertas)

    # Gráfico interactivo para visualizar el inventario de los productos en alerta
    fig = px.bar(alertas, x="Producto", y="Inventario", title="Inventario de productos en alerta", color="Inventario", color_continuous_scale="reds")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.success("✅ No hay productos en alerta.")

# Botón para simular actualización de datos
if st.button("🔄 Actualizar datos"):
    st.info("Función de actualización pendiente de implementar. Aquí podrías conectar datos reales.")
