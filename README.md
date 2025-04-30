# 🌏 Python Webflow Exporter

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

## Installation

```bash
git clone https://github.com/KoblerS/python-webflow-exporter.git
cd python-webflow-exporter
pip install -r requirements.txt
```

## Usage

```bash
python webexp.py --url https://example.webflow.io
```

### Arguments

### Arguments

| Argument         | Description                                | Default | Required |
| ---------------- | ------------------------------------------ | ------- | -------- |
| `--help`         | Show a help with available commands        | -       | ❌        |
| `--url`          | The public Webflow site URL to scrape      | –       | ✅        |
| `--output`       | Output folder where the site will be saved | out     | ❌        |
| `--remove-badge` | Whether to remove Webflow badge            | false   | ❌        |
| `--debug`        | Enable debug output                        | false   | ❌        |
| `--silent`       | Enable silent, no output                   | false   | ❌        |

### Output

After execution, your specified output folder will contain:

- All crawled HTML pages
- Associated assets like CSS, JS, images, and media
- Cleaned HTML and JS files with Webflow references rewritten

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

## License

This project is released under the [MIT License](./LICENSE.md).

## Disclaimer

This tool is provided "as-is" without any warranties. The author is not responsible for misuse or damage caused by this software. For full terms, see [DISCLAIMER.md](./DISCLAIMER.md).
