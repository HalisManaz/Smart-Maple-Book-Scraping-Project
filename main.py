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
