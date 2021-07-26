#!/usr/bin/env python
import os, requests, shutil, youtube_dl, time, socket
from mongoengine import connect, disconnect
from sys import exit
from app_variables import local_vars
from post.file_log import err_log, conn_log
from db.updater_models import Updater

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

# Error catcher for requests
def request_manager(
    url, stream=False, verify=True, retries=0, cookies=None, headers=dict()
):
    headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36"
        }
    )
    try:
        request1 = requests.get(
            url, headers=headers, stream=stream, verify=verify, cookies=cookies
        )
        request1.raise_for_status()
    except requests.exceptions.SSLError:
        return request_manager(
            url=url, stream=stream, verify=False, retries=retries, cookies=cookies
        )
    except requests.exceptions.Timeout:
        if retries < 5:
            return request_manager(
                url=url,
                stream=stream,
                verify=verify,
                retries=retries + 1,
                cookies=cookies,
            )
        else:
            return f"{url}: Giving up after {retries} retries"
    except requests.exceptions.ConnectionError as e:
        if retries < 1:
            return request_manager(
                url=url, stream=stream, verify=verify, retries=1, cookies=cookies
            )
        else:
            return f"Connection Error on {url}"
    except requests.exceptions.HTTPError as e:
        if request1.status_code == 400:
            return f"400: Bad Request ({url})"
        elif request1.status_code == 403:
            return f"403: Forbidden ({url})"
        elif request1.status_code == 404:
            return f"404: Not found ({url})"
        elif request1.status_code == 429:
            return f"429: Too Many Requests ({url})"
        else:
            return str(e)
    except Exception as e:
        return str(e)
    except:
        return f"That unknown error on {url}"
    return request1


# Python file file downloader example
def download_file(filename, link, requester=request_manager, retries=0):
    request1 = requester(url=link, stream=True)
    if not isinstance(request1, requests.models.Response):
        return request1
    if os.path.isfile(filename):
        if "Content-Length" in list(request1.headers.keys()):
            if request1.headers["Content-Length"] == str(os.path.getsize(filename)):
                return True
    if request1.status_code == 200:
        with open(filename, "wb+") as f:
            request1.raw.decode_content = True
            try:
                shutil.copyfileobj(request1.raw, f)
            except Exception as e:
                return f"Error while downloading {link}. Exception: {e}"
        if "Content-Length" in list(request1.headers.keys()):
            if request1.headers["Content-Length"] == str(os.path.getsize(filename)):
                return True
            else:
                if retries < 5:
                    download_file(
                        filename=filename,
                        link=link,
                        requester=requester,
                        retries=retries + 1,
                    )
                else:
                    return f"Error while downloading {link}. Giving up after {retries} retries"
        else:
            return True
    else:
        return f"Error while downloading {link}. Status code: {request1.status_code}"



# Selenium image downloader example (not recommended)
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


# Youtube-dl embedded example
def download_video_yt(id, filename=None):
    class MyLogger(object):
        def __init__(self, id):
            self.id = id

        def debug(self, msg):
            pass

        def warning(self, msg):
            pass

        def error(self, msg):
            return f"Youtube: Error while downloading {self.id} - {msg}"

    ydl_opts = {
        "format": "best[ext=mp4]/best[height<=1080]/best[height<=720]",
        "outtmpl": "%(id)s" if filename == None else str(filename),
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "cookiefile": f"{local_vars.yt_cookies_file}",
        "logger": MyLogger(id),
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.download([f"https://www.youtube.com/watch?v={id}"])
