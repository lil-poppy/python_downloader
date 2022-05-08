import os, requests, shutil


def download_file(filename, link, retries=0):
    request1 = requests.get(url=link, stream=True)
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
