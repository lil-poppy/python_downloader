#!/usr/bin/env python
import os, requests, shutil, youtube_dl, time, socket
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Ignore InsecureRequestWarning if verify=false is passed as an argument to requests.get()
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

def request_manager(url, stream=False, verify=True, retrys=0):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36'}
    try:
        r = requests.get(url, headers=headers, stream=stream, verify=verify)
        # Raise HTTPError if status code is 4xx or 5xx
        r.raise_for_status()
    # Catch SSLError
    except requests.exceptions.SSLError:
        # Run it again with verify=False (for SSL certificate)
        return request_manager(url=url, stream=stream, verify=False, retrys=retrys)
    # Catch Timeout
    except requests.exceptions.Timeout:
        # Retry 4 more times
        if retrys < 5:
            return request_manager(url=url, stream=stream, verify=verify, retrys=retrys+1)
        # If after 5 runs it still gets a timeout, return
        else:
            return f"Timeout on {url}"
    # Catch ConnectionError
    except requests.exceptions.ConnectionError as e:
        # Try one more time
        if retrys < 1:
            return request_manager(url=url, stream=stream, verify=verify, retrys=1)
        # If i catch the error again, return
        else:
            return f"Connection Error on {url}"
    # Catch HTTPError raised because i ran r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # Catch some common http errors
        if r.status_code == 400:
            return f"400: Bad Request ({url})"
        elif r.status_code == 403:
            return f"403: Forbidden ({url})"
        elif r.status_code == 404:
            return f"404: Not found ({url})"
        elif r.status_code == 429:
            return f"429: Too Many Requests ({url})"
        # If the error isn't specifically caught, return it as a string
        else:
            return str(e)
    # If nothing goes wrong, return r
    return r

# Requests file downloader
def download_file(filename, link):
    r = request_manager(url=link, stream=True)
    # if r is not requests.models.Response, it means is an error caugth in request_manager
    if not isinstance(r, requests.models.Response):
        return r
    # Check if the file exists
    if os.path.isfile(filename):
        if "Content-Length" in list(r.headers.keys()):
            # Check if Content-Length == it's size
            if r.headers["Content-Length"] == str(os.path.getsize(filename)):
                return "File already exists"
        # If the header doesn't contain Content-Length, we can't check if the local one is the same as the remote one, but we asume it is
        else:
            return "File already exists"
    # If the status code is 200 (OK), download the file
    if r.status_code == 200:
        with open(filename, 'wb+') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        if "Content-Length" in list(r.headers.keys()):
            # If Content-Length == to the file og the size we return
            if r.headers["Content-Length"] == str(os.path.getsize(filename)):
                return "File downloaded"
            # If Content-Length != than the file size, we restart the downloader. From experience, sometimes the connection closes and the best solution is to restart the download
            else:
                return download_file(filename, link)
        # If the header doesn't contain Content-Length, we asume we downloaded the whole file
        else:
            return "File downloaded"
    # If the status code is not 200, than we got an error
    else:
        return f"Error while downloading {link}. Status code: {r.status_code}"

# Selenium image downloader
def selenium_download(driver, img_url, filename, width=None, height=None):
    driver.get(img_url)
    driver.find_element(By.TAG_NAME, "img").click()
    orig_h = driver.execute_script("return window.outerHeight")
    orig_w = driver.execute_script("return window.outerWidth")
    margin_h = orig_h - driver.execute_script("return window.innerHeight")
    margin_w = orig_w - driver.execute_script("return window.innerWidth")
    new_h = driver.execute_script('return document.getElementsByTagName("img")[0].height')
    new_w = driver.execute_script('return document.getElementsByTagName("img")[0].width')
    if width != None:
        new_w = width
    if height != None:
        new_h = height
    driver.set_window_size(new_w + margin_w, new_h + margin_h)
    img_val = driver.get_screenshot_as_png()
    with open(filename, 'wb+') as f:
            f.write(img_val)
    return True
