from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.error import TelegramError
from PIL import Image, ImageDraw, ImageFont
import random
import locale
from datetime import datetime
import re

# Establecer el idioma a español de Colombia
locale.setlocale(locale.LC_TIME, 'es_CO.UTF-8')

# Token de Telegram
TOKEN = "7580157690:AAGxiHxtjeN8h6DQL4ajfnXFWkXTMgTPrag"
# Nombre del canal público
CANAL_PRINCIPAL = "@nqcash"
# Enlace de invitación al canal público
ENLACE_INVITACION = "https://t.me/NqCash"

# Horario de funcionamiento (en formato 24 horas)
HORA_INICIO = 0  # 12:00 AM
HORA_FIN = 24    # 12:00 AM (24 horas)

# Estados de la conversación
MENU, NOMBRE, NOMBRE_COMPLETO, CUENTA, MONTO = range(5)

# Colores de la fuente
COLOR_TEXTO = (27, 3, 27)      # Hex: #1b031b para nombres y montos positivos
COLOR_NEGATIVO = (218, 0, 129) # Hex: #da0081 para montos negativos

# Fuentes
FONT_PATH = "Manrope-Regular.ttf"      # Fuente regular para nombres y comprobante
FONT_PATH_BOLD = "Manrope-Bold.ttf"    # Fuente en negrita para montos en movimientos

# Tamaños de fuente para comprobante
FONT_SIZE_COMPROBANTE = 75             # Tamaño para comprobante
FONT_SIZE_MENOR_COMPROBANTE = 50       # Tamaño menor para ",00" (no usado aún en comprobante)

# Tamaños de fuente para movimientos
FONT_SIZE_NOMBRES_MOVIMIENTOS = 75     # Tamaño para nombres en movimientos
FONT_SIZE_MONTOS_MOVIMIENTOS = 75      # Tamaño para montos principales en movimientos
FONT_SIZE_MENOR_MOVIMIENTOS = 55       # Tamaño menor para ",00" en movimientos

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
    (270, 2820), # Nombre 6
]

POSICIONES_MONTOS = [
    (1500, 950),  # Monto 1 (negativo del usuario)
    (1500, 1320), # Monto 2 (positivo aleatorio)
    (1500, 1710), # Monto 3 (positivo aleatorio)
    (1500, 2110), # Monto 4 (negativo aleatorio)
    (1500, 2480), # Monto 5 (positivo aleatorio)
    (1500, 2850), # Monto 6 (negativo aleatorio)
]

# Margen derecho para montos (definido como MARGEN_DERECHO)
MARGEN_DERECHO = 130

# Teclado persistente con botón "Menú"
REPLY_KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("Menú")]],
    resize_keyboard=True,
    is_persistent=True
)

# Cargar nombres y apellidos desde archivos .txt
def cargar_lista(archivo):
    with open(archivo, "r", encoding="utf-8") as f:
        return [linea.strip() for linea in f.readlines()]

NOMBRES_H = cargar_lista("nombres_h.txt")
NOMBRES_M = cargar_lista("nombres_m.txt")
APELLIDOS = cargar_lista("apellidos.txt")

# Función para verificar si el usuario está en el canal público
async def usuario_en_chat(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: str) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        status = member.status
        print(f"Verificando {user_id} en {chat_id}: status={status}")
        return status in ['member', 'administrator', 'creator']
    except TelegramError as e:
        print(f"Error al verificar {user_id} en {chat_id}: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Usuario sin @"

    # Verificar horario
    hora_actual = datetime.now().hour
    if not (HORA_INICIO <= hora_actual < HORA_FIN):
        await update.message.reply_text(
            f"Lo siento, este bot solo está disponible de {HORA_INICIO}:00 a {HORA_FIN}:00. Vuelve en ese horario."
        )
        return ConversationHandler.END

    # Verificar membresía en el canal oficial
    if not await usuario_en_chat(context, user_id, CANAL_PRINCIPAL):
        await update.message.reply_text(
            f"@{username}, debes estar suscrito al canal oficial {CANAL_PRINCIPAL} para usar este bot. Únete aquí: {ENLACE_INVITACION}",
            reply_markup=REPLY_KEYBOARD
        )
        print(f"@{username} no está en el canal {CANAL_PRINCIPAL}")
        return ConversationHandler.END

    # Mensaje de bienvenida con menú
    mensaje_bienvenida = (
        "Bienvenido a NqCash\n"
        "Aquí se generan comprobantes de NEQUI\n\n"
        "📌 1: Nequi Normal\n"
        "📌 2: Nequi + Movimientos\n"
        "📌 3: Nequi Pagos QR (Próximamente)\n"
        "📌 4: Transfiya + Movimientos (Próximamente)\n\n"
        f"Únete a nuestro canal {CANAL_PRINCIPAL} para más beneficios: {ENLACE_INVITACION}\n"
        "Elige una opción ingresando un número (1-4):"
    )
    await update.message.reply_text(mensaje_bienvenida, reply_markup=REPLY_KEYBOARD)
    return MENU

async def mostrar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Usuario sin @"

    # Verificar horario
    hora_actual = datetime.now().hour
    if not (HORA_INICIO <= hora_actual < HORA_FIN):
        await update.message.reply_text(
            f"Lo siento, este bot solo está disponible de {HORA_INICIO}:00 a {HORA_FIN}:00. Vuelve en ese horario."
        )
        return ConversationHandler.END

    # Verificar membresía en el canal oficial
    if not await usuario_en_chat(context, user_id, CANAL_PRINCIPAL):
        await update.message.reply_text(
            f"@{username}, debes estar suscrito al canal oficial {CANAL_PRINCIPAL} para usar este bot. Únete aquí: {ENLACE_INVITACION}",
            reply_markup=REPLY_KEYBOARD
        )
        return ConversationHandler.END

    # Mostrar menú
    mensaje_bienvenida = (
        "Bienvenido a NqCash\n"
        "Aquí se generan comprobantes de NEQUI\n\n"
        "📌 1: Nequi Normal\n"
        "📌 2: Nequi + Movimientos\n"
        "📌 3: Nequi Pagos QR (Próximamente)\n"
        "📌 4: Transfiya + Movimientos (Próximamente)\n\n"
        "Elige una opción ingresando un número (1-4):"
    )
    await update.message.reply_text(mensaje_bienvenida, reply_markup=REPLY_KEYBOARD)
    return MENU

async def elegir_opcion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Usuario sin @"

    # Verificar membresía en el canal oficial
    if not await usuario_en_chat(context, user_id, CANAL_PRINCIPAL):
        await update.message.reply_text(
            f"@{username}, debes estar suscrito al canal oficial {CANAL_PRINCIPAL} para usar este bot. Únete aquí: {ENLACE_INVITACION}",
            reply_markup=REPLY_KEYBOARD
        )
        return ConversationHandler.END

    opcion = update.message.text
    context.user_data["opcion"] = opcion  # Guardar la opción elegida
    if opcion == "1":
        await update.message.reply_text("Has elegido 'Nequi Normal'. Ingresa tu nombre:", reply_markup=REPLY_KEYBOARD)
        return NOMBRE
    elif opcion == "2":
        await update.message.reply_text("Has elegido 'Nequi + Movimientos'. Ingresa tu nombre (para el comprobante):", reply_markup=REPLY_KEYBOARD)
        return NOMBRE
    elif opcion == "3":
        await update.message.reply_text("Opción 'Nequi Pagos QR' estará disponible próximamente. Usa 'Menú' para volver.", reply_markup=REPLY_KEYBOARD)
        return ConversationHandler.END
    elif opcion == "4":
        await update.message.reply_text("Opción 'Transfiya + Movimientos' estará disponible próximamente. Usa 'Menú' para volver.", reply_markup=REPLY_KEYBOARD)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Opción inválida. Ingresa un número entre 1 y 4:", reply_markup=REPLY_KEYBOARD)
        return MENU

async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Usuario sin @"

    # Verificar membresía en el canal oficial
    if not await usuario_en_chat(context, user_id, CANAL_PRINCIPAL):
        await update.message.reply_text(
            f"@{username}, debes estar suscrito al canal oficial {CANAL_PRINCIPAL} para usar este bot. Únete aquí: {ENLACE_INVITACION}",
            reply_markup=REPLY_KEYBOARD
        )
        return ConversationHandler.END

    nombre = update.message.text
    if not re.match(r'^[a-zA-Z\s]+$', nombre):
        await update.message.reply_text("El nombre solo puede contener letras y espacios. Intenta de nuevo:", reply_markup=REPLY_KEYBOARD)
        return NOMBRE
    context.user_data["nombre"] = nombre
    if context.user_data["opcion"] == "2":
        await update.message.reply_text("Ahora ingresa tu nombre completo (para los movimientos):", reply_markup=REPLY_KEYBOARD)
        return NOMBRE_COMPLETO
    else:
        await update.message.reply_text("Ahora ingresa el número de cuenta o Nequi (10 dígitos):", reply_markup=REPLY_KEYBOARD)
        return CUENTA

async def recibir_nombre_completo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Usuario sin @"

    # Verificar membresía en el canal oficial
    if not await usuario_en_chat(context, user_id, CANAL_PRINCIPAL):
        await update.message.reply_text(
            f"@{username}, debes estar suscrito al canal oficial {CANAL_PRINCIPAL} para usar este bot. Únete aquí: {ENLACE_INVITACION}",
            reply_markup=REPLY_KEYBOARD
        )
        return ConversationHandler.END

    nombre_completo = update.message.text
    if not re.match(r'^[a-zA-Z\s]+$', nombre_completo):
        await update.message.reply_text("El nombre completo solo puede contener letras y espacios. Intenta de nuevo:", reply_markup=REPLY_KEYBOARD)
        return NOMBRE_COMPLETO
    context.user_data["nombre_completo"] = nombre_completo
    await update.message.reply_text("Ahora ingresa el número de cuenta o Nequi (10 dígitos):", reply_markup=REPLY_KEYBOARD)
    return CUENTA

async def recibir_cuenta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Usuario sin @"

    # Verificar membresía en el canal oficial
    if not await usuario_en_chat(context, user_id, CANAL_PRINCIPAL):
        await update.message.reply_text(
            f"@{username}, debes estar suscrito al canal oficial {CANAL_PRINCIPAL} para usar este bot. Únete aquí: {ENLACE_INVITACION}",
            reply_markup=REPLY_KEYBOARD
        )
        return ConversationHandler.END

    cuenta = update.message.text
    if not (cuenta.isdigit() and len(cuenta) == 10):
        await update.message.reply_text("El número debe tener exactamente 10 dígitos numéricos. Intenta de nuevo:", reply_markup=REPLY_KEYBOARD)
        return CUENTA
    context.user_data["cuenta"] = cuenta
    await update.message.reply_text("Finalmente, ingresa el monto (solo números sin puntos ni comas):", reply_markup=REPLY_KEYBOARD)
    return MONTO

async def recibir_monto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Usuario sin @"

    # Verificar membresía en el canal oficial
    if not await usuario_en_chat(context, user_id, CANAL_PRINCIPAL):
        await update.message.reply_text(
            f"@{username}, debes estar suscrito al canal oficial {CANAL_PRINCIPAL} para usar este bot. Únete aquí: {ENLACE_INVITACION}",
            reply_markup=REPLY_KEYBOARD
        )
        return ConversationHandler.END

    monto = update.message.text
    if not monto.isdigit():
        await update.message.reply_text("El monto debe ser un número entero sin puntos ni comas. Intenta de nuevo:", reply_markup=REPLY_KEYBOARD)
        return MONTO
    context.user_data["monto"] = monto

    if context.user_data["opcion"] == "1":
        nombre_imagen = generar_imagen_comprobante(context.user_data)
        await update.message.reply_photo(photo=open(nombre_imagen, "rb"))
        await update.message.reply_text(
            "¡Comprobante generado con éxito! Usa 'Menú' para volver a las opciones.",
            reply_markup=REPLY_KEYBOARD
        )
    elif context.user_data["opcion"] == "2":
        nombre_comprobante = generar_imagen_comprobante(context.user_data)
        nombre_movimientos = generar_imagen_movimientos(context.user_data)
        await update.message.reply_photo(photo=open(nombre_comprobante, "rb"))
        await update.message.reply_photo(photo=open(nombre_movimientos, "rb"))
        await update.message.reply_text(
            "¡Comprobante y movimientos generados con éxito! Usa 'Menú' para volver a las opciones.",
            reply_markup=REPLY_KEYBOARD
        )
    return ConversationHandler.END

DESPLAZAMIENTO_X = 103

def generar_imagen_comprobante(datos):
    imagen_base = Image.open("comprobante_bg.png")
    draw = ImageDraw.Draw(imagen_base)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE_COMPROBANTE)  # Fuente regular para comprobante
    ancho_imagen, _ = imagen_base.size

    monto_raw = int(datos['monto'])
    monto = f"$ {monto_raw:,}".replace(",", ".") + ",00"
    fecha_hora = datetime.now().strftime("%d de %B de %Y") + " a"
    hora_actual = datetime.now()
    hora = hora_actual.strftime("%I:%M")
    periodo = "a. m." if hora_actual.hour < 12 else "p. m."
    hora_completa = f"las {hora} {periodo}"
    cuenta_raw = datos["cuenta"]
    cuenta = f"{cuenta_raw[:3]} {cuenta_raw[3:6]} {cuenta_raw[6:]}"
    longitud_referencia = random.randint(6, 9)
    referencia_numero = random.randint(10**(longitud_referencia-1), 10**longitud_referencia - 1)
    referencia = f"M{referencia_numero}"

    textos = {
        "nombre": datos["nombre"],
        "monto": monto,
        "cuenta": cuenta,
        "fecha": fecha_hora,
        "hora": hora_completa,
        "referencia": referencia
    }

    for key, text in textos.items():
        pos_x, pos_y = POSICIONES_COMPROBANTE[key]
        ancho_texto = draw.textbbox((0, 0), text, font=font)[2]
        pos_x = ancho_imagen - ancho_texto - 50 - DESPLAZAMIENTO_X
        draw.text((pos_x, pos_y), text, fill=COLOR_TEXTO, font=font)

    nombre_imagen = "comprobante_generado.png"
    imagen_base.save(nombre_imagen)
    return nombre_imagen

def generar_imagen_movimientos(datos):
    imagen_base = Image.open("movimientos_bg.png")
    draw = ImageDraw.Draw(imagen_base)
    font_normal = ImageFont.truetype(FONT_PATH, FONT_SIZE_NOMBRES_MOVIMIENTOS)      # Regular para nombres
    font_bold = ImageFont.truetype(FONT_PATH_BOLD, FONT_SIZE_MONTOS_MOVIMIENTOS)    # Negrita para montos
    font_menor = ImageFont.truetype(FONT_PATH_BOLD, FONT_SIZE_MENOR_MOVIMIENTOS)    # ",00" en negrita
    ancho_imagen, _ = imagen_base.size

    # Generar 6 movimientos
    movimientos = []

    # 1. Primer movimiento: Negativo con el monto del usuario (Monto 1 - Negativo)
    nombre_usuario = datos["nombre_completo"].upper()
    if len(nombre_usuario) > 21:
        nombre_usuario = nombre_usuario[:21] + "..."
    monto_raw = int(datos['monto'])
    monto_principal = f"-$ {monto_raw:,}".replace(",", ".")
    movimientos.append((nombre_usuario, monto_principal, ",00", True))

    # 2. Cinco movimientos aleatorios con signos fijos
    for i in range(5):
        genero = random.choice(["hombres", "mujeres"])
        nombres = NOMBRES_H if genero == "hombres" else NOMBRES_M
        apellido = random.choice(APELLIDOS).upper()
        if random.choice([True, False]):  # 50% de probabilidad de dos nombres
            nombre1 = random.choice(nombres).upper()
            nombre2 = random.choice([n for n in nombres if n != nombre1]).upper()  # Evitar repetición
            nombre_completo = f"{nombre1} {nombre2} {apellido}"
        else:
            nombre = random.choice(nombres).upper()
            nombre_completo = f"{nombre} {apellido}"
        if len(nombre_completo) > 21:
            nombre_completo = nombre_completo[:21] + "..."
        # Generar monto múltiplo de 100 o 1000
        monto_base = random.randint(10, 500)  # Base entre 10 y 500
        multiplicador = random.choice([100, 1000])  # Multiplicar por 100 o 1000
        monto_raw = monto_base * multiplicador
        # Asignar signo según la posición (índice 0 es Monto 2, índice 3 es Monto 5, etc.)
        es_negativo = i in [2, 4]  # Índices 2 y 4 corresponden a Monto 4 y Monto 6
        monto_principal = f"{'-$' if es_negativo else '$'} {monto_raw:,}".replace(",", ".")
        movimientos.append((nombre_completo, monto_principal, ",00", es_negativo))

    # Dibujar los movimientos en la imagen
    for i, (nombre, monto_principal, decimal, es_negativo) in enumerate(movimientos[:6]):
        # Dibujar el nombre (margen izquierdo)
        pos_x_nombre, pos_y_nombre = POSICIONES_NOMBRES[i]
        draw.text((pos_x_nombre, pos_y_nombre), nombre, fill=COLOR_TEXTO, font=font_normal)

        # Dibujar el monto principal (posición ajustable en X con margen derecho)
        _, pos_y_monto = POSICIONES_MONTOS[i]
        color_monto = COLOR_NEGATIVO if es_negativo else COLOR_TEXTO
        ancho_monto = draw.textbbox((0, 0), monto_principal, font=font_bold)[2]
        ancho_decimal = draw.textbbox((0, 0), decimal, font=font_menor)[2]
        pos_x_monto = ancho_imagen - ancho_monto - ancho_decimal - MARGEN_DERECHO  # Corregido a MARGEN_DERECHO
        draw.text((pos_x_monto, pos_y_monto), monto_principal, fill=color_monto, font=font_bold)

        # Dibujar el ",00" debajo del monto principal, más cerca
        pos_x_decimal = pos_x_monto + ancho_monto
        pos_y_decimal = pos_y_monto + FONT_SIZE_MONTOS_MOVIMIENTOS - 55  # Ajuste fino
        draw.text((pos_x_decimal, pos_y_decimal), decimal, fill=color_monto, font=font_menor)

    nombre_imagen = "movimientos_generado.png"
    imagen_base.save(nombre_imagen)
    return nombre_imagen

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operación cancelada. Usa 'Menú' para volver a las opciones.", reply_markup=REPLY_KEYBOARD)
    return ConversationHandler.END

# Configurar la aplicación de Telegram
app = Application.builder().token(TOKEN).build()

# Configurar el manejador de conversación
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        CommandHandler("menu", mostrar_menu),
        MessageHandler(filters.TEXT & filters.Regex('^Menú$'), mostrar_menu)
    ],
    states={
        MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, elegir_opcion)],
        NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
        NOMBRE_COMPLETO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre_completo)],
        CUENTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cuenta)],
        MONTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_monto)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)

# Iniciar el bot
if __name__ == "__main__":
    print("Bot en ejecución...")
    app.run_polling()