#!/usr/bin/env python
import os
import shutil

import requests
import youtube_dl

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)


def request_manager(url, retries=0, headers=None, method="GET", **kwargs):
    default_headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"
    }
    if headers is None:
        headers = default_headers
    else:
        headers.update(default_headers)
    try:
        if method == "GET":
            request1 = requests.get(url, headers=headers, **kwargs)
        elif method == "POST":
            request1 = requests.post(url, headers=headers, **kwargs)
        request1.raise_for_status()
    except requests.exceptions.SSLError:
        if method == "GET":
            request1 = requests.get(url, headers=headers, verify=False, **kwargs)
        elif method == "POST":
            request1 = requests.post(url, headers=headers, verify=False, **kwargs)
    except requests.exceptions.Timeout:
        if retries < 5:
            if method == "GET":
                request1 = request_manager(
                    url, headers=headers, retries=retries + 1, **kwargs
                )
            elif method == "POST":
                request1 = request_manager(
                    url, headers=headers, retries=retries + 1, **kwargs
                )
        else:
            return f"{url}: Giving up after {retries} retries"
    except requests.exceptions.ConnectionError:
        if retries < 1:
            if method == "GET":
                request1 = request_manager(url, headers=headers, retries=1, **kwargs)
            elif method == "POST":
                request1 = request_manager(url, headers=headers, retries=1, **kwargs)
        else:
            return f"Connection Error on {url}"
    except requests.exceptions.HTTPError as e:
        if request1.status_code == 400:
            return f"400: Bad Request ({url})"
        if request1.status_code == 403:
            return f"403: Forbidden ({url})"
        if request1.status_code == 404:
            return f"404: Not found ({url})"
        if request1.status_code == 429:
            return f"429: Too Many Requests ({url})"
        return str(e)
    except Exception as e:
        return str(e)
    except:
        return f"That unknown error on {url}"
    return request1


def download_file(filename, link, requester=request_manager, retries=0):
    request1 = requester(url=link, stream=True)
    if not isinstance(request1, requests.models.Response):
        return request1
    if os.path.isfile(filename):
        if "Content-Length" in list(request1.headers.keys()):
            if request1.headers["Content-Length"] == str(os.path.getsize(filename)):
                return 0
    if request1.status_code == 200:
        with open(filename, "wb+") as f:
            request1.raw.decode_content = True
            try:
                shutil.copyfileobj(request1.raw, f)
            except Exception as e:
                return f"Error while downloading {link}. Exception: {e}"
        if "Content-Length" in list(request1.headers.keys()):
            if request1.headers["Content-Length"] == str(os.path.getsize(filename)):
                return 0
            if retries < 5:
                download_file(
                    filename=filename,
                    link=link,
                    requester=requester,
                    retries=retries + 1,
                )
            else:
                return (
                    f"Error while downloading {link}. Giving up after {retries} retries"
                )
        else:
            return 0
    else:
        return f"Error while downloading {link}. Status code: {request1.status_code}"


def download_video_yt(uid, filename=None):
    class MyLogger:
        def __init__(self, uid):
            self.uid = uid

        def debug(self, msg):
            pass

        def warning(self, msg):
            pass

        def error(self, msg):
            if "ERROR: giving up after 0 retries" not in msg:
                return f"Youtube: Error while downloading {self.uid} - {msg}"
            return 1

    ydl_opts = {
        "format": "best[ext=mp4]",
        "outtmpl": str(filename),
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "cookiefile": "yt_cookies.txt", # Cookies file
        "logger": MyLogger(uid),
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.download([f"https://www.youtube.com/watch?v={uid}"])


def download_video_tw(link, filename):
    class MyLogger:
        def __init__(self, link):
            self.link = link

        def debug(self, msg):
            pass

        def warning(self, msg):
            pass

        def error(self, msg):
            return f"Twitch: Error while downloading {self.link} - {msg}"

    ydl_opts = {
        "format": "best[ext=mp4]",
        "outtmpl": str(filename),
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "logger": MyLogger(link),
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.download([link])


def download_audio_tw(link, filename):
    class MyLogger:
        def __init__(self, link):
            self.link = link

        def debug(self, msg):
            pass

        def warning(self, msg):
            pass

        def error(self, msg):
            return f"Twitch: Error while downloading {self.link} - {msg}"

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": str(filename),
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "logger": MyLogger(link),
        "writethumbnail": True,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.download([link])


def download_youtube_dl(link, filename):
    class MyLogger:
        def __init__(self, link):
            self.link = link

        def debug(self, msg):
            pass

        def warning(self, msg):
            pass

        def error(self, msg):
            return f"Downloader youtube-dl: Error while downloading {self.link} - {msg}"
            
    ydl_opts = {
        "outtmpl": filename,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "logger": MyLogger(link),
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.download([link])
