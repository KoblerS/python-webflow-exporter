"""Python Webflow Exporter CLI
This script allows you to scrape a Webflow site for assets and internal links,
download them, and process the HTML files to fix asset links. It also provides 
an option to remove the Webflow badge from the HTML files.
"""

from urllib.parse import urlparse, urljoin
import re
import json
import argparse
import os
import sys
import logging
from datetime import datetime
from importlib.metadata import version
import requests
from bs4 import BeautifulSoup
from halo import Halo

VERSION_NUM = version("python-webflow-exporter")
CDN_URL_REGEX = r"^(.*?)website-files\.com"
# pylint: disable=line-too-long
SCAN_CDN_REGEX = r"https:\/\/(?:[\w.-]+)\.website-files\.com(?:\/[a-f0-9]{24})?(?:\/(?:js|css|images))?(?:\/[\w\-./%]+)?"

logger = logging.getLogger(__name__)

stdout_log_formatter = logging.Formatter(
    '%(message)s'
)

stdout_log_handler = logging.StreamHandler(stream=sys.stdout)
stdout_log_handler.setLevel(logging.INFO)
stdout_log_handler.setFormatter(stdout_log_formatter)
logger.addHandler(stdout_log_handler)

def main():
    """Main function to handle command line arguments and initiate the scraping process."""

    parser = argparse.ArgumentParser(description="Python Webflow Exporter CLI")
    parser.add_argument("--url", required=True, help="the URL to fetch data from")
    parser.add_argument("--output", default="out", help="the folder to save the output to")
    parser.add_argument(
        "--remove-badge", 
        action="store_true",
        help="remove Webflow badge"
    )
    parser.add_argument(
        "--generate-sitemap", 
        action="store_true",
        help="generate a sitemap.xml file"
    )
    parser.add_argument(
        "--version", 
        action="version",
        version=f"python-webflow-exporter version: {VERSION_NUM}",
        help="show the version of the package"
    )
    parser.add_argument("--debug", action="store_true", help="enable debug mode")
    parser.add_argument("--silent", action="store_true", help="silent, no output")
    args = parser.parse_args()

    if args.debug and args.silent:
        logger.error("Invalid configuration: 'debug' and 'silent' options cannot be used together.")
        return

    if args.silent:
        logger.setLevel(logging.ERROR)

    if args.debug:
        logger.info("Debug mode enabled.")
        logger.setLevel(logging.DEBUG)

    output_path = os.path.join(os.getcwd(), args.output)
    if not check_url(args.url):
        return

    if not check_output_path_exists(output_path):
        logger.error("Output path does not exist. Please provide a valid path.")
        return

    # Clear output folder and create it if it doesn't exist
    clear_output_folder(output_path)

    spinner = Halo(text='Scraping the web...', spinner='dots')
    spinner.start()
    html_sites = scan_html(args.url)
    spinner.stop()

    logger.debug("Assets found: %s", json.dumps(html_sites, indent=2))

    spinner.start(text='Downloading...')

    # Download scraped assets
    download_assets(html_sites, output_path)
    spinner.stop()

    logger.info("Assets downloaded to %s", output_path)

    if args.remove_badge:
        spinner.start(text='Removing webflow badge...')
        remove_badge(output_path)
        spinner.stop()

    if args.generate_sitemap:
        spinner.start(text='Generating sitemap...')
        generate_sitemap(output_path, html_sites)
        spinner.stop()

    spinner.stop()

def check_url(url):
    """Check if the URL is a valid Webflow URL."""

    request = requests.get(url, timeout=10)
    if request.status_code != 200:
        logger.error("Invalid URL. Please provide a valid Webflow URL.")
        return False

    # Check for multiple Webflow indicators
    try:
        soup = BeautifulSoup(request.text, 'html.parser')

        webflow_indicators = []

        # Check 1: Links with "website-files.com" (existing check)
        links = soup.find_all('link', href=True)
        has_webflow_links = any("website-files.com" in link['href'] for link in links)
        if has_webflow_links:
            webflow_indicators.append("website-files.com links")

        # Check 2: Scripts with "website-files.com" (especially webflow.js)
        scripts = soup.find_all('script', src=True)
        has_webflow_scripts = any("website-files.com" in script['src'] for script in scripts)
        if has_webflow_scripts:
            webflow_indicators.append("website-files.com scripts")

        # Check 3: Meta generator tag with "Webflow"
        meta_generator = soup.find('meta', attrs={'name': 'generator', 'content': True})
        has_webflow_meta = (meta_generator and
                          'webflow' in meta_generator.get('content', '').lower())
        if has_webflow_meta:
            webflow_indicators.append("Webflow meta generator")

        # If any indicators are found, consider it a valid Webflow site
        if webflow_indicators:
            logger.debug("Webflow site detected with indicators: %s", ', '.join(webflow_indicators))
            return True

        logger.error(
            "The provided URL does not appear to be a Webflow site. "
            "No Webflow indicators found (website-files.com links/scripts or Webflow meta generator tag). "
            "Ensure the site is a valid Webflow site."
        )
        return False
    except (requests.RequestException, AttributeError) as e:
        logger.error("Error while parsing the URL: %s", e)
        return False

def check_output_path_exists(path):
    """Check if the output path exists."""

    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        return False
    return True

def clear_output_folder(path):
    """Clear the output folder if it exists, or create it if it doesn't."""

    if os.path.exists(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    else:
        os.makedirs(path)

def scan_html(url):
    """Scan the website for assets and internal links and return a dictionary."""

    visited = set()
    html = []
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

        print(f"Scanning {current_url}...")
        logger.debug("Found HTML page: %s", current_url)

        html.append(current_url)
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
                if re.match(CDN_URL_REGEX, css_url) is not None:
                    assets["css"].add(css_url)
                    logger.debug("Found CSS: %s", css_url)

        for link in soup.find_all('link', rel=["apple-touch-icon", "shortcut icon"]):
            href = link.get('href')
            if href:
                image_url = urljoin(current_url + "/", href)
                if re.match(CDN_URL_REGEX, image_url) is not None:
                    assets["images"].add(image_url)
                    logger.debug("Found image file: %s", css_url)

        for script in soup.find_all('script', src=True):
            src = script['src']
            if src:
                js_url = urljoin(current_url + "/", src)
                if re.match(CDN_URL_REGEX, js_url) is not None:
                    assets["js"].add(js_url)
                    logger.debug("Found Javascript file: %s", css_url)

        for img in soup.find_all('img', src=True):
            src = img['src']
            if src:
                img_url = urljoin(current_url + "/", src)
                if re.match(CDN_URL_REGEX, img_url) is not None:
                    assets["images"].add(img_url)
                    logger.debug("Found image file: %s", css_url)

        for media in soup.find_all(['video', 'audio'], src=True):
            src = media['src']
            if src:
                media_url = urljoin(current_url + "/", src)
                if re.match(CDN_URL_REGEX, media_url) is not None:
                    assets["media"].add(media_url)
                    logger.debug("Found media file: %s", css_url)

    recursive_scan(url)

    return {
        "html": sorted(html),
        "css": sorted(assets["css"]),
        "js": sorted(assets["js"]),
        "images": sorted(assets["images"]),
        "media": sorted(assets["media"])
    }

def download_assets(assets, output_folder):
    """Download assets from the CDN and save them to the output folder."""
    def download_file(url, output_path, asset_type):
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            if asset_type == 'html':
                process_html(output_path)
            elif asset_type == 'css':
                process_css(output_path, output_folder)
        except requests.RequestException as e:
            logger.error("Failed to download asset %s: %s", url, e)

    for asset_type, urls in assets.items():
        logger.debug("Downloading %s assets...", asset_type)
        for url in urls:
            # Create the output path by preserving the folder structure
            parsed_uri = urlparse(url)
            relative_path = url.replace(
                parsed_uri.scheme + "://", ""
            ).replace(parsed_uri.netloc, "")
            if asset_type != 'html':
                relative_path = re.sub(
                    SCAN_CDN_REGEX,
                    asset_type + "/",
                    url
                )
            if asset_type == 'html':
                if relative_path == "":
                    relative_path = "index.html"
                else:
                    relative_path = f"{relative_path}.html"

            output_path = os.path.join(output_folder,  relative_path.strip("/"))

            logger.info("Downloading %s to %s", url, output_path)
            download_file(url, output_path, asset_type)

def process_html(file):
    """Process the HTML file to fix asset links and format the HTML."""

    with open(file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Process JS
    for tag in soup.find_all([ 'script']):
        if tag.has_attr('src') and re.match(CDN_URL_REGEX, tag['src']) is not None:
            tag['src'] = re.sub(SCAN_CDN_REGEX, "/js/", tag['src'])

    # Process CSS
    for tag in soup.find_all([ 'link'], rel="stylesheet"):
        if tag.has_attr('href') and re.match(CDN_URL_REGEX, tag['href']) is not None:
            tag['href'] = re.sub(SCAN_CDN_REGEX, "/css/", tag['href'])

    # Process links like favicons
    for tag in soup.find_all([ 'link'], rel=["apple-touch-icon", "shortcut icon"]):
        if tag.has_attr('href') and re.match(CDN_URL_REGEX, tag['href']) is not None:
            tag['href'] = re.sub(SCAN_CDN_REGEX, "/images/", tag['href']).replace("//", "/")

    # Process IMG
    for tag in soup.find_all([ 'img']):
        if tag.has_attr('src') and re.match(CDN_URL_REGEX, tag['src']) is not None:
            tag['src'] = re.sub(SCAN_CDN_REGEX, "/images/", tag['src']).replace("//", "/")

    # Process Media
    for tag in soup.find_all([ 'video', 'audio']):
        if tag.has_attr('src') and re.match(CDN_URL_REGEX, tag['src']) is not None:
            tag['src'] = re.sub(SCAN_CDN_REGEX, "/media/", tag['src'])

    # Format and unminify the HTML
    formatted_html = soup.prettify()

    output_file = os.path.join(os.path.dirname(file), os.path.basename(file))
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(str(formatted_html))

    logger.debug("Processed %s", file)

def process_css(file_path, output_folder):
    """Process the CSS file to fix asset links."""

    if not os.path.exists(file_path):
        logger.error("CSS folder does not exist: %s", file_path)
        return

    with open(file_path, 'r+', encoding='utf-8') as f:
        content = f.read()
        logger.info("Processing CSS file: %s", file_path)

        # Find all image URLs in the CSS content
        image_urls = re.findall(SCAN_CDN_REGEX, content)
        print("Found %d image URLs in CSS file", image_urls)
        for match in image_urls:
            full_url = match[0]
            if full_url:
                # Download the image to the output path/images
                image_output_path = os.path.join(os.path.dirname(output_folder), "images", os.path.basename(full_url))
                try:
                    response = requests.get(full_url, stream=True, timeout=10)
                    response.raise_for_status()
                    os.makedirs(os.path.dirname(image_output_path), exist_ok=True)
                    with open(image_output_path, 'wb') as img_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            img_file.write(chunk)
                    logger.info("Downloaded image: %s", full_url)
                except requests.RequestException as e:
                    logger.error("Failed to download image %s: %s", full_url, e)

        # Replace CDN URLs with local paths for images
        updated_content = re.sub(SCAN_CDN_REGEX, "/images/", content).replace("//", "/")
        f.seek(0)
        f.write(updated_content)
        f.truncate()

def remove_badge(output_path):
    """Remove Webflow badge from the HTML files by modifying the JS files."""
    js_folder = os.path.join(os.getcwd(), output_path, "js")
    if not os.path.exists(js_folder):
        return

    for root, _, files in os.walk(js_folder):
        for file in files:
            if file.endswith(".js"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r+', encoding='utf-8') as f:
                    content = f.read()
                    if content.find('class="w-webflow-badge"') != -1:
                        logger.info("\nRemoving Webflow badge from %s", file_path)
                        content = content.replace(r'/\.webflow\.io$/i.test(h)', 'false')
                        content = content.replace('if(a){i&&e.remove();', 'if(true){i&&e.remove();')
                        f.seek(0)
                        f.write(content)
                        f.truncate()

def generate_sitemap(output_path, html_sites):
    """Generate a sitemap.xml file from the HTML files."""
    sitemap_path = os.path.join(output_path, "sitemap.xml")
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap-image/1.1">\n')
        for url in html_sites["html"]:
            f.write('  <url>\n')
            f.write(f'    <loc>{url}</loc>\n')
            current_date = datetime.now().strftime("%Y-%m-%d")
            f.write(f'    <lastmod>{current_date}</lastmod>\n')
            f.write('  </url>\n')
        f.write('</urlset>\n')

    logger.info("Sitemap generated at %s", sitemap_path)

if __name__ == "__main__":
    main()
