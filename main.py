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

            if len(titles) < 100:
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
        if author == "Unknown":
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
                "author": author,
                "publisher": publisher,
                "price": price,
            }
        )
        self.logger.info(
            f"Kitap {self.num_books}: {title} | Yazar: {author} | Yayınevi: {publisher} | Fiyat: {price}"
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    urls = [base_url_kitapyurdu, base_url_kitapsepeti]

    for url in urls:
        with BookScraper(url, headers) as scraper:
            scraper.step()


if __name__ == "__main__":
    schedule.every(1).minutes.do(main)

    while True:
        schedule.run_pending()
        time.sleep(1)
