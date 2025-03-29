# Tamaños de fuente para movimientos
FONT_SIZE_NOMBRES_MOVIMIENTOS = 80     # Tamaño para nombres en movimientos
FONT_SIZE_MONTOS_MOVIMIENTOS = 80     # Tamaño para montos principales en movimientos
FONT_SIZE_MENOR_MOVIMIENTOS = 70       # Tamaño menor para ",00" en movimientos

# Posiciones de los textos en la imagen del comprobante
POSICIONES_COMPROBANTE = {
    "nombre": (1400, 1600),
    "monto": (1400, 1785),
    "cuenta": (1400, 1970),
    "fecha": (1400, 2150),
    "referencia": (1400, 2430),
    "hora": (1400, 2240)
}

# Posiciones para movimientos_bg (nombres a la izquierda, montos con X ajustable)
POSICIONES_NOMBRES = [
    (270, 920),  # Nombre 1 (usuario)
    (270, 1290), # Nombre 2
    (270, 1680), # Nombre 3
    (270, 2080), # Nombre 4
    (270, 2450), # Nombre 5
    (270, 2820), # Nombre 6 (nuevo)
]

POSICIONES_MONTOS = [
    (1500, 950),  # Monto 1 (negativo del usuario)
    (1500, 1320), # Monto 2 (negativo aleatorio)
    (1500, 1710), # Monto 3 (negativo aleatorio)
    (1500, 2110), # Monto 4 (positivo aleatorio)
    (1500, 2480), # Monto 5 (positivo aleatorio)
    (1500, 2850), # Monto 6 (positivo o negativo aleatorio)