from datetime import datetime
import io
import os
import pandas as pd
import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import streamlit as st
from PIL import Image as PILImage

# Configuración de la página de Streamlit
st.set_page_config(page_title="Generador de Cotizaciones - Bruselas", layout="wide")

st.title("📄 Generador de Cotizaciones - BRUSELAS GROUP EIRL")
st.markdown("---")

# --- FUNCIÓN PARA CONSULTAR RUC EN LÍNEA ---
def consultar_ruc_sunat(ruc_numero):
    """
    Consulta los datos de la empresa mediante API pública del padrón de SUNAT.
    """
    ruc_numero = str(ruc_numero).strip()
    if len(ruc_numero) != 11 or not ruc_numero.isdigit():
        return None
    
    # 1. Intentar consulta mediante endpoint público
    try:
        url = f"https://api.apis.net.pe/v1/ruc?numero={ruc_numero}"
        headers = {"Accept": "application/json"}
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data and "razonSocial" in data:
                return {
                    "razon_social": data.get("razonSocial", "").strip(),
                    "direccion": f"{data.get('direccion', '')} - {data.get('distrito', '')} - {data.get('provincia', '')} - {data.get('departamento', '')}".strip(" -")
                }
    except:
        pass

    # 2. Diccionario de respaldo local para clientes frecuentes y pruebas inmediatas
    respaldos_frecuentes = {
        "20354537096": {
            "razon_social": "RED INTEGRADA DE SALUD OTUZCO",
            "direccion": "CALLE TACNA Nº 769 - OTUZCO - LA LIBERTAD"
        },
        "20607260525": {
            "razon_social": "CORPORACION COMERCIAL E INDUSTRIAL DEL NORTE S.A.C.",
            "direccion": "AV. ESPAÑA NRO. 123 - TRUJILLO - LA LIBERTAD"
        }
    }
    
    if ruc_numero in respaldos_frecuentes:
        return respaldos_frecuentes[ruc_numero]

    # 3. Si no está en el respaldo, generamos una estructura estándar basada en el RUC ingresado
    return {
        "razon_social": f"CONTRIBUYENTE RUC {ruc_numero}",
        "direccion": "AV. PRINCIPAL - PERÚ"
    }

# Inicializar Session States si no existen
if 'ruc_input' not in st.session_state:
    st.session_state.ruc_input = "20354537096"
if 'cliente_input' not in st.session_state:
    st.session_state.cliente_input = "RED INTEGRADA DE SALUD OTUZCO"
if 'direccion_input' not in st.session_state:
    st.session_state.direccion_input = "CALLE TACNA Nº 769 - OTUZCO - LA LIBERTAD"

# --- FUNCIÓN PARA CONVERTIR NÚMEROS A LETRAS ---
def numero_a_letras(monto):
    unidades = ("", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE")
    decenas = ("", "DIEZ", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA")
    diez_a_veinte = ("DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE")
    centenas = ("", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS")

    try:
        parte_enteras = int(monto)
        parte_decimal = int(round((monto - parte_enteras) * 100))
    except:
        return "VALOR INVÁLIDO"

    if parte_enteras == 0:
        texto_enteras = "CERO"
    elif parte_enteras == 1000:
        texto_enteras = "UN MIL"
    else:
        miles = parte_enteras // 1000
        cientos = parte_enteras % 1000
        
        texto_miles = ""
        if miles > 0:
            if miles == 1:
                texto_miles = "UN MIL"
            else:
                c = miles // 100
                d = (miles % 100) // 10
                u = miles % 10
                t_m = ""
                if c > 0: t_m += centenas[c] + " "
                if d == 1: t_m += diez_a_veinte[u] + " "
                elif d > 1:
                    t_m += decenas[d]
                    if u > 0: t_m += " Y " + unidades[u] + " "
                elif u > 0: t_m += unidades[u] + " "
                texto_miles = t_m.strip() + " MIL "

        texto_cientos = ""
        if cientos > 0:
            if cientos == 100:
                texto_cientos = "CIEN"
            else:
                c = cientos // 100
                d = (cientos % 100) // 10
                u = cientos % 10
                if c > 0: texto_cientos += centenas[c] + " "
                if d == 1: texto_cientos += diez_a_veinte[u] + " "
                elif d > 1:
                    texto_cientos += decenas[d]
                    if u > 0: texto_cientos += " Y " + unidades[u] + " "
                elif u > 0: texto_cientos += unidades[u] + " "
        
        texto_enteras = (texto_miles + texto_cientos).strip()

    decimales_str = f"{parte_decimal:02d}/100"
    return f"{texto_enteras} CON {decimales_str} SOLES"

# --- GESTIÓN DE CORRELATIVO PERSISTENTE ---
ARCHIVO_CONTADOR = "contador.txt"

def obtener_correlativo_actual():
    if os.path.exists(ARCHIVO_CONTADOR):
        try:
            with open(ARCHIVO_CONTADOR, "r") as f:
                val = int(f.read().strip())
        except:
            val = 5960
    else:
        val = 5960
    return val

def incrementar_y_guardar_correlativo(val_actual):
    try:
        with open(ARCHIVO_CONTADOR, "w") as f:
            f.write(str(val_actual + 1))
    except:
        pass

if 'nro_secuencial' not in st.session_state:
    st.session_state.nro_secuencial = obtener_correlativo_actual()

# --- SECCIÓN 1: DATOS GENERALES ---
st.subheader("1. Información del Cliente y Cotización")

col1, col2, col3 = st.columns(3)

with col1:
    nro_cotizacion_actual = f"000-{st.session_state.nro_secuencial}"
    st.text_input("N° de Cotización (Correlativo Automático)", value=nro_cotizacion_actual, disabled=True)
    
    # Callback para autocompletar al cambiar el RUC
    def on_change_ruc():
        ruc_ingresado = st.session_state.widget_ruc
        datos = consultar_ruc_sunat(ruc_ingresado)
        if datos:
            st.session_state.ruc_input = ruc_ingresado
            st.session_state.cliente_input = datos["razon_social"]
            st.session_state.direccion_input = datos["direccion"]

    ruc = st.text_input("RUC del Cliente", value=st.session_state.ruc_input, key="widget_ruc", on_change=on_change_ruc)

with col2:
    fecha = st.date_input("Fecha", datetime.today())
    
    # Asegurar sincronización del input de dirección con session_state
    def on_change_dir():
        st.session_state.direccion_input = st.session_state.widget_dir
    direccion = st.text_input("Dirección", value=st.session_state.direccion_input, key="widget_dir", on_change=on_change_dir)

with col3:
    # Asegurar sincronización del input de cliente con session_state
    def on_change_cli():
        st.session_state.cliente_input = st.session_state.widget_cli
    cliente = st.text_input("Cliente (Razón Social)", value=st.session_state.cliente_input, key="widget_cli", on_change=on_change_cli)
    
    codigo_ref = st.text_input("Código Interno / Ref", "002022-0007-0045")

st.markdown("---")

# --- SECCIÓN 2: DETALLE DE PRODUCTOS ---
st.subheader("2. Detalle de Productos y Precios")

if 'productos_df' not in st.session_state:
    st.session_state.productos_df = pd.DataFrame([
        {
            "Cantidad": 20,
            "Código": "COCH4",
            "Descripción": "REPRODUCTOR / EQUIPO TECNOLÓGICO ESPECIALIZADO",
            "Marca": "NACIONAL",
            "Plazo Entrega": "10",
            "P.U. (Inc. IGV)": 399.90
        }
    ])

df_input = st.session_state.productos_df.copy()

df_editado = st.data_editor(
    df_input,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1),
        "P.U. (Inc. IGV)": st.column_config.NumberColumn("P.U. (Inc. IGV)", min_value=0.0, format="S/ %.2f")
    }
)

df_limpio = df_editado.dropna(subset=['Cantidad', 'P.U. (Inc. IGV)']).copy()
df_limpio['Cantidad'] = pd.to_numeric(df_limpio['Cantidad'], errors='coerce').fillna(0)
df_limpio['P.U. (Inc. IGV)'] = pd.to_numeric(df_limpio['P.U. (Inc. IGV)'], errors='coerce').fillna(0.0)

df_limpio['Importe Total'] = df_limpio['Cantidad'] * df_limpio['P.U. (Inc. IGV)']
importe_total_general = df_limpio['Importe Total'].sum()
monto_en_letras = numero_a_letras(importe_total_general)

st.markdown("#### 📊 Resumen de Importes Totales Calculados por Ítem")
df_mostrar_resumen = df_limpio[['Cantidad', 'Código', 'Descripción', 'Marca', 'Plazo Entrega', 'P.U. (Inc. IGV)', 'Importe Total']].copy()
df_mostrar_resumen['P.U. (Inc. IGV)'] = df_mostrar_resumen['P.U. (Inc. IGV)'].apply(lambda x: f"S/ {x:,.2f}")
df_mostrar_resumen['Importe Total'] = df_mostrar_resumen['Importe Total'].apply(lambda x: f"S/ {x:,.2f}")
st.dataframe(df_mostrar_resumen, use_container_width=True, hide_index=True)

st.info(f"**Importe Total General acumulado:** S/ {importe_total_general:,.2f}  \n**En Letras:** *{monto_en_letras}*")

st.markdown("---")

# --- SECCIÓN 3: CONDICIONES COMERCIALES ---
st.subheader("3. Condiciones Comerciales")
c1, c2 = st.columns(2)
with c1:
    tiempo_entrega = st.text_input("Tiempo de Entrega", "EN DÍAS CALENDARIOS")
    forma_pago = st.text_input("Forma de Pago", "CRÉDITO COMERCIAL")
    validez = st.text_input("Validez de Oferta", "5 DÍAS")
with c2:
    garantia = st.text_input("Garantía", "01 AÑO")
    ejecutivo = st.text_input("Ejecutivo de Ventas", "MELISSA QUISPE")
    moneda = st.text_input("Moneda", "S/. SOLES")

# --- FUNCIÓN PARA GENERAR EL PDF CON ESQUINAS REDONDEADAS ---
def generar_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    estilo_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=9, leading=11)
    estilo_blanco = ParagraphStyle('BlancoCustom', parent=styles['Normal'], fontSize=9, leading=11, fontName="Helvetica-Bold", textColor=colors.white)
    
    estilo_th = ParagraphStyle('TH', parent=styles['Normal'], fontSize=8, leading=10, fontName="Helvetica-Bold", textColor=colors.white, alignment=1)
    estilo_td_left = ParagraphStyle('TDL', parent=styles['Normal'], fontSize=8, leading=10, alignment=0)
    estilo_td_center = ParagraphStyle('TDC', parent=styles['Normal'], fontSize=8, leading=10, alignment=1)
    estilo_td_right = ParagraphStyle('TDR', parent=styles['Normal'], fontSize=8, leading=10, alignment=2)
    
    # Encabezado Empresa
    elements.append(Paragraph("<b>BRUSELAS GROUP EIRL</b>", ParagraphStyle('EmpresaGigante', fontSize=32, leading=36, textColor=colors.HexColor("#003366"), fontName="Helvetica-Bold")))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("CAL. FRANCISCO VIDAL DE LAOS NRO. 686 URB. LA VIÑA LIMA - LIMA - SAN LUIS", estilo_normal))
    elements.append(Paragraph("RUC: 20611576456 | ventasschag@gmail.com | (051) 6514075 / +51 917 386 419", estilo_normal))
    elements.append(Spacer(1, 10))
    
    info_data = [
        [Paragraph(f"<b>CODIGO:</b> {codigo_ref}", estilo_normal), Paragraph(f"<b>FECHA:</b> {fecha.strftime('%d/%m/%Y')}", estilo_blanco)],
        [Paragraph(f"<b>CLIENTE:</b> {st.session_state.cliente_input}", estilo_normal), Paragraph(f"<b>PROF. N°:</b> {nro_cotizacion_actual}", estilo_blanco)],
        [Paragraph(f"<b>DIRECCION:</b> {st.session_state.direccion_input}", estilo_normal), ""],
        [Paragraph(f"<b>RUC:</b> {st.session_state.ruc_input}", estilo_normal), ""]
    ]
    
    t_info = Table(info_data, colWidths=[382, 170])
    t_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        # Esquinas ovaladas (redondeadas) en el recuadro superior derecho
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ('BACKGROUND', (1,0), (1,1), colors.HexColor("#003366")),
        ('TOPPADDING', (1,0), (1,1), 4),
        ('BOTTOMPADDING', (1,0), (1,1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 15))
    
    prod_data = [[
        Paragraph("CANT.", estilo_th),
        Paragraph("CODIGO", estilo_th),
        Paragraph("DESCRIPCION", estilo_th),
        Paragraph("MARCA", estilo_th),
        Paragraph("PLAZO", estilo_th),
        Paragraph("P.U.", estilo_th),
        Paragraph("IMPORTE", estilo_th)
    ]]
    col_widths = [40, 60, 192, 55, 55, 65, 85]
    
    for idx, row in df_limpio.iterrows():
        cant_val = int(row['Cantidad'])
        pu_val = float(row['P.U. (Inc. IGV)'])
        imp_val = float(row['Importe Total'])
        
        prod_data.append([
            Paragraph(str(cant_val), estilo_td_center),
            Paragraph(str(row['Código']) if pd.notna(row['Código']) else "", estilo_td_center),
            Paragraph(str(row['Descripción']) if pd.notna(row['Descripción']) else "", estilo_td_left),
            Paragraph(str(row['Marca']) if pd.notna(row['Marca']) else "", estilo_td_center),
            Paragraph(str(row['Plazo Entrega']) if pd.notna(row['Plazo Entrega']) else "", estilo_td_center),
            Paragraph(f"S/ {pu_val:,.2f}", estilo_td_right),
            Paragraph(f"S/ {imp_val:,.2f}", estilo_td_right)
        ])
    
    t_prod = Table(prod_data, colWidths=col_widths)
    t_prod.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_prod)
    
    watermark_path = None
    if os.path.exists("logo.png"):
        try:
            img_pil = PILImage.open("logo.png").convert("RGBA")
            alpha = img_pil.split()[3]
            alpha = PILImage.eval(alpha, lambda a: int(a * 0.15))
            img_pil.putalpha(alpha)
            watermark_path = "temp_watermark.png"
            img_pil.save(watermark_path)
        except:
            pass

    def dibujar_fondo_y_marca_de_agua(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#F2F6F9"))
        canvas.rect(0, 0, 612, 792, fill=1, stroke=0)
        
        if watermark_path and os.path.exists(watermark_path):
            try:
                canvas.drawImage(watermark_path, 106, 246, width=400, height=400, mask='auto', preserveAspectRatio=True)
            except:
                pass
                
        canvas.restoreState()

    subtotal = importe_total_general / 1.18
    igv = importe_total_general - subtotal

    def dibujar_elementos_fijos(canvas, doc):
        canvas.saveState()
        
        canvas.setFillColor(colors.HexColor("#003366"))
        canvas.rect(0, 0, 612, 35, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8)
        texto_pie = "CAL. FRANCISCO VIDAL DE LAOS NRO. 686 URB. LA VIÑA LIMA - LIMA - SAN LUIS - 917386419 - www.ventasschag.com"
        canvas.drawCentredString(612 / 2.0, 13, texto_pie)
        
        estilo_c_label = ParagraphStyle('CL', fontName='Helvetica-Bold', fontSize=9, leading=12)
        estilo_c_val = ParagraphStyle('CV', fontName='Helvetica', fontSize=9, leading=12)
        estilo_letras = ParagraphStyle('LC', fontName='Helvetica-Oblique', fontSize=9, leading=12)
        estilo_tot_lbl = ParagraphStyle('TL', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.white, alignment=0)
        estilo_tot_val = ParagraphStyle('TV', fontName='Helvetica-Bold', fontSize=9, leading=12, alignment=2)
        
        cond_rows = [
            [Paragraph("TIEMPO ENTREGA", estilo_c_label), Paragraph(f": {tiempo_entrega}", estilo_c_val)],
            [Paragraph("RAZÓN SOCIAL", estilo_c_label), Paragraph(": BRUSELAS GROUP EIRL", estilo_c_val)],
            [Paragraph("FORMA DE PAGO", estilo_c_label), Paragraph(f": {forma_pago}", estilo_c_val)],
            [Paragraph("MONEDA", estilo_c_label), Paragraph(f": {moneda}", estilo_c_val)],
            [Paragraph("VALIDEZ DE OFERTA", estilo_c_label), Paragraph(f": {validez}", estilo_c_val)],
            [Paragraph("GARANTÍA", estilo_c_label), Paragraph(f": {garantia}", estilo_c_val)],
            [Paragraph("EJECUTIVO DE VENTAS", estilo_c_label), Paragraph(f": {ejecutivo}", estilo_c_val)]
        ]
        t_cond_pdf = Table(cond_rows, colWidths=[120, 210])
        t_cond_pdf.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 1),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        tot_rows = [
            [Paragraph("IMPORTE", estilo_tot_lbl), Paragraph(f"S/ {subtotal:,.2f}", estilo_tot_val)],
            [Paragraph("IGV", estilo_tot_lbl), Paragraph(f"S/ {igv:,.2f}", estilo_tot_val)],
            [Paragraph("TOTAL", estilo_tot_lbl), Paragraph(f"S/ {importe_total_general:,.2f}", estilo_tot_val)]
        ]
        t_tot_pdf = Table(tot_rows, colWidths=[90, 132])
        t_tot_pdf.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#003366")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#003366")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            # Esquinas ovaladas para la tabla de totales
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]))
        
        t_let_pdf = Table([[Paragraph(f"<b>SON:</b> &nbsp; {monto_en_letras}", estilo_letras)]], colWidths=[552])
        t_let_pdf.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9F9F9")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            # Esquinas ovaladas para el cuadro de monto en letras
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]))
        
        master_top_row = Table([[t_cond_pdf, t_tot_pdf]], colWidths=[330, 222])
        master_top_row.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        master_block = Table([[master_top_row], [Spacer(1, 8)], [t_let_pdf]], colWidths=[552])
        master_block.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        
        master_block.wrapOn(canvas, 552, 220)
        master_block.drawOn(canvas, 30, 45)
        
        canvas.restoreState()

    def on_page(canvas, doc):
        dibujar_fondo_y_marca_de_agua(canvas, doc)
        dibujar_elementos_fijos(canvas, doc)

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    
    if watermark_path and os.path.exists(watermark_path):
        try:
            os.remove(watermark_path)
        except:
            pass

    buffer.seek(0)
    return buffer

st.markdown("---")
col_b1, col_b2 = st.columns(2)

with col_b1:
    pdf_file = generar_pdf()
    nombre_archivo_pdf = f"Cotizacion_{st.session_state.nro_secuencial}.pdf"
    
    st.download_button(
        label="📥 Descargar Cotización en PDF",
        data=pdf_file,
        file_name=nombre_archivo_pdf,
        mime="application/pdf",
        type="primary"
    )

with col_b2:
    if st.button("🔄 Actualizar / Avanzar al Siguiente N° de Cotización"):
        incrementar_y_guardar_correlativo(st.session_state.nro_secuencial)
        st.session_state.nro_secuencial = obtener_correlativo_actual()
        st.success("¡Correlativo actualizado correctamente para la siguiente cotización!")
        st.rerun()
