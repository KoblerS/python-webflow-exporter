# Python Webflow Exporter

Python Webflow Exporter is a command-line tool that recursively scrapes and downloads all assets (HTML, CSS, JS, images, media) from public `.webflow.io` websites. It provides optional Webflow badge removal and automatic sitemap generation.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Dependencies and Environment Setup
- **Python Version**: Requires Python 3.10+ (tested with Python 3.12.3)
- **Install Dependencies**: 
  ```bash
  pip install -r requirements.txt
  ```
  - **Timing**: Takes ~10 seconds. NEVER CANCEL. Set timeout to 30+ seconds.
  - **Dependencies**: requests, argparse, beautifulsoup4, halo, pylint, setuptools

### Build and Installation
- **CRITICAL BUILD LIMITATION**: Standard installation methods (`pip install -e .`, `python -m build`) frequently fail due to network timeouts when accessing PyPI repositories. This appears to be an environment limitation, not a code issue.

- **Primary Installation Method** (may fail due to network issues):
  ```bash
  pip install -e .
  ```
  - **Timing**: 15-30 seconds when successful. NEVER CANCEL. Set timeout to 60+ minutes due to potential network delays.
  - **Failure Mode**: Often fails with "Read timed out" errors from PyPI.

- **Alternative Build Method** (also may fail):
  ```bash
  pip install build
  python -m build
  ```
  - **Timing**: 15-30 seconds when successful. NEVER CANCEL. Set timeout to 60+ minutes.

- **Development Workaround** (for testing when installation fails):
  ```bash
  # Run CLI directly with path adjustment
  export PYTHONPATH=/home/runner/work/python-webflow-exporter/python-webflow-exporter:$PYTHONPATH
  # Note: Direct execution may fail due to package metadata issues
  ```

### Linting (ALWAYS WORKS)
- **Run Linting**:
  ```bash
  pylint webexp
  ```
  - **Timing**: ~4 seconds. NEVER CANCEL. Set timeout to 15+ seconds.
  - **Configuration**: Uses `.pylintrc` with custom rules (max-locals=20, max-branches=20, max-statements=60)
  - **Expected Result**: Should achieve 10.00/10 score

### CLI Usage
- **Help Command**:
  ```bash
  webexp --help
  # OR if not installed:
  python -m webexp.cli --help
  ```
  - **Timing**: ~0.2 seconds

- **Basic Usage**:
  ```bash
  webexp --url https://example.webflow.io
  webexp --url https://example.webflow.io --output my_output --remove-badge --generate-sitemap
  ```

- **Available Options**:
  - `--url URL` (required): Public Webflow site URL to scrape
  - `--output OUTPUT` (default: "out"): Output folder
  - `--remove-badge`: Remove Webflow badge from JS files
  - `--generate-sitemap`: Generate sitemap.xml file
  - `--debug`: Enable debug output
  - `--silent`: Silent mode, no output
  - `--version`: Show version

## Validation and Testing

### Manual Validation Scenarios
After making changes, ALWAYS test the following scenarios:

1. **CLI Help and Version**:
   ```bash
   webexp --help
   webexp --version
   ```

2. **URL Validation** (if network available):
   ```bash
   webexp --url https://valid-webflow-site.webflow.io --output test_out --debug
   ```
   - Should validate URL and detect Webflow-specific assets
   - Creates output directory structure
   - Downloads HTML, CSS, JS, images, and media files

3. **Error Handling**:
   ```bash
   webexp --url https://invalid-site.com --output test_out
   ```
   - Should gracefully handle invalid URLs
   - Should provide clear error messages

4. **Linting Validation** (CRITICAL - always run):
   ```bash
   pylint webexp
   ```
   - Must achieve perfect score (10.00/10)
   - CI will fail if linting issues exist

### Pre-commit Validation
ALWAYS run before committing changes:
```bash
pylint webexp
```
- **Timing**: ~4 seconds. NEVER CANCEL.
- **Requirement**: Must pass with 10.00/10 score or CI (.github/workflows/deploy-branch.yaml) will fail

## CI/CD Pipeline Information

### GitHub Workflows
- **Linting**: `.github/workflows/deploy-branch.yaml`
  - Runs on push to main and pull requests
  - Uses Python 3.12
  - Installs requirements and runs `pylint webexp`
  - **Timing**: Typically 2-3 minutes total

- **Building**: Same workflow includes build test
  - Runs `pip install setuptools` and `python -m pip install .`
  - **Timing**: 2-5 minutes depending on network

- **Release**: `.github/workflows/release.yaml`
  - Publishes to PyPI on release
  - Uses `python -m build` and `twine upload`

## Common Tasks and Quick Reference

### Repository Structure
```
.
├── .github/workflows/     # CI/CD pipelines
├── webexp/               # Main package directory
│   ├── __init__.py      # Empty package init
│   └── cli.py           # Complete CLI implementation (400+ lines)
├── .gitignore           # Excludes out/, *.egg-info/, __pycache__/, build/, dist/
├── .pylintrc            # Linting configuration
├── pyproject.toml       # Build configuration and dependencies
├── requirements.txt     # Exact dependency versions
├── README.md            # User documentation
└── LICENSE.md, DISCLAIMER.md  # Legal documents
```

### Key Files to Monitor
- **webexp/cli.py**: Main application logic - monitor after making changes
- **pyproject.toml**: Build configuration and dependencies
- **requirements.txt**: Dependency versions (keep in sync with pyproject.toml)
- **.pylintrc**: Linting rules that must be followed

### Package Details
- **Entry Point**: `webexp = "webexp.cli:main"` (defined in pyproject.toml)
- **Build System**: setuptools with pyproject.toml
- **Dependencies**: All pinned to specific versions for reliability

## Troubleshooting

### Network Timeout Issues
- **Problem**: `pip install` commands timeout with "Read timed out" errors
- **Cause**: Environment network limitations when accessing PyPI
- **Workaround**: Use direct file execution methods for development
- **Note**: This is an environment issue, not a code issue

### Version Detection Issues
- **Problem**: `importlib.metadata.version("python-webflow-exporter")` fails
- **Cause**: Package not properly installed due to network issues
- **Workaround**: Temporarily hardcode version for development testing

### CLI Execution Issues
- **Problem**: Cannot run `webexp` command after installation failure
- **Solution**: Use `python -m webexp.cli` or direct file execution
- **Note**: May still require version detection workaround

## Development Notes

- **No Test Files**: Repository contains no automated tests - rely on manual validation
- **Code Quality**: Maintains perfect pylint score (10.00/10)
- **Network Dependencies**: CLI functionality requires internet access to scrape websites
- **Build Reliability**: Installation process may be unreliable due to network timeouts - this is a known limitation