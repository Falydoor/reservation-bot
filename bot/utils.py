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
