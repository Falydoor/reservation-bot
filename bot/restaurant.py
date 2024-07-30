import abc
import datetime as dt
import logging
from enum import Enum

import requests
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter, Retry

from bot.base_bot import BaseBot

logger = logging.getLogger()


class RestaurantEnum(str, Enum):
    # Resy
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
    # Hillstone
    HILLSTONE = "278278"
    # SevenRooms
    NOBU_SHOREDITCH = "noburestaurantshoreditch"


class RestaurantBot(BaseBot):
    restaurant: RestaurantEnum

    def __call__(self):
        if self.tries % 50 == 0:
            logger.info("Try N°%s for %s", self.tries + 1, self.restaurant.name)
        self.tries += 1
        self.get_reservations()

    @abc.abstractmethod
    def get_reservations(self):
        pass

    def get_headers(self):
        return {
            "user-agent": str(UserAgent().chrome),
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

    def call_api(self, url, params):
        s = requests.Session()
        retries = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502])
        s.mount('https://', HTTPAdapter(max_retries=retries))
        try:
            return s.get(url, params=params, headers=self.get_headers()).json()
        except requests.exceptions.RetryError:
            logger.error("Max retries exceeded for %s", self.restaurant.name)
            return {}
        except requests.exceptions.RequestException as e:
            logger.error("Unable to get %s tables for %s : %s (%i)",
                         self.type,
                         self.restaurant.name,
                         e.response.text,
                         e.response.status_code)
            return {}


class ResyBot(RestaurantBot):
    days_range: int = 0
    ignore_type: str = ".*(outdoor|patio).*"
    last_check: dt.datetime = dt.datetime.now() - dt.timedelta(days=1)
    interval_check: dt.timedelta = dt.timedelta(seconds=5)

    def get_headers(self):
        return super().get_headers() | {
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "accept": "application/json, text/plain, */*",
            "authorization": 'ResyAPI api_key="VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"',
            "sec-fetch-site": "same-site",
            "x-origin": "https://resy.com",
            "referer": "https://resy.com/",
            "origin": "https://resy.com",
        }

    def get_reservations(self):
        # Get days with available slot
        days = [dt.date.today() + dt.timedelta(days=x) for x in
                range(self.days_range)] if self.days_range else self.days
        params = {
            "venue_id": self.restaurant.value,
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
            params = {
                "lat": 0,
                "long": 0,
                "day": day.strftime("%Y-%m-%d"),
                "party_size": self.party_size,
                "venue_id": self.restaurant.value
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


class SevenRoomsBot(RestaurantBot):
    def get_headers(self):
        return super().get_headers() | {
            "authority": "www.sevenrooms.com",
            "accept": "*/*",
            "sec-fetch-site": "same-site",
            "referer": f"https://www.sevenrooms.com/reservations/{self.restaurant.value}",
            "cookie": ";".join(["csrftoken=faopNzAoETCqEK2xEVIbcWR9Cr6A7pgq",
                                "G_AUTH2_MIGRATION=enforced",
                                "__stripe_mid=165dc533-329f-4706-81be-b4e9a7ee18915e0353",
                                "__stripe_sid=f313669e-b0bc-43b7-bdbb-57a8144761504fc6d8"])
        }

    def get_reservations(self):
        for day in self.days:
            day_str = day.strftime("%m-%d-%Y")
            params = {
                "venue": self.restaurant.value,
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
            for types in response_json.get("data", {}).get("availability", {}).get(day.strftime("%Y-%m-%d"), []):
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


class HillStoneBot(RestaurantBot):
    def get_headers(self):
        return super().get_headers() | {
            "accept": "application/json, text/plain, */*",
            "origin": "https://reservations.getwisely.com",
            "referer": "https://reservations.getwisely.com/",
            "sec-fetch-site": "cross-site",
        }

    def get_reservations(self):
        for day in self.days:
            params = {
                "merchant_id": self.restaurant.value,
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
