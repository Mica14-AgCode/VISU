import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="VISU - Análisis de Cultivos",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para el logo VISU
st.markdown("""
<style>
    .visu-logo-container {
        text-align: center;
        margin: 20px 0 30px 0;
        padding: 20px;
    }
    
    .visu-minimal {
        font-size: 60px;
        font-weight: 300;
        letter-spacing: 15px;
        color: #C0C0C0;
        margin-bottom: 10px;
        margin-left: 15px;
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
</style>
""", unsafe_allow_html=True)

def main():
    # Logo VISU
    st.markdown("""
    <div class="visu-logo-container">
        <div class="minimal-container">
            <div class="visu-minimal">VISU</div>
            <div class="eye-underline">
                <div class="eye-dot"></div>
            </div>
        </div>
        <div class="tagline">AGRICULTURAL INTELLIGENCE</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Título principal
    st.markdown("# 🌾 Análisis de Rotación de Cultivos")
    st.markdown("### Powered by Google Earth Engine")
    
    # Mensaje de estado
    st.success("✅ Aplicación iniciada correctamente - Versión 1.0")
    
    # Funcionalidades disponibles
    st.markdown("---")
    st.markdown("## 🚀 Funcionalidades Disponibles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📁 Análisis por KMZ
        - Carga de archivos KMZ
        - Análisis de rotación de cultivos
        - Mapas interactivos
        
        ### 🏢 Análisis por CUIT
        - Consulta automática de coordenadas
        - Análisis masivo de campos
        - Reportes consolidados
        """)
    
    with col2:
        st.markdown("""
        ### 🌊 Análisis de Riesgo Hídrico
        - Detección de zonas de inundación
        - Análisis histórico 1984-2025
        - Mapas de riesgo
        
        ### �� Reportes y Visualización
        - Generación de PDFs
        - Gráficos interactivos
        - Exportación de datos
        """)
    
    # Estado del desarrollo
    st.markdown("---")
    st.markdown("## 🔧 Estado del Desarrollo")
    
    st.info("🚧 La aplicación está en desarrollo activo. Las funcionalidades se añadirán gradualmente.")
    
    # Información técnica
    st.markdown("---")
    st.markdown("## 🛠️ Información Técnica")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Streamlit", "1.46.1")
    with col2:
        st.metric("Python", "3.13+")
    with col3:
        st.metric("Status", "🟢 Online")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 14px;'>"
        "© 2025 VISU - Agricultural Intelligence Platform"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
