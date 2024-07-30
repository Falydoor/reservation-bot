import datetime as dt
import logging

import requests
from bs4 import BeautifulSoup

from bot.base_bot import BaseBot
from bot.utils import BotException

logger = logging.getLogger()


class GolfBot(BaseBot):
    type: str = "harborlinks"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__qualname__ = "Bot.Golf"

    def __call__(self):
        if self.type == "harborlinks":
            self.get_reservations_harborlinks()
        else:
            raise BotException(f"Unknown reservation type {self.type}")

    def get_reservations_harborlinks(self):
        for day in self.days:
            day_str = day.strftime("%m/%d/%Y")
            data_raw = f"CriteriaDate={day_str}&date={day_str}&CriteriaTime={self.hour_start}:00+AM&NumberOfPlayers={self.party_size}&Holes=18&Criteria.Facilities.Count=3&Facilities[0].IsChecked=true&Facilities[0].IsChecked=false&Facilities[0].FacilityID=24d73934-5205-4b14-b1cc-1f7daeb919a4&Facilities[0].ConsoleFacilityID=baf38b57-7a39-42ce-ab35-9f40bc7d5de8&Facilities[0].IsFavorite=False&Facilities[1].IsChecked=false&Facilities[1].FacilityID=e6b9aa2b-92ca-4021-af9b-9696ea9ddbfc&Facilities[1].ConsoleFacilityID=5f569fa1-d03a-4854-8a8c-44cc2c83fe84&Facilities[1].IsFavorite=False&Facilities[2].IsChecked=false&Facilities[2].FacilityID=73cf891c-d49d-49e1-820c-63f226440534&Facilities[2].ConsoleFacilityID=04266ec3-23b4-4b7d-8f12-c80e66e38f38&Facilities[2].IsFavorite=False&X-Requested-With=XMLHttpRequest"
            headers = {"content-type": "application/x-www-form-urlencoded"}
            response = requests.post(
                "https://www.goibsvision.com/WebRes/Club/harborlinks/BrowseTeeTimes",
                data=data_raw,
                headers=headers,
            )
            soup = BeautifulSoup(response.text, "html.parser")
            times = soup.find_all("td", {"class": "time"})
            for time in times:
                slot_time = dt.datetime.strptime(time.text, "%I:%M %p").time()
                slot_datetime = dt.datetime.combine(day, slot_time)

                reservation = {
                    "name": f"Harbor Links for {self.party_size}+ : {slot_datetime}",
                    "datetime": slot_datetime,
                    "party_size_min": self.party_size,
                    "party_size_max": self.party_size,
                }

                self.notify(reservation)
