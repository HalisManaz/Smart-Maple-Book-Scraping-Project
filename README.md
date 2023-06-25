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
