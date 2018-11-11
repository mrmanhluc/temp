from selenium import webdriver
import urllib
import pandas as pd
import logging
import commond as food
import platform
import selenium.webdriver.chrome.service as service


class WebDriver:
    def __init__(self):
        self.current = food.CURRENT_TIME
        self.journey_type = food.JOURNEY_TYPE
        self.locale = food.LOCALE
        self.origin = food.DEPARTURE
        self.adt = food.PASSENGER
        self.destination = food.DESTINATION
        self.from_date = food.FROM_DATE
        self.flightInfo = {
            'journeyType': [],
            'departure': [],
            'destination': [],
            'search_date': [],
            'departure_datetime': [],
            'arrival_datetime': [],
            'stops': [],
            'passenger': [],
            'prices': [],
            'flight_number': [],
        }

        self.driver = self._setup
        self.driver.implicitly_wait(food.WAITING_TIME)
        url = self._generate_url(food.FROM_DATE)
        self.driver.get(url)

    # Can run both environment Linux and Windows
    @property
    def _setup(self):
        os_name = platform.system()
        # setup when run on Windows
        if (os_name == 'Windows'):
            return webdriver.Chrome(food.WINDOWS_CHROME_DRIVER)

        # setup when run on Linux
        a_service = service.Service(food.LINUX_CHROME_DRIVER)
        a_service.start()
        capabilities = {'chrome.binary': food.LINUX_CHROME_STABLE, "chromeOptions": {"args": ['--no-sandbox']}}

        return webdriver.Remote(a_service.service_url, capabilities)

    def _generate_url(self, search_date):
        trip_info = {
            'domain': 'https://fly.vietnamairlines.com/dx/VNDX/#/flight-selection?',
            'variances': {
                'journeyType': self.journey_type,
                'locale': self.locale,
                'origin': self.origin,
                'destination': self.destination,
                'ADT': self.adt,  # Adult numbers
                'CHD': 0,
                'INT': 0,
                'date': search_date,
                'execution': 'e1s1'
            }
        }
        return trip_info['domain'] + urllib.parse.urlencode(trip_info['variances'])

    # Find button which can request to next day and call event click
    def _click_next(self):
        # flights_date have button which can choose day of flights
        btn_flight_days = self.driver.find_element_by_class_name('days')
        is_click = False

        for btn_flight_day in btn_flight_days.find_elements_by_tag_name('button'):
            if is_click:
                btn_flight_day.click()
                break
            print('Test Next Button')
            # we have to click on next button which have attribute aria-pressed.
            # aria-pressed has mean this button are seleting.
            if btn_flight_day.get_attribute('aria-pressed') == 'true':
                is_click = True


class FlightSpider(WebDriver):
    def __init__(self):
        super().__init__()

    # Close driver when finished
    def __del__(self):
        self.driver.close()

    def _feed(self, col_name, value):
        self.flightInfo[col_name].append(value)

    def _feed_info(self):
        self._feed('journeyType', food.JOURNEY_TYPE)
        self._feed('departure', food.DEPARTURE)
        self._feed('destination', food.DESTINATION)
        self._feed('search_date', self.current)
        self._feed('passenger', food.PASSENGER)

    def crawl(self):
        request_count = 0
        while request_count < food.REQUEST_DAYS:
            request_count += 1
            try:
                dashboard = self.driver.find_element_by_class_name('flights-table')
                flights = dashboard.find_elements_by_class_name('dxp-flight')

                for flight in flights:

                    self._feed_info()

                    depart_arrive_time = flight.find_elements_by_class_name('dxp-time')
                    stop_or_not = flight.find_element_by_xpath("//td[@class='column flight-stops']").text
                    flight_number = flight.find_element_by_class_name("flight-number").text

                    self._feed('departure_datetime', depart_arrive_time[0].get_attribute('datetime'))
                    self._feed('arrival_datetime', depart_arrive_time[1].get_attribute('datetime'))
                    self._feed('stops', stop_or_not)
                    self._feed('flight_number', flight_number)

                    prices = []
                    for price in flight.find_elements_by_class_name("price-container"):
                        prices.append(price.text)
                    self._feed('prices', prices)

                self._click_next()
            except ValueError:
                logging.basicConfig(format='%(asctime)s %(message)s')
                logging.warning('Elements are not found.')

    def _generate_filename(self):
        return str(self.current.year) + str(self.current.month) + \
               str(self.current.day) + str('_') + str(self.current.hour) + \
               str(self.current.minute) + str('.csv')

    def save(self):
        pd.DataFrame(self.flightInfo).to_csv(self._generate_filename(), index=False)


def __main__():
    spider = FlightSpider()
    spider.crawl()
    spider.save()


__main__()
