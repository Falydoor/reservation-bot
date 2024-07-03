import smtplib
import ssl
from email.mime.text import MIMEText


class BotException(Exception):
    pass


class Mail:
    def __init__(self):
        self.port = "465"
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


def get_headers():
    return {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "accept-language": "en-US,en;q=0.9",
        "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "cache-control": "no-cache",
    }


def get_resy_headers():
    return get_headers() | {
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "accept": "application/json, text/plain, */*",
        "authorization": 'ResyAPI api_key="VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"',
        "sec-fetch-site": "same-site",
        "x-origin": "https://resy.com",
        "referer": "https://resy.com/",
        "origin": "https://resy.com",
    }


def get_hillstone_headers():
    return get_headers() | {
        "accept": "application/json, text/plain, */*",
        "origin": "https://reservations.getwisely.com",
        "referer": "https://reservations.getwisely.com/",
        "sec-fetch-site": "cross-site",
    }


def get_sevenrooms_headers():
    return get_headers() | {
        "authority": "www.sevenrooms.com",
        "accept": "*/*",
        "sec-fetch-site": "same-site",
        "referer": "https://www.sevenrooms.com/reservations/noburestaurantshoreditch",
        "cookie": "csrftoken=faopNzAoETCqEK2xEVIbcWR9Cr6A7pgq; G_AUTH2_MIGRATION=enforced; __stripe_mid=165dc533-329f-4706-81be-b4e9a7ee18915e0353; __stripe_sid=f313669e-b0bc-43b7-bdbb-57a8144761504fc6d8",
    }


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
