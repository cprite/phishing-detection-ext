import tldextract
import socket
import requests
import dns.resolver
import ssl
import ipaddress
import whois
import os
import time
import re
from datetime import datetime
from urllib.parse import urlparse
from requests.exceptions import RequestException


def qty_dot_url(url):
    return url.count('.')

def qty_hyphen_url(url):
    return url.count('-')

def qty_underline_url(url):
    return url.count('_')

def qty_slash_url(url):
    return url.count('/')

def qty_questionmark_url(url):
    return url.count('?')

def qty_equal_url(url):
    return url.count('=')

def qty_at_url(url):
    return url.count('@')

def qty_and_url(url):
    return url.count('&')

def qty_exclamation_url(url):
    return url.count('!')

def qty_space_url(url):
    return url.count(' ')

def qty_tilde_url(url):
    return url.count('~')

def qty_comma_url(url):
    return url.count(',')

def qty_plus_url(url):
    return url.count('+')

def qty_asterisk_url(url):
    return url.count('*')

def qty_hashtag_url(url):
    return url.count('#')

def qty_dollar_url(url):
    return url.count('$')

def qty_percent_url(url):
    return url.count('%')

def qty_tld_url(url):
    from tld import get_tld
    try:
        tld = get_tld(url, as_object=True)
        return 1 if tld else 0
    except:
        return 0

def length_url(url):
    return len(url)

def qty_dot_domain(url):
    domain = urlparse(url).netloc
    return domain.count('.')

def qty_hyphen_domain(url):
    domain = urlparse(url).netloc
    return domain.count('-')

def qty_underline_domain(url):
    domain = urlparse(url).netloc
    return domain.count('_')

def qty_slash_domain(url):
    domain = urlparse(url).netloc
    return domain.count('/')

def qty_questionmark_domain(url):
    domain = urlparse(url).netloc
    return domain.count('?')

def qty_equal_domain(url):
    domain = urlparse(url).netloc
    return domain.count('=')

def qty_at_domain(url):
    domain = urlparse(url).netloc
    return domain.count('@')

def qty_and_domain(url):
    domain = urlparse(url).netloc
    return domain.count('&')

def qty_exclamation_domain(url):
    domain = urlparse(url).netloc
    return domain.count('!')

def qty_space_domain(url):
    domain = urlparse(url).netloc
    return domain.count(' ')

def qty_tilde_domain(url):
    domain = urlparse(url).netloc
    return domain.count('~')

def qty_comma_domain(url):
    domain = urlparse(url).netloc
    return domain.count(',')

def qty_plus_domain(url):
    domain = urlparse(url).netloc
    return domain.count('+')

def qty_asterisk_domain(url):
    domain = urlparse(url).netloc
    return domain.count('*')

def qty_hashtag_domain(url):
    domain = urlparse(url).netloc
    return domain.count('#')

def qty_dollar_domain(url):
    domain = urlparse(url).netloc
    return domain.count('$')

def qty_percent_domain(url):
    domain = urlparse(url).netloc
    return domain.count('%')

def qty_vowels_domain(url):
    domain = urlparse(url).netloc
    return sum(1 for char in domain if char.lower() in 'aeiou')

def domain_length(url):
    domain = urlparse(url).netloc
    return len(domain)

def domain_in_ip(url):
    domain = urlparse(url).netloc
    try:
        ipaddress.ip_address(domain)
        return 1
    except ValueError:
        return 0

def server_client_domain(url):
    domain = urlparse(url).netloc.lower()
    return domain.count('server') + domain.count('client')

def qty_dot_directory(url):
    path = urlparse(url).path
    return path.count('.')

def qty_hyphen_directory(url):
    path = urlparse(url).path
    return path.count('-')

def qty_underline_directory(url):
    path = urlparse(url).path
    return path.count('_')

def qty_slash_directory(url):
    path = urlparse(url).path
    return path.count('/')

def qty_questionmark_directory(url):
    path = urlparse(url).path
    return path.count('?')

def qty_equal_directory(url):
    path = urlparse(url).path
    return path.count('=')

def qty_at_directory(url):
    path = urlparse(url).path
    return path.count('@')

def qty_and_directory(url):
    path = urlparse(url).path
    return path.count('&')

def qty_exclamation_directory(url):
    path = urlparse(url).path
    return path.count('!')

def qty_space_directory(url):
    path = urlparse(url).path
    return path.count(' ')

def qty_tilde_directory(url):
    path = urlparse(url).path
    return path.count('~')

def qty_comma_directory(url):
    path = urlparse(url).path
    return path.count(',')

def qty_plus_directory(url):
    path = urlparse(url).path
    return path.count('+')

def qty_asterisk_directory(url):
    path = urlparse(url).path
    return path.count('*')

def qty_hashtag_directory(url):
    path = urlparse(url).path
    return path.count('#')

def qty_dollar_directory(url):
    path = urlparse(url).path
    return path.count('$')

def qty_percent_directory(url):
    path = urlparse(url).path
    return path.count('%')

def directory_length(url):
    path = urlparse(url).path
    return len(path)

def qty_dot_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('.')

def qty_hyphen_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('-')

def qty_underline_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('_')

def qty_slash_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('/')

def qty_questionmark_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('?')

def qty_equal_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('=')

def qty_at_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('@')

def qty_and_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('&')

def qty_exclamation_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('!')

def qty_space_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count(' ')

def qty_tilde_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('~')

def qty_comma_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count(',')

def qty_plus_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('+')

def qty_asterisk_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('*')

def qty_hashtag_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('#')

def qty_dollar_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('$')

def qty_percent_file(url):
    file_part = os.path.basename(urlparse(url).path)
    return file_part.count('%')

def file_length(url):
    file_part = os.path.basename(urlparse(url).path)
    return len(file_part)

def qty_dot_params(url):
    params = urlparse(url).query
    return params.count('.')

def qty_hyphen_params(url):
    params = urlparse(url).query
    return params.count('-')

def qty_underline_params(url):
    params = urlparse(url).query
    return params.count('_')

def qty_slash_params(url):
    params = urlparse(url).query
    return params.count('/')

def qty_questionmark_params(url):
    params = urlparse(url).query
    return params.count('?')

def qty_equal_params(url):
    params = urlparse(url).query
    return params.count('=')

def qty_at_params(url):
    params = urlparse(url).query
    return params.count('@')

def qty_and_params(url):
    params = urlparse(url).query
    return params.count('&')

def qty_exclamation_params(url):
    params = urlparse(url).query
    return params.count('!')

def qty_space_params(url):
    params = urlparse(url).query
    return params.count(' ')

def qty_tilde_params(url):
    params = urlparse(url).query
    return params.count('~')

def qty_comma_params(url):
    params = urlparse(url).query
    return params.count(',')

def qty_plus_params(url):
    params = urlparse(url).query
    return params.count('+')

def qty_asterisk_params(url):
    params = urlparse(url).query
    return params.count('*')

def qty_hashtag_params(url):
    params = urlparse(url).query
    return params.count('#')

def qty_dollar_params(url):
    params = urlparse(url).query
    return params.count('$')

def qty_percent_params(url):
    params = urlparse(url).query
    return params.count('%')

def params_length(url):
    params = urlparse(url).query
    return len(params)

def tld_present_params(url):
    params = urlparse(url).query
    return any(tldextract.extract(param).suffix for param in params.split('&'))

def qty_params(url):
    params = urlparse(url).query
    return len(params.split('&')) if params else 0

def email_in_url(url):
    return '@' in url

def time_response(url):
    # This function needs an HTTP request to measure response time
    start_time = time.time()
    requests.get(url)
    end_time = time.time()
    return end_time - start_time

def domain_spf(url):
    domain = urlparse(url).netloc
    
    try:
        answers = dns.resolver.query(domain, 'TXT')
        for rdata in answers:
            if 'v=spf1' in str(rdata):
                return True
        return False
    except dns.resolver.NoAnswer:
        return False
    except Exception as e:
        print(f"An error occurred in DNS query: {e}")
        return False

def get_domain_activation_time(url):
    domain = urlparse(url).netloc
    
    try:
        w = whois.whois(domain)
        if w.creation_date:
            if isinstance(w.creation_date, list):
                creation_date = w.creation_date[0]
            else:
                creation_date = w.creation_date
            domain_age = (datetime.now() - creation_date).days
            return domain_age
        else:
            return None
    except Exception as e:
        print(f"Error retrieving domain activation time: {e}")
        return None

def get_domain_expiration_time(url):
    domain = urlparse(url).netloc
    
    try:
        w = whois.whois(domain)
        if w.expiration_date:
            if isinstance(w.expiration_date, list):
                expiration_date = w.expiration_date[0]
            else:
                expiration_date = w.expiration_date
            days_until_expiration = (expiration_date - datetime.now()).days
            return days_until_expiration
        else:
            return None
    except Exception as e:
        print(f"Error retrieving domain expiration time: {e}")
        return None

def qty_ip_resolved(url):
    domain = urlparse(url).netloc
    
    try:
        return len(socket.gethostbyname_ex(domain)[2])
    except socket.gaierror:
        return 0

def qty_nameservers(url):
    domain = urlparse(url).netloc
    
    try:
        answers = dns.resolver.query(domain, 'NS')
        return len(answers)
    except dns.exception.DNSException:
        return 0

def qty_mx_servers(url):
    domain = urlparse(url).netloc
    
    try:
        answers = dns.resolver.query(domain, 'MX')
        return len(answers)
    except dns.exception.DNSException:
        return 0

def ttl_hostname(url):
    hostname = url.split("//")[-1].split("/")[0].split('?')[0]
    
    try:
        answer = dns.resolver.query(hostname, 'A')
        return answer.rrset.ttl
    except dns.exception.DNSException:
        return 0

def tls_ssl_certificate(url):
    try:
        # This is a very basic check for an SSL certificate
        return ssl.get_server_certificate((url, 443))
    except Exception:
        return 0

def qty_redirects(url):
    try:
        response = requests.get(url)
        return len(response.history)
    except requests.RequestException:
        return 0

def google_index(url):
    try:
        response = requests.get(f"https://www.google.com/search?q=info:{url}")
        return "did not match any documents" not in response.text
    except Exception as e:
        print(f"Error fetching Google index information: {e}")
        return 0

def url_shortened(url):
    # This function should check if the URL is a shortened URL.
    # This could be done by checking against a list of known URL shortening services.
    known_shorteners = ['bit.ly', 'goo.gl', 'tinyurl.com', 'ow.ly']
    for shortener in known_shorteners:
        if shortener in url:
            return 1
    return 0
