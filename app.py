# ===================================================================
# VISU - AGRICULTURAL INTELLIGENCE PLATFORM
# Análisis de Rotación de Cultivos y Riesgo Hídrico
# Powered by Streamlit + Google Earth Engine
# ===================================================================

import streamlit as st
import pandas as pd
import numpy as np
import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
import requests
import tempfile
import os
from io import BytesIO
import base64

# Configuración de la página
st.set_page_config(
    page_title="VISU - Agricultural Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para el logo VISU
st.markdown("""
<style>
.visu-logo {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px 0;
    background: linear-gradient(135deg, #0E1117 0%, #262730 100%);
    border-radius: 10px;
    margin-bottom: 30px;
    box-shadow: 0 4px 15px rgba(0, 210, 190, 0.3);
}

.visu-text {
    font-size: 48px;
    font-weight: bold;
    color: #00D2BE;
    text-shadow: 0 0 20px rgba(0, 210, 190, 0.5);
    letter-spacing: 8px;
    margin-right: 20px;
}

.visu-tagline {
    font-size: 14px;
    color: #FAFAFA;
    font-weight: 300;
    letter-spacing: 2px;
    text-transform: uppercase;
    opacity: 0.8;
}

.status-card {
    background: rgba(0, 210, 190, 0.1);
    border: 1px solid #00D2BE;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
}

.feature-card {
    background: rgba(38, 39, 48, 0.8);
    border-radius: 8px;
    padding: 20px;
    margin: 10px 0;
    border-left: 4px solid #00D2BE;
}

.metric-container {
    background: rgba(0, 210, 190, 0.05);
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    border: 1px solid rgba(0, 210, 190, 0.3);
}
</style>
""", unsafe_allow_html=True)

# Funciones auxiliares
@st.cache_data
def load_sample_data():
    """Cargar datos de ejemplo para demostración"""
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='MS')
    crops = ['Soja', 'Maíz', 'Trigo', 'Girasol', 'Sorgo']
    
    data = []
    for date in dates:
        for crop in crops:
            data.append({
                'fecha': date,
                'cultivo': crop,
                'hectareas': np.random.randint(100, 1000),
                'rendimiento': np.random.uniform(2000, 8000),
                'riesgo_hidrico': np.random.uniform(0, 100)
            })
    
    return pd.DataFrame(data)

def validate_cuit(cuit):
    """Validar formato de CUIT"""
    if not cuit or len(cuit) != 13:
        return False
    
    # Verificar formato XX-XXXXXXXX-X
    if cuit[2] != '-' or cuit[11] != '-':
        return False
    
    # Verificar que sean números
    numbers = cuit.replace('-', '')
    if not numbers.isdigit():
        return False
    
    return True

def parse_kmz_file(uploaded_file):
    """Parsear archivo KMZ y extraer coordenadas"""
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as kmz:
            # Buscar archivo KML dentro del KMZ
            kml_file = None
            for filename in kmz.namelist():
                if filename.endswith('.kml'):
                    kml_file = filename
                    break
            
            if not kml_file:
                return None, "No se encontró archivo KML en el KMZ"
            
            # Leer y parsear el KML
            kml_content = kmz.read(kml_file)
            root = ET.fromstring(kml_content)
            
            # Extraer coordenadas
            coordinates = []
            for placemark in root.iter():
                if placemark.tag.endswith('coordinates'):
                    coord_text = placemark.text.strip()
                    coords = coord_text.split(' ')
                    for coord in coords:
                        if coord.strip():
                            parts = coord.split(',')
                            if len(parts) >= 2:
                                lon, lat = float(parts[0]), float(parts[1])
                                coordinates.append([lat, lon])
            
            if not coordinates:
                return None, "No se encontraron coordenadas en el archivo KMZ"
            
            return coordinates, "Archivo KMZ procesado exitosamente"
    
    except Exception as e:
        return None, f"Error al procesar archivo KMZ: {str(e)}"

def simulate_earth_engine_data(coordinates):
    """Simular datos de Google Earth Engine"""
    if not coordinates:
        return None
    
    # Simular datos de cultivos por año
    years = [2020, 2021, 2022, 2023, 2024]
    crops = ['Soja', 'Maíz', 'Trigo', 'Girasol', 'Sorgo']
    
    data = []
    for year in years:
        for crop in crops:
            data.append({
                'año': year,
                'cultivo': crop,
                'hectareas': np.random.randint(50, 500),
                'ndvi_promedio': np.random.uniform(0.3, 0.8),
                'precipitacion': np.random.uniform(400, 1200),
                'riesgo_inundacion': np.random.uniform(0, 100)
            })
    
    return pd.DataFrame(data)

def create_rotation_chart(df):
    """Crear gráfico de rotación de cultivos"""
    fig = px.bar(
        df.groupby(['año', 'cultivo']).agg({'hectareas': 'sum'}).reset_index(),
        x='año',
        y='hectareas',
        color='cultivo',
        title='Rotación de Cultivos por Año',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )
    
    return fig

def create_risk_map(coordinates):
    """Crear mapa de riesgo hídrico"""
    if not coordinates:
        return None
    
    # Calcular centro del polígono
    center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
    center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
    
    # Crear mapa base
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    
    # Agregar polígono del campo
    folium.Polygon(
        locations=coordinates,
        color='#00D2BE',
        weight=3,
        fill=True,
        fillColor='#00D2BE',
        fillOpacity=0.3,
        popup="Campo Analizado"
    ).add_to(m)
    
    # Agregar marcadores de riesgo simulados
    for i in range(5):
        risk_lat = center_lat + np.random.uniform(-0.01, 0.01)
        risk_lon = center_lon + np.random.uniform(-0.01, 0.01)
        risk_level = np.random.randint(1, 4)
        
        color = 'green' if risk_level == 1 else 'orange' if risk_level == 2 else 'red'
        
        folium.CircleMarker(
            location=[risk_lat, risk_lon],
            radius=8,
            color=color,
            fill=True,
            popup=f"Riesgo Hídrico: {'Bajo' if risk_level == 1 else 'Medio' if risk_level == 2 else 'Alto'}",
            tooltip=f"Nivel {risk_level}"
        ).add_to(m)
    
    return m

def main():
    # Header con logo VISU
    st.markdown("""
    <div class="visu-logo">
        <div class="visu-text">VISU</div>
        <div class="visu-tagline">Agricultural Intelligence</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar para navegación
    st.sidebar.title("🌾 Navegación")
    page = st.sidebar.selectbox(
        "Seleccionar análisis:",
        ["🏠 Inicio", "🏢 Análisis por CUIT", "📁 Análisis por KMZ", "🌊 Riesgo Hídrico", "📊 Reportes"]
    )
    
    if page == "🏠 Inicio":
        show_home_page()
    elif page == "🏢 Análisis por CUIT":
        show_cuit_analysis()
    elif page == "📁 Análisis por KMZ":
        show_kmz_analysis()
    elif page == "🌊 Riesgo Hídrico":
        show_risk_analysis()
    elif page == "📊 Reportes":
        show_reports()

def show_home_page():
    """Mostrar página de inicio"""
    st.title("🌾 Plataforma de Inteligencia Agrícola")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-container">
            <h3>🏢 Análisis por CUIT</h3>
            <p>Consulta automática de campos por CUIT del productor</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-container">
            <h3>📁 Análisis por KMZ</h3>
            <p>Carga de archivos KMZ para análisis detallado</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-container">
            <h3>🌊 Riesgo Hídrico</h3>
            <p>Análisis de zonas de inundación 1984-2025</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-container">
            <h3>📊 Reportes PDF</h3>
            <p>Generación de informes profesionales</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Estado del sistema
    st.markdown("""
    <div class="status-card">
        <h3>🚀 Estado del Sistema</h3>
        <p>✅ Google Earth Engine: Conectado</p>
        <p>✅ Base de datos CUIT: Disponible</p>
        <p>✅ Análisis KMZ: Operativo</p>
        <p>✅ Mapas interactivos: Funcionando</p>
    </div>
    """, unsafe_allow_html=True)

def show_cuit_analysis():
    """Mostrar análisis por CUIT"""
    st.title("🏢 Análisis por CUIT")
    st.markdown("Ingresa el CUIT del productor para obtener información de sus campos")
    
    # Input de CUIT
    cuit = st.text_input("CUIT del Productor", placeholder="XX-XXXXXXXX-X")
    
    if st.button("🔍 Buscar Campos"):
        if not validate_cuit(cuit):
            st.error("❌ Formato de CUIT inválido. Usar formato: XX-XXXXXXXX-X")
            return
        
        with st.spinner("Consultando base de datos..."):
            # Simular búsqueda
            st.success(f"✅ CUIT {cuit} encontrado en la base de datos")
            
            # Mostrar información simulada
            st.subheader("📍 Campos Encontrados")
            
            campos_data = {
                'campo': ['Campo Norte', 'Campo Sur', 'Campo Este'],
                'superficie': [245, 189, 312],
                'ubicacion': ['Pergamino, Buenos Aires', 'Venado Tuerto, Santa Fe', 'Marcos Juárez, Córdoba'],
                'ultimo_cultivo': ['Soja', 'Maíz', 'Trigo']
            }
            
            df_campos = pd.DataFrame(campos_data)
            st.dataframe(df_campos, use_container_width=True)
            
            # Selector de campo
            campo_seleccionado = st.selectbox("Seleccionar campo para análisis:", df_campos['campo'].tolist())
            
            if st.button("🚀 Analizar Campo Seleccionado"):
                with st.spinner("Procesando análisis con Google Earth Engine..."):
                    # Simular análisis
                    show_field_analysis(campo_seleccionado)

def show_kmz_analysis():
    """Mostrar análisis por KMZ"""
    st.title("📁 Análisis por Archivo KMZ")
    st.markdown("Carga un archivo KMZ de Google Earth para analizar el campo")
    
    # Upload de archivo
    uploaded_file = st.file_uploader("Seleccionar archivo KMZ", type=['kmz'])
    
    if uploaded_file is not None:
        st.success(f"✅ Archivo '{uploaded_file.name}' cargado exitosamente")
        
        if st.button("🔍 Procesar Archivo KMZ"):
            with st.spinner("Procesando archivo KMZ..."):
                coordinates, message = parse_kmz_file(uploaded_file)
                
                if coordinates:
                    st.success(message)
                    st.info(f"📍 Se encontraron {len(coordinates)} puntos de coordenadas")
                    
                    # Mostrar mapa
                    st.subheader("🗺️ Ubicación del Campo")
                    risk_map = create_risk_map(coordinates)
                    if risk_map:
                        st_folium(risk_map, width=700, height=500)
                    
                    # Análisis con Earth Engine simulado
                    if st.button("�� Analizar con Google Earth Engine"):
                        with st.spinner("Procesando análisis satelital..."):
                            ee_data = simulate_earth_engine_data(coordinates)
                            show_earth_engine_analysis(ee_data)
                else:
                    st.error(f"❌ {message}")

def show_risk_analysis():
    """Mostrar análisis de riesgo hídrico"""
    st.title("🌊 Análisis de Riesgo Hídrico")
    st.markdown("Análisis histórico de zonas de inundación (1984-2025)")
    
    # Parámetros de análisis
    col1, col2 = st.columns(2)
    
    with col1:
        year_range = st.slider("Rango de años", 1984, 2025, (2020, 2024))
        
    with col2:
        risk_threshold = st.slider("Umbral de riesgo (%)", 0, 100, 50)
    
    # Datos simulados de riesgo
    years = list(range(year_range[0], year_range[1] + 1))
    risk_data = []
    
    for year in years:
        for month in range(1, 13):
            risk_data.append({
                'año': year,
                'mes': month,
                'riesgo_inundacion': np.random.uniform(0, 100),
                'precipitacion': np.random.uniform(0, 200)
            })
    
    df_risk = pd.DataFrame(risk_data)
    
    # Gráfico de riesgo histórico
    st.subheader("📈 Riesgo Histórico de Inundaciones")
    
    fig_risk = px.line(
        df_risk.groupby('año').agg({'riesgo_inundacion': 'mean'}).reset_index(),
        x='año',
        y='riesgo_inundacion',
        title='Riesgo Promedio de Inundación por Año'
    )
    
    fig_risk.add_hline(y=risk_threshold, line_dash="dash", line_color="red", 
                       annotation_text=f"Umbral de Riesgo: {risk_threshold}%")
    
    fig_risk.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )
    
    st.plotly_chart(fig_risk, use_container_width=True)
    
    # Estadísticas
    high_risk_years = df_risk[df_risk['riesgo_inundacion'] > risk_threshold]['año'].nunique()
    st.metric("Años con riesgo alto", high_risk_years)

def show_reports():
    """Mostrar sección de reportes"""
    st.title("📊 Generación de Reportes")
    st.markdown("Genera reportes profesionales en formato PDF")
    
    # Opciones de reporte
    report_type = st.selectbox(
        "Tipo de reporte:",
        ["📋 Reporte Completo", "🌾 Análisis de Cultivos", "🌊 Evaluación de Riesgo", "📈 Comparativo Histórico"]
    )
    
    # Parámetros del reporte
    col1, col2 = st.columns(2)
    
    with col1:
        include_maps = st.checkbox("Incluir mapas", value=True)
        include_charts = st.checkbox("Incluir gráficos", value=True)
    
    with col2:
        include_recommendations = st.checkbox("Incluir recomendaciones", value=True)
        include_raw_data = st.checkbox("Incluir datos en crudo", value=False)
    
    if st.button("📄 Generar Reporte PDF"):
        with st.spinner("Generando reporte..."):
            # Simular generación de PDF
            st.success("✅ Reporte generado exitosamente")
            
            # Botón de descarga simulado
            st.download_button(
                label="💾 Descargar Reporte PDF",
                data=b"PDF content would be here",
                file_name=f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )

def show_field_analysis(campo_name):
    """Mostrar análisis detallado de un campo"""
    st.subheader(f"📊 Análisis del {campo_name}")
    
    # Datos simulados
    sample_data = load_sample_data()
    
    # Gráfico de rotación
    rotation_chart = create_rotation_chart(sample_data)
    st.plotly_chart(rotation_chart, use_container_width=True)
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Superficie Total", "245 ha")
    
    with col2:
        st.metric("Rendimiento Promedio", "6,250 kg/ha")
    
    with col3:
        st.metric("Riesgo Hídrico", "15%", delta="-5%")

def show_earth_engine_analysis(data):
    """Mostrar análisis de Google Earth Engine"""
    st.subheader("🛰️ Análisis Satelital")
    
    if data is not None:
        # Gráfico de rotación
        rotation_chart = create_rotation_chart(data)
        st.plotly_chart(rotation_chart, use_container_width=True)
        
        # Tabla de datos
        st.subheader("📋 Datos Detallados")
        st.dataframe(data, use_container_width=True)
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Hectáreas Totales", f"{data['hectareas'].sum():,}")
        
        with col2:
            st.metric("NDVI Promedio", f"{data['ndvi_promedio'].mean():.2f}")
        
        with col3:
            st.metric("Precipitación Media", f"{data['precipitacion'].mean():.0f} mm")
        
        with col4:
            st.metric("Riesgo Promedio", f"{data['riesgo_inundacion'].mean():.1f}%")

# Ejecutar aplicación
if __name__ == "__main__":
    main()
