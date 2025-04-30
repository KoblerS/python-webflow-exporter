import requests
import argparse
import os
from bs4 import BeautifulSoup
from halo import Halo
from urllib.parse import urlparse, urljoin
import re
import json

CDN_URL = "https://cdn.prod.website-files.com"
SCAN_CDN_REGEX = r"https://cdn\.prod\.website-files\.com/([a-f0-9]{24})/"

def main():
  parser = argparse.ArgumentParser(description="Python Webflow Exporter CLI")
  parser.add_argument("--url", required=True, help="The URL to fetch data from")
  parser.add_argument("--output", default="out", help="The file to save the output to")
  parser.add_argument("--remove-badge", default="true", help="Remove Badge from the HTML")
  parser.add_argument("--debug", action="store_true", help="Enable debug mode")
  args = parser.parse_args()

  output_path = os.path.join(os.getcwd(), args.output)
  if not check_url(args.url):
    print("Invalid URL. Please provide a valid Webflow URL.")
    return
  
  if not check_output_path_exists(output_path):
    print("Output path does not exist. Please provide a valid path.")
    return
  
  clear_output_folder(output_path)

  spinner = Halo(text='Scraping...', spinner='dots')
  spinner.start()
  sites = scan_sites(args.url)
  spinner.stop()

  if args.debug:
    print(f"Assets found: {json.dumps(sites, indent=2)}")

  spinner.start(text='Downloading assets...')

  download_assets(sites, output_path)

  if args.remove_badge.lower() == "true":
     remove_badge()

  spinner.stop()
  print(f"Assets downloaded to {output_path}")


def check_url(url):
  return url.startswith("https://") and url.rstrip("/").endswith(".webflow.io")

def check_output_path_exists(path):
  folder = os.path.dirname(path)
  if not os.path.exists(folder):
    return False
  return True

def clear_output_folder(path):
  if os.path.exists(path):
    for root, dirs, files in os.walk(path, topdown=False):
      for name in files:
        os.remove(os.path.join(root, name))
      for name in dirs:
        os.rmdir(os.path.join(root, name))
  else:
    os.makedirs(path)

def scan_sites(url):
    visited = set()
    sites = []
    assets = {"css": set(), "js": set(), "images": set(), "media": set()}

    base_domain = urlparse(url).netloc

    def recursive_scan(current_url):
        current_url = current_url.rstrip("/")
        if current_url in visited:
            return
        visited.add(current_url)

        try:
            response = requests.get(current_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException:
            return

        # Only scan HTML pages
        if "text/html" not in response.headers.get("Content-Type", ""):
            return

        sites.append(current_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find internal links
        for link in soup.find_all('a', href=True):
            href = link['href']
            joined_url = urljoin(current_url + "/", href)
            parsed_url = urlparse(joined_url)

            # Only follow internal links
            if parsed_url.netloc == base_domain:
                normalized_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
                recursive_scan(normalized_url)

        # Collect assets
        for css in soup.find_all('link', rel="stylesheet"):
            href = css.get('href')
            if href:
                css_url = urljoin(current_url + "/", href)
                if css_url.startswith(CDN_URL):
                    assets["css"].add(css_url)

        for link in soup.find_all('link', rel=["apple-touch-icon", "shortcut icon"]):
            href = link.get('href')
            if href:
                image_url = urljoin(current_url + "/", href)
                if image_url.startswith(CDN_URL):
                    assets["images"].add(image_url)

        for script in soup.find_all('script', src=True):
            src = script['src']
            if src:
                js_url = urljoin(current_url + "/", src)
                if js_url.startswith(CDN_URL):
                    assets["js"].add(js_url)

        for img in soup.find_all('img', src=True):
            src = img['src']
            if src:
                img_url = urljoin(current_url + "/", src)
                if img_url.startswith(CDN_URL):
                    assets["images"].add(img_url)

        for media in soup.find_all(['video', 'audio'], src=True):
            src = media['src']
            if src:
                media_url = urljoin(current_url + "/", src)
                if media_url.startswith(CDN_URL):
                    assets["media"].add(media_url)

    recursive_scan(url)

    return {
        "sites": sorted(sites),
        "css": sorted(assets["css"]),
        "js": sorted(assets["js"]),
        "images": sorted(assets["images"]),
        "media": sorted(assets["media"])
    }

def download_assets(assets, output_folder):
  def download_file(url, output_path, asset_type):
    try:
      headers = {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
      }
      response = requests.get(url, stream=True, headers=headers)
      response.raise_for_status()
      os.makedirs(os.path.dirname(output_path), exist_ok=True)
      with open(output_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
          file.write(chunk)
          if asset_type == 'sites':
            process_html(output_path)
    except requests.RequestException as e:
      print(f"Failed to download {url}: {e}")

  for asset_type, urls in assets.items():
    print(f"Downloading {asset_type} assets...")
    for url in urls:
      # Create the output path by preserving the folder structure
      parsed_uri = urlparse(url)
      relative_path = url.replace(parsed_uri.scheme + "://", "").replace(parsed_uri.netloc, "")
      if asset_type != 'sites':
        relative_path = re.sub(SCAN_CDN_REGEX, "images/" if asset_type == "images" else "", url)
         
      if asset_type == 'sites':
        if relative_path == "":
          relative_path = "index.html"
        else:
          relative_path = f"{relative_path}.html"

      output_path = os.path.join(
        output_folder, 
        relative_path.strip("/")
      )

      print(f"Downloading {url} to {output_path}")
      download_file(url, output_path, asset_type)

def process_html(file):
  with open(file, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f)

  # Process JS
  for tag in soup.find_all([ 'script']):
    if tag.has_attr('src') and tag['src'].startswith(CDN_URL):
      tag['src'] = re.sub(SCAN_CDN_REGEX, "/", tag['src'])

  # Process CSS
  for tag in soup.find_all([ 'link'], rel="stylesheet"):
    if tag.has_attr('href') and tag['href'].startswith(CDN_URL):
      tag['href'] = re.sub(SCAN_CDN_REGEX, "/", tag['href'])

  # Process links like favicons
  for tag in soup.find_all([ 'link'], rel=["apple-touch-icon", "shortcut icon"]):
    if tag.has_attr('href') and tag['href'].startswith(CDN_URL):
      tag['href'] = re.sub(SCAN_CDN_REGEX, "/images/", tag['href'])

  # Process IMG
  for tag in soup.find_all([ 'img']):
    if tag.has_attr('src') and tag['src'].startswith(CDN_URL):
      tag['src'] = re.sub(SCAN_CDN_REGEX, "/images/", tag['src'])

  # Process Media
  for tag in soup.find_all([ 'video', 'audio']):
    if tag.has_attr('src') and tag['src'].startswith(CDN_URL):
      tag['src'] = re.sub(SCAN_CDN_REGEX, "/media/", tag['src'])

  # Format and unminify the HTML
  formatted_html = soup.prettify()

  with open(file, 'w', encoding='utf-8') as f:
    f.write(str(soup))

  print(f"Processed {file}")

def remove_badge():
   print("Removing Webflow badge...")

if __name__ == "__main__":
  main()