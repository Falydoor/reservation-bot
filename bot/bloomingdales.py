import logging

import requests
from fake_useragent import UserAgent

from bot.base_bot import BaseBot

logger = logging.getLogger(__name__)


class BloomingdalesBot(BaseBot):
    product: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__qualname__ = "Bot.BloomingdalesBot"

    def __call__(self):
        self.check_size_and_color()

    def get_headers(self):
        return {
            "user-agent": str(UserAgent().chrome),
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7,es;q=0.6",
            "sec-ch-ua": '"Google Chrome";v="140", "Chromium";v="140", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "cache-control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
        }

    def check_size_and_color(self):
        r = requests.get(f"https://www.bloomingdales.com/shop/product/{self.product}", headers=self.get_headers())
        if r.status_code != 200:
            logger.info(r.status_code)
            return
        if "Sorry, this item is currently unavailable." not in r.text:
            logger.info("Color available")
            self.notify("Bloomingdales", "Bloomingdale's color available")
