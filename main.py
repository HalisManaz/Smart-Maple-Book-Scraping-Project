import logging
import os
import smtplib
import time
from email.mime.text import MIMEText
from urllib.parse import parse_qs, urlparse

import pymongo
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import schedule
from pymongo import MongoClient

load_dotenv()


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
        self.client = MongoClient("mongodb://smartmaple_mongo:27017/")
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

    def send_email(self, recipient_email):
        """
        Sends an email to the specified recipient with the results of the scraping.

        Args:
            recipient_email (str): The email address to send the email to.

        Returns:
            None
        """

        # create message
        self.logger.info(f"Sending email to {recipient_email}")
        message = MIMEText(
            f"Scraping finished! Number of books: {str(self.num_books-1)} scraped from {self.url}."
        )

        if self.collection == self.db["kitapsepeti"]:
            message["Subject"] = f"Kitapsepeti Scraping Finished."
        if self.collection == self.db["kitapyurdu"]:
            message["Subject"] = f"Kitapyurdu Scraping Finished."

        message["From"] = os.getenv("EMAIL_ADDRESS")
        message["To"] = recipient_email

        # send message
        with smtplib.SMTP("smtp.office365.com", 587) as smtp:
            smtp.starttls()
            smtp.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
            smtp.send_message(message)

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
                self.send_email(os.getenv("EMAIL_RECEIVER"))
                return None, None, None, None

            self.page_num += 1
            return titles, authors, publishers, prices

    def extract_book_info(
        self, title: str, author: str, publisher: str, price: float
    ) -> bool:
        if self.collection == self.db["kitapsepeti"]:
            title = title.get_text(strip=True)
            if not author:
                author = ["Unknown"]
            else:
                author = [author_name.get_text(strip=True) for author_name in author]
            price = price.get_text(strip=True)[:-3]
            price = price.strip().replace(".", "_")
            price = float(price.strip().replace(",", "."))
            publisher = publisher.get_text(strip=True)

        if self.collection == self.db["kitapyurdu"]:
            title = title.find("span").text.strip()
            author = author.find_all("a", {"class": "alt"})
            if not author:
                author = ["Unknown"]
            else:
                author = [author_name.text.strip() for author_name in author]
            price = price.find("span", {"class": "value"})
            price = price.text.strip().replace(".", "_")
            price = float(price.strip().replace(",", "."))
            publisher = publisher.find("span").find("a").find("span").text

        return title, author, publisher, price

    def stop_condition(self, url: str, titles: list) -> bool:
        if "kitapsepeti" in url:
            response = requests.get(url)

            # Parse the URL
            parsed_url = urlparse(response.url)

            # Get the query parameters
            query_params = parse_qs(parsed_url.query)

            # Extract the value of the 'pg' parameter
            pg_value = query_params.get("pg", [None])[0]

            if self.page_num > int(pg_value):
                self.logger.info(
                    f"{self.num_books-1} books scraped from kitapsepeti.com."
                )
                return True
            else:
                return False

        elif "kitapyurdu" in url:
            if self.repated_page == 2:
                self.logger.info(
                    f"{self.num_books-1} books scraped from kitapsepeti.com."
                )
                return True

            # parse the URL
            parsed_url = urlparse(url)

            # extract the query parameters as a dictionary
            query_params = parse_qs(parsed_url.query)

            # extract the limit value
            limit = int(query_params["limit"][0])
            if len(titles) < limit:
                self.repated_page += 1

    def check_database(
        self, title: str, author: str, publisher: str, session=None
    ) -> bool:
        """
        Check if a book with the given title, author, and publisher exists in the database.

        Args:
            title (str): Title of the book.
            author (str): Author of the book.
            publisher (str): Publisher of the book.
            session (pymongo.client_session.ClientSession, optional): MongoDB client session. Defaults to None.

        Returns:
            bool: True if the book exists in the database, False otherwise.
        """
        query = {"title": title, "author": author, "publisher": publisher}
        if session is not None and isinstance(
            session, pymongo.client_session.ClientSession
        ):
            book_count = self.collection.count_documents(query, session=session)
        if author == ["Unknown"]:
            return True
        else:
            book_count = self.collection.count_documents(query)

        if book_count > 0:
            self.logger.info(f"Already exists in the database - {title}.")
        return book_count > 0

    def upload_to_mongodb(
        self,
        title: str,
        author: str,
        publisher: str,
        price: float,
    ) -> None:
        self.collection.insert_one(
            {
                "title": title,
                "author": [author_name for author_name in author],
                "publisher": publisher,
                "price": price,
            }
        )
        author_repr = ", ".join(author)
        self.logger.info(
            f"Kitap {self.num_books}: {title} | Yazar: {author_repr} | Yayınevi: {publisher} | Fiyat: {price}"
        )
        self.num_books += 1

    def step(self) -> bool:
        """
        Execute the appropriate scraping method based on the website provided.

        Returns:
            bool: True if there are more pages to scrape, False otherwise.
        """
        while True:
            titles, authors, publishers, prices = self.scrape_books()

            if (
                titles is None
                or authors is None
                or publishers is None
                or prices is None
            ):
                break

            for title, author, publisher, price in zip(
                titles, authors, publishers, prices
            ):
                title, author, publisher, price = self.extract_book_info(
                    title, author, publisher, price
                )
                if self.check_database(title, author, publisher):
                    continue
                else:
                    self.upload_to_mongodb(title, author, publisher, price)


def main():
    base_url_kitapyurdu = "https://www.kitapyurdu.com/index.php?route=product/search&filter_name=Python&filter_in_stock=0&limit=100"
    base_url_kitapsepeti = "https://www.kitapsepeti.com/arama?q=Python&stock=1"
    headers = {
        "User-Agent": os.getenv("HEADERS"),
    }
    urls = [base_url_kitapyurdu, base_url_kitapsepeti]

    for url in urls:
        with BookScraper(url, headers) as scraper:
            scraper.step()


if __name__ == "__main__":
    # Every minute
    # schedule.every(1).minutes.do(main)

    # Every day at 00:00
    schedule.every().day.at("00:00").do(main)

    while True:
        schedule.run_pending()
        time.sleep(1)
