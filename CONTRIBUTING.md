# Contributing to VISU

¡Gracias por tu interés en contribuir al proyecto VISU! 🌾

## Cómo Contribuir

### Reportar Problemas
1. Usa el [issue tracker](https://github.com/Mica14-AgCode/VISU/issues)
2. Describe el problema en detalle
3. Incluye pasos para reproducir el error
4. Adjunta capturas de pantalla si es necesario

### Proponer Mejoras
1. Abre un issue describiendo la mejora
2. Explica por qué sería útil
3. Proporciona ejemplos de uso

### Enviar Código
1. Fork el repositorio
2. Crea una rama para tu feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit tus cambios: `git commit -m "Agregar nueva funcionalidad"`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

## Estándares de Código

### Python
- Usar PEP 8 para el estilo de código
- Documentar funciones con docstrings
- Usar type hints cuando sea posible
- Mantener funciones pequeñas y claras

### Streamlit
- Usar `st.cache_data` para datos que no cambian
- Organizat el código en funciones reutilizables
- Comentar secciones complejas del UI

### Git
- Commits claros y descriptivos
- Un commit por feature/fix
- Usar presente: "Agregar" no "Agregado"

## Configuración del Desarrollo

```bash
# Clonar el repositorio
git clone https://github.com/Mica14-AgCode/VISU.git
cd VISU

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\\Scripts\\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
streamlit run app.py
```

## Proceso de Review

1. Todo código debe ser reviewado antes del merge
2. Los tests deben pasar
3. La documentación debe estar actualizada
4. El código debe seguir los estándares establecidos

## Licencia

Al contribuir, aceptas que tu código sea liberado bajo la [MIT License](LICENSE).
