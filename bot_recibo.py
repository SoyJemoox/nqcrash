import logging
import random
import datetime
import locale
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from PIL import Image, ImageDraw, ImageFont  # Para generar el recibo en imagen

# Configuración del logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Estados del bot
ESPERANDO_NOMBRE, ESPERANDO_CUENTA, ESPERANDO_MONTO = range(3)

# Token del bot de Telegram
TOKEN = "TU_TOKEN_AQUI"

# Configuración de localización para que los meses estén en español
try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")  # Linux/Mac
except:
    try:
        locale.setlocale(locale.LC_TIME, "es-CO")  # Windows
    except:
        pass  # Si no funciona, seguirá con la configuración predeterminada

# Variable para controlar si el usuario está ingresando datos
ingresando_datos = False

# Función para generar una referencia única
def generar_referencia():
    numero = random.randint(100000, 99999999)  # Genera un número aleatorio de 6 a 8 dígitos
    return f"M{numero}"

# Función para generar la imagen del recibo
def generar_imagen_recibo(datos):
    # Cargar la imagen base
    imagen_base = Image.open("recibo_base.png")  # Imagen de fondo del recibo
    draw = ImageDraw.Draw(imagen_base)

    # Cargar una fuente (usa una fuente TrueType, por ejemplo "arial.ttf")
    try:
        fuente = ImageFont.truetype("arial.ttf", 30)  # Ajusta el tamaño según necesites
    except:
        fuente = ImageFont.load_default()  # Usa una fuente predeterminada si no encuentra la fuente TTF

    # Coordenadas para escribir los datos en la imagen
    draw.text((100, 100), f"Nombre: {datos['nombre']}", fill="black", font=fuente)
    draw.text((100, 150), f"Cuenta: {datos['cuenta']}", fill="black", font=fuente)
    draw.text((100, 200), f"Monto: {datos['monto']}", fill="black", font=fuente)
    draw.text((100, 250), f"Fecha: {datos['hora']}", fill="black", font=fuente)
    draw.text((100, 300), f"Referencia: {datos['referencia']}", fill="black", font=fuente)

    # Guardar la imagen generada
    nombre_imagen = "recibo_generado.png"
    imagen_base.save(nombre_imagen)
    return nombre_imagen

# Función que inicia el bot
async def start(update: Update, context: CallbackContext) -> None:
    global ingresando_datos
    ingresando_datos = False  # Reiniciar estado
    keyboard = [["Generar Recibo"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "¡Bienvenido al generador de recibos! 📄\n\nPresiona el botón para generar un recibo.",
        reply_markup=reply_markup
    )

# Función que inicia el proceso de generación de recibo
async def generar_recibo(update: Update, context: CallbackContext) -> int:
    global ingresando_datos
    if ingresando_datos:
        await update.message.reply_text("⚠️ Ya estás generando un recibo. Termina antes de iniciar otro.")
        return ConversationHandler.END

    ingresando_datos = True
    await update.message.reply_text("Por favor, envía tu nombre y apellido:")
    return ESPERANDO_NOMBRE

# Recibe el nombre
async def recibir_nombre(update: Update, context: CallbackContext) -> int:
    context.user_data["nombre"] = update.message.text
    await update.message.reply_text("Ahora ingresa el número de cuenta (10 dígitos):")
    return ESPERANDO_CUENTA

# Recibe el número de cuenta
async def recibir_cuenta(update: Update, context: CallbackContext) -> int:
    cuenta = update.message.text
    if not cuenta.isdigit() or len(cuenta) != 10:
        await update.message.reply_text("⚠️ El número de cuenta debe contener exactamente 10 dígitos.")
        return ESPERANDO_CUENTA

    context.user_data["cuenta"] = cuenta
    await update.message.reply_text("Por favor, ingresa el monto (sin puntos ni comas):")
    return ESPERANDO_MONTO

# Recibe el monto y genera el recibo
async def recibir_monto(update: Update, context: CallbackContext) -> int:
    global ingresando_datos
    monto = update.message.text
    if not monto.isdigit():
        await update.message.reply_text("⚠️ El monto debe ser un número válido.")
        return ESPERANDO_MONTO

    # Formatear monto con puntos de mil y sin espacio entre "$" y el número
    monto_formateado = f"${int(monto):,}".replace(",", ".")

    # Obtener fecha y hora en formato solicitado
    fecha_actual = datetime.datetime.now()
    fecha_formateada = fecha_actual.strftime("%d de %B de %Y a las %I:%M %p")
    fecha_formateada = fecha_formateada.replace("AM", "a. m.").replace("PM", "p. m.")

    referencia = generar_referencia()

    datos = {
        "nombre": context.user_data["nombre"],
        "cuenta": context.user_data["cuenta"],
        "monto": monto_formateado,
        "hora": fecha_formateada,
        "referencia": referencia
    }

    # Generar la imagen con los datos
    nombre_imagen = generar_imagen_recibo(datos)

    # Enviar imagen del recibo
    with open(nombre_imagen, "rb") as imagen:
        await update.message.reply_photo(photo=imagen, caption="📄 Recibo generado correctamente.")

    ingresando_datos = False  # Restablecer estado

    # Mostrar nuevamente el botón "Generar Recibo"
    keyboard = [["Generar Recibo"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Puedes generar otro recibo cuando lo necesites. 📜", reply_markup=reply_markup)

    return ConversationHandler.END

# Cancelar el proceso
async def cancelar(update: Update, context: CallbackContext) -> int:
    global ingresando_datos
    ingresando_datos = False
    await update.message.reply_text("🚫 Operación cancelada.")
    return ConversationHandler.END

# Función principal
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(Generar Recibo)$"), generar_recibo)],
        states={
            ESPERANDO_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
            ESPERANDO_CUENTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cuenta)],
            ESPERANDO_MONTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_monto)],
        },
        fallbacks=[CommandHandler("cancel", cancelar)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
