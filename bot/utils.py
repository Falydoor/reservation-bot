import smtplib
import ssl
from email.mime.text import MIMEText


class BotException(Exception):
    pass


class Mail:
    def __init__(self):
        self.port = 465
        self.smtp_server_domain_name = "smtp.gmail.com"
        self.sender_mail = "EMAIL"
        self.password = ""

    def send(self, subject, content, to):
        self.send_mail(
            subject,
            content,
            to,
        )

    def send_mail(self, subject, content, to):
        ssl_context = ssl.create_default_context()
        service = smtplib.SMTP_SSL(
            self.smtp_server_domain_name, self.port, context=ssl_context
        )
        service.login(self.sender_mail, self.password)
        msg = MIMEText(content)
        msg["Subject"] = subject
        msg["To"] = ", ".join(to)
        msg["From"] = self.sender_mail
        service.send_message(msg)
        service.quit()


I_SODI = "443"
FOUR_CHARLES = "834"
CARBONE = "6194"
DON_ANGIE = "1505"
SAN_SABINO = "78799"
TWELVE_CHAIRS = "4994"
RAOULS = "7241"
TORRISI = "64593"
DOUBLE_CHICKEN = "42534"
THE_NINES = "7490"
CI_SIAMO = "54724"
LARTUSI = "25973"
THAI_VILLA = "52944"
PRANAKHON = "66711"
BLUE_BOX = "70161"
MONKEY_BAR = "60058"
SADELLE = "29967"
KEENS = "3413"
COTE = "72271"
VIA_CAROTTA = "2567"
LILLIA = "418"
LASER_WOLF = "58848"
SHUKETTE = "8579"
AU_CHEVAL = "5769"
MINETTA_TAVERN = "9846"
SHMONE = "59072"
