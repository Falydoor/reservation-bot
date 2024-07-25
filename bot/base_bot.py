import datetime as dt
import logging
import re
from datetime import date
from queue import Queue
from typing import List

from pydantic import BaseModel, ConfigDict

from bot.utils import Mail

logger = logging.getLogger()


class BaseBot(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    type: str = ""
    party_size: int = 2
    mail_to: List[str] = ["EMAIL"]
    hour_start: int = 19
    hour_end: int = 21
    days: List[date] = [dt.date.today()]
    mailed_reservations: dict = {}
    skipped_reservations: List[str] = []
    queue: Queue
    mail: Mail = Mail()
    tries: int = 0

    def notify(self, reservation, ignore_type=""):
        key = f"{reservation['name']} on {reservation['datetime']} for {reservation['party_size_min']}+"

        skip = False

        # Skip type
        if "type" in reservation and re.match(
                ignore_type,
                reservation["type"],
                re.IGNORECASE,
        ):
            skip = True

        # Skip hours
        if (
                reservation["datetime"].hour < self.hour_start
                or reservation["datetime"].hour > self.hour_end
        ):
            skip = True

        # Skip
        if skip:
            if key not in self.skipped_reservations:
                self.skipped_reservations.append(key)
                logger.info("Found reservation for %s (skipped)", key)
            return

        # Send notification
        if (key not in self.mailed_reservations) or (
                (self.mailed_reservations[key] + dt.timedelta(minutes=5))
                < dt.datetime.now()
        ):
            self.mailed_reservations[key] = dt.datetime.now()
            logger.info("Notification for %s", key)

            # Send Mac notification
            self.queue.put(key)

            # Send email
            self.mail.send(
                key,
                f"Party size : {reservation['party_size_min']}-{reservation['party_size_max']}",
                self.mail_to,
            )
