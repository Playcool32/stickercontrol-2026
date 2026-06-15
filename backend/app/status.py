"""
Reglas de estado de una figurita en la coleccion de un usuario.

    quantity=0, is_pasted=False  -> FALTANTE
    quantity>=1, is_pasted=False -> DISPONIBLE_PARA_PEGAR
    is_pasted=True, quantity=0   -> PEGADA_SIN_REPETIDA
    is_pasted=True, quantity>=1  -> PEGADA_CON_REPETIDA

Repetidas:
    is_pasted=True  -> repetidas = quantity
    is_pasted=False -> repetidas = max(quantity - 1, 0)
"""

FALTANTE = "FALTANTE"
DISPONIBLE_PARA_PEGAR = "DISPONIBLE_PARA_PEGAR"
PEGADA_SIN_REPETIDA = "PEGADA_SIN_REPETIDA"
PEGADA_CON_REPETIDA = "PEGADA_CON_REPETIDA"


def compute_status(quantity: int, is_pasted: bool) -> str:
    if is_pasted:
        return PEGADA_CON_REPETIDA if quantity >= 1 else PEGADA_SIN_REPETIDA
    return DISPONIBLE_PARA_PEGAR if quantity >= 1 else FALTANTE


def compute_repetidas(quantity: int, is_pasted: bool) -> int:
    if is_pasted:
        return quantity
    return max(quantity - 1, 0)
