from urllib.parse import urlparse
import re
import whois
import requests
from requests.exceptions import RequestException
import socket
from bs4 import BeautifulSoup
import tldextract
from datetime import datetime

def having_IP_Address(url):
    # Pattern to detect IP address
    ip_address_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    match = re.search(ip_address_pattern, url)
    return 1 if match else 0

def is_valid(url):
    try:
        html_content = requests.get(url, timeout=5)
        html_content.raise_for_status()  # Raise an exception for HTTP errors
        html_content = html_content.text
        return 1
    except RequestException as e:
        print(f"Error fetching HTML content for {url}: {e}")
        return 0
    
def domain_age(url):
    try:
        domain = urlparse(url).hostname
        whois_info = whois.whois(domain)
        creation_date = whois_info.creation_date
        if isinstance(creation_date, list):
            creation_date = min(creation_date)
        age = (datetime.now() - creation_date).days
        return age
    except Exception as e:
        print(f"Error fetching domain age: {e}")
        return 0

def length_url(url):
    return len(url)

def nb_at(url):
    return '@' in url

def has_redirect(url):
    try:
        html_content = requests.get(url, timeout=5)
        html_content.raise_for_status()  # Raise an exception for HTTP errors
        html_content = html_content.text
    except RequestException as e:
        print(f"Error fetching HTML content for {url}: {e}")
        return 0
    
    soup = BeautifulSoup(html_content, 'html.parser')
    meta_refresh = soup.find("meta", {"http-equiv": "refresh"})
    return bool(meta_refresh)

def is_slash(url):
    return '/' in url

def domain_length(url):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        return len(domain)
    except Exception as e:
        print(f"Error parsing URL: {e}")
        return None

def nos_of_subdomain(url):
    try:
        extracted = tldextract.extract(url)
        subdomains = extracted.subdomain.split('.')
        # Filter out empty strings in case of no subdomains
        subdomains = [sub for sub in subdomains if sub]
        return len(subdomains)
    except Exception as e:
        print(f"Error processing URL: {e}")
        return None
