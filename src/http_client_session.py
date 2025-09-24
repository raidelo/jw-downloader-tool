from requests import Session

from constants import DEFAULT_USER_AGENT

session = Session()
session.headers = {"User-Agent": DEFAULT_USER_AGENT}
