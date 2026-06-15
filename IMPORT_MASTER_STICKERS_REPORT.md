# Reporte de importacion - master_stickers

- Archivo origen: `docs/StickerAlbumWC2026.xlsm`
- Hoja usada: `Stickers`
- CSV generado: `data/stickers_master.csv`
- Codigos detectados (total): **980**

## Cantidad por grupo

| Grupo | Cantidad |
|---|---|
| A | 80 |
| B | 80 |
| C | 80 |
| D | 80 |
| E | 80 |
| F | 80 |
| G | 80 |
| H | 80 |
| I | 80 |
| J | 80 |
| K | 80 |
| L | 80 |
| (especiales) | 20 |

## Cantidad por pais (country_code)

| country_code | Cantidad |
|---|---|
| ALG | 20 |
| ARG | 20 |
| AUS | 20 |
| AUT | 20 |
| BEL | 20 |
| BIH | 20 |
| BRA | 20 |
| CAN | 20 |
| CIV | 20 |
| COD | 20 |
| COL | 20 |
| CPV | 20 |
| CRO | 20 |
| CUW | 20 |
| CZE | 20 |
| ECU | 20 |
| EGY | 20 |
| ENG | 20 |
| ESP | 20 |
| FRA | 20 |
| FWC | 20 |
| GER | 20 |
| GHA | 20 |
| HAI | 20 |
| IRN | 20 |
| IRQ | 20 |
| JAP | 20 |
| JOR | 20 |
| KOR | 20 |
| KSA | 20 |
| MAR | 20 |
| MEX | 20 |
| NED | 20 |
| NOR | 20 |
| NZL | 20 |
| PAN | 20 |
| PAR | 20 |
| POR | 20 |
| QAT | 20 |
| RSA | 20 |
| SCO | 20 |
| SEN | 20 |
| SUI | 20 |
| SWE | 20 |
| TUN | 20 |
| TUR | 20 |
| URU | 20 |
| USA | 20 |
| UZB | 20 |

## Codigos duplicados ignorados

Ninguno.

## Celdas ignoradas (no son codigos de figurita)

Ninguna.

## Filas dudosas / corregidas

| Fila | Columna | Valor original | Codigo corregido | Pais |
|---|---|---|---|---|
| 12 | 18 | `Che16` | `CZE16` | Czech Republic |

El codigo se corrige al prefijo dominante de la fila (el codigo de pais que comparten el resto de las celdas), para que el pais quede con sus 20 figuritas sin huecos.

## Codigos especiales importados

- `00` -> Logo Oficial Mundial 2026
