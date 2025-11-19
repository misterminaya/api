import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

# Email configuration from environment variables
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM=os.getenv("MAIL_FROM", "noreply@example.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Movie Reviews API"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)


async def send_otp_email(email: str, username: str, otp_code: str):
    """Send OTP verification email to user"""

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Verificacion de cuenta</h2>
            <p>Hola <strong>{username}</strong>,</p>
            <p>Gracias por registrarte en Movie Reviews API.</p>
            <p>Tu codigo de verificacion es:</p>
            <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 24px; letter-spacing: 5px; margin: 20px 0;">
                <strong>{otp_code}</strong>
            </div>
            <p>Este codigo expira en <strong>10 minutos</strong>.</p>
            <p>Si no solicitaste este codigo, puedes ignorar este correo.</p>
            <br>
            <p>Saludos,<br>El equipo de Movie Reviews API</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Codigo de verificacion - Movie Reviews API",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html
    )

    await fm.send_message(message)


async def send_welcome_email(email: str, username: str):
    """Send welcome email after successful registration"""

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Bienvenido a Movie Reviews API!</h2>
            <p>Hola <strong>{username}</strong>,</p>
            <p>Tu cuenta ha sido verificada exitosamente.</p>
            <p>Ahora puedes:</p>
            <ul>
                <li>Iniciar sesion en tu cuenta</li>
                <li>Crear resenas de peliculas</li>
                <li>Ver resenas de otros usuarios</li>
            </ul>
            <p>Gracias por unirte a nuestra comunidad!</p>
            <br>
            <p>Saludos,<br>El equipo de Movie Reviews API</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Registro exitoso - Bienvenido a Movie Reviews API",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html
    )

    await fm.send_message(message)


async def resend_otp_email(email: str, username: str, otp_code: str):
    """Resend OTP verification email"""

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Nuevo codigo de verificacion</h2>
            <p>Hola <strong>{username}</strong>,</p>
            <p>Has solicitado un nuevo codigo de verificacion.</p>
            <p>Tu nuevo codigo es:</p>
            <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 24px; letter-spacing: 5px; margin: 20px 0;">
                <strong>{otp_code}</strong>
            </div>
            <p>Este codigo expira en <strong>10 minutos</strong>.</p>
            <p>Si no solicitaste este codigo, puedes ignorar este correo.</p>
            <br>
            <p>Saludos,<br>El equipo de Movie Reviews API</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Nuevo codigo de verificacion - Movie Reviews API",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html
    )

    await fm.send_message(message)
