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
    """Convierte un número decimal a formato de letras en Soles."""
    # Librería interna simple para convertir números (versión estándar)
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
        # Conversión simplificada para montos comunes de cotización (hasta 999,999)
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

# --- SECCIÓN 2: DETALLE DE PRODUCTOS / ÍTEMS ---
st.subheader("2. Detalle de Productos")

cant = st.number_input("Cantidad", min_value=1, value=20)
codigo_prod = st.text_input("Código de Producto", "COCH4")
descripcion = st.text_area("Descripción del Producto", "REPRODUCTOR / EQUIPO TECNOLÓGICO ESPECIALIZADO")
marca = st.text_input("Marca", "NACIONAL")
plazo_entrega = st.text_input("Plazo de Entrega (días)", "10")
precio_unitario = st.number_input("Precio Unitario (P.U.) con IGV", min_value=0.0, value=399.90)

# Cálculo automático de importes
importe_total_item = cant * precio_unitario
monto_en_letras = numero_a_letras(importe_total_item)

st.info(f"**Importe Total calculado:** S/ {importe_total_item:,.2f}  \n**En Letras:** *{monto_en_letras}*")

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

# --- FUNCIÓN PARA GENERAR EL PDF ---
def generar_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    estilo_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=9, leading=11)
    estilo_bold = ParagraphStyle('BoldCustom', parent=styles['Normal'], fontSize=9, leading=11, fontName="Helvetica-Bold")
    estilo_letras = ParagraphStyle('LetrasCustom', parent=styles['Normal'], fontSize=8, leading=10, fontName="Helvetica-Oblique")
    
    # Encabezado Empresa
    elements.append(Paragraph("<b>BRUSELAS GROUP EIRL</b>", ParagraphStyle('Empresa', fontSize=18, leading=20, textColor=colors.HexColor("#003366"), fontName="Helvetica-Bold")))
    elements.append(Paragraph("CAL. FRANCISCO VIDAL DE LAOS NRO. 686 URB. LA VIÑA LIMA - LIMA - SAN LUIS", estilo_normal))
    elements.append(Paragraph("RUC: 20611576456 | ventasschag@gmail.com | (051) 6514075 / +51 917 386 419", estilo_normal))
    elements.append(Spacer(1, 10))
    
    subtotal = importe_total_item / 1.18
    igv = importe_total_item - subtotal
    
    # Datos de cliente y cabecera
    info_data = [
        [Paragraph(f"<b>CODIGO:</b> {codigo_ref}", estilo_normal), Paragraph(f"<b>FECHA:</b> {fecha.strftime('%d/%m/%Y')}", estilo_normal)],
        [Paragraph(f"<b>CLIENTE:</b> {cliente}", estilo_normal), Paragraph(f"<b>PROF. N°:</b> {nro_cotizacion}", estilo_normal)],
        [Paragraph(f"<b>DIRECCION:</b> {direccion}", estilo_normal), ""],
        [Paragraph(f"<b>RUC:</b> {ruc}", estilo_normal), ""]
    ]
    
    t_info = Table(info_data, colWidths=[380, 150])
    t_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (1,0), (1,1), 1, colors.HexColor("#003366")),
        ('BACKGROUND', (1,0), (1,1), colors.HexColor("#003366")),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 15))
    
    # Tabla de Productos
    prod_data = [
        ["CANT.", "CODIGO", "DESCRIPCION", "MARCA", "PLAZO ENTREGA", "P.U.", "IMPORTE"],
        [str(cant), codigo_prod, descripcion, marca, plazo_entrega, f"S/ {precio_unitario:,.2f}", f"S/ {importe_total_item:,.2f}"]
    ]
    
    t_prod = Table(prod_data, colWidths=[40, 60, 210, 50, 60, 50, 60])
    t_prod.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_prod)
    
    # Fila de Total en Letras justo debajo de la tabla (igual al formato original)
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
    
    # Totales (Importe, IGV, Total)
    totales_data = [
        ["IMPORTE", f"S/ {subtotal:,.2f}"],
        ["IGV", f"S/ {igv:,.2f}"],
        ["TOTAL", f"S/ {importe_total_item:,.2f}"]
    ]
    
    t_totales = Table(totales_data, colWidths=[100, 100])
    t_totales.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#003366")),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0,0), (0,-1), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    
    wrapper_totales = Table([["", t_totales]], colWidths=[330, 200])
    elements.append(wrapper_totales)
    elements.append(Spacer(1, 15))
    
    # Condiciones comerciales
    cond_data = [
        [Paragraph("<b>TIEMPO ENTREGA</b>", estilo_normal), f": {tiempo_entrega}"],
        [Paragraph("<b>RAZÓN SOCIAL</b>", estilo_normal), ": BRUSELAS GROUP EIRL"],
        [Paragraph("<b>FORMA DE PAGO</b>", estilo_normal), f": {forma_pago}"],
        [Paragraph("<b>MONEDA</b>", estilo_normal), f": {moneda}"],
        [Paragraph("<b>VALIDEZ DE OFERTA</b>", estilo_normal), f": {validez}"],
        [Paragraph("<b>GARANTÍA</b>", estilo_normal), f": {garantia}"],
        [Paragraph("<b>EJECUTIVO DE VENTAS</b>", estilo_normal), f": {ejecutivo}"]
    ]
    
    t_cond = Table(cond_data, colWidths=[130, 300])
    t_cond.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(t_cond)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- BOTÓN PARA DESCARGAR EL PDF ---
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