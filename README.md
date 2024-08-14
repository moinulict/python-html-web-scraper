# Python HTML Web Scraper

A powerful and customizable Python-based web scraper designed to extract HTML content, including images, JavaScript, and CSS files. This tool allows you to scrape and download entire web pages, making it ideal for data analysis, offline viewing, or site mirroring.

## Features

- Scrape HTML content, images, JavaScript, and CSS files.
- Save the scraped content in a specified directory.
- Simple configuration via environment variables.

## Requirements

- Python 3.7 or higher
- Virtual environment (optional but recommended)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/moinulict/python-html-web-scraper.git
cd python-html-web-scraper

```
### 2. Set Up the Virtual Environment
It's recommended to use a virtual environment to manage dependencies. Here's how you can set it up using venv:

```bash
python3 -m venv venv
source venv/bin/activate
```

Note: If you don't have venv installed, you can install it using:

```bash
sudo apt-get update
sudo apt-get install python3-venv
```

### 3. Install Dependencies
With the virtual environment activated, install the required Python packages:

```bash
pip install -r requirements.txt
```

### Configuration
Set up the environment variables required for the scraper. Create a .env file in the project's root directory with the following content:

```bash
SCRAPE_URL=https://your-website.com
SCRAPE_DIR=website_content
```

- `SCRAPE_URL`: Replace https://your-website.com with the URL of the website you want to scrape.
- `SCRAPE_DIR`: Specifies the directory where the scraped content will be saved. You can change website_content to any directory name you prefer.

### Usage
After completing the above steps, you can run the scraper using:

```bash
python main.py
```

The scraper will start downloading the content from the specified SCRAPE_URL and save it in the SCRAPE_DIR directory.

### Deactivating the Virtual Environment
Once you're done, you can deactivate the virtual environment by running:
```bash
deactivate
```

### Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue.

### License
This project is licensed under the MIT License - see the LICENSE file for details.
