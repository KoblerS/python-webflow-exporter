import requests
import argparse
import os
from bs4 import BeautifulSoup
from halo import Halo
from urllib.parse import urlparse

CDN_URL = "https://cdn.prod.website-files.com"

def main():
  parser = argparse.ArgumentParser(description="Python Webflow Exporter CLI")
  parser.add_argument("--url", required=True, help="The URL to fetch data from")
  parser.add_argument("--output", default="out", help="The file to save the output to")
  args = parser.parse_args()

  output_path = os.path.join(os.getcwd(), args.output)

  print(output_path)

  if not check_url(args.url):
    print("Invalid URL. Please provide a valid Webflow URL.")
    return
  
  if not check_output_path_exists(output_path):
    print("Output path does not exist. Please provide a valid path.")
    return

  spinner = Halo(text='Scraping...', spinner='dots')
  spinner.start()
  sites = scan_sites(args.url)
  spinner.stop()
  print(sites)

  print(output_path)

  spinner.start(text='Downloading assets...')
  download_assets(sites, output_path)
  spinner.stop()
  print(f"Assets downloaded to {output_path}")


def check_url(url):
  return url.startswith("https://") and url.rstrip("/").endswith(".webflow.io")

def check_output_path_exists(path):
  folder = os.path.dirname(path)
  if not os.path.exists(folder):
    return False
  return True

def scan_sites(url):
  visited = set()
  sites = []
  assets = {"css": set(), "js": set(), "images": set(), "media": set()}

  def recursive_scan(current_url):
    current_url = current_url.rstrip("/")  # Remove trailing slash
    if current_url in visited:
      return
    visited.add(current_url)

    try:
      response = requests.get(current_url)
      response.raise_for_status()
    except requests.RequestException as e:
      return

    sites.append(current_url)

    # Parse the page content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find internal links in the page
    for link in soup.find_all('a', href=True):
      href = link['href']
      if href.startswith("/") or href.startswith(current_url):
        next_url = href if href.startswith("http") else current_url.rstrip("/") + "/" + href.lstrip("/")
        if next_url.startswith(current_url):  # Ensure it's an internal link
          recursive_scan(next_url)

    # Find CSS files
    for css in soup.find_all('link', rel="stylesheet"):
      href = css.get('href')
      if href:
        css_url = href if href.startswith("http") else current_url.rstrip("/") + "/" + href.lstrip("/")
        if css_url.startswith(CDN_URL):
          assets["css"].add(css_url)

    # Find JavaScript files
    for script in soup.find_all('script', src=True):
      src = script['src']
      if src:
        js_url = src if src.startswith("http") else current_url.rstrip("/") + "/" + src.lstrip("/")
        if js_url.startswith(CDN_URL):
          assets["js"].add(js_url)

    # Find images
    for img in soup.find_all('img', src=True):
      src = img['src']
      if src:
        img_url = src if src.startswith("http") else current_url.rstrip("/") + "/" + src.lstrip("/")
        if img_url.startswith(CDN_URL):
          assets["images"].add(img_url)

    # Find other media (e.g., video, audio)
    for media in soup.find_all(['video', 'audio'], src=True):
      src = media['src']
      if src:
        media_url = src if src.startswith("http") else current_url.rstrip("/") + "/" + src.lstrip("/")
        if media_url.startswith(CDN_URL):
          assets["media"].add(media_url)

  recursive_scan(url)
  return {"sites": sites, **{key: list(value) for key, value in assets.items()}}

def download_assets(assets, output_folder):
  def download_file(url, output_path, asset_type):
    try:
      response = requests.get(url, stream=True)
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
      if relative_path == "":
        relative_path = "index.html"
      else:
        relative_path = f"{relative_path}.html"
      
      # Ensure the relative path does not overwrite the folder structure
      output_path = os.path.join(output_folder, relative_path.lstrip("/"))
      print(f"Downloading {url} to {output_path}")
      download_file(url, output_path, asset_type)

def process_html(file):
  with open(file, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

  # Replace all URLs in the file that start with CDN_URL with an empty string
  for tag in soup.find_all(['link', 'script', 'img', 'video', 'audio']):
    if tag.has_attr('href') and tag['href'].startswith(CDN_URL):
      tag['href'] = tag['href'].replace(CDN_URL, "")
    if tag.has_attr('src') and tag['src'].startswith(CDN_URL):
      tag['src'] = tag['src'].replace(CDN_URL, "")

  with open(file, 'w', encoding='utf-8') as f:
    f.write(str(soup))

  print(f"Processed {file}")

if __name__ == "__main__":
  main()