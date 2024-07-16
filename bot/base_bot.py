import datetime as dt
import logging
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

    def notify(self, reservation, skip=False):
        # Skip hours
        if (
                reservation["datetime"].hour < self.hour_start
                or reservation["datetime"].hour > self.hour_end
        ):
            skip = True

        # Skip
        if skip:
            if reservation["name"] not in self.skipped_reservations:
                logger.info(f"Skipped {reservation['name']}")
                self.skipped_reservations.append(reservation["name"])
            return

        # Send notification
        if (reservation["name"] not in self.mailed_reservations) or (
                (self.mailed_reservations[reservation["name"]] + dt.timedelta(minutes=5))
                < dt.datetime.now()
        ):
            self.mailed_reservations[reservation["name"]] = dt.datetime.now()
            logger.info(f"Found reservation : {reservation['name']}")

            # Send Mac notification
            self.queue.put(reservation["name"])

            # Send email
            self.mail.send(
                reservation["name"],
                f"Party size : {reservation['party_size_min']}-{reservation['party_size_max']}",
                self.mail_to,
            )
