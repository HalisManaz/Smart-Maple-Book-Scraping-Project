# **Smart Maple Pyhton Developer Project**

<p align="center">
  <img src="https://boluteknokent.com.tr/resim/upload/sb423.png" alt="TURK AI Image" width="400">
</p>

## **Project Overview**

This project aims to develop a Python application that scrapes product data from two popular book websites - [www.kitapyurdu.com](http://www.kitapyurdu.com/) and [www.kitapsepeti.com](http://www.kitapsepeti.com/), specifically focusing on Python-related books. The application collects the following details about each book:

- Book title
- Publisher
- Authors
- Price of the book

The acquired data is stored in a `MongoDB` database.

## **Project Structure**
- app/
    - main.py
    - Dockerfile
    - docker-compose.yml
    - README.md
    - requirements.txt
    - .gitignore


## **Prerequisites**
* Docker
* Docker Compose


## **Technologies and Libraries Used**

The project uses the following Python libraries:

1. **Requests**: Used for making HTTP requests to the websites.

2. **BeautifulSoup4**: Used for parsing the HTML content of the web pages and extracting the required data.

3. **pymongo**: Used for interacting with MongoDB, for tasks like storing and retrieving data.

4. **schedule**: Used for scheduling the web scraping tasks at specific times.

5. **logging**: Used for generating log messages for debugging and understanding the flow of the program.

The project is designed to be run in a Docker environment. Docker is used for setting up isolated containers for the Python application and MongoDB. Docker Compose is used to manage these multiple containers as a single service.

## **Running the Application**

The application is designed to be run in a Docker environment. You need to have Docker and Docker Compose installed to run the application. To start the application, navigate to the project directory in your terminal and run the command `docker-compose up`.

This will start the two Docker containers: one for the Python application and one for MongoDB. The Python application will start scraping data from the specified websites and store the data in the MongoDB database.


## **How the Application Works**

The application follows these general steps:

1. Connects to the MongoDB database.
2. Makes a GET request to the specified web page.
3. Parses the HTML content of the page and extracts the required data (book title, authors, publisher, and price).
4. Stores the extracted data in the MongoDB database.
5. Repeats the process for the next page until all the pages have been scraped.
6. The application also checks if a book already exists in the database before inserting it, in order to prevent duplicates.

All these steps are encapsulated in the `BookScraper` class.

## **UML Diagram**

<p align="center">
  <img src="https://showme.redstarplugin.com/d/FJvuvPsB" alt="TURK AI Image" width="800">
</p>

## **Application Features**

- **Scraping Multiple Websites**: The application is designed to scrape data from multiple websites. Currently, it scrapes data from two popular book websites, but it can be easily extended to scrape data from more websites.

- **Scheduling**: The application uses the `schedule` library to run the web scraping tasks at specific times. By default, the application is scheduled to run every day at 12 AM.

- **Logging**: The application uses Python's built-in `logging` module to log messages that are useful for understanding the flow of the program and for debugging.

- **Dockerized Application**: The Python application and MongoDB are containerized using Docker, ensuring that the application runs in the same environment regardless of where it is deployed.

- **Error Handling**: The application includes error handling for common issues like connection errors, ensuring that the application can recover from these issues and continue running.



## **Documentation**
The following documentation is available in the project directory:

* **requirements.txt**: A list of Python dependencies required to run the application.
* **docker-compose.yml**: The Docker Compose configuration file for the application.
* **main.py**: The primary Python script that houses the scraping logic and database interaction. It orchestrates the scraping of the book websites and populates the MongoDB with relevant data.
* **Dockerfile**: This file is used for creating a Docker image for the application. It specifies the base Python image, sets the working directory, copies the requirements.txt file and installs the requirements, and finally sets the command to run the application.
* **.gitignore**: A file that specifies files and folders to be ignored by Git. Its useful for ensuring that unwanted files, like those generated during runtime or personal IDE settings, don't get committed to the Git repository.
* **README.md**: The file you are currently reading. It provides a high-level overview of the project, its setup, and instructions for running and using the application.

## **Future Improvements**

The current implementation of the application is fairly basic and there is room for several improvements. For example, the application could be enhanced with the following feature:

- **User Interface**: The application could include a simple user interface that allows users to start and stop the web scraping process, choose which websites to scrape
