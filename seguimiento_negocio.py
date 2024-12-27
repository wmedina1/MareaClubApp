import importlib.metadata
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime
import time
from io import BytesIO
import base64

# Archivos necesarios
MENU_FILE = "menu.xlsx"
CONSUMOS_FILE = "consumos.xlsx"
BACKUP_DIR = "In"

# Crear directorio de backups si no existe
os.makedirs(BACKUP_DIR, exist_ok=True)

# Función para cargar menú
def cargar_menu():
    if os.path.exists(MENU_FILE):
        return pd.read_excel(MENU_FILE)
    else:
        return pd.DataFrame(columns=["ID", "Producto", "Precio", "Ganancias"])

# Función para cargar consumos
def cargar_consumos():
    if os.path.exists(CONSUMOS_FILE):
        consumos_df = pd.read_excel(CONSUMOS_FILE)
        # Verificar si las columnas requeridas existen
        columnas_requeridas = ["Cliente", "Producto", "Cantidad", "Precio Unitario", "Ganancia", "Total", "Fecha", "Pago"]
        for columna in columnas_requeridas:
            if columna not in consumos_df.columns:
                consumos_df[columna] = None
        return consumos_df
    else:
        return pd.DataFrame(columns=["Cliente", "Producto", "Cantidad", "Precio Unitario", "Ganancia", "Total", "Fecha", "Pago"])

# Guardar consumos
def guardar_consumos(consumos_df):
    consumos_df.to_excel(CONSUMOS_FILE, index=False)

# Registrar consumo
def registrar_consumo(cliente, producto, cantidad, precio_unitario, ganancia):
    total = cantidad * precio_unitario
    ganancia_total = cantidad * ganancia
    fecha = datetime.datetime.now().strftime("%Y-%m-%d")

    nuevo_consumo = {
        "Cliente": cliente,
        "Producto": producto,
        "Cantidad": cantidad,
        "Precio Unitario": precio_unitario,
        "Ganancia": ganancia_total,
        "Total": total,
        "Fecha": fecha,
        "Pago": None
    }
    consumos_df = cargar_consumos()
    consumos_df = pd.concat([consumos_df, pd.DataFrame([nuevo_consumo])], ignore_index=True)
    guardar_consumos(consumos_df)
    return nuevo_consumo

# Actualizar pago de un cliente
def actualizar_pago(cliente, metodo_pago):
    consumos_df = cargar_consumos()
    consumos_df.loc[consumos_df["Cliente"] == cliente, "Pago"] = metodo_pago
    guardar_consumos(consumos_df)
    return consumos_df[consumos_df["Cliente"] == cliente]

# Generar reporte diario
def generar_reporte_diario():
    consumos_df = cargar_consumos()
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
    reporte_diario = consumos_df[consumos_df["Fecha"] == fecha_actual]

    if not reporte_diario.empty:
        total_vendido = reporte_diario["Total"].sum()
        ganancias_totales = reporte_diario["Ganancia"].sum()
        unidades_vendidas = reporte_diario["Cantidad"].sum()

        # KPIs
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Vendido", f"RD$ {total_vendido:,.2f}")
        col2.metric("Ganancias Totales", f"RD$ {ganancias_totales:,.2f}")
        col3.metric("Unidades Vendidas", f"{unidades_vendidas:,}")

        # Centrando las gráficas
        col4, col5 = st.columns(2)

        with col4:
            productos_vendidos = reporte_diario.groupby("Producto")["Cantidad"].sum()
            plt.figure(figsize=(6, 5))
            productos_vendidos.plot(kind="barh", color="skyblue", title="Cantidad de Productos Vendidos")
            plt.xlabel("Cantidad")
            plt.tight_layout()
            st.pyplot(plt.gcf())  # Mostrar la gráfica centrada

        with col5:
            ingresos_por_producto = reporte_diario.groupby("Producto")["Total"].sum()
            plt.figure(figsize=(6, 5))
            ingresos_por_producto.plot(kind="barh", color="green", title="Ingresos por Producto")
            plt.xlabel("Ingresos (RD$)")
            plt.tight_layout()
            st.pyplot(plt.gcf())  # Mostrar la gráfica centrada

        # Colocar Resumen por Cliente y Métodos de Pago en la misma fila
        col6, col7 = st.columns(2)

        with col6:
            st.subheader("Resumen por Cliente")
            resumen_clientes = reporte_diario.groupby("Cliente")[["Total", "Ganancia"]].sum().reset_index()
            st.dataframe(resumen_clientes)

        with col7:
            st.subheader("Métodos de Pago")
            metodos_pago = reporte_diario["Pago"].value_counts()
            plt.figure(figsize=(4, 4))
            metodos_pago.plot(kind="pie", autopct="%1.1f%%", title="Distribución por Método de Pago")
            plt.ylabel("")
            plt.tight_layout()
            st.pyplot(plt.gcf())  # Gráfico de pastel más pequeño

        # Clientes que han pagado y no han pagado
        st.subheader("Clientes que han Pagado")
        clientes_pagados = reporte_diario[reporte_diario["Pago"].notna()]
        st.dataframe(clientes_pagados[["Cliente", "Pago", "Total"]])

        st.subheader("Clientes que NO han Pagado")
        clientes_no_pagados = reporte_diario[reporte_diario["Pago"].isna()]
        st.dataframe(clientes_no_pagados[["Cliente", "Total"]])
        total_no_pagados = clientes_no_pagados["Total"].sum()
        st.write(f"Total no pagado: RD$ {total_no_pagados:,.2f}")
    else:
        st.write("No hay datos para el día de hoy.")
        
# Generar factura en formato impreso
# Generar factura en formato impreso
def imprimir_factura(cliente_df, cliente_seleccionado):
    total_cliente = cliente_df["Total"].sum()
    factura_texto = f"""
Factura para: **{cliente_seleccionado}**
===============================================================
Cantidad   Producto                                   Total
---------------------------------------------------------------
"""
    for _, row in cliente_df.iterrows():
        factura_texto += f"{row['Cantidad']:<10}{row['Producto']:<40}RD$ {row['Total']:>10,.2f}\n"
    factura_texto += f"""
===============================================================
{'Total acumulado:':<50}RD$ {total_cliente:,.2f}
===============================================================
"""
    st.markdown(f"```\n{factura_texto}\n```")

  
# Generar reporte diario en formato HTML
def generar_reporte_diario_html(reporte_diario):
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
    html_content = f"""
    <html>
    <head>
        <title>Reporte Diario - {fecha_actual}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; text-align: left; padding: 8px; }}
            th {{ background-color: #f2f2f2; }}
            .kpi {{ font-size: 18px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h1>Reporte Diario</h1>
        <div class="kpi">Total Vendido: RD$ {reporte_diario["Total"].sum():,.2f}</div>
        <div class="kpi">Ganancias Totales: RD$ {reporte_diario["Ganancia"].sum():,.2f}</div>
        <div class="kpi">Unidades Vendidas: {reporte_diario["Cantidad"].sum()}</div>
        <table>
            <thead>
                <tr>
                    <th>Cliente</th>
                    <th>Producto</th>
                    <th>Cantidad</th>
                    <th>Total</th>
                    <th>Pago</th>
                </tr>
            </thead>
            <tbody>
    """
    for _, row in reporte_diario.iterrows():
        html_content += f"""
        <tr>
            <td>{row['Cliente']}</td>
            <td>{row['Producto']}</td>
            <td>{row['Cantidad']}</td>
            <td>RD$ {row['Total']:,.2f}</td>
            <td>{row['Pago']}</td>
        </tr>
        """
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    html_path = os.path.join(BACKUP_DIR, f"reporte_diario_{fecha_actual}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    st.success(f"Reporte en HTML guardado en {html_path}.")

# Función para generar un enlace de descarga
def generar_descarga(filepath, label):
    with open(filepath, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(filepath)}">{label}</a>'
    return href

# Modificación en cerrar_dia
def cerrar_dia():
    consumos_df = cargar_consumos()
    clientes_no_pagados = consumos_df[consumos_df["Pago"].isna()]
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")

    if not clientes_no_pagados.empty:
        total_pendiente = clientes_no_pagados["Total"].sum()
        st.warning(f"Faltan {len(clientes_no_pagados)} clientes por pagar con un total de RD$ {total_pendiente:.2f}.")
        st.dataframe(clientes_no_pagados[["Cliente", "Total"]])
        if st.button("Sí, cerrar el día de todos modos", key="confirmar_cierre_btn"):
            backup_path = os.path.join(BACKUP_DIR, f"consumos_{fecha_actual}.xlsx")
            consumos_df.to_excel(backup_path, index=False)

            guardar_consumos(pd.DataFrame(columns=consumos_df.columns))
            st.success(f"Día cerrado. Datos guardados en {backup_path}.")
            descargar_reporte = generar_descarga(backup_path, "Descargar Reporte")
            st.markdown(descargar_reporte, unsafe_allow_html=True)
    else:
        backup_path = os.path.join(BACKUP_DIR, f"consumos_{fecha_actual}.xlsx")
        consumos_df.to_excel(backup_path, index=False)

        guardar_consumos(pd.DataFrame(columns=consumos_df.columns))
        st.success(f"Día cerrado. Datos guardados en {backup_path}.")
        descargar_reporte = generar_descarga(backup_path, "Descargar Reporte")
        st.markdown(descargar_reporte, unsafe_allow_html=True)


# Cargar datos iniciales
menu_df = cargar_menu()

# Configuración de la página de Streamlit
st.set_page_config(page_title="Marea Club - Registro de Consumos", layout="wide")
st.title("Registro de Consumos - Marea Club")

# Organización del diseño
col1, col2 = st.columns(2)

with col1:
    st.header("Registrar Consumo")
    cliente = st.text_input("Nombre del Cliente", value="", key="cliente_input", help="Escriba el nombre del cliente. Si ya existe, aparecerá en las sugerencias.")
    if not cliente.strip():
        st.error("El nombre del cliente no puede estar vacío.")
    else:
        nombres_registrados = cargar_consumos()["Cliente"].dropna().unique().tolist()
        if cliente in nombres_registrados:
            st.info("Cliente ya registrado.")
        producto_seleccionado = st.selectbox("Producto", menu_df["Producto"], key="producto_select")
        cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1, key="cantidad_input")
        precio_unitario = menu_df[menu_df["Producto"] == producto_seleccionado]["Precio"].values[0]
        ganancia = menu_df[menu_df["Producto"] == producto_seleccionado]["Ganancias"].values[0]

        if st.button("Registrar Consumo", key="registrar_consumo_btn"):
            nuevo_consumo = registrar_consumo(cliente, producto_seleccionado, cantidad, precio_unitario, ganancia)
            st.success(f"Consumo registrado: Cliente: {nuevo_consumo['Cliente']}, Producto: {nuevo_consumo['Producto']}, Cantidad: {nuevo_consumo['Cantidad']}")
            nombres_registrados = cargar_consumos()["Cliente"].dropna().unique().tolist()
            st.query_params["update"] = "true"
        
        
with col2:
    st.header("Asignar Pago")
    clientes_no_pagados = cargar_consumos()
    clientes_no_pagados = clientes_no_pagados[clientes_no_pagados["Pago"].isna()]["Cliente"].dropna().unique()
    if len(clientes_no_pagados) > 0:
        cliente_pago = st.selectbox("Nombre del Cliente para Asignar Pago", clientes_no_pagados, key="cliente_pago_select")
        metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Tarjeta", "Transferencia", "Mixto"], key="metodo_pago_select")
        if st.button("Registrar Pago", key="registrar_pago_btn"):
            cliente_actualizado = actualizar_pago(cliente_pago, metodo_pago)
            if not cliente_actualizado.empty:
                st.success(f"Pago registrado para {cliente_pago}: {metodo_pago}")
            else:
                st.error("Error al registrar el pago. Verifique los datos ingresados.")
    else:
        st.info("Todos los clientes han registrado su pago.")


# Nueva fila de columnas
col3, col4 = st.columns(2)

with col3:
    st.header("Detalles del Cliente - Factura")
    cliente_seleccionado = st.selectbox("Consultar Cliente", nombres_registrados, key="cliente_seleccionado_input")
    if st.button("Mostrar Detalles", key="mostrar_detalles_btn"):
        consumos_df = cargar_consumos()
        cliente_df = consumos_df[consumos_df["Cliente"] == cliente_seleccionado]
        if not cliente_df.empty:
            imprimir_factura(cliente_df, cliente_seleccionado)
        else:
            st.write("No se encontraron consumos para este cliente.")

with col4:
    st.header("Cierre del Día")
    if st.button("Cerrar Día", key="cerrar_dia_btn"):
        cerrar_dia()

# Sección para generar reporte diario
st.header("Reporte Diario")
if st.button("Generar Reporte Diario", key="generar_reporte_btn"):
    generar_reporte_diario()
