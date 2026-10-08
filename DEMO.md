# StickerControl Demo Roura

Demo pública e interactiva de StickerControl 2026 para el portfolio de Roura Lab.

- **Rama:** `demo-roura`, creada desde `main` @ `4586599` (`v1.4-trade-match`).
- **Destino previsto:** `https://stickercontrol-demo.roura.com.ar/`.

Todo el comportamiento de demo se activa con `DEMO_MODE=true` (backend) y `VITE_DEMO_MODE=true` (frontend). Sin esas variables, la app funciona igual que la versión de producción: login con Google, perfil editable y contacto real.

## Qué ve el visitante

1. Un botón **"Probar la demo"**. No hay registro ni Google.
2. Un álbum precargado al ~55 %: pegadas, faltantes, repetidas y algunas conseguidas sin pegar.
3. Puede marcar y desmarcar, sumar repetidas, completar un país, agregar notas y generar el link público de solo lectura.
4. En **Cerca** e **Intercambios** aparecen 8 coleccionistas ficticios (nombres inventados, ciudades reales con coordenadas aproximadas). Las coincidencias las calcula **el algoritmo existente** (`crud.get_missing_and_duplicate_codes`) cruzando su álbum con las colecciones ficticias. Si el visitante marca una figurita, los cruces cambian.
5. **"Ver mensaje"** muestra el texto que se mandaría por WhatsApp. No se abre WhatsApp ni se genera ningún link `wa.me` ni `mailto`.
6. Una banda fija avisa que los datos son ficticios. **"Reiniciar demo"** vuelve al álbum inicial y **"Terminar demo"** borra el sandbox.

## Arquitectura

```
Visitante ──HTTPS──► nginx (vhost stickercontrol-demo, rate limit, CSP)
                       ├─ /            → public/ (build Vite, VITE_DEMO_MODE=true, VITE_BASE=/)
                       └─ /api/*       → 127.0.0.1:8012  uvicorn (1 worker, usuario stickerdemo)
                                            └─ SQLite propia: /var/www/stickercontrol-demo/data/demo.db (WAL)
timers systemd: purge (cada hora) · reset (00:00 ART)
```

| Tema | Decisión |
|---|---|
| Aislamiento de producción | Instancia, usuario de sistema, puerto, base, `.env` y vhost propios. No usa nada de `/var/www/skillgames` ni secretos históricos |
| Sesiones | `POST /api/auth/demo` crea un **sandbox**: un usuario `visitor-<uuid>@visitor.demo.invalid` con el álbum plantilla. La cookie firmada guarda `user_id`, email y vencimiento. Cada request valida que el sandbox exista y que el email coincida, así una cookie vieja nunca abre el sandbox de otro aunque SQLite reutilice el id |
| Sin Google | Con `DEMO_MODE`, `POST /api/auth/google` devuelve 404. El frontend no carga el script de Google |
| Datos ficticios | `app/demo.py`: colecciones generadas en forma determinista (semilla fija) sobre el catálogo real de 980 figuritas. Coleccionistas `collector-<slug>@collector.demo.invalid`, públicos, sin teléfono ni email |
| Privacidad entre visitantes | El perfil del visitante es de solo lectura (`PATCH /api/profile` → 403) y nunca es público. Cerca e Intercambios solo muestran coleccionistas ficticios |
| Reinicio | Los sandboxes vencen a las 6 h (`purge` horario). Reset diario completo (`reset`): borra visitantes y regenera coleccionistas. "Reiniciar demo" y "Terminar demo" reemplazan o borran el sandbox al instante |
| Abuso | Límite en la app: 10 sandboxes cada 10 min por IP y tope global de 300 (evicta los más viejos). Topes de cantidad (20) y notas (280). nginx: 10 r/s en `/api/`, 5/min en `/api/auth/demo`, 20 conexiones por IP, body ≤ 16 KB. systemd: `MemoryMax=200M`, `CPUQuota=50%`. Sin `/docs` ni `/openapi.json` |
| Salvaguarda de datos | `demo_admin.py` exige `DEMO_MODE=true` y **se niega a operar** si la base tiene algún usuario que no sea demo |

## Desarrollo local

```bash
# Backend (desde backend/)
DEMO_MODE=true DATABASE_URL=sqlite:///./demo_local.db python demo_admin.py seed
DEMO_MODE=true DATABASE_URL=sqlite:///./demo_local.db SESSION_SECRET=<32+ caracteres> \
  .venv/Scripts/python -m uvicorn app.main:app --port 8000

# Frontend (desde frontend/)
VITE_DEMO_MODE=true npm run dev        # http://localhost:5173
```

`*.db` está en `.gitignore`. En Windows, compilá con PowerShell (`$env:VITE_BASE="/"`). En Git Bash, MSYS convierte `VITE_BASE=/` en una ruta de Windows; si lo usás, poné `MSYS2_ENV_CONV_EXCL=VITE_BASE`.

## Tests

```bash
cd backend
.venv/Scripts/python -m unittest discover -s tests -v    # Windows
.venv/bin/python -m unittest discover -s tests -v        # Linux
```

Los 25 tests de `tests/test_demo.py` corren sobre una base SQLite temporal y cubren:
- acceso sin Google;
- álbum precargado y desglose de estados (539 + 429 + 12 = 980; 168 repetidas como copias extra);
- aislamiento entre visitantes;
- que los cruces coincidan con intersecciones calculadas en el test desde los datos crudos;
- que no haya links de WhatsApp ni email;
- topes, rate limit y evicción;
- purga, reset y cookie vieja;
- salvaguarda contra bases reales.

## Despliegue (pendiente de autorización)

Plantillas en `deploy/demo/`, **sin instalar**:

| Archivo | Destino |
|---|---|
| `stickercontrol-demo.service` | `/etc/systemd/system/` |
| `stickercontrol-demo-{purge,reset}.{service,timer}` | `/etc/systemd/system/` |
| `stickercontrol-demo.nginx.conf` | `/etc/nginx/sites-available/stickercontrol-demo` |
| `stickercontrol-demo-ratelimit.conf` | `/etc/nginx/conf.d/` |
| `stickercontrol-demo-security-headers.conf` | `/etc/nginx/snippets/` |
| `demo.env.example` | `/var/www/stickercontrol-demo/.env` (600, secretos nuevos) |

Estructura en el VPS, mismo patrón que turismo-demo:

```
/var/www/stickercontrol-demo/
├── app/           código (git archive de un commit de demo-roura) + backend/.venv
├── builds/<commit>/   build del frontend
├── public -> builds/<commit>
├── data/demo.db   única carpeta escribible por el servicio
└── .env
```
