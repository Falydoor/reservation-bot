import logging

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from bot.base_bot import BaseBot

logger = logging.getLogger(__name__)


class MacysBot(BaseBot):
    product: str
    color: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__qualname__ = "Bot.MacysBot"

    def __call__(self):
        self.check_size_and_color()

    def get_headers(self):
        return {
            "user-agent": str(UserAgent().chrome),
            "accept-language": "en-US,en;q=0.9",
            "sec-ch-ua": '"Google Chrome";v="140", "Chromium";v="140", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "cache-control": "no-cache",
        }

    def check_size_and_color(self):
        r = requests.get(f"https://www.macys.com/shop/product/{self.product}", headers=self.get_headers())
        if r.status_code != 200:
            logger.info(r.status_code)
            return
        soup = BeautifulSoup(r.text, "html.parser")
        colors = soup.find_all("input", attrs={"class": "color-swatch-sprite-radio"})
        for color in colors:
            label = color.get("aria-label")
            if self.color in label.casefold():
                logger.info(label)
                self.notify("Macys", "Macy's color available")
