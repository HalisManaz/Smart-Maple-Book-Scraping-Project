import logging
import time
import pymongo
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from pymongo import MongoClient
import schedule


class BookScraper:
    def __init__(self, url: str, headers: dict) -> None:
        """
        Initialize the BookScraper class.

        Args:
            url (str): The URL to scrape.
            headers (dict): The headers to use for the request.
        """
        self.url = url
        self.headers = headers
        self.num_books = 1
        self.page_num = 1
        self.repated_page = 0
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["smartmaple"]
        if "kitapsepeti" in url:
            self.collection = self.db["kitapsepeti"]
        if "kitapyurdu" in url:
            self.collection = self.db["kitapyurdu"]

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Check if logger already has handlers
        if not self.logger.handlers:
            # Create StreamHandler
            handler = logging.StreamHandler()
            # Create Log Formatter
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(handler)

    def __enter__(self) -> "BookScraper":
        """
        Enter the context of the BookScraper class.

        Returns:
            BookScraper: The BookScraper instance.
        """
        self.connect_mongo()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Exit the context of the BookScraper class.

        Args:
            exc_type: The type of the exception.
            exc_value: The value of the exception.
            traceback: The traceback of the exception.
        """
        self.disconnect_mongo()

    def connect_mongo(self) -> None:
        """
        Connect to the MongoDB instance.
        """
        try:
            # Check connection to MongoDB
            # Check if the MongoDB instance is available
            self.client.admin.command("ping")
            self.logger.info("Connected to MongoDB.")
        except Exception as e:
            self.logger.error(f"Error connecting to MongoDB: {e}")

    def disconnect_mongo(self) -> None:
        """
        Disconnect from the MongoDB instance.
        """
        self.client.close()

    def scrape_books(self) -> bool:
        """
        Scrape books from website.

        Returns:
            bool: True if there are more pages to scrape, False otherwise.
        """
        self.logger.info("Book scraping started..")

        while True:
            if self.collection == self.db["kitapsepeti"]:
                url = f"{self.url}&pg={self.page_num}"
                self.logger.info(f"Scraping page: {url}..\n\n")
                r = requests.get(url=url, headers=self.headers).content
                soup = BeautifulSoup(r, "html.parser")

                titles = soup.find_all(
                    "a", class_="fl col-12 text-description detailLink"
                )
                authors = soup.find_all("a", id="productModelText")
                publishers = soup.find_all("a", class_="col col-12 text-title mt")
                prices = soup.find_all("div", class_="col col-12 currentPrice")

            elif self.collection == self.db["kitapyurdu"]:
                url = f"{self.url}&page={self.page_num}"
                self.logger.info(f"Scraping page: {url}..\n\n")
                r = requests.get(url=url, headers=self.headers).content
                soup = BeautifulSoup(r, "html.parser")

                prices = soup.find_all("div", {"class": "price-new"})
                authors = soup.find_all("div", {"class": "author compact ellipsis"})
                publishers = soup.find_all("div", {"class": "publisher"})
                titles = soup.find_all("div", {"class": "name ellipsis"})

            if self.stop_condition(url, titles):
                self.logger.info(f"Scraping finished.")
                return None, None, None, None

            self.page_num += 1
            return titles, authors, publishers, prices

    def extract_book_info(
        self, title: str, author: str, publisher: str, price: float
    ) -> bool:
        if self.collection == self.db["kitapsepeti"]:
            price = price.get_text(strip=True)[:-3]
            price = price.strip().replace(".", "_")
            price = float(price.strip().replace(",", "."))
            author = author.get_text(strip=True)
            publisher = publisher.get_text(strip=True)
            title = title.get_text(strip=True)

        if self.collection == self.db["kitapyurdu"]:
            title = title.find("span").text.strip()
            price = price.find("span", {"class": "value"})
            price = price.text.strip().replace(".", "_")
            price = float(price.strip().replace(",", "."))
            author = author.find("a", {"class": "alt"})
            if not author:
                author = "Unknown"
            else:
                author = author.text.strip()
            publisher = publisher.find("span").find("a").find("span").text

        return title, author, publisher, price
