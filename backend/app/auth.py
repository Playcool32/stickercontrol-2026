"""
Autenticacion - placeholder de Fase 0.

En Fase 0 la app es de un solo usuario local (id=1, creado por
database.init_db()). Todas las rutas dependen de get_current_user_id() en
lugar de leer el usuario de una sesion/token, para que en Fase 1 (login con
Google + multiples usuarios) solo haga falta reemplazar esta funcion por una
que decodifique la sesion/JWT real - las rutas no cambian.
"""

DEFAULT_USER_ID = 1


def get_current_user_id() -> int:
    return DEFAULT_USER_ID
