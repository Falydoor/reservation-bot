import logging
from datetime import datetime, timedelta, date
from queue import Queue

from apscheduler import Scheduler
from apscheduler.triggers.interval import IntervalTrigger
from mac_notifications import client

import bot.utils as utils
from bot.golf import Golf
from bot.restaurant import Restaurant


def call_restaurant(restaurant_class):
    restaurant_class()


if __name__ == "__main__":
    INTERVAL = 15

    # Root logger
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.getLogger().handlers[0].setFormatter(formatter)
    logging.getLogger('apscheduler').setLevel(logging.ERROR)

    scheduler = Scheduler()
    queue = Queue()

    restaurants = [
        Restaurant(id=utils.I_SODI, party_size=3, hour_end=20, days=[date(2024, 7, 2), date(2024, 7, 3)], queue=queue),
    ]
    for i, restaurant in enumerate(restaurants):
        scheduler.add_schedule(
            call_restaurant,
            trigger=IntervalTrigger(
                seconds=INTERVAL,
                start_time=datetime.now() + timedelta(seconds=i * INTERVAL / len(restaurants)),
            ),
            kwargs={"restaurant_class": restaurant},
        )

    # Golf
    scheduler.add_schedule(
        Golf(queue=queue),
        trigger=IntervalTrigger(
            seconds=INTERVAL,
        ),
    )

    # Start scheduler
    scheduler.start_in_background()

    # Wait for message in queue
    while True:
        msg = queue.get()
        if msg:
            # Send MAC notification
            client.create_notification(
                title="Reservation Bot",
                subtitle=msg,
                icon="icon/reservation.png",
            )
