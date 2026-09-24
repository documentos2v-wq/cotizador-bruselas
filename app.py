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

# --- FUNCIÓN PARA GENERAR EL PDF CON BLOQUE INFERIOR FIJO ---
def generar_pdf():
    buffer = io.BytesIO()
    # Márgenes estándar, el bloque inferior se dibuja de forma absoluta en el canvas
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
    elements.append(Paragraph("<b>BRUSELAS GROUP EIRL</b>", ParagraphStyle('Empresa', fontSize=18, leading=20, textColor=colors.HexColor("#003366"), fontName="Helvetica-Bold")))
    elements.append(Paragraph("CAL. FRANCISCO VIDAL DE LAOS NRO. 686 URB. LA VIÑA LIMA - LIMA - SAN LUIS", estilo_normal))
    elements.append(Paragraph("RUC: 20611576456 | ventasschag@gmail.com | (051) 6514075 / +51 917 386 419", estilo_normal))
    elements.append(Spacer(1, 10))
    
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
    
    # --- FUNCIÓN PARA DIBUJAR EL BLOQUE INFERIOR FIJO Y EL PIE DE PÁGINA ---
    subtotal = importe_total_general / 1.18
    igv = importe_total_general - subtotal

    def dibujar_elementos_fijos(canvas, doc):
        canvas.saveState()
        
        # 1. Franja Azul del Pie de Página (Abajo del todo)
        canvas.setFillColor(colors.HexColor("#003366"))
        canvas.rect(0, 0, 612, 35, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8)
        texto_pie = "CAL. FRANCISCO VIDAL DE LAOS NRO. 686 URB. LA VIÑA LIMA - LIMA - SAN LUIS - 917386419 - www.ventasschag.com"
        canvas.drawCentredString(612 / 2.0, 13, texto_pie)
        
        # 2. Construcción de la Tabla Inferior (Condiciones, Totales y Letras) en posición fija
        # Estilos internos para el bloque inferior
        estilo_c_label = ParagraphStyle('CL', fontName='Helvetica-Bold', fontSize=7, leading=9)
        estilo_c_val = ParagraphStyle('CV', fontName='Helvetica', fontSize=7, leading=9)
        estilo_letras = ParagraphStyle('LC', fontName='Helvetica-Oblique', fontSize=7, leading=9)
        estilo_tot_lbl = ParagraphStyle('TL', fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=colors.white, alignment=0)
        estilo_tot_val = ParagraphStyle('TV', fontName='Helvetica-Bold', fontSize=7, leading=9, alignment=2)
        
        # Datos de Condiciones Comerciales (Izquierda)
        cond_rows = [
            [Paragraph("TIEMPO ENTREGA", estilo_c_label), Paragraph(f": {tiempo_entrega}", estilo_c_val)],
            [Paragraph("RAZÓN SOCIAL", estilo_c_label), Paragraph(": BRUSELAS GROUP EIRL", estilo_c_val)],
            [Paragraph("FORMA DE PAGO", estilo_c_label), Paragraph(f": {forma_pago}", estilo_c_val)],
            [Paragraph("MONEDA", estilo_c_label), Paragraph(f": {moneda}", estilo_c_val)],
            [Paragraph("VALIDEZ DE OFERTA", estilo_c_label), Paragraph(f": {validez}", estilo_c_val)],
            [Paragraph("GARANTÍA", estilo_c_label), Paragraph(f": {garantia}", estilo_c_val)],
            [Paragraph("EJECUTIVO DE VENTAS", estilo_c_label), Paragraph(f": {ejecutivo}", estilo_c_val)]
        ]
        t_cond_pdf = Table(cond_rows, colWidths=[105, 220])
        t_cond_pdf.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ]))
        
        # Datos de Totales (Derecha)
        tot_rows = [
            [Paragraph("IMPORTE", estilo_tot_lbl), Paragraph(f"S/ {subtotal:,.2f}", estilo_tot_val)],
            [Paragraph("IGV", estilo_tot_lbl), Paragraph(f"S/ {igv:,.2f}", estilo_tot_val)],
            [Paragraph("TOTAL", estilo_tot_lbl), Paragraph(f"S/ {importe_total_general:,.2f}", estilo_tot_val)]
        ]
        t_tot_pdf = Table(tot_rows, colWidths=[90, 115])
        t_tot_pdf.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#003366")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#003366")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        
        # Fila de Total en Letras
        t_let_pdf = Table([[Paragraph(f"<b>SON:</b> &nbsp; {monto_en_letras}", estilo_letras)]], colWidths=[532])
        t_let_pdf.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9F9F9")),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        
        # Contenedor Maestro inferior que une Condiciones (izq) y Totales (der)
        master_top_row = Table([[t_cond_pdf, t_tot_pdf]], colWidths=[325, 207])
        master_top_row.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('RIGHTPADDING', (0,0), (0,0), 10),
        ]))
        
        master_block = Table([[master_top_row], [Spacer(1, 4)], [t_let_pdf]], colWidths=[532])
        master_block.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        
        # Envoltorio con caja roja sutil (igual al recuadro de referencia) para alinear perfectamente
        box_container = Table([[master_block]], colWidths=[552])
        box_container.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#999999")),
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        
        # Posición fija exacta desde la esquina inferior izquierda de la página (X=30, Y=45)
        box_container.wrapOn(canvas, 552, 200)
        box_container.drawOn(canvas, 30, 45)
        
        canvas.restoreState()

    doc.build(elements, onFirstPage=dibujar_elementos_fijos, onLaterPages=dibujar_elementos_fijos)
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
