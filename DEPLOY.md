# Deploy — StickerControl 2026 bajo SkillGames

> Estado actual: **Fase 0.6.2**, sin login/OAuth/chat/invitaciones (single-user
> local, `id=1`). Esta guía describe el deploy real bajo
> `https://www.skillgames.com.ar/stickercontrol`, con el frontend servido en
> `/stickercontrol/` y el backend proxificado en `/stickercontrol/api/`.

## Requisitos en el VPS

- Ubuntu 22.04+ con Python 3.10+, Node.js 18+, nginx
- Acceso por SSH y un usuario no-root con permisos sudo

## 1. Backend (systemd)

1. Clonar el repo y crear el entorno virtual:

   ```bash
   cd /opt/stickercontrol-2026/backend
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   cp .env.example .env   # ajustar DATABASE_URL / CORS_ORIGINS
   .venv/bin/python seed_db.py
   ```

2. Editar `.env`:

   ```bash
   DATABASE_URL=sqlite:///./stickercontrol.db
   CORS_ORIGINS=https://www.skillgames.com.ar
   ```

   > Como el frontend y la API se sirven bajo el mismo origen
   > (`www.skillgames.com.ar`) gracias al proxy de nginx, CORS no es
   > estrictamente necesario en producción, pero se deja configurado por si
   > se accede directo al backend (puerto 127.0.0.1:8000) durante pruebas.

3. Crear el servicio `/etc/systemd/system/stickercontrol-backend.service`:

   ```ini
   [Unit]
   Description=StickerControl 2026 backend
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/opt/stickercontrol-2026/backend
   ExecStart=/opt/stickercontrol-2026/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
   Restart=on-failure
   EnvironmentFile=/opt/stickercontrol-2026/backend/.env

   [Install]
   WantedBy=multi-user.target
   ```

4. Habilitar y arrancar:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now stickercontrol-backend
   sudo systemctl status stickercontrol-backend
   ```

   El backend queda escuchando solo en `127.0.0.1:8000` (no expuesto
   directamente a internet); nginx lo proxifica bajo `/stickercontrol/api/`.

## 2. Frontend (build estático)

1. Generar el build de producción (usa `base: "/stickercontrol/"`, definido
   en `vite.config.js` para `mode === "production"`, que es el modo por
   defecto de `vite build`):

   ```bash
   cd /opt/stickercontrol-2026/frontend
   npm install
   npm run build   # genera dist/ con rutas /stickercontrol/...
   ```

2. El contenido de `dist/` se sirve directamente con nginx (ver sección
   siguiente). No hace falta copiarlo a otra carpeta.

## 3. Nginx — `/stickercontrol`

Configuración real para `www.skillgames.com.ar`, agregada dentro del
`server {}` existente del sitio (no se crea un server nuevo, se agrega un
bloque más al sitio de SkillGames):

```nginx
server {
    listen 443 ssl;
    server_name www.skillgames.com.ar;

    # ... resto de la configuración existente de SkillGames ...

    # API de StickerControl 2026 (proxy al backend FastAPI en :8000)
    # IMPORTANTE: este bloque va ANTES del bloque /stickercontrol/ para que
    # nginx lo matchee primero (mayor especificidad de prefijo).
    location /stickercontrol/api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend de StickerControl 2026 (build estático de Vite)
    location /stickercontrol/ {
        alias /opt/stickercontrol-2026/frontend/dist/;
        try_files $uri $uri/ /stickercontrol/index.html;
    }
}
```

Notas:

- `proxy_pass http://127.0.0.1:8000/api/;` con barra final hace que nginx
  reemplace el prefijo `/stickercontrol/api/` por `/api/` al reenviar la
  petición al backend. Es decir, `GET /stickercontrol/api/nearby` llega al
  backend como `GET /api/nearby` (que es la ruta real definida en
  `app/main.py`).
- `alias` (no `root`) es necesario porque la carpeta `dist/` no se llama
  `stickercontrol` — `alias` reemplaza el prefijo de la URL por la ruta del
  filesystem.
- `try_files ... /stickercontrol/index.html` permite que las rutas de React
  Router (`/stickercontrol/cerca`, `/stickercontrol/faltantes`, etc.) recarguen
  correctamente al hacer F5 o entrar por URL directa: si el archivo no existe
  en `dist/`, nginx sirve `index.html` y React Router toma el control con
  `basename="/stickercontrol"`.

Recargar nginx:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 4. Base de datos SQLite

- Ubicación: `/opt/stickercontrol-2026/backend/stickercontrol.db` (definida
  por `DATABASE_URL=sqlite:///./stickercontrol.db`, relativa al
  `WorkingDirectory` del servicio systemd).
- Se crea sola al arrancar el backend (`init_db()`); `seed_db.py` carga el
  catálogo de figuritas (`master_stickers`).

### Backup recomendado

SQLite permite copiar el archivo en caliente con `.backup` (más seguro que
`cp` mientras el proceso puede estar escribiendo). Script sugerido
`/opt/stickercontrol-2026/backend/backup.sh`:

```bash
#!/bin/bash
set -e
DB=/opt/stickercontrol-2026/backend/stickercontrol.db
DEST=/opt/stickercontrol-2026/backups
mkdir -p "$DEST"
sqlite3 "$DB" ".backup '$DEST/stickercontrol-$(date +%F).db'"
# conservar solo los últimos 14 backups
ls -1t "$DEST"/stickercontrol-*.db | tail -n +15 | xargs -r rm
```

Cron diario (`crontab -e` del usuario `www-data` o vía
`/etc/cron.d/stickercontrol-backup`):

```cron
0 3 * * * /opt/stickercontrol-2026/backend/backup.sh
```

## 5. Rutas verificadas bajo `/stickercontrol`

Con el build de producción (`base: "/stickercontrol/"` + `basename` en
`BrowserRouter` + `BASE_URL` en el cliente API), las siguientes rutas
funcionan tal cual bajo `https://www.skillgames.com.ar`:

| Ruta                              | Descripción                          |
|-----------------------------------|---------------------------------------|
| `/stickercontrol/`                 | Dashboard (landing + resumen)          |
| `/stickercontrol/buscar`           | Buscador de figuritas                  |
| `/stickercontrol/album`            | Álbum completo agrupado A-L            |
| `/stickercontrol/faltantes`        | Faltantes + texto WhatsApp             |
| `/stickercontrol/repetidas`        | Repetidas + texto WhatsApp             |
| `/stickercontrol/intercambios`     | "Próximamente"                         |
| `/stickercontrol/cerca`            | Usuarios cerca (perfil + intercambio)  |
| `/stickercontrol/api/...`          | API FastAPI (proxificada a `:8000/api/...`) |

Entrar directamente por URL (sin pasar por `/stickercontrol/`) o recargar
con F5 en cualquiera de estas rutas funciona gracias al `try_files` de
nginx descrito arriba.

## Pendiente para producción real

- HTTPS ya cubierto por la configuración existente de
  `www.skillgames.com.ar` (este bloque se agrega dentro de ese `server {}`).
- Variables de entorno de Google OAuth (Fase 1) — no aplica todavía (no hay
  login).
- Monitoreo del servicio (`systemctl status stickercontrol-backend`,
  `journalctl -u stickercontrol-backend`).
