import os, requests, shutil

def download_file(filename, link):
    r = requests.get(url=link, stream=True)
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