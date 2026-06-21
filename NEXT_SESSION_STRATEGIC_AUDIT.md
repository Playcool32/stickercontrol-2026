# Auditoría estratégica — próxima sesión (2026-06-21)

## 1. Estado actual del proyecto

- Repo limpio (`git status` sin cambios), último commit: `6903be5 docs: release notes and pre-deploy audit for Fase 2B public share`.
- `npm run build` (frontend) y `python -m compileall` (backend) ejecutados ahora mismo: **sin errores, sin warnings**. No hay imports rotos ni deuda de compilación.
- No hay endpoints huérfanos ni componentes sin uso: `routes/trades.py` es un placeholder intencional (`{"implemented": false}`), documentado como tal, no código muerto. Las páginas/componentes frontend existentes corresponden todas a funcionalidad activa.
- **`TODO.md` está desactualizado**: solo llega hasta "Fase 0.6.2" y no refleja que Fase 2A (Google Login) y Fase 2B (share público) ya se implementaron y liberaron. Riesgo de confusión en próximas sesiones si se lee como fuente de verdad.

## 2. Qué quedó terminado

- MVP single-user completo (búsqueda, colección, álbum, faltantes/repetidas con texto WhatsApp).
- Catálogo real (980 figuritas) con fix de orden de grupos H/I/L y código JAP→JPN — **verificado solo en local**.
- "Usuarios cerca" (perfil público + matching + contacto WhatsApp/email), con auditoría forense y fix de privacidad aplicado (B1).
- Login Google multiusuario (Fase 2A): sesión por cookie, aislamiento de datos por usuario, validado por smoke tests con mocks (19/19 OK).
- Link público de solo lectura del álbum (release v1.2 / "Fase 2B" en la nomenclatura de releases — distinto del "Fase 2" de intercambios del TODO).
- Varias rondas de mejoras responsive/mobile, con build OK en cada una.

## 3. Qué quedó pendiente (explícito en los docs)

- **Verificación end-to-end del login Google con credenciales reales** (Client ID real, navegador, local y producción). Nunca se hizo, solo mocks.
- **Confirmación de que `GOOGLE_CLIENT_ID`, `SESSION_SECRET`, `SESSION_COOKIE_SECURE`, `CORS_ORIGINS` están configuradas en el VPS** de skillgames.com.ar. No hay evidencia documental de que esto se haya hecho.
- **Aplicar el fix JAP→JPN y orden de grupos en la base de datos de producción del VPS** — marcado como riesgo crítico en `RELEASE_v1.2_PUBLIC_SHARE.md`, solo aplicado en local hasta ahora.
- **Confirmar que el release v1.2 (share público) está realmente deployado** en skillgames.com.ar — checklist de pre/post-deploy sin marcar.
- Validación visual en Android real de los últimos cambios responsive (P1 + reestructuración) — solo verificado por build, no en dispositivo.
- Sistema de intercambios (Fase 2 del TODO, distinto del "2B" de share): sigue siendo placeholder puro, sin lógica.
- Guardado diferido en `StickerCard` (auditado en `DEFERRED_SAVE_AUDIT.md`, no implementado, requiere decisiones de producto).
- Export/backup descargable de la DB (Fase 3 del TODO).
- Revocar `share_token` (sin UI) y rate limiting en endpoints públicos — riesgos menores señalados, no resueltos.
- **"Carga masiva por selección" / bulk mark country: no aparece mencionada en ninguno de los ~18 documentos del proyecto.** No está diseñada, ni auditada, ni siquiera esbozada — sería trabajo nuevo desde cero.

## 4. Riesgos actuales

- **Riesgo crítico de datos en producción**: si el fix JAP→JPN no se aplicó en el VPS, cualquier usuario real en producción está viendo el álbum con el código de país y orden de grupos incorrectos — esto es visible inmediatamente y daña la primera impresión de alguien que llega desde Reddit.
- **Riesgo de funcionalidad rota silenciosa**: el login Google nunca se probó con credenciales reales. Cosas que los mocks no capturan (cookies `Secure` en HTTPS real, `SameSite`, configuración de CORS, el comportamiento real del popup de Google Identity Services) podrían fallar exactamente en el escenario que más importa: un usuario nuevo intentando entrar por primera vez.
- **Riesgo de que la funcionalidad estrella para validación (share público) no esté ni deployada**: sin esto confirmado, no se puede ejecutar el plan de "mostrarle el álbum a otra persona", que es básicamente el corazón de la validación pedida.
- **Deuda de documentación**: `TODO.md` desincronizado de los releases reales puede llevar a reimplementar o re-auditar algo que ya existe (o, peor, a no encontrar algo que sí está hecho).
- Ningún test automatizado más allá de smoke scripts ad-hoc por feature — no hay red de seguridad ante regresiones al tocar código compartido (p. ej. `get_current_user_id()`).

## 5. Próxima tarea recomendada

**Cerrar el ciclo de verificación/deploy de lo que ya está construido (login Google real + fix JAP/orden de grupos en VPS + confirmar deploy de v1.2), antes de escribir una sola línea de código nueva.**

Concretamente, en este orden:
1. Backup de la DB de producción.
2. Aplicar la migración JAP→JPN + orden de grupos en el VPS.
3. Configurar/confirmar variables de entorno de Google Login en el VPS.
4. Deployar (o confirmar deployado) el frontend+backend de v1.2.
5. Probar en el navegador, con una cuenta de Google real, contra `https://www.skillgames.com.ar/stickercontrol/`: login → marcar unas figuritas → generar link público → abrirlo en otra sesión/incógnito → ver que el álbum se vea bien y con los grupos/JPN correctos.

## 6. Justificación

El objetivo de esta etapa es validar si gente real usaría la app, no agregar funcionalidad. Las dos piezas que convierten esto en algo que "alguien de Reddit" pueda probar ya existen en el código: login multiusuario y link de álbum compartible de solo lectura. Pero **ninguna de las dos está confirmada como funcionando en producción**, y una de ellas (orden de grupos / país Japón) tiene un bug conocido que probablemente sigue visible en el sitio real. Agregar una funcionalidad nueva (como carga masiva) sobre una base no verificada en producción es invertir esfuerzo en algo que el primer usuario real ni va a poder usar correctamente, o que vería con datos visiblemente rotos. La mayor fricción hoy no es "falta de funcionalidad", es "no sabemos si lo que ya existe funciona para un desconocido real".

## 7. Estimación de complejidad

- Verificación/deploy (tarea recomendada): **baja-media**. No requiere código nuevo; requiere acceso al VPS, correr una migración ya escrita y probada localmente, configurar variables de entorno, redeployar y hacer una prueba manual con una cuenta de Google real. Estimado: 1–2 horas, asumiendo acceso SSH/credenciales disponibles. El riesgo principal no es de diseño sino operativo (algo en el entorno real del VPS que no se ve desde local).
- Carga masiva por selección (bulk mark country), para referencia: **media**. Requiere UI nueva (selección múltiple en Buscar o Álbum, acción "marcar todo el país como faltante/disponible"), un endpoint backend de bulk-update, y una confirmación antes de aplicar. Estimado: 3–5 horas. No es complejidad alta, pero es trabajo nuevo no auditado todavía.

## 8. ¿Implementar carga masiva por selección antes de mostrar la app públicamente?

**No.** Recomiendo no implementarla todavía, por dos razones:
- No resuelve la fricción más probable de un primer usuario nuevo (login, ver el álbum, entender qué hacer) — es una mejora de productividad para alguien que ya usa la app a fondo, no un blocker de activación.
- Es más valioso primero soltar la app a un grupo chico de usuarios reales con lo que ya existe (login + share) y ver qué fricción reportan de verdad, que adivinar que "carga masiva" es lo que falta. Si varios usuarios reales se quejan de tener que marcar figurita por figurita, ahí se justifica con evidencia real en vez de intuición.
