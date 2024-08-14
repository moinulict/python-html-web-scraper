import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

visited_urls = set()

def create_directory_for_file(file_path):
    """Create directory for the file if it doesn't exist."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def download_file(session, url, directory, relative_path):
    """Download a file and save it to the specified directory with the given relative path."""
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        # Construct the full file path
        file_path = os.path.join(directory, relative_path)
        
        # Create necessary directories
        create_directory_for_file(file_path)
        
        # Save the file
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded: {relative_path}")
        return True
    except Exception as e:
        print(f"Failed to download {url}. Error: {e}")
        return False

def extract_urls_from_css(css_content):
    """Extract all URLs from CSS content."""
    url_pattern = re.compile(r'url\(["\']?(.*?)["\']?\)')
    return url_pattern.findall(css_content)

def download_and_store_css(session, css_url, base_directory):
    """Download a CSS file and store it in the directory specified by its reference."""
    css_parsed_url = urlparse(css_url)
    css_relative_path = css_parsed_url.path.lstrip('/')
    css_file_path = os.path.join(base_directory, css_relative_path)
    
    if download_file(session, css_url, base_directory, css_relative_path):
        # Load the downloaded CSS file to download referenced assets
        with open(css_file_path, 'r', encoding='utf-8') as file:
            css_content = file.read()
        
        # Extract URLs from CSS and download assets
        urls_in_css = extract_urls_from_css(css_content)
        for asset_url in urls_in_css:
            asset_url_clean = asset_url.strip('\'"')
            if asset_url_clean.startswith('data:'):  # Skip base64 encoded images
                continue
            asset_full_url = urljoin(css_url, asset_url_clean)
            asset_parsed_url = urlparse(asset_full_url)
            asset_relative_path = asset_parsed_url.path.lstrip('/')
            download_file(session, asset_full_url, base_directory, asset_relative_path)

def extract_background_image_url(style_content):
    """Extract the URL from a background-image style."""
    url_pattern = re.compile(r'url\(["\']?(.*?)["\']?\)')
    match = url_pattern.search(style_content)
    return match.group(1) if match else None

def clean_url(url):
    """Remove 'foores/' prefix from a URL if it exists."""
    return url.replace('foores/', '')

def download_images(session, tag, attr, html_url, base_directory):
    """Download images from src, data-src, and similar attributes."""
    img_url = tag.get(attr)
    if img_url:
        full_url = urljoin(html_url, img_url)
        relative_path = clean_url(urlparse(full_url).path.lstrip('/'))
        if download_file(session, full_url, base_directory, relative_path):
            # Update the tag's attribute to point to the local file
            tag[attr] = relative_path

def scrape_html(session, html_url, base_directory):
    """Scrape an HTML page and download its assets."""
    html_parsed_url = urlparse(html_url)
    html_relative_path = html_parsed_url.path.lstrip('/')
    if not html_relative_path:
        html_relative_path = 'index.html'
    
    html_file_path = os.path.join(base_directory, html_relative_path)
    
    # Ensure we don't visit the same page multiple times
    if html_url in visited_urls:
        return
    visited_urls.add(html_url)

    try:
        response = session.get(html_url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to retrieve the webpage {html_url}. Error: {e}")
        return

    # Ensure base directory exists
    create_directory_for_file(html_file_path)
    
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')

    # ---------- Download CSS Files ----------
    css_files = soup.find_all('link', rel='stylesheet')
    for css in css_files:
        css_href = css.get('href')
        if css_href:
            css_url = urljoin(html_url, css_href)
            download_and_store_css(session, css_url, base_directory)
            css['href'] = css_href

    # ---------- Download JS Files ----------
    js_files = soup.find_all('script', src=True)
    for js in js_files:
        js_src = js.get('src')
        if js_src:
            js_url = urljoin(html_url, js_src)
            js_relative_path = clean_url(urlparse(js_url).path.lstrip('/'))
            download_file(session, js_url, base_directory, js_relative_path)

    # ---------- Download Images from <img> Tags, Favicons, and Data Attributes ----------
    img_tags = soup.find_all('img') + soup.find_all('link', rel=lambda x: x and 'icon' in x)
    for img in img_tags:
        download_images(session, img, 'src', html_url, base_directory)
        download_images(session, img, 'data-src', html_url, base_directory)
    
    # Handle images referenced in data attributes (e.g., data-bg, style attributes)
    data_attrs = ['data-bg', 'data-original', 'data-background']
    for tag in soup.find_all():
        # Handle data-* attributes
        for attr in data_attrs:
            data_url = tag.get(attr)
            if data_url:
                # Extract the URL within the data attribute
                data_url_clean = extract_background_image_url(data_url)
                if data_url_clean:
                    data_full_url = urljoin(html_url, data_url_clean)
                    data_relative_path = clean_url(urlparse(data_full_url).path.lstrip('/'))
                    if download_file(session, data_full_url, base_directory, data_relative_path):
                        # Update the data attribute to point to the local file
                        tag[attr] = f"url('{data_relative_path}')"
        
        # Handle style attributes
        style_content = tag.get('style')
        if style_content:
            style_url = extract_background_image_url(style_content)
            if style_url:
                style_full_url = urljoin(html_url, style_url)
                style_relative_path = clean_url(urlparse(style_full_url).path.lstrip('/'))
                if download_file(session, style_full_url, base_directory, style_relative_path):
                    # Update the style attribute to point to the local file
                    tag['style'] = style_content.replace(style_url, style_relative_path)

    # ---------- Find and Download Other Linked HTML Files ----------
    html_links = soup.find_all('a', href=True)
    for link in html_links:
        link_href = link['href']
        if link_href.endswith('.html') or link_href.endswith('/'):
            # Construct the full URL and recurse
            linked_html_url = urljoin(html_url, link_href)
            scrape_html(session, linked_html_url, base_directory)
            link['href'] = link_href

    # ---------- Save the Updated HTML ----------
    with open(html_file_path, 'w', encoding='utf-8') as file:
        file.write(soup.prettify(formatter=None))
    print(f"Saved HTML to {html_file_path}")

def scrape_website(url, base_directory):
    """Scrape the website and maintain its folder structure."""
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    print(f"Starting to scrape website: {url}")
    scrape_html(session, url, base_directory)
    print("Scraping completed.")

# Load the URL and directory from environment variables
url = os.getenv('SCRAPE_URL', 'https://your-website.com')  # Default to 'https://your-website.com' if not set
base_directory = os.getenv('SCRAPE_DIR', 'website_content')  # Default to 'website_content' if not set

scrape_website(url, base_directory)
