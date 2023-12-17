from urllib.parse import urlparse
import re
import whois
import requests
import socket
from bs4 import BeautifulSoup
import tldextract
from datetime import datetime

def length_url(url):
    return len(url)

def length_hostname(url):
    try:
        return len(urlparse(url).hostname)
    except:
        return 0

def ip(url):
    try:
        # Parse the URL to get the hostname
        hostname = urlparse(url).hostname

        # Try to resolve the hostname to an IP address
        ip_address = socket.gethostbyname(hostname)

        # Check if the resolved IP address is the same as the original hostname
        return ip_address == hostname
    except:
        # If any error occurs during the process, return False
        return False

def nb_dots(url):
    return url.count('.')

def nb_hyphens(url):
    return url.count('-')

def nb_at(url):
    return url.count('@')

def nb_qm(url):
    return url.count('?')

def nb_and(url):
    return url.count('&')

def nb_or(url):
    return url.count('|')

def nb_or(url):
    return url.count('|')

def nb_eq(url):
    return url.count('=')

def nb_underscore(url):
    return url.count('_')

def nb_tilde(url):
    return url.count('~')

def nb_percent(url):
    return url.count('%')

def nb_slash(url):
    return url.count('/')

def nb_star(url):
    return url.count('*')

def nb_colon(url):
    return url.count(':')

def nb_comma(url):
    return url.count(',')

def nb_semicolon(url):
    return url.count(';')

def nb_dollar(url):
    return url.count('$')

def nb_space(url):
    return url.count(' ')

def nb_www(url):
    return url.count('www')

def nb_com(url):
    return url.count('.com')

def nb_dslash(url):
    return url.count('//')

def http_in_path(url):
    return 'http' in urlparse(url).path

def https_token(url):
    return 'https' in url

def ratio_digits_url(url):
    total_chars = len(url)
    digits = sum(c.isdigit() for c in url)
    return digits / total_chars if total_chars > 0 else 0

def ratio_digits_host(url):
    try:
        hostname = urlparse(url).hostname
        total_chars = len(hostname)
        digits = sum(c.isdigit() for c in hostname)
        return digits / total_chars if total_chars > 0 else 0
    except:
        return 0

def punycode(url):
    return any(ord(char) > 128 for char in url)

def port(url):
    try:
        return urlparse(url).port
    except:
        return 0

def tld_in_path(url):
    try:
        path = urlparse(url).path
        tld = urlparse(url).suffix
        return tld in path
    except:
        return 0

def tld_in_subdomain(url):
    try:
        subdomain = urlparse(url).hostname.split('.')[0]
        tld = urlparse(url).suffix
        return tld in subdomain
    except:
        return 0

def abnormal_subdomain(url):
    try:
        subdomain = urlparse(url).hostname.split('.')[0]
        return not subdomain.isalnum()
    except:
        return 0

def nb_subdomains(url):
    try:
        return len(urlparse(url).hostname.split('.'))
    except:
        return 0

def prefix_suffix(url):
    try:
        return urlparse(url).hostname.startswith('www.') or urlparse(url).hostname.endswith('.com')
    except:
        return 0

def random_domain(url):
    try:
        return len(urlparse(url).hostname) > 10 and not urlparse(url).hostname.isalnum()
    except:
        return 0

def shortening_service(url):
    try:
        return any(service in url for service in ['bit.ly', 'tinyurl', 'goo.gl'])
    except:
        return 0

def path_extension(url):
    try:
        path = urlparse(url).path
        return '.' in path
    except:
        return 0

def nb_redirection(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return len(response.history)
    except:
        return 0

def nb_external_redirection(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return sum(urlparse(url).netloc not in urlparse(r.url).netloc for r in response.history)
    except:
        return 0

def length_words_raw(url):
    try:
        words = re.findall(r'\w+', url)
        return len(words)
    except:
        return 0

def tld_in_path(url):
    try:
        path = urlparse(url).path
        ext = tldextract.extract(url)
        return ext.suffix in path
    except:
        return 0

def tld_in_subdomain(url):
    try:
        subdomain = urlparse(url).hostname.split('.')[0]
        ext = tldextract.extract(url)
        return ext.suffix in subdomain
    except:
        return 0

def abnormal_subdomain(url):
    try:
        subdomain = urlparse(url).hostname.split('.')[0]
        return not subdomain.isalnum()
    except:
        return 0

def nb_subdomains(url):
    try:
        return len(urlparse(url).hostname.split('.'))
    except:
        return 0

def prefix_suffix(url):
    try:
        return urlparse(url).hostname.startswith('www.') or urlparse(url).hostname.endswith('.com')
    except:
        return 0

def random_domain(url):
    try:
        return len(urlparse(url).hostname) > 10 and not urlparse(url).hostname.isalnum()
    except:
        return 0

def shortening_service(url):
    try:
        return any(service in url for service in ['bit.ly', 'tinyurl', 'goo.gl'])
    except:
        return 0

def path_extension(url):
    try:
        path = urlparse(url).path
        return '.' in path
    except:
        return 0

def nb_redirection(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return len(response.history)
    except Exception as e:
        print(f"Error counting redirections: {e}")
        return 0

def nb_external_redirection(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return sum(urlparse(url).netloc not in urlparse(r.url).netloc for r in response.history)
    except Exception as e:
        print(f"Error counting external redirections: {e}")
        return 0

def length_words_raw(url):
    try:
        words = re.findall(r'\w+', url)
        return len(words)
    except:
        return 0

def char_repeat(url):
    try:
        repeated_chars = re.findall(r'(\w)\1+', url)
        return len(repeated_chars)
    except:
        return 0

def shortest_words_raw(url):
    try:
        words = re.findall(r'\w+', url)
        return min(len(word) for word in words) if words else 0
    except:
        return 0

def shortest_word_host(url):
    try:
        hostname = urlparse(url).hostname
        words = re.findall(r'\w+', hostname)
        return min(len(word) for word in words) if words else 0
    except:
        return 0

def shortest_word_path(url):
    try:
        path = urlparse(url).path
        words = re.findall(r'\w+', path)
        return min(len(word) for word in words) if words else 0
    except:
        return 0

def longest_words_raw(url):
    try:
        words = re.findall(r'\w+', url)
        return max(len(word) for word in words) if words else 0
    except:
        return 0

def longest_word_host(url):
    try:
        hostname = urlparse(url).hostname
        words = re.findall(r'\w+', hostname)
        return max(len(word) for word in words) if words else 0
    except:
        return 0

def longest_word_path(url):
    try:
        path = urlparse(url).path
        words = re.findall(r'\w+', path)
        return max(len(word) for word in words) if words else 0
    except:
        return 0

def avg_words_raw(url):
    try:
        words = re.findall(r'\w+', url)
        return sum(len(word) for word in words) / len(words) if words else 0
    except:
        return 0

def avg_word_host(url):
    try:
        hostname = urlparse(url).hostname
        words = re.findall(r'\w+', hostname)
        return sum(len(word) for word in words) / len(words) if words else 0
    except:
        return 0

def avg_word_path(url):
    try:
        path = urlparse(url).path
        words = re.findall(r'\w+', path)
        return sum(len(word) for word in words) / len(words) if words else 0
    except:
        return 0

def suspecious_tld(url):
    try:
        ext = tldextract.extract(url)
        return ext.suffix.lower() in ['tk', 'ml', 'ga', 'cf', 'gq']
    except:
        return 0

def nb_hyperlinks(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return len(soup.find_all('a'))
    except Exception as e:
        print(f"Error fetching hyperlinks: {e}")
        return 0

def ratio_intHyperlinks(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        int_links = sum(urlparse(link.get('href')).netloc == urlparse(url).netloc for link in soup.find_all('a'))
        return int_links / len(soup.find_all('a')) if len(soup.find_all('a')) > 0 else 0
    except Exception as e:
        print(f"Error fetching hyperlinks: {e}")
        return 0

def ratio_extHyperlinks(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        ext_links = sum(urlparse(link.get('href')).netloc != urlparse(url).netloc for link in soup.find_all('a'))
        return ext_links / len(soup.find_all('a')) if len(soup.find_all('a')) > 0 else 0
    except Exception as e:
        print(f"Error fetching hyperlinks: {e}")
        return 0

def ratio_nullHyperlinks(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        null_links = sum(link.get('href') is None for link in soup.find_all('a'))
        return null_links / len(soup.find_all('a')) if len(soup.find_all('a')) > 0 else 0
    except Exception as e:
        print(f"Error fetching hyperlinks: {e}")
        return 0

def nb_extCSS(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return len(soup.find_all('link', {'rel': 'stylesheet'}))
    except Exception as e:
        print(f"Error fetching external CSS: {e}")
        return 0

def ratio_intRedirection(url):
    try:
        response = requests.head(url, allow_redirects=True)
        int_redirections = sum(urlparse(r.url).netloc == urlparse(url).netloc for r in response.history)
        return int_redirections / len(response.history) if len(response.history) > 0 else 0
    except Exception as e:
        print(f"Error fetching redirections: {e}")
        return 0

def ratio_extRedirection(url):
    try:
        response = requests.head(url, allow_redirects=True)
        ext_redirections = sum(urlparse(r.url).netloc != urlparse(url).netloc for r in response.history)
        return ext_redirections / len(response.history) if len(response.history) > 0 else 0
    except Exception as e:
        print(f"Error fetching external redirections: {e}")
        return 0

def ratio_intErrors(url):
    try:
        response = requests.head(url, allow_redirects=True)
        int_errors = sum(r.status_code >= 400 and r.status_code < 500 for r in response.history)
        return int_errors / len(response.history) if len(response.history) > 0 else 0
    except Exception as e:
        print(f"Error fetching errors: {e}")
        return 0

def ratio_extErrors(url):
    try:
        response = requests.head(url, allow_redirects=True)
        ext_errors = sum(r.status_code >= 400 and r.status_code < 500 for r in response.history)
        return ext_errors / len(response.history) if len(response.history) > 0 else 0
    except Exception as e:
        print(f"Error fetching external errors: {e}")
        return 0

def login_form(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return len(soup.find_all('input', {'type': 'password'})) > 0
    except Exception as e:
        print(f"Error fetching login form: {e}")
        return 0

def external_favicon(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        favicons = soup.find_all('link', rel='icon')
        return any(link.get('href') and 'http' in link.get('href') for link in favicons)
    except Exception as e:
        print(f"Error fetching external favicon information: {e}")
        return 0

def links_in_tags(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return len(soup.find_all('a'))
    except Exception as e:
        print(f"Error fetching hyperlinks: {e}")
        return 0

def submit_email(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return len(soup.find_all('input', {'type': 'email'})) > 0
    except Exception as e:
        print(f"Error fetching email submission form: {e}")
        return 0

def ratio_intMedia(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get all media elements
        all_media = soup.find_all(['img', 'video', 'audio'])

        # Get internal media elements (assuming internal media is hosted on the same domain)
        internal_media = [media for media in all_media if url in media.get('src', '')]

        # Calculate the ratio
        total_media_count = len(all_media)
        internal_media_count = len(internal_media)

        return internal_media_count / total_media_count if total_media_count > 0 else 0
    except Exception as e:
        print(f"Error calculating ratio of internal media: {e}")
        return 0

def ratio_extMedia(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get all media elements
        all_media = soup.find_all(['img', 'video', 'audio'])

        # Get external media elements (assuming external media is hosted on a different domain)
        parsed_url = urlparse(url)
        external_media = [media for media in all_media if urlparse(media.get('src', '')).hostname != parsed_url.hostname]

        # Calculate the ratio
        total_media_count = len(all_media)
        external_media_count = len(external_media)

        return external_media_count / total_media_count if total_media_count > 0 else 0
    except Exception as e:
        print(f"Error calculating ratio of external media: {e}")
        return 0

def sfh(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return len(soup.find_all('form', {'action': ''})) > 0
    except Exception as e:
        print(f"Error fetching submit form handler: {e}")
        return 0

def iframe(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return len(soup.find_all('iframe')) > 0
    except Exception as e:
        print(f"Error fetching iframe tags: {e}")
        return 0

def popup_window(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return len(soup.find_all('script', {'onload': 'window.open'})) > 0
    except Exception as e:
        print(f"Error fetching popup window scripts: {e}")
        return 0

def safe_anchor(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        anchors = soup.find_all('a')
        return all(anchor.get('rel') == 'nofollow' for anchor in anchors)
    except Exception as e:
        print(f"Error fetching anchors: {e}")
        return 0

def onmouseover(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return len(soup.find_all(onmouseover=True)) > 0
    except Exception as e:
        print(f"Error fetching onmouseover events: {e}")
        return 0

def right_clic(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return len(soup.find_all(oncontextmenu=True)) > 0
    except Exception as e:
        print(f"Error fetching right-click events: {e}")
        return 0

def empty_title(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return not soup.title or not soup.title.string.strip()
    except Exception as e:
        print(f"Error fetching title: {e}")
        return 0

def domain_in_title(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.lower() if soup.title else ""
        domain = urlparse(url).hostname.lower()
        return domain in title
    except Exception as e:
        print(f"Error fetching title: {e}")
        return 0

def domain_with_copyright(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        copyright_text = "copyright" in soup.text.lower()
        domain = urlparse(url).hostname.lower()
        return copyright_text and domain in soup.text.lower()
    except Exception as e:
        print(f"Error fetching copyright information: {e}")
        return 0

def whois_registered_domain(url):
    try:
        domain = urlparse(url).hostname
        whois_info = whois.whois(domain)
        return whois_info.registrar is not None
    except Exception as e:
        print(f"Error fetching WHOIS information: {e}")
        return 0

def domain_registration_length(url):
    try:
        domain = urlparse(url).hostname
        whois_info = whois.whois(domain)
        expiration_date = whois_info.expiration_date
        if isinstance(expiration_date, list):
            expiration_date = min(expiration_date)
        registration_length = (expiration_date - whois_info.creation_date).days
        return registration_length
    except Exception as e:
        print(f"Error fetching domain registration length: {e}")
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

def google_index(url):
    try:
        response = requests.get(f"https://www.google.com/search?q=info:{url}")
        return "did not match any documents" not in response.text
    except Exception as e:
        print(f"Error fetching Google index information: {e}")
        return 0
