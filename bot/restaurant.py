import datetime as dt
import logging
import re

import requests

from bot.base_bot import BaseBot
from bot.utils import BotException, get_resy_headers, get_hillstone_headers, get_sevenrooms_headers

logger = logging.getLogger("reservation_bot")


class Restaurant(BaseBot):
    id: str = ""
    type: str = "resy"
    days_range: int = 0
    ignore_type: str = ".*(outdoor|patio).*"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__qualname__ = "Bot.Restaurant"

    def __call__(self):
        if self.type == "resy":
            self.get_reservations_resy()
        elif self.type == "sevenrooms":
            self.get_reservations_sevenrooms()
        elif self.type == "hillstone":
            self.get_reservations_hillstone()
        else:
            raise BotException(f"Unknown reservation type {self.type}")

    def call_api(self, url, headers):
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise BotException(
                f"Unable to get {self.type} tables for {self.id} : {response.text} ({response.status_code})")

        return response.json()

    def get_reservations_resy(self):
        # Get days with available slot
        days = [dt.date.today() + dt.timedelta(days=x) for x in
                range(self.days_range)] if self.days_range else self.days
        start_date = dt.date.today().strftime("%Y-%m-%d")
        end_date = max(days).strftime("%Y-%m-%d")
        url = f"https://api.resy.com/4/venue/calendar?venue_id={self.id}&num_seats={self.party_size}&start_date={start_date}&end_date={end_date}"
        response_json = self.call_api(url, get_resy_headers())

        # Set available days
        scheduled_days = [
            dt.date.fromisoformat(schedule["date"])
            for schedule in response_json["scheduled"]
            if schedule["inventory"]["reservation"] == "available"
        ]

        # Iterate days
        for day in [day for day in days if day in scheduled_days]:
            logger.info("REST call for %s (%s)", day, self.id)
            day_str = day.strftime("%Y-%m-%d")
            url = f"https://api.resy.com/4/find?lat=0&long=0&day={day_str}&party_size={self.party_size}&venue_id={self.id}"
            response_json = self.call_api(url, get_resy_headers())

            # Iterate slots
            for venue in response_json["results"]["venues"]:
                for slot in venue["slots"]:
                    slot_datetime = dt.datetime.fromisoformat(slot["date"]["start"])
                    reservation = {
                        "name": f"{venue['venue']['name']} for {slot['size']['min']}+ : {slot_datetime} ({slot['config']['type']})",
                        "datetime": slot_datetime,
                        "party_size_min": slot["size"]["min"],
                        "party_size_max": slot["size"]["max"],
                    }
                    logger.info(reservation["name"])

                    skip = False

                    # Skip type
                    if not skip and re.match(
                            self.ignore_type,
                            slot["config"]["type"],
                            re.IGNORECASE,
                    ):
                        skip = True

                    self.notify(reservation, skip)

    def get_reservations_hillstone(self):
        for day in self.days:
            search_ts = int(
                dt.datetime.combine(day, dt.time(self.hour_start)).timestamp() * 1000
            )
            url = f"https://loyaltyapi.wisely.io/v2/web/reservations/inventory?merchant_id={self.id}&party_size={self.party_size}&search_ts={search_ts}&show_reservation_types=1&limit=5"
            response_json = self.call_api(url, get_hillstone_headers())

            # Iterate slots
            for reservation_type in response_json["types"]:
                for slot in reservation_type["times"]:
                    slot_datetime = dt.datetime.fromtimestamp(
                        slot["reserved_ts"] / 1000
                    )
                    reservation = {
                        "name": f"Hillstone for {slot['min_party_size']}+ : {slot_datetime}",
                        "datetime": slot_datetime,
                        "party_size_min": slot['min_party_size'],
                        "party_size_max": slot['max_party_size'],
                    }

                    self.notify(reservation)

    def get_reservations_sevenrooms(self):
        for day in self.days:
            day_str = day.strftime("%m-%d-%Y")
            url = f"https://www.sevenrooms.com/api-yoa/availability/widget/range?venue={self.id}&time_slot={self.hour_start}:00&party_size={self.party_size}&halo_size_interval=16&start_date={day_str}&num_days=1&channel=SEVENROOMS_WIDGET&selected_lang_code=en"
            response_json = self.call_api(url, get_sevenrooms_headers())

            # Iterate slots
            for types in response_json["data"]["availability"].get(day_str, []):
                if types.get("shift_category") == "BRUNCH":
                    for time in types["times"]:
                        if "cost" in time:
                            slot_datetime = dt.datetime.fromisoformat(time['real_datetime_of_slot'])
                            reservation = {
                                "name": f"{time['public_time_slot_description']} for {self.party_size}+ : {slot_datetime}",
                                "datetime": slot_datetime,
                                "party_size_min": self.party_size,
                                "party_size_max": self.party_size,
                            }

                            self.notify(reservation)
