# OVRA AI Widget - Guía de Integración

## 🚀 Integración Rápida

### 1. Incluir el Script
```html
<script src="https://tudominio.com/ovra-widget.js"></script>
```

### 2. Configuración Opcional
```html
<script>
window.ovraWidgetConfig = {
    apiUrl: 'https://api.ovra.ai',
    buttonColor: '#007bff',
    position: 'bottom-right',
    theme: 'light',
    title: 'Asistente Fiscal OVRA'
};
</script>
```

## ⚙️ Opciones de Configuración

| Opción | Tipo | Valor por defecto | Descripción |
|--------|------|------------------|-------------|
| `apiUrl` | string | `'http://localhost:8000'` | URL de la API del backend |
| `buttonColor` | string | `'#000000'` | Color del botón flotante |
| `position` | string | `'bottom-right'` | Posición del widget (`bottom-right`, `bottom-left`) |
| `theme` | string | `'light'` | Tema del widget (`light`, `dark`) |
| `title` | string | `'Asistente Fiscal OVRA'` | Título mostrado en el header |

## 🎨 Personalización

### Colores Personalizados
```javascript
window.ovraWidgetConfig = {
    buttonColor: '#ff6b6b', // Rojo coral
    // El widget automáticamente generará colores hover más oscuros
};
```

### Posicionamiento
```javascript
window.ovraWidgetConfig = {
    position: 'bottom-left', // Esquina inferior izquierda
};
```

## 📱 Responsive Design

El widget es completamente responsive y se adapta automáticamente a:
- **Desktop**: Ventana flotante de 380x600px
- **Mobile**: Pantalla completa para mejor experiencia

## 🔒 Seguridad y Privacidad

- **CORS**: Configurado para permitir embedding desde cualquier dominio
- **Datos**: Solo se requiere email para el registro
- **Almacenamiento**: Utiliza localStorage para persistir sesiones
- **Cumplimiento**: Requiere aceptación explícita de términos y privacidad

## 🛠️ Integración por Plataforma

### WordPress
1. **Tema**: Añadir en `footer.php` antes de `</body>`
2. **Plugin**: Usar "Insert Headers and Footers"
3. **Customizer**: En "HTML/CSS/JavaScript adicional"

### Shopify
1. Ir a "Themes" > "Actions" > "Edit code"
2. Editar `theme.liquid`
3. Añadir el código antes de `</body>`

### HTML Estático
```html
<!DOCTYPE html>
<html>
<head>
    <title>Mi Sitio Web</title>
</head>
<body>
    <!-- Tu contenido aquí -->
    
    <!-- Widget OVRA -->
    <script>
        window.ovraWidgetConfig = {
            apiUrl: 'https://api.ovra.ai',
            buttonColor: '#007bff'
        };
    </script>
    <script src="https://tudominio.com/ovra-widget.js"></script>
</body>
</html>
```

## 🔧 API Endpoints

El widget utiliza los siguientes endpoints:

- `POST /widget/register/` - Registro de usuario
- `POST /chat/message/` - Envío de mensajes

## 🎯 Funcionalidades

- ✅ Registro simple con email
- ✅ Validación de términos y privacidad
- ✅ Chat en tiempo real
- ✅ Formato de respuestas con markdown
- ✅ Referencias legales en respuestas
- ✅ Persistencia de sesiones
- ✅ Animaciones de carga
- ✅ Mensajes de error amigables

## 🐛 Solución de Problemas

### El widget no aparece
- Verificar que el script se carga correctamente
- Comprobar la consola del navegador por errores
- Verificar que no hay conflictos con otros scripts

### Problemas de conexión
- Verificar que la API esté disponible
- Comprobar configuración de CORS
- Verificar que `apiUrl` sea correcta

### Problemas de estilo
- El widget utiliza CSS aislado con alta especificidad
- Verificar que no hay conflictos con otros estilos
- Probar en modo incógnito

## 📞 Soporte

Para problemas o preguntas sobre la integración:
1. Verificar esta documentación
2. Comprobar los logs del navegador
3. Contactar al equipo de desarrollo

## 🚀 Próximas Características

- [ ] Temas personalizables
- [ ] Más opciones de posicionamiento
- [ ] Integración con Google Analytics
- [ ] Soporte para múltiples idiomas
- [ ] Widget inline (no flotante)
- [ ] Callbacks personalizados