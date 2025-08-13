# Growth for Impact - Job Listings Scraper

A production-ready web scraper that enriches company data with job listings information. This tool can automatically find company websites, careers pages, and extract job postings from various ATS (Applicant Tracking System) providers.

## Features

- **Company Website Discovery**: Automatically finds company websites using common domain patterns
- **Careers Page Detection**: Locates careers/jobs pages from company websites
- **ATS Provider Detection**: Identifies 11+ common ATS providers (Lever, Greenhouse, Workable, SmartRecruiters, etc.)
- **Job Extraction**: Extracts up to 3 most recent job postings per company with:
  - Job title
  - Location
  - URL
  - Short description
- **Playwright Support**: Handles JavaScript-heavy sites that require browser automation
- **Comprehensive Logging**: Detailed logging to both console and file
- **Rate Limiting**: Built-in delays to avoid being blocked
- **Error Handling**: Robust error handling with graceful fallbacks

## Requirements

- Python 3.10 or higher
- Internet connection
- Windows, macOS, or Linux

## Installation

1. **Clone or download the project files**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Install Playwright browsers** (required for JavaScript-heavy sites):
   ```bash
   playwright install
   ```

## Usage

### Basic Usage

```bash
python scraper.py --input "your_input_file.xlsx" --output "output.xlsx" --rows 50
```

### Command Line Options

- `--input`: Input Excel file path (required)
- `--output`: Output Excel file path (required)
- `--rows`: Number of rows to process (default: 50)
- `--start`: Starting row index (default: 0)
- `--no-playwright`: Disable Playwright (use only requests)
- `--verbose`: Enable verbose logging

### Examples

```bash
# Process first 25 companies
python scraper.py --input "companies.xlsx" --output "results.xlsx" --rows 25

# Process companies starting from row 50
python scraper.py --input "companies.xlsx" --output "results.xlsx" --start 50 --rows 30

# Disable Playwright (faster but may miss some sites)
python scraper.py --input "companies.xlsx" --output "results.xlsx" --no-playwright

# Enable verbose logging
python scraper.py --input "companies.xlsx" --output "results.xlsx" --verbose
```

## Input File Format

Your Excel file should contain a column with company names. The scraper will automatically detect columns with names like:
- "Company"
- "company"
- "Company Name"
- "Organization"
- etc.

### Example Input Format

| Company Name |
|--------------|
| Google       |
| Microsoft    |
| Apple        |
| ...          |

## Output Format

The scraper generates an Excel file with two sheets:

### Data Sheet
Contains enriched company data with the following columns:
- Company Name
- Website
- LinkedIn
- Careers Page URL
- Jobs Platform (detected ATS)
- Job 1-3: Title, Location, URL, Description
- Notes

### Methodology Sheet
Documents the scraping approach and tools used.

## Supported ATS Providers

The scraper can detect and extract jobs from:
- **Lever** (lever.co)
- **Greenhouse** (greenhouse.io)
- **Workable** (workable.com)
- **SmartRecruiters** (smartrecruiters.com)
- **Zoho Recruit** (zohorecruit.com)
- **iCIMS** (icims.com)
- **Breezy** (breezy.hr)
- **Indeed** (indeed.com)
- **BambooHR** (bamboohr.com)
- **Jobvite** (jobs.jobvite.com)
- **Bullhorn** (bullhorn.com)
- **Generic fallback** for unknown providers

## How It Works

1. **Website Discovery**: Tries common domain patterns (company.com, company.co, etc.)
2. **Careers Page Detection**: Scans company websites for careers/jobs links
3. **ATS Detection**: Identifies ATS provider from careers page URL
4. **Job Extraction**: Uses ATS-specific selectors to extract job details
5. **Fallback**: Generic extraction for unknown ATS providers

## Logging

The scraper creates detailed logs:
- Console output with progress information
- `scraper.log` file with detailed debugging information
- Use `--verbose` flag for additional logging

## Performance Considerations

- **Rate Limiting**: 2-second delay between requests to avoid being blocked
- **Playwright**: Slower but handles JavaScript-heavy sites
- **Requests-only**: Faster but may miss dynamic content
- **Memory Usage**: Processes companies one at a time to minimize memory usage

## Troubleshooting

### Common Issues

1. **"Input file not found"**
   - Ensure the input file path is correct
   - Use absolute paths if needed

2. **"No company-like column found"**
   - Ensure your Excel file has a column with company names
   - Column name should contain "company" (case-insensitive)

3. **Playwright installation issues**
   - Run `playwright install` after installing requirements
   - On Linux, you may need additional dependencies

4. **Slow performance**
   - Use `--no-playwright` for faster processing
   - Reduce the number of rows with `--rows`

5. **Missing job data**
   - Some companies may not have public job listings
   - ATS providers may change their structure
   - Check the log file for specific errors

### Getting Help

1. Check the `scraper.log` file for detailed error information
2. Use `--verbose` flag for additional debugging output
3. Ensure your internet connection is stable
4. Try processing a smaller number of companies first

## Limitations

- **Accuracy**: Website discovery is based on common patterns and may not find all companies
- **Rate Limits**: Some websites may block automated requests
- **Dynamic Content**: JavaScript-heavy sites require Playwright
- **ATS Changes**: ATS providers may update their structure, requiring scraper updates
- **Manual Verification**: Results should be manually verified for production use

## Legal and Ethical Considerations

- Respect website terms of service and robots.txt files
- Use reasonable rate limiting to avoid overwhelming servers
- Consider reaching out to companies for official data when possible
- This tool is for educational and research purposes

## Contributing

To improve the scraper:
1. Add new ATS provider patterns to `COMMON_ATS`
2. Enhance job extraction functions for specific providers
3. Improve website discovery algorithms
4. Add support for additional data sources

## License

This project is provided as-is for educational and research purposes. Please ensure compliance with applicable laws and website terms of service. 