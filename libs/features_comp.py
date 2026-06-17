"""
features_comp.py — runtime feature extraction for the No Phishing extension.

Only the features the current model actually consumes are computed here. The
model (see train.py / cyberguard_phishing_detection.ipynb) was retrained on a
screened subset of the Kaggle "Web page phishing detection" dataset, so the 60+
features the old TensorFlow model used were dropped. The remaining 22 are listed
in saved_models/feature_names.json and implemented below.

Each function takes the URL and returns a numeric value (booleans are coerced to
1/0 by the caller). Network/WHOIS lookups fail closed to 0 so a single bad URL
never breaks a prediction.
"""

import re
import socket  # noqa: F401  (kept for parity with dataset extraction tooling)
from datetime import datetime
from urllib.parse import urlparse

import requests
import tldextract  # noqa: F401
import whois
from bs4 import BeautifulSoup

# Suspicious tokens commonly found in phishing URLs (Hannousse & Yahiouche).
PHISH_HINTS = [
    "wp", "login", "includes", "admin", "content", "site", "images", "js",
    "alibaba", "css", "myaccount", "dropbox", "themes", "plugins", "signin",
    "view",
]


# --- Lexical features (URL string only) ------------------------------------

def length_url(url):
    return len(url)


def length_hostname(url):
    try:
        return len(urlparse(url).hostname)
    except Exception:
        return 0


def nb_dots(url):
    return url.count('.')


def nb_hyphens(url):
    return url.count('-')


def nb_qm(url):
    return url.count('?')


def nb_eq(url):
    return url.count('=')


def nb_slash(url):
    return url.count('/')


def nb_www(url):
    return url.count('www')


def ratio_digits_url(url):
    total = len(url)
    digits = sum(c.isdigit() for c in url)
    return digits / total if total > 0 else 0


def phish_hints(url):
    lowered = url.lower()
    return sum(lowered.count(hint) for hint in PHISH_HINTS)


def shortest_word_host(url):
    try:
        words = re.findall(r'\w+', urlparse(url).hostname)
        return min(len(w) for w in words) if words else 0
    except Exception:
        return 0


def shortest_word_path(url):
    try:
        words = re.findall(r'\w+', urlparse(url).path)
        return min(len(w) for w in words) if words else 0
    except Exception:
        return 0


def longest_word_path(url):
    try:
        words = re.findall(r'\w+', urlparse(url).path)
        return max(len(w) for w in words) if words else 0
    except Exception:
        return 0


# --- Content features (require fetching the page) --------------------------

def nb_hyperlinks(url):
    try:
        soup = BeautifulSoup(requests.get(url).text, 'html.parser')
        return len(soup.find_all('a'))
    except Exception:
        return 0


def ratio_intHyperlinks(url):
    try:
        soup = BeautifulSoup(requests.get(url).text, 'html.parser')
        anchors = soup.find_all('a')
        if not anchors:
            return 0
        netloc = urlparse(url).netloc
        internal = sum(urlparse(a.get('href')).netloc == netloc for a in anchors)
        return internal / len(anchors)
    except Exception:
        return 0


def ratio_extHyperlinks(url):
    try:
        soup = BeautifulSoup(requests.get(url).text, 'html.parser')
        anchors = soup.find_all('a')
        if not anchors:
            return 0
        netloc = urlparse(url).netloc
        external = sum(urlparse(a.get('href')).netloc != netloc for a in anchors)
        return external / len(anchors)
    except Exception:
        return 0


def ratio_extRedirection(url):
    try:
        history = requests.head(url, allow_redirects=True).history
        if not history:
            return 0
        netloc = urlparse(url).netloc
        external = sum(urlparse(r.url).netloc != netloc for r in history)
        return external / len(history)
    except Exception:
        return 0


def ratio_extErrors(url):
    try:
        history = requests.head(url, allow_redirects=True).history
        if not history:
            return 0
        errors = sum(400 <= r.status_code < 500 for r in history)
        return errors / len(history)
    except Exception:
        return 0


def safe_anchor(url):
    try:
        soup = BeautifulSoup(requests.get(url).text, 'html.parser')
        anchors = soup.find_all('a')
        return all(a.get('rel') == 'nofollow' for a in anchors)
    except Exception:
        return 0


def domain_in_title(url):
    try:
        soup = BeautifulSoup(requests.get(url).text, 'html.parser')
        title = soup.title.string.lower() if soup.title and soup.title.string else ""
        return urlparse(url).hostname.lower() in title
    except Exception:
        return 0


# --- WHOIS features --------------------------------------------------------

def domain_registration_length(url):
    try:
        info = whois.whois(urlparse(url).hostname)
        expiration = info.expiration_date
        if isinstance(expiration, list):
            expiration = min(expiration)
        return (expiration - info.creation_date).days
    except Exception:
        return 0


def domain_age(url):
    try:
        info = whois.whois(urlparse(url).hostname)
        creation = info.creation_date
        if isinstance(creation, list):
            creation = min(creation)
        return (datetime.now() - creation).days
    except Exception:
        return 0
