import abc
import datetime as dt
import logging

import requests
from requests.adapters import HTTPAdapter, Retry

from bot.base_bot import BaseBot
from bot.utils import get_resy_headers, get_hillstone_headers, get_sevenrooms_headers

logger = logging.getLogger()


class Restaurant(BaseBot):
    id: str = ""

    def __call__(self):
        if self.tries % 50 == 0:
            logger.info("Try N°%s for %s", self.tries + 1, self.id)
        self.tries += 1
        self.get_reservations()

    @abc.abstractmethod
    def get_reservations(self):
        pass

    @abc.abstractmethod
    def get_headers(self):
        pass

    def call_api(self, url, params):
        s = requests.Session()
        retries = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502])
        s.mount('https://', HTTPAdapter(max_retries=retries))
        try:
            return s.get(url, params=params, headers=self.get_headers()).json()
        except requests.exceptions.RetryError:
            logger.error("Max retries exceeded for %s", self.id)
            return {}
        except requests.exceptions.RequestException as e:
            logger.error("Unable to get %s tables for %s : %s (%i)",
                         self.type,
                         self.id,
                         e.response.text,
                         e.response.status_code)
            return {}


class Resy(Restaurant):
    days_range: int = 0
    ignore_type: str = ".*(outdoor|patio).*"
    last_check: dt.datetime = dt.datetime.now() - dt.timedelta(days=1)
    interval_check: dt.timedelta = dt.timedelta(seconds=5)

    def get_headers(self):
        return get_resy_headers()

    def get_reservations(self):
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
            for schedule in response_json.get("scheduled", [])
            if schedule["inventory"]["reservation"] == "available"
        ]

        if (dt.datetime.now() - self.last_check) < self.interval_check:
            return

        # Iterate days
        for day in [day for day in days if day in scheduled_days]:
            logger.info("Checking %s (%s)", day, self.id)
            params = {
                "lat": 0,
                "long": 0,
                "day": day.strftime("%Y-%m-%d"),
                "party_size": self.party_size,
                "venue_id": self.id
            }
            response_json = self.call_api("https://api.resy.com/4/find", params)
            self.last_check = dt.datetime.now()

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


class SevenRooms(Restaurant):
    def get_headers(self):
        return get_sevenrooms_headers()

    def get_reservations(self):
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
                    for slot in types["times"]:
                        if "cost" in slot:
                            slot_datetime = dt.datetime.fromisoformat(slot['real_datetime_of_slot'])
                            reservation = {
                                "name": slot['public_time_slot_description'],
                                "datetime": slot_datetime,
                                "party_size_min": self.party_size,
                                "party_size_max": self.party_size,
                            }

                            self.notify(reservation)


class HillStone(Restaurant):
    def get_headers(self):
        return get_hillstone_headers()

    def get_reservations(self):
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
