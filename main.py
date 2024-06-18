import logging
from datetime import datetime, timedelta
from queue import Queue

from apscheduler import Scheduler
from apscheduler.triggers.interval import IntervalTrigger
from mac_notifications import client

import bot.utils as utils
from bot.golf import Golf
from bot.restaurant import Restaurant

if __name__ == "__main__":
    INTERVAL = 15

    # Logger
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("reservation_bot")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("main.log")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.handlers[0].setFormatter(formatter)

    scheduler = Scheduler()
    queue = Queue()

    restaurants = [
        Restaurant(id=utils.FOUR_CHARLES, days_range=21, queue=queue),
        Restaurant(id=utils.CARBONE, days_range=35, queue=queue),
    ]
    for i, restaurant in enumerate(restaurants):
        scheduler.add_schedule(
            restaurant,
            trigger=IntervalTrigger(
                seconds=INTERVAL,
                start_time=datetime.now() + timedelta(seconds=i * INTERVAL / len(restaurants)),
            ),
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
