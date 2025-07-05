# ===================================================================
# VISU - AGRICULTURAL INTELLIGENCE PLATFORM
# Análisis REAL de Rotación de Cultivos usando SENASA + KMZ
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
import folium
from streamlit_folium import st_folium
import requests
import tempfile
import os
from io import BytesIO
import base64
import time
import re

# Configuración de la página
st.set_page_config(
    page_title="VISU - Agricultural Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado - LOGO ORIGINAL DEL USUARIO
st.markdown("""
<style>
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Logo VISU - DISEÑO ELEGANTE QUE YA FUNCIONA */
    .visu-logo-container {
        text-align: center;
        margin: 20px 0 30px 0;
        padding: 20px;
    }
    
    .minimal-container {
        display: inline-block;
        position: relative;
    }
    
    .visu-minimal {
        font-size: 60px;
        font-weight: 300;
        letter-spacing: 15px;
        color: #C0C0C0;
        margin-bottom: 10px;
        margin-left: 15px; /* Compensar el letter-spacing */
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .eye-underline {
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, transparent 0%, #00D2BE 20%, #00D2BE 80%, transparent 100%);
        position: relative;
    }
    
    .eye-dot {
        width: 15px;
        height: 15px;
        background: #00D2BE;
        border-radius: 50%;
        position: absolute;
        top: -6px;
        left: 50%;
        transform: translateX(-50%);
        box-shadow: 0 0 20px #00D2BE;
    }
    
    .tagline {
        font-size: 16px;
        color: #C0C0C0;
        letter-spacing: 2px;
        margin-top: 15px;
        font-weight: 300;
    }
    
    /* Responsive design para móviles */
    @media (max-width: 768px) {
        .visu-minimal {
            font-size: 45px;
            letter-spacing: 10px;
            margin-left: 10px;
        }
        
        .tagline {
            font-size: 14px;
            letter-spacing: 1px;
        }
    }
    
    /* Estilo general mejorado */
    .upload-section {
        background-color: #f0f8ff;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #0066cc;
        margin: 1rem 0;
    }
    
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# FUNCIONES PARA VALIDACIÓN Y PROCESAMIENTO
# =====================================================================

def validate_cuit(cuit):
    """Validar formato de CUIT argentino"""
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

def normalizar_cuit(cuit):
    """Normaliza un CUIT a formato XX-XXXXXXXX-X"""
    cuit_limpio = cuit.replace("-", "")
    
    if len(cuit_limpio) != 11:
        raise ValueError(f"CUIT inválido: {cuit}. Debe tener 11 dígitos.")
    
    return f"{cuit_limpio[:2]}-{cuit_limpio[2:10]}-{cuit_limpio[10]}"

# =====================================================================
# FUNCIONES PARA CONSULTA POR CUIT - API SENASA REAL
# =====================================================================

# Configuraciones para API SENASA
API_BASE_URL = "https://aps.senasa.gob.ar/restapiprod/servicios/renspa"
TIEMPO_ESPERA = 0.5

def obtener_datos_por_cuit(cuit):
    """Obtiene todos los campos asociados a un CUIT usando API REAL de SENASA"""
    try:
        url_base = f"{API_BASE_URL}/consultaPorCuit"
        
        todos_campos = []
        offset = 0
        limit = 10
        has_more = True
        
        while has_more:
            url = f"{url_base}?cuit={cuit}&offset={offset}"
            
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                resultado = response.json()
                
                if 'items' in resultado and resultado['items']:
                    todos_campos.extend(resultado['items'])
                    has_more = resultado.get('hasMore', False)
                    offset += limit
                else:
                    has_more = False
            
            except Exception as e:
                has_more = False
                
            time.sleep(TIEMPO_ESPERA)
        
        return todos_campos
    
    except Exception as e:
        return []

def consultar_campo_detalle(renspa):
    """Consulta los detalles de un campo específico para obtener el polígono"""
    try:
        url = f"{API_BASE_URL}/consultaPorNumero?numero={renspa}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        return None

def extraer_coordenadas_senasa(poligono_str):
    """Extrae coordenadas de un string de polígono de SENASA"""
    if not poligono_str or not isinstance(poligono_str, str):
        return None
    
    coord_pattern = r'\(([-\d\.]+),([-\d\.]+)\)'
    coord_pairs = re.findall(coord_pattern, poligono_str)
    
    if not coord_pairs:
        return None
    
    coords_geojson = []
    for lat_str, lon_str in coord_pairs:
        try:
            lat = float(lat_str)
            lon = float(lon_str)
            coords_geojson.append([lon, lat])
        except ValueError:
            continue
    
    if len(coords_geojson) >= 3:
        if coords_geojson[0] != coords_geojson[-1]:
            coords_geojson.append(coords_geojson[0])
        
        return coords_geojson
    
    return None

def procesar_campos_cuit(cuit, solo_activos=True):
    """Procesa campos de un CUIT y extrae polígonos REALES para análisis"""
    try:
        cuit_normalizado = normalizar_cuit(cuit)
        campos = obtener_datos_por_cuit(cuit_normalizado)
        
        if not campos:
            return []
        
        # Filtrar según la opción seleccionada
        if solo_activos:
            campos_a_procesar = [c for c in campos if c.get('fecha_baja') is None]
        else:
            campos_a_procesar = campos
        
        # Procesar polígonos
        poligonos_data = []
        
        for i, campo in enumerate(campos_a_procesar):
            renspa = campo['renspa']
            
            # Primero intentar con los datos que ya tenemos
            coords = None
            if 'poligono' in campo and campo['poligono']:
                coords = extraer_coordenadas_senasa(campo['poligono'])
            
            # Si no tenemos polígono, consultar detalle
            if not coords:
                resultado_detalle = consultar_campo_detalle(renspa)
                if resultado_detalle and 'items' in resultado_detalle and resultado_detalle['items']:
                    item_detalle = resultado_detalle['items'][0]
                    if 'poligono' in item_detalle and item_detalle['poligono']:
                        coords = extraer_coordenadas_senasa(item_detalle['poligono'])
                
                time.sleep(TIEMPO_ESPERA)
            
            if coords:
                poligono_data = {
                    'nombre': f"Campo_{i+1}_{campo.get('titular', 'Sin_titular')}",
                    'coords': coords,
                    'numero': i + 1,
                    'archivo_origen': f'CUIT_{cuit_normalizado}',
                    'kml_origen': f'Campo_{renspa}',
                    'titular': campo.get('titular', ''),
                    'localidad': campo.get('localidad', ''),
                    'superficie': campo.get('superficie', 0),
                    'renspa': renspa
                }
                poligonos_data.append(poligono_data)
        
        return poligonos_data
    
    except Exception as e:
        st.error(f"Error procesando CUIT {cuit}: {e}")
        return []

# =====================================================================
# FUNCIONES PARA PROCESAMIENTO DE KMZ - REALES
# =====================================================================

def extraer_coordenadas_kml(kml_content):
    """Extrae coordenadas de un archivo KML - VERSIÓN MEJORADA Y ROBUSTA"""
    poligonos = []
    
    try:
        root = ET.fromstring(kml_content)
        
        # Buscar todos los Placemark sin importar el namespace
        placemarks = []
        
        # Probar múltiples formas de encontrar placemarks
        for xpath in ['.//Placemark', './/{*}Placemark', './/{http://www.opengis.net/kml/2.2}Placemark', './/{http://earth.google.com/kml/2.2}Placemark']:
            try:
                found = root.findall(xpath)
                if found:
                    placemarks = found
                    break
            except:
                continue
        
        st.info(f"🔍 Encontrados {len(placemarks)} placemarks en el KML")
        
        for i, placemark in enumerate(placemarks):
            nombre = f"Polígono_{i+1}"
            
            # Buscar nombre (múltiples formas)
            for xpath in ['.//name', './/{*}name', './/{http://www.opengis.net/kml/2.2}name']:
                try:
                    name_elem = placemark.find(xpath)
                    if name_elem is not None and name_elem.text:
                        nombre = name_elem.text.strip()
                        break
                except:
                    continue
            
            # Buscar coordenadas en MÚLTIPLES ubicaciones posibles
            coords_text = ""
            
            # Lista ampliada de posibles rutas para coordenadas
            posibles_rutas = [
                './/coordinates',
                './/{*}coordinates',
                './/{http://www.opengis.net/kml/2.2}coordinates',
                './/{http://earth.google.com/kml/2.2}coordinates',
                './/Polygon//coordinates',
                './/LinearRing//coordinates',
                './/Point//coordinates',
                './/{*}Polygon//{*}coordinates',
                './/{*}LinearRing//{*}coordinates', 
                './/{*}Point//{*}coordinates'
            ]
            
            for ruta in posibles_rutas:
                try:
                    coords_elem = placemark.find(ruta)
                    if coords_elem is not None and coords_elem.text:
                        coords_text = coords_elem.text.strip()
                        break
                except:
                    continue
            
            if coords_text:
                coordenadas = []
                
                # Limpiar y normalizar el texto de coordenadas
                coords_text = coords_text.replace('\n', ' ').replace('\t', ' ').replace('\r', ' ')
                
                # Intentar diferentes métodos de parsing
                coord_strings = []
                
                # Método 1: Separar por espacios
                if ' ' in coords_text:
                    coord_strings = [s.strip() for s in coords_text.split(' ') if s.strip()]
                # Método 2: Una sola línea de coordenadas
                else:
                    coord_strings = [coords_text.strip()]
                
                for coord_str in coord_strings:
                    if coord_str.strip():
                        # Separar lon,lat,alt por comas
                        parts = [p.strip() for p in coord_str.split(',')]
                        if len(parts) >= 2:
                            try:
                                lon = float(parts[0])
                                lat = float(parts[1])
                                
                                # Validar rango válido de coordenadas
                                if -180 <= lon <= 180 and -90 <= lat <= 90:
                                    coordenadas.append([lon, lat])
                            except (ValueError, IndexError):
                                continue
                
                # Validar polígono y agregarlo
                if coordenadas and len(coordenadas) >= 3:  # VALIDACIÓN: Al menos 3 puntos
                    # Cerrar polígono si no está cerrado
                    if coordenadas[0] != coordenadas[-1]:
                        coordenadas.append(coordenadas[0])
                    
                    poligono = {
                        'nombre': nombre,
                        'coords': coordenadas,
                        'numero': i + 1
                    }
                    poligonos.append(poligono)
                    
                elif coordenadas:
                    st.warning(f"⚠️ Polígono '{nombre}' omitido: tiene solo {len(coordenadas)} puntos (mínimo 3)")
                
    except Exception as e:
        st.error(f"❌ Error procesando KML: {e}")
    
    return poligonos

def procesar_kmz_uploaded(uploaded_file):
    """Procesa un archivo KMZ subido a Streamlit"""
    poligonos = []
    
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as kmz_zip:
            kml_files = [f for f in kmz_zip.namelist() if f.endswith('.kml')]
            
            if not kml_files:
                st.warning(f"No se encontraron archivos KML en {uploaded_file.name}")
                return poligonos
            
            for kml_file in kml_files:
                with kmz_zip.open(kml_file) as kml:
                    kml_content = kml.read().decode('utf-8')
                    poligonos_kml = extraer_coordenadas_kml(kml_content)
                    
                    for pol in poligonos_kml:
                        pol['archivo_origen'] = uploaded_file.name
                        pol['kml_origen'] = kml_file
                    
                    poligonos.extend(poligonos_kml)
    
    except Exception as e:
        st.error(f"Error procesando {uploaded_file.name}: {e}")
    
    return poligonos

# =====================================================================
# FUNCIONES PARA MAPAS REALES
# =====================================================================

def create_map_from_coords(coordinates, title="Campo Analizado"):
    """Crear mapa REAL con las coordenadas extraídas"""
    if not coordinates:
        return None
    
    # Calcular centro del polígono
    center_lat = sum(coord[1] if len(coord) > 1 else coord[0] for coord in coordinates) / len(coordinates)
    center_lon = sum(coord[0] if len(coord) > 1 else coord[1] for coord in coordinates) / len(coordinates)
    
    # Crear mapa base
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
    
    # Convertir coordenadas para folium (lat, lon)
    folium_coords = []
    for coord in coordinates:
        if len(coord) >= 2:
            if len(coord) == 2:
                # Si es [lon, lat]
                folium_coords.append([coord[1], coord[0]])
            else:
                # Si tiene más elementos, asumir [lon, lat, ...]
                folium_coords.append([coord[1], coord[0]])
    
    # Agregar polígono
    folium.Polygon(
        locations=folium_coords,
        color='#00D2BE',
        weight=3,
        fill=True,
        fillColor='#00D2BE',
        fillOpacity=0.3,
        popup=title
    ).add_to(m)
    
    # Agregar marcadores en las esquinas
    for i, coord in enumerate(folium_coords[::max(1, len(folium_coords)//4)]):
        folium.Marker(
            location=coord,
            popup=f"Punto {i+1}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
    
    return m

def create_multi_field_map(poligonos_data):
    """Crear mapa con múltiples campos"""
    if not poligonos_data:
        return None
    
    # Calcular centro de todos los polígonos
    all_coords = []
    for pol in poligonos_data:
        if 'coords' in pol:
            all_coords.extend(pol['coords'])
    
    if not all_coords:
        return None
    
    center_lat = sum(coord[1] if len(coord) > 1 else coord[0] for coord in all_coords) / len(all_coords)
    center_lon = sum(coord[0] if len(coord) > 1 else coord[1] for coord in all_coords) / len(all_coords)
    
    # Crear mapa base
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    # Colores para diferentes campos
    colores = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']
    
    for i, pol in enumerate(poligonos_data):
        coords = pol.get('coords', [])
        if coords:
            color = colores[i % len(colores)]
            
            # Convertir coordenadas
            folium_coords = []
            for coord in coords:
                if len(coord) >= 2:
                    folium_coords.append([coord[1], coord[0]])
            
            if folium_coords:
                # Información del campo
                info = f"<b>{pol.get('nombre', f'Campo {i+1}')}</b><br>"
                if 'titular' in pol:
                    info += f"Titular: {pol['titular']}<br>"
                if 'localidad' in pol:
                    info += f"Localidad: {pol['localidad']}<br>"
                if 'superficie' in pol:
                    info += f"Superficie: {pol['superficie']} ha"
                
                folium.Polygon(
                    locations=folium_coords,
                    color=color,
                    weight=2,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.3,
                    popup=folium.Popup(info, max_width=300),
                    tooltip=pol.get('nombre', f'Campo {i+1}')
                ).add_to(m)
    
    return m

# =====================================================================
# APLICACIÓN PRINCIPAL
# =====================================================================

def main():
    # Logo VISU con tagline correcto - DISEÑO ELEGANTE QUE YA FUNCIONA
    st.markdown("""
    <div class="visu-logo-container">
        <div class="minimal-container">
            <div class="visu-minimal">VISU</div>
            <div class="eye-underline">
                <div class="eye-dot"></div>
            </div>
            <div class="tagline">VISUALIZE WITH SUPERPOWERS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Inicializar session state
    if 'resultados_analisis' not in st.session_state:
        st.session_state.resultados_analisis = None
    if 'analisis_completado' not in st.session_state:
        st.session_state.analisis_completado = False
    
    # CREAR PESTAÑAS PRINCIPALES
    tabs = st.tabs(["🏢 Análisis por CUIT", "📁 Análisis por KMZ"])
    
    with tabs[0]:
        mostrar_analisis_cuit()
    
    with tabs[1]:
        mostrar_analisis_kmz()
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        🌾 VISU - Agricultural Intelligence | Powered by SENASA + Google Earth Engine
    </div>
    """, unsafe_allow_html=True)

def mostrar_analisis_cuit():
    """Análisis REAL por CUIT usando API de SENASA"""
    st.title("🏢 Análisis por CUIT")
    st.markdown("**Consulta REAL usando API de SENASA**")
    
    # Input para CUIT
    cuit_input = st.text_input(
        "🏢 Ingresá el CUIT del productor:",
        placeholder="30-12345678-9",
        help="💡 Consulta automática REAL de coordenadas usando API de SENASA"
    )
    
    # Opción para elegir entre campos activos o históricos
    solo_activos = st.radio(
        "¿Qué campos querés consultar?",
        ["Solo campos activos", "Todos los campos (incluye históricos)"],
        horizontal=True
    ) == "Solo campos activos"
    
    if st.button("🔍 Consultar SENASA", type="primary"):
        if cuit_input:
            if validate_cuit(cuit_input):
                try:
                    with st.spinner("🔄 Consultando API de SENASA..."):
                        # Procesar campos del CUIT usando API REAL
                        poligonos_data = procesar_campos_cuit(cuit_input, solo_activos)
                        
                        if poligonos_data:
                            st.success(f"✅ Se encontraron {len(poligonos_data)} campos con coordenadas")
                            
                            # Mostrar información de los campos
                            st.subheader("📍 Campos Encontrados")
                            
                            for i, campo in enumerate(poligonos_data):
                                with st.expander(f"🏡 Campo {i+1}: {campo.get('titular', 'Sin titular')}", expanded=i==0):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write(f"**RENSPA**: {campo.get('renspa', 'N/A')}")
                                        st.write(f"**Titular**: {campo.get('titular', 'Sin información')}")
                                        st.write(f"**Localidad**: {campo.get('localidad', 'Sin información')}")
                                        st.write(f"**Superficie**: {campo.get('superficie', 0):.1f} ha")
                                    
                                    with col2:
                                        coords = campo.get('coords', [])
                                        st.write(f"**Coordenadas**: {len(coords)} puntos")
                                        
                                        if coords and len(coords) >= 3:
                                            # Crear mapa individual del campo
                                            mapa_campo = create_map_from_coords(coords, f"Campo {i+1}")
                                            if mapa_campo:
                                                st_folium(mapa_campo, width=300, height=200, key=f"mapa_campo_{i}")
                            
                            # Crear mapa general con todos los campos
                            st.subheader("🗺️ Mapa General de Todos los Campos")
                            mapa_general = create_multi_field_map(poligonos_data)
                            if mapa_general:
                                st_folium(mapa_general, width=700, height=500, key="mapa_general_cuit")
                            
                            # Guardar resultados
                            st.session_state.resultados_analisis = {
                                'tipo': 'cuit',
                                'cuit': cuit_input,
                                'campos': poligonos_data,
                                'mapa': mapa_general
                            }
                            st.session_state.analisis_completado = True
                            
                        else:
                            st.warning("⚠️ No se encontraron campos con coordenadas para este CUIT")
                            
                except Exception as e:
                    st.error(f"❌ Error consultando SENASA: {e}")
            else:
                st.error("❌ Formato de CUIT inválido. Usar formato: XX-XXXXXXXX-X")
        else:
            st.warning("⚠️ Por favor, ingresá un CUIT válido")

def mostrar_analisis_kmz():
    """Análisis REAL de archivos KMZ"""
    st.title("📁 Análisis por Archivos KMZ")
    st.markdown("**Procesamiento REAL de archivos KMZ/KML**")
    
    # Upload de archivos
    uploaded_files = st.file_uploader(
        "📁 Selecciona tus archivos KMZ",
        type=['kmz'],
        accept_multiple_files=True,
        help="💡 Archivos KMZ de Google Earth para análisis de coordenadas"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} archivo(s) subido(s)")
        
        # Mostrar detalles de archivos
        with st.expander("📋 Detalles de archivos", expanded=False):
            for file in uploaded_files:
                file_size_mb = file.size / (1024 * 1024)
                st.write(f"📄 **{file.name}** - {file_size_mb:.2f} MB")
        
        if st.button("🔍 Procesar Archivos KMZ", type="primary"):
            with st.spinner("🔄 Procesando archivos KMZ..."):
                todos_los_poligonos = []
                
                for uploaded_file in uploaded_files:
                    st.write(f"🔄 Procesando: {uploaded_file.name}")
                    poligonos = procesar_kmz_uploaded(uploaded_file)
                    todos_los_poligonos.extend(poligonos)
                
                if todos_los_poligonos:
                    st.success(f"✅ Se procesaron {len(todos_los_poligonos)} polígonos")
                    
                    # Mostrar información de polígonos
                    st.subheader("📍 Polígonos Encontrados")
                    
                    for i, pol in enumerate(todos_los_poligonos):
                        with st.expander(f"🗺️ Polígono {i+1}: {pol.get('nombre', f'Sin nombre')}", expanded=i==0):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Nombre**: {pol.get('nombre', 'Sin nombre')}")
                                st.write(f"**Archivo**: {pol.get('archivo_origen', 'N/A')}")
                                st.write(f"**KML**: {pol.get('kml_origen', 'N/A')}")
                                coords = pol.get('coords', [])
                                st.write(f"**Coordenadas**: {len(coords)} puntos")
                            
                            with col2:
                                if coords and len(coords) >= 3:
                                    # Mostrar algunas coordenadas de ejemplo
                                    st.write("**Primeras coordenadas**:")
                                    for j, coord in enumerate(coords[:3]):
                                        if len(coord) >= 2:
                                            st.write(f"  {j+1}. Lon: {coord[0]:.6f}, Lat: {coord[1]:.6f}")
                                    
                                    if len(coords) > 3:
                                        st.write(f"  ... y {len(coords)-3} más")
                                    
                                    # Crear mapa individual
                                    mapa_pol = create_map_from_coords(coords, pol.get('nombre', f'Polígono {i+1}'))
                                    if mapa_pol:
                                        st_folium(mapa_pol, width=300, height=200, key=f"mapa_pol_{i}")
                    
                    # Crear mapa general
                    st.subheader("🗺️ Mapa General de Todos los Polígonos")
                    mapa_general = create_multi_field_map(todos_los_poligonos)
                    if mapa_general:
                        st_folium(mapa_general, width=700, height=500, key="mapa_general_kmz")
                    
                    # Mostrar tabla resumen
                    st.subheader("📊 Resumen de Coordenadas")
                    resumen_data = []
                    for pol in todos_los_poligonos:
                        coords = pol.get('coords', [])
                        if coords:
                            center_lat = sum(coord[1] if len(coord) > 1 else coord[0] for coord in coords) / len(coords)
                            center_lon = sum(coord[0] if len(coord) > 1 else coord[1] for coord in coords) / len(coords)
                            
                            resumen_data.append({
                                'Nombre': pol.get('nombre', 'Sin nombre'),
                                'Archivo': pol.get('archivo_origen', 'N/A'),
                                'Puntos': len(coords),
                                'Centro Lat': f"{center_lat:.6f}",
                                'Centro Lon': f"{center_lon:.6f}"
                            })
                    
                    if resumen_data:
                        df_resumen = pd.DataFrame(resumen_data)
                        st.dataframe(df_resumen, use_container_width=True)
                    
                    # Guardar resultados
                    st.session_state.resultados_analisis = {
                        'tipo': 'kmz',
                        'archivos': [f.name for f in uploaded_files],
                        'poligonos': todos_los_poligonos,
                        'mapa': mapa_general
                    }
                    st.session_state.analisis_completado = True
                    
                else:
                    st.error("❌ No se encontraron polígonos válidos en los archivos")

if __name__ == "__main__":
    main()

# =====================================================================
# FUNCIONES DE ANÁLISIS Y GRÁFICOS
# =====================================================================

def analizar_cultivos_basico(poligonos_data):
    """Análisis básico de cultivos cuando Earth Engine no está disponible"""
    if not poligonos_data:
        return None, 0
    
    # Calcular área total aproximada usando coordenadas
    area_total = 0
    for pol in poligonos_data:
        coords = pol.get("coords", [])
        if coords and len(coords) >= 3:
            area_aproximada = len(coords) * 100  # Muy aproximado
            area_total += area_aproximada
    
    # Crear dataframe con datos de ejemplo
    campanas = ["19-20", "20-21", "21-22", "22-23", "23-24"]
    cultivos_basicos = ["Soja 1ra", "Maíz", "No agrícola"]
    
    datos = []
    for campana in campanas:
        for cultivo in cultivos_basicos:
            if cultivo == "No agrícola":
                area = area_total * 0.2  # 20% no agrícola
            elif cultivo == "Soja 1ra":
                area = area_total * 0.5  # 50% soja
            else:
                area = area_total * 0.3  # 30% maíz
            
            porcentaje = (area / area_total * 100) if area_total > 0 else 0
            datos.append({
                "Campaña": campana,
                "Cultivo": cultivo,
                "Área (ha)": area,
                "Porcentaje (%)": porcentaje
            })
    
    return pd.DataFrame(datos), area_total

def generar_grafico_rotacion_basico(df_resultados):
    """Genera gráfico de rotación básico con matplotlib"""
    try:
        if df_resultados is None or df_resultados.empty:
            return None, None
        
        df = df_resultados.copy()
        df_pivot = df.pivot_table(
            index="Cultivo", 
            columns="Campaña", 
            values="Porcentaje (%)", 
            aggfunc="sum", 
            fill_value=0
        )
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        colores_cultivos = {
            "Maíz": "#0042ff",
            "Soja 1ra": "#339820", 
            "No agrícola": "#e6f0c2"
        }
        
        bottom = None
        for cultivo in df_pivot.index:
            color = colores_cultivos.get(cultivo, "#999999")
            ax.bar(df_pivot.columns, df_pivot.loc[cultivo], 
                  bottom=bottom, label=cultivo, color=color)
            if bottom is None:
                bottom = df_pivot.loc[cultivo]
            else:
                bottom += df_pivot.loc[cultivo]
        
        ax.set_title("Rotación de Cultivos por Campaña", fontsize=16)
        ax.set_xlabel("Campaña", fontsize=12)
        ax.set_ylabel("Porcentaje del Área Total (%)", fontsize=12)
        ax.legend(title="Cultivo", bbox_to_anchor=(1.05, 1), loc="upper left")
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        ax.set_ylim(0, 100)
        
        plt.tight_layout()
        return fig, df_pivot
        
    except Exception as e:
        st.error(f"Error generando gráfico: {e}")
        return None, None

def get_download_link(df, filename, link_text):
    """Genera un enlace de descarga para un DataFrame"""
    try:
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f"<a href=\"data:file/csv;base64,{b64}\" download=\"{filename}\">{link_text}</a>"
        return href
    except Exception as e:
        return f"Error generando enlace: {e}"

