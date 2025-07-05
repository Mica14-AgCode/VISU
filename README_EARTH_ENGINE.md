# 🛰️ Integración Google Earth Engine - VISU

Este archivo explica cómo integrar **Google Earth Engine** real en la aplicación VISU para análisis satelital avanzado.

## 🔧 Configuración Requerida

### 1. Service Account de Google Earth Engine

Para usar Google Earth Engine necesitás:

1. **Crear cuenta en Google Earth Engine**: https://earthengine.google.com/
2. **Crear un proyecto en Google Cloud Console**
3. **Crear Service Account**:
   - Ir a Google Cloud Console
   - APIs & Services → Credentials  
   - Create Credentials → Service Account
   - Descargar la clave JSON

### 2. Configurar Secrets en Streamlit Cloud

En Streamlit Cloud, ir a App Settings → Secrets y agregar:

```toml
[gee_service_account]
type = "service_account"
project_id = "tu-project-id"
private_key_id = "tu-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nTU_PRIVATE_KEY_AQUI\n-----END PRIVATE KEY-----\n"
client_email = "tu-service-account@tu-project.iam.gserviceaccount.com"
client_id = "tu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/tu-service-account%40tu-project.iam.gserviceaccount.com"
```

## 📊 Análisis Disponibles

### 1. NDVI (Normalized Difference Vegetation Index)
- **Fuente**: Sentinel-2 Surface Reflectance
- **Resolución**: 10 metros
- **Frecuencia**: Serie temporal mensual
- **Uso**: Monitoreo de salud vegetal y crecimiento

### 2. Precipitación
- **Fuente**: CHIRPS (Climate Hazards Group)
- **Resolución**: ~5.5 km
- **Frecuencia**: Datos diarios agregados mensualmente
- **Uso**: Análisis de disponibilidad hídrica

### 3. Riesgo de Inundación
- **Fuente**: JRC Global Surface Water
- **Resolución**: 30 metros
- **Período**: 1984-2021
- **Uso**: Evaluación de riesgo histórico de inundación

### 4. Clasificación de Cultivos
- **Fuente**: Sentinel-2 con índices espectrales
- **Índices**: NDVI, EVI
- **Frecuencia**: Análisis estacional
- **Uso**: Identificación de tipos de cultivo

## 🚀 Despliegue

### Streamlit Cloud
1. Configurar secrets como se mostró arriba
2. Push del código con la integración
3. Verificar que las dependencias se instalen correctamente

### Local
1. Instalar dependencias: `pip install earthengine-api`
2. Autenticar: `earthengine authenticate`
3. Ejecutar: `streamlit run app.py`

**¡Con esta integración, VISU tendrá capacidades de análisis satelital a nivel profesional!** 🛰️🌾
