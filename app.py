from datetime import datetime
import io
import os
import pandas as pd
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

def incrementar_y_guardar_correlativo():
    actual = obtener_correlativo_actual()
    nuevo = actual + 1
    try:
        with open(ARCHIVO_CONTADOR, "w") as f:
            f.write(str(nuevo))
    except:
        pass
    return nuevo

if 'nro_secuencial' not in st.session_state:
    st.session_state.nro_secuencial = obtener_correlativo_actual()

# Inicializar Session States de Clientes si no existen
if 'ruc_input' not in st.session_state:
    st.session_state.ruc_input = "20607260525"
if 'cliente_input' not in st.session_state:
    st.session_state.cliente_input = "ALIADOS ESTRATEGICOS DEL NORTE E.I.R.L."
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

# --- SECCIÓN 1: DATOS GENERALES Y ACCESO RUC SUNAT ---
st.subheader("1. Información del Cliente y Cotización")

st.markdown("##### 🔍 Asistente de Consulta RUC (SUNAT)")
col_s1, col_s2 = st.columns([2, 3])
with col_s1:
    st.markdown(
        """
        <a href="https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias" target="_blank" 
           style="display: inline-block; background-color: #003366; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: bold; text-align: center;">
           🌐 Abrir Portal Oficial SUNAT
        </a>
        """,
        unsafe_allow_html=True
    )
with col_s2:
    st.info("💡 Consejo: Consulta el RUC en SUNAT, copia los datos y pégalos abajo para llenar el formulario automáticamente.")

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    nro_cotizacion_actual = f"000-{st.session_state.nro_secuencial}"
    st.text_input("N° de Cotización (Correlativo Automático)", value=nro_cotizacion_actual, disabled=True)
    
    ruc = st.text_input("RUC del Cliente", value=st.session_state.ruc_input, key="ruc_input")

with col2:
    fecha = st.date_input("Fecha", datetime.today())
    direccion = st.text_input("Dirección (Fiscal / SUNAT)", value=st.session_state.direccion_input, key="direccion_input")

with col3:
    cliente = st.text_input("Cliente (Razón Social)", value=st.session_state.cliente_input, key="cliente_input")
    codigo_ref = st.text_input("Código Interno / Ref", "002022-0007-0045")

st.markdown("---")

# --- SECCIÓN 2: DETALLE DE PRODUCTOS (ADAPTADO VERTICALMENTE) ---
st.subheader("2. Detalle de Productos y Precios")

if 'productos_lista' not in st.session_state:
    st.session_state.productos_lista = [
        {
            "Cantidad": 20,
            "Código": "COCH4",
            "Descripción": "REPRODUCTOR / EQUIPO TECNOLÓGICO ESPECIALIZADO",
            "Marca": "NACIONAL",
            "Plazo Entrega": "10",
            "P.U. (Inc. IGV)": 399.90
        }
    ]

st.markdown("Añade o edita los productos de forma vertical (ideal para celular y PC):")

nuevos_productos = []
for idx, prod in enumerate(st.session_state.productos_lista):
    st.markdown(f"**📦 Ítem N° {idx + 1}**")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        canti = st.number_input(f"Cantidad {idx+1}", min_value=1, step=1, value=int(prod["Cantidad"]), key=f"cant_{idx}")
        codi = st.text_input(f"Código {idx+1}", value=str(prod["Código"]), key=f"cod_{idx}")
        marca_v = st.text_input(f"Marca {idx+1}", value=str(prod["Marca"]), key=f"mar_{idx}")
    with col_v2:
        plazo_v = st.text_input(f"Plazo Entrega {idx+1}", value=str(prod["Plazo Entrega"]), key=f"pla_{idx}")
        pu_v = st.number_input(f"P.U. (Inc. IGV) {idx+1}", min_value=0.0, format="%.2f", value=float(prod["P.U. (Inc. IGV)"]), key=f"pu_{idx}")
    
    desc_v = st.text_area(f"Descripción {idx+1}", value=str(prod["Descripción"]), key=f"desc_{idx}")
    
    nuevos_productos.append({
        "Cantidad": canti,
        "Código": codi,
        "Descripción": desc_v,
        "Marca": marca_v,
        "Plazo Entrega": plazo_v,
        "P.U. (Inc. IGV)": pu_v
    })
    st.markdown("---")

st.session_state.productos_lista = nuevos_productos
df_limpio = pd.DataFrame(st.session_state.productos_lista)

col_add, col_rem = st.columns(2)
with col_add:
    if st.button("➕ Agregar otro producto"):
        st.session_state.productos_lista.append({
            "Cantidad": 1,
            "Código": "",
            "Descripción": "",
            "Marca": "NACIONAL",
            "Plazo Entrega": "10",
            "P.U. (Inc. IGV)": 0.0
        })
        st.rerun()
with col_rem:
    if len(st.session_state.productos_lista) > 1:
        if st.button("🗑️ Quitar último producto"):
            st.session_state.productos_lista.pop()
            st.rerun()

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

# --- FUNCIÓN PARA GENERAR EL PDF ---
def generar_pdf(nro_cotiz_str):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=85, bottomMargin=40)
    elements = []
    
    styles = getSampleStyleSheet()
    estilo_normal = ParagraphStyle('NormalCustom', parent=styles['Normal'], fontSize=9, leading=11)
    
    # Estilo perfectamente centrado verticalmente para la cabecera azul de Fecha y Cotización
    estilo_blanco_centrado = ParagraphStyle(
        'BlancoCentrado', 
        parent=styles['Normal'], 
        fontSize=9, 
        leading=14, 
        fontName="Helvetica-Bold", 
        textColor=colors.white,
        alignment=0
    )
    
    estilo_th = ParagraphStyle('TH', parent=styles['Normal'], fontSize=8, leading=10, fontName="Helvetica-Bold", textColor=colors.white, alignment=1)
    estilo_td_left = ParagraphStyle('TDL', parent=styles['Normal'], fontSize=8, leading=10, alignment=0)
    estilo_td_center = ParagraphStyle('TDC', parent=styles['Normal'], fontSize=8, leading=10, alignment=1)
    estilo_td_right = ParagraphStyle('TDR', parent=styles['Normal'], fontSize=8, leading=10, alignment=2)
    
    # Encabezado Empresa dentro del cuerpo
    elements.append(Paragraph("<b>BRUSELAS GROUP EIRL</b>", ParagraphStyle('EmpresaGigante', fontSize=32, leading=36, textColor=colors.HexColor("#003366"), fontName="Helvetica-Bold")))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("CAL. FRANCISCO VIDAL DE LAOS NRO. 686 URB. LA VIÑA LIMA - LIMA - SAN LUIS", estilo_normal))
    elements.append(Paragraph("RUC: 20611576456 | ventasschag@gmail.com | (051) 6514075 / +51 917 386 419", estilo_normal))
    elements.append(Spacer(1, 10))
    
    info_data = [
        [Paragraph(f"<b>CODIGO:</b> {codigo_ref}", estilo_normal), Paragraph(f"<b>FECHA:</b> {fecha.strftime('%d/%m/%Y')}", estilo_blanco_centrado)],
        [Paragraph(f"<b>CLIENTE:</b> {cliente}", estilo_normal), Paragraph(f"<b>PROF. N°:</b> {nro_cotiz_str}", estilo_blanco_centrado)],
        [Paragraph(f"<b>DIRECCION:</b> {direccion}", estilo_normal), ""],
        [Paragraph(f"<b>RUC:</b> {ruc}", estilo_normal), ""]
    ]
    
    t_info = Table(info_data, colWidths=[382, 170])
    t_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),  # Alineación vertical centrada
        ('BACKGROUND', (1,0), (1,1), colors.HexColor("#003366")),
        ('TOPPADDING', (1,0), (1,1), 5),
        ('BOTTOMPADDING', (1,0), (1,1), 5),
        ('LEFTPADDING', (1,0), (1,1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
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
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
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

    # Procesar sello transparente
    sello_path_proc = None
    if os.path.exists("sello.png"):
        try:
            sello_pil = PILImage.open("sello.png").convert("RGBA")
            datas = sello_pil.getdata()
            new_data = []
            for item in datas:
                if item[0] > 220 and item[1] > 220 and item[2] > 220:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            sello_pil.putdata(new_data)
            sello_path_proc = "temp_sello_transparente.png"
            sello_pil.save(sello_path_proc)
        except:
            pass

    def dibujar_fondo_y_decoraciones(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#F2F6F9"))
        canvas.rect(0, 0, 612, 792, fill=1, stroke=0)
        
        # Encabezado superior
        canvas.setFillColor(colors.HexColor("#003366"))
        canvas.rect(0, 721, 612, 71, fill=1, stroke=0)
        
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(30, 765, "BRUSELAS GROUP EIRL")
        
        canvas.setFont("Helvetica", 8)
        canvas.drawString(30, 745, "PROPUESTA ECONÓMICA Y COMERCIAL")
        
        redes_texto = "■ f: /BruselasGroup   |   ■ WA: +51 917 386 419   |   ■ IG: @BruselasGroup   |   ■ TK: @BruselasEIRL"
        canvas.drawRightString(612 - 30, 755, redes_texto)
        
        # Pie de página
        canvas.setFillColor(colors.HexColor("#003366"))
        canvas.rect(0, 0, 612, 35, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8)
        texto_pie = "CAL. FRANCISCO VIDAL DE LAOS NRO. 686 URB. LA VIÑA LIMA - LIMA - SAN LUIS - 917386419 - www.ventasschag.com"
        canvas.drawCentredString(612 / 2.0, 13, texto_pie)
        
        if watermark_path and os.path.exists(watermark_path):
            try:
                canvas.drawImage(watermark_path, 106, 230, width=400, height=400, mask='auto', preserveAspectRatio=True)
            except:
                pass
                
        canvas.restoreState()

    subtotal = importe_total_general / 1.18
    igv = importe_total_general - subtotal

    def dibujar_elementos_fijos(canvas, doc):
        canvas.saveState()
        
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
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#003366")),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ]))
        
        t_let_pdf = Table([[Paragraph(f"<b>SON:</b> &nbsp; {monto_en_letras}", estilo_letras)]], colWidths=[552])
        t_let_pdf.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#666666")),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9F9F9")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ]))
        
        # --- UBICACIÓN ÓPTIMA Y LIMPIA DEL BLOQUE INFERIOR ---
        master_top_row = Table([[t_cond_pdf, t_tot_pdf]], colWidths=[330, 222])
        master_top_row.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        
        master_block = Table([[master_top_row], [Spacer(1, 8)], [t_let_pdf]], colWidths=[552])
        master_block.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        
        master_block.wrapOn(canvas, 552, 220)
        master_block.drawOn(canvas, 30, 46)
        
        # --- SELLO, LÍNEA Y DATOS DE LA EMPRESA BIEN DISTRIBUIDOS ---
        if sello_path_proc and os.path.exists(sello_path_proc):
            try:
                # Sello ubicado a la altura perfecta (Y = 95)
                canvas.drawImage(sello_path_proc, 365, 95, width=170, height=80, mask='auto', preserveAspectRatio=True)
            except:
                pass
                
        # Línea decorativa elegante debajo del sello
        canvas.setStrokeColor(colors.HexColor("#003366"))
        canvas.setLineWidth(1)
        canvas.line(360, 92, 552, 92)
        
        # Datos oficiales de la empresa debajo de la línea
        canvas.setFillColor(colors.HexColor("#003366"))
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawCentredString(456, 80, "BRUSELAS GROUP EIRL")
        
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#333333"))
        canvas.drawCentredString(456, 70, "RUC: 20611576456")
        canvas.drawCentredString(456, 60, "SAN LUIS - LIMA - LIMA")
        
        canvas.restoreState()

    def on_page(canvas, doc):
        dibujar_fondo_y_decoraciones(canvas, doc)
        dibujar_elementos_fijos(canvas, doc)

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    
    if watermark_path and os.path.exists(watermark_path):
        try:
            os.remove(watermark_path)
        except:
            pass
            
    if sello_path_proc and os.path.exists(sello_path_proc):
        try:
            os.remove(sello_path_proc)
        except:
            pass

    buffer.seek(0)
    return buffer

st.markdown("---")

nro_cotizacion_actual = f"000-{st.session_state.nro_secuencial}"

col_b1, col_b2 = st.columns(2)

with col_b1:
    pdf_file = generar_pdf(nro_cotizacion_actual)
    nombre_archivo_pdf = f"Cotizacion_{st.session_state.nro_secuencial}.pdf"
    
    clicked = st.download_button(
        label="📥 Descargar Cotización en PDF",
        data=pdf_file,
        file_name=nombre_archivo_pdf,
        mime="application/pdf",
        type="primary"
    )
    
    if clicked:
        nuevo_val = incrementar_y_guardar_correlativo()
        st.session_state.nro_secuencial = nuevo_val
        st.rerun()

with col_b2:
    if st.button("🔄 Forzar Siguiente N° de Cotización"):
        st.session_state.nro_secuencial = incrementar_y_guardar_correlativo()
        st.success("¡Correlativo avanzado correctamente!")
        st.rerun()
