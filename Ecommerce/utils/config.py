from fastapi_mail import ConnectionConfig
import os
from dotenv import load_dotenv
load_dotenv()


MAIL = os.getenv("MAIL")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
conf = ConnectionConfig(
    MAIL_USERNAME=MAIL,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM="donharsh1011@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

