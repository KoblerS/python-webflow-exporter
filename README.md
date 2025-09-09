# 🌏 Python Webflow Exporter

[![PyPI version](https://img.shields.io/pypi/v/python-webflow-exporter)](https://pypi.org/project/python-webflow-exporter/)
[![python](https://img.shields.io/badge/Python-3.10-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://spdx.org/licenses/MIT.html)

A command-line tool to recursively scrape and download all assets (HTML, CSS, JS, images, media) from a public `.webflow.io` website. It also provides the option to automatically remove the Webflow badge from downloaded JavaScript files.

> [!CAUTION]
> ⚠️ DISCLAIMER: This repository is intended for **educational and personal use only**. It includes scripts and tools that may interact with websites created using Webflow. **The purpose of this repository is not to harm, damage, or interfere with Webflow’s platform, branding, or services.**
> By using this repository, you agree to the following:
>
> - You are solely responsible for how you use the contents of this repository.
> - The author does not condone the use of this code for commercial projects or to violate Webflow’s terms of service.
> - The author is not affiliated with Webflow Inc. in any way.
> - The author assumes no liability or responsibility for any damage, loss, or legal issues resulting from the use of this repository.
>
> If you are unsure about whether your intended use complies with applicable laws or platform terms, please consult legal counsel or refrain from using this repository.

## Features

- Recursively scans and downloads:
  - All linked internal pages
  - Stylesheets, JavaScript, images, and media files from Webflow CDN
- Optional removal of Webflow badge
- Fast processing
- Complete export of site
- Automatic creation of a sitemap.xml

## Installation

### Option 1: Install with pip

```bash
pip install python-webflow-exporter
```

### Option 2: Run directly with uv (recommended for one-time use)

First, install `uv` if you haven't already:

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**macOS (with Homebrew):**
```bash
brew install uv
```

**Windows:**
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

For other installation methods, see the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

Then run the tool directly:

```bash
uv tool run --from python-webflow-exporter webexp --url https://example.webflow.io
```

No installation required - `uv` will automatically handle dependencies and run the tool.

## Usage

### After pip installation

```bash
webexp --url https://example.webflow.io
```

### Arguments

| Argument             | Description                                | Default | Required |
| -------------------- | ------------------------------------------ | ------- | -------- |
| `--help`             | Show a help with available commands        | -       | ❌       |
| `--version`          | Print the current version                  | -       | ❌       |
| `--url`              | The public Webflow site URL to scrape      | –       | ✅       |
| `--output`           | Output folder where the site will be saved | out     | ❌       |
| `--remove-badge`     | remove Webflow badge                       | false   | ❌       |
| `--generate-sitemap` | generate a sitemap.xml file                | false   | ❌       |
| `--debug`            | Enable debug output                        | false   | ❌       |
| `--silent`           | Enable silent, no output                   | false   | ❌       |

### Output

After execution, your specified output folder will contain:

- All crawled HTML pages
- Associated assets like CSS, JS, images, and media
- Cleaned HTML and JS files with Webflow references rewritten
- Optionally removing the webflow badge

## Development Requirements

Make sure you have Python 3.8+ installed. Required packages are:

- requests
- argparse
- beautifulsoup4
- halo

_Optional:_

- pyinstaller
- pylint

They are included in `requirements.txt`.

## Local development

Clone the script and run the following commands to test it

```bash
git clone https://github.com/KoblerS/python-webflow-exporter.git
cd python-webflow-exporter

pip install -e .
```

Refer to [#usage](#usage) for more information on how to use the CLI.

## License

This project is released under the [MIT License](https://github.com/KoblerS/python-webflow-exporter/blob/main/LICENSE.md).

## Disclaimer

This tool is provided "as-is" without any warranties. The author is not responsible for misuse or damage caused by this software. For full terms, see [DISCLAIMER.md](https://github.com/KoblerS/python-webflow-exporter/blob/main/DISCLAIMER.md).
