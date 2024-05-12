import re
import requests
from requests.exceptions import RequestException
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import datetime
import whois

def having_IP_Address(url):
    # Pattern to detect IP address
    ip_address_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    match = re.search(ip_address_pattern, url)
    return 1 if match else 0


# Check if URL is using a URL shortening service
def Shortining_Service(url):
    shorteners = ["bit.ly", "tinyurl.com", "goo.gl", "ow.ly", "t.co"]
    parsed_url = urlparse(url).netloc
    if any(shortener in parsed_url for shortener in shorteners):
        return 1
    return 0

# Check for '@' symbol in URL
def having_At_Symbol(url):
    return 1 if "@" in url else 0

# Check for redirecting using '//'
def double_slash_redirecting(url):
    return 1 if "//" in urlparse(url).path[6:] else 0

# Check for '-' symbol in the domain part of URL
def Prefix_Suffix(url):
    domain = urlparse(url).netloc
    return 1 if '-' in domain else 0

# Check the number of subdomains
def having_Sub_Domain(url):
    subdomains = urlparse(url).netloc.split('.')
    if len(subdomains) == 2:
        return -1
    elif len(subdomains) == 3:
        return 0
    else:
        return 1

# Check SSL certificate status (simplified)
def SSLfinal_State(url):
    try:
        requests.get(url, verify=True)
        return 1
    except requests.exceptions.SSLError:
        return 0

# Check favicon (simple check)
def Favicon(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    icon_link = soup.find('link', rel='shortcut icon')
    if icon_link:
        favicon_url = icon_link['href']
        if urlparse(url).netloc not in favicon_url:
            return 0
    return 1

# Check the port number (simplified)
def port(url):
    parsed_url = urlparse(url)
    if parsed_url.port and parsed_url.port != 80 and parsed_url.port != 443:
        return 0
    return 1

# Check for HTTPS token in domain part
def HTTPS_token(url):
    domain = urlparse(url).netloc
    return 1 if 'https' in domain else 0

def Request_URL(url):
    try:
        html_content = requests.get(url, timeout=5)
        html_content.raise_for_status()  # Raise an exception for HTTP errors
        html_content = html_content.text
    except RequestException as e:
        print(f"Error fetching HTML content for {url}: {e}")
        return 0

    soup = BeautifulSoup(html_content, 'html.parser')
    total_requests = 0
    external_requests = 0

    for tag in soup.find_all(['img', 'script', 'link']):
        if tag.get('src') or tag.get('href'):
            resource_url = tag.get('src') if tag.get('src') else tag.get('href')
            resource_url = urljoin(url, resource_url)
            parsed_domain = urlparse(url).netloc
            parsed_resource_domain = urlparse(resource_url).netloc

            if parsed_domain not in parsed_resource_domain:
                external_requests += 1
            total_requests += 1

    if total_requests == 0:
        return 0

    ratio = external_requests / total_requests
    if ratio > 0.5:  # Threshold can be adjusted based on specific needs
        return 1
    else:
        return 0
    
def URL_of_Anchor(url):
    try:
        html_content = requests.get(url, timeout=5)
        html_content.raise_for_status()  # Raise an exception for HTTP errors
        html_content = html_content.text
    except RequestException as e:
        print(f"Error fetching HTML content for {url}: {e}")
        return 0

    soup = BeautifulSoup(html_content, 'html.parser')
    total_anchors = 0
    suspicious_anchors = 0

    for tag in soup.find_all('a'):
        anchor_href = tag.get('href', '')
        if anchor_href == '' or anchor_href.startswith('#'):
            suspicious_anchors += 1
        else:
            parsed_domain = urlparse(url).netloc
            parsed_href_domain = urlparse(urljoin(url, anchor_href)).netloc

            if parsed_domain not in parsed_href_domain:
                suspicious_anchors += 1

        total_anchors += 1

    if total_anchors == 0:
        return 0
    
    ratio = suspicious_anchors / total_anchors
    if ratio > 0.5:  # Threshold can be adjusted based on specific needs
        return 1
    else:
        return 0
    
def Links_in_tags(url):
    try:
        html_content = requests.get(url, timeout=5)
        html_content.raise_for_status()  # Raise an exception for HTTP errors
        html_content = html_content.text
    except RequestException as e:
        print(f"Error fetching HTML content for {url}: {e}")
        return 0

    soup = BeautifulSoup(html_content, 'html.parser')
    tags = soup.find_all(['link', 'script', 'meta'])
    total_tags = len(tags)
    suspicious_tags = 0

    for tag in tags:
        tag_url = tag.get('href') or tag.get('src')
        if not tag_url:
            continue

        parsed_domain = urlparse(url).netloc
        parsed_tag_domain = urlparse(urljoin(url, tag_url)).netloc

        if parsed_domain not in parsed_tag_domain:
            suspicious_tags += 1

    if total_tags == 0:
        return 0

    ratio = suspicious_tags / total_tags
    return 1 if ratio > 0.5 else 0

def SFH(url):
    try:
        html_content = requests.get(url, timeout=5)
        html_content.raise_for_status()  # Raise an exception for HTTP errors
        html_content = html_content.text
    except RequestException as e:
        print(f"Error fetching HTML content for {url}: {e}")
        return 0

    soup = BeautifulSoup(html_content, 'html.parser')
    forms = soup.find_all('form')
    for form in forms:
        action = form.get('action', '').lower()

        if action == '' or action == 'about:blank':
            return 1
        if not action.startswith('http'):
            return 1
        if urlparse(url).netloc not in urlparse(action).netloc:
            return 1

    return 0

def Submitting_to_email(url):
    try:
        html_content = requests.get(url, timeout=5)
        html_content.raise_for_status()  # Raise an exception for HTTP errors
        html_content = html_content.text
    except RequestException as e:
        print(f"Error fetching HTML content for {url}: {e}")
        return 0

    soup = BeautifulSoup(html_content, 'html.parser')
    forms = soup.find_all('form')
    for form in forms:
        action = form.get('action', '').lower()

        if 'mailto:' in action:
            return 1

    return 0

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

def has_onmouseover(url):
    try:
        html_content = requests.get(url, timeout=5)
        html_content.raise_for_status()  # Raise an exception for HTTP errors
        html_content = html_content.text
    except RequestException as e:
        print(f"Error fetching HTML content for {url}: {e}")
        return 0
    
    return "onmouseover=" in html_content

def has_disabled_right_click(html_content):
    return "event.button==2" in html_content or "event.button == 2" in html_content

def has_popup_window(html_content):
    return "window.open(" in html_content

def has_iframe(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return bool(soup.find_all("iframe"))

def Domain_age(url):
    try:
        # Extract the domain name from the URL
        domain = urlparse(url).hostname

        # Get WHOIS information for the domain
        whois_info = whois.whois(domain)

        # Extract the creation date
        creation_date = whois_info.creation_date

        # If there are multiple creation dates, use the earliest one
        if isinstance(creation_date, list):
            creation_date = min(creation_date)

        # Calculate the age of the domain in days
        age_days = (datetime.datetime.now() - creation_date).days

        # Return 1 if the domain is older than a year, otherwise 0
        return 1

    except Exception as e:
        print(f"Error fetching domain age: {e}")
        return 0
    
def google_index(url):
    try:
        response = requests.get(f"https://www.google.com/search?q=info:{url}")
        return "did not match any documents" not in response.text
    except Exception as e:
        print(f"Error fetching Google index information: {e}")
        return 0
    
def Links_pointing_to_page(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        links = soup.find_all("a", href=True)

        external_links_count = 0
        domain = urlparse(url).netloc

        for link in links:
            href = link.get("href")
            if not href.startswith("#") and urlparse(href).netloc != domain:
                external_links_count += 1

        return 1
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0
