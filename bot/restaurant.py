import datetime as dt
import logging

import requests

from bot.base_bot import BaseBot
from bot.utils import BotException, get_resy_headers, get_hillstone_headers, get_sevenrooms_headers

logger = logging.getLogger()


class Restaurant(BaseBot):
    id: str = ""
    type: str = "resy"
    days_range: int = 0
    ignore_type: str = ".*(outdoor|patio).*"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__qualname__ = "Bot.Restaurant"

    def __call__(self):
        if self.tries % 50 == 0:
            logger.info("Try N°%s for %s", self.tries, self.id)
        self.tries += 1
        if self.type == "resy":
            self.get_reservations_resy()
        elif self.type == "sevenrooms":
            self.get_reservations_sevenrooms()
        elif self.type == "hillstone":
            self.get_reservations_hillstone()
        else:
            raise BotException(f"Unknown reservation type {self.type}")

    def get_headers(self):
        if self.type == "resy":
            return get_resy_headers()
        elif self.type == "sevenrooms":
            return get_sevenrooms_headers()
        elif self.type == "hillstone":
            return get_hillstone_headers()
        else:
            raise BotException(f"Unknown reservation type {self.type}")

    def call_api(self, url, params):
        r = requests.get(url, params=params, headers=self.get_headers())
        if r.status_code != 200:
            logger.error("Unable to get %s tables for %s : %s (%i)", self.type, self.id, r.text, r.status_code)
            return {}

        return r.json()

    def get_reservations_resy(self):
        # Get days with available slot
        days = [dt.date.today() + dt.timedelta(days=x) for x in
                range(self.days_range)] if self.days_range else self.days
        params = {
            "venue_id": self.id,
            "num_seats": self.party_size,
            "start_date": dt.date.today().strftime("%Y-%m-%d"),
            "end_date": max(days).strftime("%Y-%m-%d")
        }
        response_json = self.call_api("https://api.resy.com/4/venue/calendar", params)

        # Set available days
        scheduled_days = [
            dt.date.fromisoformat(schedule["date"])
            for schedule in response_json["scheduled"]
            if schedule["inventory"]["reservation"] == "available"
        ]

        # Iterate days
        for day in [day for day in days if day in scheduled_days]:
            logger.info("REST call for %s (%s)", day, self.id)
            params = {
                "lat": 0,
                "long": 0,
                "day": day.strftime("%Y-%m-%d"),
                "party_size": self.party_size,
                "venue_id": self.id
            }
            response_json = self.call_api("https://api.resy.com/4/find", params)

            # Iterate slots
            for venue in response_json.get("results", {}).get("venues", []):
                for slot in venue["slots"]:
                    slot_datetime = dt.datetime.fromisoformat(slot["date"]["start"])
                    reservation = {
                        "name": f"{venue['venue']['name']} ({slot['config']['type']})",
                        "datetime": slot_datetime,
                        "party_size_min": slot["size"]["min"],
                        "party_size_max": slot["size"]["max"],
                        "type": slot["config"]["type"],
                    }

                    self.notify(reservation, self.ignore_type)

    def get_reservations_hillstone(self):
        for day in self.days:
            params = {
                "merchant_id": self.id,
                "party_size": self.party_size,
                "search_ts": int(dt.datetime.combine(day, dt.time(self.hour_start)).timestamp() * 1000),
                "show_reservation_types": 1,
                "limit": 5
            }
            response_json = self.call_api("https://loyaltyapi.wisely.io/v2/web/reservations/inventory", params)

            # Iterate slots
            for reservation_type in response_json.get("types", []):
                for slot in reservation_type["times"]:
                    slot_datetime = dt.datetime.fromtimestamp(
                        slot["reserved_ts"] / 1000
                    )
                    reservation = {
                        "name": "Hillstone",
                        "datetime": slot_datetime,
                        "party_size_min": slot['min_party_size'],
                        "party_size_max": slot['max_party_size'],
                    }

                    self.notify(reservation)

    def get_reservations_sevenrooms(self):
        for day in self.days:
            day_str = day.strftime("%m-%d-%Y")
            params = {
                "venue": self.id,
                "time_slot": f"{self.hour_start}:00",
                "party_size": self.party_size,
                "halo_size_interval": 16,
                "start_date": day_str,
                "num_days": 1,
                "channel": "SEVENROOMS_WIDGET",
                "selected_lang_code": "en"
            }
            response_json = self.call_api("https://www.sevenrooms.com/api-yoa/availability/widget/range", params)

            # Iterate slots
            for types in response_json.get("data", {}).get("availability", {}).get(day_str, []):
                if types.get("shift_category") == "BRUNCH":
                    for time in types["times"]:
                        if "cost" in time:
                            slot_datetime = dt.datetime.fromisoformat(time['real_datetime_of_slot'])
                            reservation = {
                                "name": time['public_time_slot_description'],
                                "datetime": slot_datetime,
                                "party_size_min": self.party_size,
                                "party_size_max": self.party_size,
                            }

                            self.notify(reservation)
