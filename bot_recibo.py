import logging
import random
import datetime
import locale
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

# Configuración del logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Estados del bot
ESPERANDO_NOMBRE, ESPERANDO_CUENTA, ESPERANDO_MONTO = range(3)

# Token del bot de Telegram
TOKEN = "7580157690:AAGlbMF78J1_Y-TWbDizeCMaGT6FAxcwNVE"

# Configuración de localización para formato de fecha en español
locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")  # Para Linux/Mac
# locale.setlocale(locale.LC_TIME, "es-CO")  # En Windows puede ser necesario usar esta opción

# Variable para controlar si el usuario está ingresando datos
ingresando_datos = False

# Función para generar una referencia única
def generar_referencia():
    numero = random.randint(100000, 99999999)  # Genera un número aleatorio de 6 a 8 dígitos
    return f"M{numero}"

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

    # Dar formato de moneda con puntos de mil
    monto_formateado = f"${int(monto):,}".replace(",", ".")

    # Obtener fecha y hora en formato solicitado
    fecha_actual = datetime.datetime.now()
    fecha_formateada = fecha_actual.strftime("%d de %B de %Y a las %I:%M %p").lower()
     # Corregir "AM" y "PM" a "a. m." y "p. m."
    fecha_formateada = fecha_formateada.replace("AM", "a. m.").replace("PM", "p. m.")

    referencia = generar_referencia()

    datos = {
        "nombre": context.user_data["nombre"],
        "cuenta": context.user_data["cuenta"],
        "monto": monto_formateado,
        "hora": fecha_formateada,
        "referencia": referencia
    }

    # Enviar mensaje con la información
    await update.message.reply_text(
        f"📄 *Recibo generado con éxito!*\n\n"
        f"👤 *Nombre:* {datos['nombre']}\n"
        f"🏦 *Cuenta:* {datos['cuenta']}\n"
        f"💰 *Monto:* {datos['monto']}\n"
        f"🕒 *Fecha:* {datos['hora']}\n"
        f"🔢 *Referencia:* {datos['referencia']}",
        parse_mode="Markdown"
    )

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

    # Manejador de conversación
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
