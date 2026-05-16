import logging

from selenium import webdriver
from selenium.common import TimeoutException, StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from bot.base_bot import BaseBot

logger = logging.getLogger()


class TicketMasterBot(BaseBot):
    event_uri: str
    timeout: int = 15

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__qualname__ = "Bot.TicketMaster"

    def __call__(self):
        self.check_standard_tickets()

    def wait(self, driver, by, selector):
        return WebDriverWait(driver, self.timeout).until(
            EC.presence_of_element_located((by, selector))
        )

    def wait_and_click(self, driver, by, selector, attempts=1):
        try:
            self.wait(driver, by, selector).click()
        except (StaleElementReferenceException, ElementClickInterceptedException) as e:
            logger.info("%s for %s with attempt N°%i", type(e).__name__, selector, attempts)
            if attempts < 3:
                self.wait_and_click(driver, by, selector, attempts + 1)

    def check_standard_tickets(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-crash-reporter")
        options.add_argument("--no-crashpad")
        driver = webdriver.Chrome(options=options)

        try:
            driver.get(f"https://www.ticketmaster.com/{self.event_uri}")
            self.wait_and_click(driver, By.CSS_SELECTOR, "button[data-bdd='accept-modal-accept-button']")
            self.wait_and_click(driver, By.ID, "edp-quantity-filter-button")
            element = self.wait(driver, By.CSS_SELECTOR, "div[data-bdd='ticket-checkboxes-collapse-toggle']")
            if "Standard Ticket" in element.text:
                self.notify("TM", "TM standard ticket available")
        except TimeoutException:
            logger.info("TicketMasterBot timed out")
        finally:
            driver.quit()
