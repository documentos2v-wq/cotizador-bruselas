from datetime import datetime
import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import streamlit as st

# Configuración de la página de Streamlit
st.set_page_config(page_title="Generador de Cotizaciones - Bruselas", layout="wide")

st.title("📄 Generador de Cotizaciones - BRUSELAS GROUP EIRL")
st.markdown("---")

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
    return f"{texto_enteras} CON {decimales_str}"

# --- SECCIÓN 1: DATOS GENERALES ---
st.subheader("1. Información del Cliente y Cotización")
col1, col2, col3 = st.columns(3)

with col1:
    nro_cotizacion = st.text_input("N° de Cotización", "000-5960")
    cliente = st.text_input("Cliente", "RED INTEGRADA DE SALUD OTUZCO")
with col2:
    fecha = st.date_input("Fecha", datetime.today())
    direccion = st.text_input("Dirección", "CALLE TACNA Nº 769 - OTUZCO - LA LIBERTAD")
with col3:
    ruc = st.text_input("RUC del Cliente", "20354537096")
    codigo_ref = st.text_input("Código Interno / Ref", "002022-0007-0045")

st.markdown("---")

# --- SECCIÓN 2: DETALLE DE PRODUCTOS ---
st.subheader("2. Detalle de Productos (Casillas de Precios Unitarios y Cantidades)")

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

df_editado = st.data_editor(
    st.session_state.productos_df,
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

df_limpio['Importe'] = df_limpio['Cantidad'] * df_limpio['P.U. (Inc. IGV)']
importe_total_general = df_limpio['Importe'].sum()
monto_en_letras = numero_a_letras(importe_total_general)

st.info(f"**Importe Total General calculado:** S/ {importe_total_general:,.2f}  \n**En Letras:** *{monto_en_letras}*")

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

# --- FUNCIÓN PARA DIBUJAR EL PIE DE PÁGINA EN EL PDF ---
def agregar_pie_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#003366"))
    canvas.rect(0, 0, 612, 35, fill=1, stroke=0)
    
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8)
    texto_pie = "CAL. FRANCISCO VIDAL DE LAOS NRO. 686 URB. LA VIÑA LIMA - LIMA - SAN LUIS - 917386419 - www.ventasschag.com"
    canvas.drawCentredString(612 / 2.0, 13, texto_pie)
    canvas.restoreState()

# --- FUNCIÓN PARA GENERAR EL PDF ---
def generar_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=50)
    elements = []
    
    styles = getSampleStyleSheet()
    estilo_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=9, leading=11)
    estilo_blanco = ParagraphStyle('BlancoCustom', parent=styles['Normal'], fontSize=9, leading=11, fontName="Helvetica-Bold", textColor=colors.white)
    estilo_letras = ParagraphStyle('LetrasCustom', parent=styles['Normal'], fontSize=8, leading=10, fontName="Helvetica-Oblique")
    
    # Estilos reducidos para las condiciones comerciales
    estilo_cond_label = ParagraphStyle('CondLabel', parent=styles['Normal'], fontSize=7, leading=9, fontName="Helvetica-Bold")
    estilo_cond_value = ParagraphStyle('CondValue', parent=styles['Normal'], fontSize=7, leading=9)
    
    estilo_th = ParagraphStyle('TH', parent=styles['Normal'], fontSize=8, leading=10, fontName="Helvetica-Bold", textColor=colors.white, alignment=1)
    estilo_td_left = ParagraphStyle('TDL', parent=styles['Normal'], fontSize=8, leading=10, alignment=0)
    estilo_td_center = ParagraphStyle('TDC', parent=styles['Normal'], fontSize=8, leading=10, alignment=1)
    estilo_td_right = ParagraphStyle('TDR', parent=styles['Normal'], fontSize=8, leading=10, alignment=2)
    
    # Encabezado Empresa
    elements.append(Paragraph("<b>BRUSELAS GROUP EIRL</b>", ParagraphStyle('Empresa', fontSize=18, leading=20, textColor=colors.HexColor("#003366"), fontName="Helvetica-Bold")))
    elements.append(Paragraph("CAL. FRANCISCO VIDAL DE LAOS NRO. 686 URB. LA VIÑA LIMA - LIMA - SAN LUIS", estilo_normal))
    elements.append(Paragraph("RUC: 20611576456 | ventasschag@gmail.com | (051) 6514075 / +51 917 386 419", estilo_normal))
    elements.append(Spacer(1, 10))
    
    subtotal = importe_total_general / 1.18
    igv = importe_total_general - subtotal
    
    info_data = [
        [Paragraph(f"<b>CODIGO:</b> {codigo_ref}", estilo_normal), Paragraph(f"<b>FECHA:</b> {fecha.strftime('%d/%m/%Y')}", estilo_blanco)],
        [Paragraph(f"<b>CLIENTE:</b> {cliente}", estilo_normal), Paragraph(f"<b>PROF. N°:</b> {nro_cotizacion}", estilo_blanco)],
        [Paragraph(f"<b>DIRECCION:</b> {direccion}", estilo_normal), ""],
        [Paragraph(f"<b>RUC:</b> {ruc}", estilo_normal), ""]
    ]
    
    t_info = Table(info_data, colWidths=[380, 150])
    t_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (1,0), (1,1), 1, colors.HexColor("#003366")),
        ('BACKGROUND', (1,0), (1,1), colors.HexColor("#003366")),
        ('TOPPADDING', (1,0), (1,1), 4),
        ('BOTTOMPADDING', (1,0), (1,1), 4),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 15))
    
    prod_data = [[
        Paragraph("CANT.", estilo_th),
        Paragraph("CODIGO", estilo_th),
        Paragraph("DESCRIPCION", estilo_th),
        Paragraph("MARCA", estilo_th),
        Paragraph("PLAZO ENTREGA", estilo_th),
        Paragraph("P.U.", estilo_th),
        Paragraph("IMPORTE", estilo_th)
    ]]
    
    for _, row in df_limpio.iterrows():
        cant_val = int(row['Cantidad'])
        pu_val = float(row['P.U. (Inc. IGV)'])
        imp_val = cant_val * pu_val
        prod_data.append([
            Paragraph(str(cant_val), estilo_td_center),
            Paragraph(str(row['Código']) if pd.notna(row['Código']) else "", estilo_td_center),
            Paragraph(str(row['Descripción']) if pd.notna(row['Descripción']) else "", estilo_td_left),
            Paragraph(str(row['Marca']) if pd.notna(row['Marca']) else "", estilo_td_center),
            Paragraph(str(row['Plazo Entrega']) if pd.notna(row['Plazo Entrega']) else "", estilo_td_center),
            Paragraph(f"S/ {pu_val:,.2f}", estilo_td_right),
            Paragraph(f"S/ {imp_val:,.2f}", estilo_td_right)
        ])
    
    t_prod = Table(prod_data, colWidths=[40, 60, 210, 50, 60, 50, 60])
    t_prod.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_prod)
    
    letras_data = [[Paragraph(f"<b>SON:</b> &nbsp; <i>{monto_en_letras}</i>", estilo_letras)]]
    t_letras = Table(letras_data, colWidths=[530])
    t_letras.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9F9F9")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_letras)
    elements.append(Spacer(1, 10))
    
    totales_data = [
        ["IMPORTE", f"S/ {subtotal:,.2f}"],
        ["IGV", f"S/ {igv:,.2f}"],
        ["TOTAL", f"S/ {importe_total_general:,.2f}"]
    ]
    
    t_totales = Table(totales_data, colWidths=[100, 100])
    t_totales.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#003366")),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0,0), (0,-1), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    
    wrapper_totales = Table([["", t_totales]], colWidths=[330, 200])
    elements.append(wrapper_totales)
    
    # Espaciador más grande para empujar las condiciones comerciales más hacia abajo
    elements.append(Spacer(1, 25))
    
    # Condiciones comerciales con letra más pequeña y compacta
    cond_data = [
        [Paragraph("TIEMPO ENTREGA", estilo_cond_label), Paragraph(f": {tiempo_entrega}", estilo_cond_value)],
        [Paragraph("RAZÓN SOCIAL", estilo_cond_label), Paragraph(": BRUSELAS GROUP EIRL", estilo_cond_value)],
        [Paragraph("FORMA DE PAGO", estilo_cond_label), Paragraph(f": {forma_pago}", estilo_cond_value)],
        [Paragraph("MONEDA", estilo_cond_label), Paragraph(f": {moneda}", estilo_cond_value)],
        [Paragraph("VALIDEZ DE OFERTA", estilo_cond_label), Paragraph(f": {validez}", estilo_cond_value)],
        [Paragraph("GARANTÍA", estilo_cond_label), Paragraph(f": {garantia}", estilo_cond_value)],
        [Paragraph("EJECUTIVO DE VENTAS", estilo_cond_label), Paragraph(f": {ejecutivo}", estilo_cond_value)]
    ]
    
    t_cond = Table(cond_data, colWidths=[110, 250])
    t_cond.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    elements.append(t_cond)
    
    doc.build(elements, onFirstPage=agregar_pie_pagina, onLaterPages=agregar_pie_pagina)
    buffer.seek(0)
    return buffer

st.markdown("---")
if st.button("📥 Generar y Descargar Cotización en PDF"):
    pdf_file = generar_pdf()
    st.success("¡Cotización generada con éxito!")
    st.download_button(
        label="Descargar Archivo PDF",
        data=pdf_file,
        file_name=f"Cotizacion_{nro_cotizacion.replace('-', '_')}.pdf",
        mime="application/pdf"
    )
