FROM nginx:1.27-alpine

# Eliminar config por defecto
RUN rm -f /etc/nginx/conf.d/default.conf

# Copiar config personalizada
COPY nginx.conf /etc/nginx/nginx.conf

# Crear directorio para archivos estáticos
RUN mkdir -p /var/www/static

EXPOSE 80
EXPOSE 443

CMD ["nginx", "-g", "daemon off;"]
