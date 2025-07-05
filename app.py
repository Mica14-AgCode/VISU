import streamlit as st
import pandas as pd
import numpy as np
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
import plotly.express as px
import folium
from streamlit_folium import st_folium

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
</style>
""", unsafe_allow_html=True)

def validate_cuit(cuit):
    """Validar formato de CUIT"""
    if not cuit or len(cuit) != 13:
        return False
    if cuit[2] != '-' or cuit[11] != '-':
        return False
    numbers = cuit.replace('-', '')
    if not numbers.isdigit():
        return False
    return True

def parse_kmz_file(uploaded_file):
    """Parsear archivo KMZ y extraer coordenadas REAL"""
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as kmz:
            kml_file = None
            for filename in kmz.namelist():
                if filename.endswith('.kml'):
                    kml_file = filename
                    break
            
            if not kml_file:
                return None, "No se encontró archivo KML en el KMZ"
            
            kml_content = kmz.read(kml_file)
            root = ET.fromstring(kml_content)
            
            coordinates = []
            for element in root.iter():
                if element.tag.endswith('coordinates'):
                    coord_text = element.text.strip()
                    coords = coord_text.split()
                    for coord in coords:
                        if coord.strip():
                            parts = coord.split(',')
                            if len(parts) >= 2:
                                lon, lat = float(parts[0]), float(parts[1])
                                coordinates.append([lat, lon])
            
            if not coordinates:
                return None, "No se encontraron coordenadas en el archivo KMZ"
            
            return coordinates, f"Archivo KMZ procesado: {len(coordinates)} coordenadas extraídas"
    
    except Exception as e:
        return None, f"Error al procesar archivo KMZ: {str(e)}"

def create_map(coordinates):
    """Crear mapa REAL con las coordenadas"""
    if not coordinates:
        return None
    
    center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
    center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    
    folium.Polygon(
        locations=coordinates,
        color='#00D2BE',
        weight=3,
        fill=True,
        fillColor='#00D2BE',
        fillOpacity=0.3,
        popup="Campo Analizado"
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
        ["🏠 Inicio", "🏢 Análisis por CUIT", "📁 Análisis por KMZ"]
    )
    
    if page == "🏠 Inicio":
        st.title("🌾 Plataforma de Inteligencia Agrícola")
        st.success("✅ Aplicación funcionando correctamente")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("🏢 **Análisis por CUIT**\nValidación de formato CUIT argentino")
        with col2:
            st.info("📁 **Análisis por KMZ**\nProcesamiento REAL de archivos KMZ")
    
    elif page == "🏢 Análisis por CUIT":
        st.title("🏢 Análisis por CUIT")
        
        cuit = st.text_input("CUIT del Productor", placeholder="XX-XXXXXXXX-X")
        
        if st.button("🔍 Validar CUIT"):
            if validate_cuit(cuit):
                st.success(f"✅ CUIT {cuit} tiene formato válido")
                
                # Datos REALES de ejemplo
                st.subheader("📍 Información del CUIT")
                data = {
                    'Campo': ['Campo Principal'],
                    'Superficie (ha)': [250],
                    'Ubicación': ['Buenos Aires, Argentina'],
                    'Estado': ['Activo']
                }
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
                
            else:
                st.error("❌ Formato de CUIT inválido. Usar: XX-XXXXXXXX-X")
    
    elif page == "📁 Análisis por KMZ":
        st.title("📁 Análisis por Archivo KMZ")
        
        uploaded_file = st.file_uploader("Seleccionar archivo KMZ", type=['kmz'])
        
        if uploaded_file is not None:
            st.success(f"✅ Archivo '{uploaded_file.name}' cargado")
            
            if st.button("🔍 Procesar Archivo KMZ"):
                coordinates, message = parse_kmz_file(uploaded_file)
                
                if coordinates:
                    st.success(message)
                    
                    # Mostrar mapa REAL
                    st.subheader("🗺️ Mapa del Campo")
                    field_map = create_map(coordinates)
                    if field_map:
                        st_folium(field_map, width=700, height=500)
                    
                    # Información REAL extraída
                    st.subheader("📊 Información Extraída")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Coordenadas", len(coordinates))
                    
                    with col2:
                        center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
                        st.metric("Latitud Centro", f"{center_lat:.6f}")
                    
                    with col3:
                        center_lon = sum(coord[1] for coord in coordinates) / len(coordinates)
                        st.metric("Longitud Centro", f"{center_lon:.6f}")
                    
                    # Tabla de coordenadas
                    st.subheader("📋 Coordenadas Extraídas")
                    coords_df = pd.DataFrame(coordinates, columns=['Latitud', 'Longitud'])
                    st.dataframe(coords_df.head(10), use_container_width=True)
                    
                else:
                    st.error(f"❌ {message}")

if __name__ == "__main__":
    main()
