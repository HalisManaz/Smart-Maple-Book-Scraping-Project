import logging
import time
import pymongo
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from pymongo import MongoClient
import schedule
