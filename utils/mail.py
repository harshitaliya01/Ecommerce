from random import randint
from fastapi_mail import FastMail, MessageSchema
from utils.config import conf

def generate_otp() -> str:
    return str(randint(100000, 999999))

async def send_otp_email(email: str, otp: str):

    message = MessageSchema(
        subject="Your Verification OTP",
        recipients=[email],
        body=f"Your OTP is: {otp}\nThis OTP will expire in 10 minutes.",
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)