# Step 21: Instrucciones completas de despliegue a producción

Guía para llevar las notificaciones in-app (Step 21) a producción.

---

## Resumen

- **Sin Sockudo**: Las notificaciones funcionan (bandeja, badge, marcar leídas). Se actualizan al abrir el dropdown.
- **Con Sockudo**: Infraestructura lista para realtime. El frontend actual no conecta a Sockudo (falta `pusher-js`); las notificaciones se actualizan al abrir el dropdown. Configurar Sockudo ahora deja todo listo para cuando se agregue la conexión WebSocket en el frontend.

---

## Parte 1: Despliegue básico (sin Sockudo)

### 1.1 Commit y push

```bash
git add .
git status
git commit -m "feat[step-21]: In-app notifications (bandeja + API + UI)"
git push origin main
```

### 1.2 En el servidor de producción

```bash
cd /ruta/al/proyecto
./bin/deploy-production.sh
```

El script ya hace:
- `git pull`
- `docker compose build` (incluye el nuevo `app.js`)
- `migrate` (aplica `0015_add_inapp_notifications`)
- `collectstatic`
- Reinicio de servicios

### 1.3 Verificación

1. Iniciar sesión como veterinario.
2. Ver la campana en la navbar.
3. Admin → Usuarios → seleccionar usuario → Acción "Enviar notificación de prueba" → Ejecutar.
4. Abrir el dropdown de la campana y ver la notificación.

---

## Parte 2: Sockudo (realtime opcional)

### 2.1 Variables de entorno en `.env`

Agregar o editar en el servidor:

```bash
# In-App Notifications Realtime (Sockudo - Step 21)
SOCKUDO_ENABLED=true
SOCKUDO_APP_ID=adlab-app
SOCKUDO_APP_KEY=adlab-key
SOCKUDO_APP_SECRET=<generar-secreto-fuerte-aqui>
SOCKUDO_HTTP_URL=http://sockudo:6001
SOCKUDO_WS_HOST=adlab.fmoreyra.com.ar
SOCKUDO_WS_PORT=443
SOCKUDO_WS_USE_TLS=true
```

**Importante**: Generar un secreto fuerte para `SOCKUDO_APP_SECRET`:

```bash
openssl rand -hex 32
```

### 2.2 Perfil de Compose

En `.env`, agregar `sockudo` a `COMPOSE_PROFILES`:

```bash
COMPOSE_PROFILES=postgres,redis,nginx,certbot,sockudo
```

### 2.3 Nginx (laboratory.conf no está en git)

Editar manualmente `nginx/conf.d/laboratory.conf` en el servidor.

Dentro del bloque `server` HTTPS (el que tiene `listen 443`), agregar **una línea** antes de "Deny access to sensitive files":

```nginx
include /etc/nginx/conf.d/snippets/sockudo-websocket.conf;
```

Ejemplo del bloque completo:

```nginx
    location /up {
        proxy_pass http://django_app/up;
        access_log off;
    }

    include /etc/nginx/conf.d/snippets/sockudo-websocket.conf;

    location ~ /\.(?!well-known) {
        deny all;
    }
```

### 2.4 Levantar Sockudo y recargar Nginx

```bash
# Levantar el contenedor Sockudo
docker compose -f compose.yaml -f compose.production.yaml up -d sockudo

# Recargar Nginx para aplicar el include
docker compose -f compose.yaml -f compose.production.yaml exec nginx nginx -s reload
```

### 2.5 Verificación de Sockudo

```bash
# Ver que Sockudo está corriendo
docker compose -f compose.yaml -f compose.production.yaml ps sockudo

# Probar WebSocket (desde el servidor)
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  "https://adlab.fmoreyra.com.ar/app/adlab-key?protocol=5&client=js&version=7.0.3"
```

Debería devolver `101 Switching Protocols` si el proxy funciona.

---

## Parte 3: Deploy completo (checklist)

### Pre-deploy (local)

- [ ] Tests pasando: `make test-with-sqlite`
- [ ] Commit con mensaje correcto
- [ ] Push a `main`

### En el servidor

- [ ] `./bin/deploy-production.sh`
- [ ] Verificar campana y dropdown (sin Sockudo)

### Si usás Sockudo

- [ ] Variables en `.env` (SOCKUDO_*)
- [ ] `sockudo` en COMPOSE_PROFILES
- [ ] Línea `include` en `laboratory.conf`
- [ ] `docker compose up -d sockudo`
- [ ] `nginx -s reload`

---

## Troubleshooting

### La campana no aparece

- Verificar que el usuario está autenticado.
- Revisar la consola del navegador (errores JS).
- Verificar que `collectstatic` se ejecutó y que `app.js` está en `/static/js/`.

### Las notificaciones no se crean

- Revisar logs: `docker compose logs web`
- Verificar que la migración `0015` se aplicó: `make manage ARGS="showmigrations protocols"`

### Sockudo: 502 en /app/

- Sockudo no está corriendo: `docker compose up -d sockudo`
- El include no está en laboratory.conf o la ruta es incorrecta.
- Verificar que el snippet existe: `ls nginx/conf.d/snippets/sockudo-websocket.conf`

### Sockudo: conexión WebSocket falla

- Verificar `SOCKUDO_WS_HOST` y `SOCKUDO_WS_USE_TLS` (debe ser `true` en HTTPS).
- Verificar que Nginx tiene los headers `Upgrade` y `Connection`.
