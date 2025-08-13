"""
Growth for Impact - Job Listings Scraper
--------------------------------------
This script is a production-ready scraper you can run locally to:
- Read the input Excel file with company names
- Enrich each row with website, LinkedIn, careers page, jobs listings page
- Detect common ATS providers (Lever, Greenhouse, Zoho, Workable, SmartRecruiters, iCIMS)
- Scrape up to 3 most recent job postings per company (title, location, date, url, short desc)
- Write results back to a new Excel file (Data + Methodology tabs)

Notes:
- This script uses requests + BeautifulSoup for lightweight scraping and Playwright for JS-heavy sites.
- You MUST run this locally (internet required). The execution environment where you run it needs Python 3.10+.

How to run (recommended):
1. Create a virtualenv: python -m venv venv && source venv/bin/activate
2. Install deps: pip install -r requirements.txt
3. Run: python scraper.py --input "Growth For Impact Data Assignment.xlsx" --output "output.xlsx" --rows 50

After installing playwright: playwright install

--------------------------------------
"""

import re
import time
import json
import argparse
import logging
from pathlib import Path
from urllib.parse import urlparse, urljoin
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from playwright.sync_api import sync_playwright, Page, Browser
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Config ---
COMMON_ATS = [
    ("lever", re.compile(r"lever\.co|jobs\.lever\.co", re.I)),
    ("greenhouse", re.compile(r"greenhouse\.io|boards\.greenhouse\.io", re.I)),
    ("workable", re.compile(r"workable\.com|jobseekers\.workable\.com", re.I)),
    ("smartrecruiters", re.compile(r"smartrecruiters\.com", re.I)),
    ("zohorecruit", re.compile(r"zohorecruit\.com", re.I)),
    ("icims", re.compile(r"icims\.com", re.I)),
    ("breezy", re.compile(r"breezy\.hr", re.I)),
    ("indeed", re.compile(r"indeed\.com", re.I)),
    ("bamboo", re.compile(r"bamboohr\.com", re.I)),
    ("jobvite", re.compile(r"jobs\.jobvite\.com", re.I)),
    ("bullhorn", re.compile(r"bullhorn\.com", re.I)),
    ("personio", re.compile(r"personio\.com|jobs\.personio\.com", re.I)),
    ("teamtailor", re.compile(r"teamtailor\.com", re.I)),
    ("wellfound", re.compile(r"wellfound\.com", re.I)),
    ("calendly", re.compile(r"calendly\.com", re.I)),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Common careers page patterns
CAREERS_PATTERNS = [
    "careers", "jobs", "join-us", "join", "work-with-us", "we-are-hiring",
    "open-positions", "current-openings", "opportunities", "team", "about/careers"
]

# --- Helpers ---

def safe_get(url: str, timeout: int = 15) -> Optional[requests.Response]:
    """Safely make HTTP request with error handling."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return r
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request failed for {url}: {e}")
        return None

def find_company_website(company_name: str) -> Optional[str]:
    """Try to find company website using common patterns."""
    # Clean company name
    clean_name = re.sub(r'[^\w\s]', '', company_name).strip().lower()
    clean_name = re.sub(r'\s+', '', clean_name)
    
    # Common TLDs to try
    tlds = ['.com', '.co', '.org', '.net', '.io', '.ai', '.tech']
    
    for tld in tlds:
        candidate = f"https://{clean_name}{tld}"
        r = safe_get(candidate)
        if r and r.status_code == 200:
            logger.info(f"Found website for {company_name}: {candidate}")
            return candidate
    
    return None

def find_careers_link_from_home(root_url: str, playwright_page: Optional[Page] = None) -> Optional[str]:
    """Fetch root_url and look for likely careers/jobs links."""
    if playwright_page:
        try:
            playwright_page.goto(root_url, wait_until='networkidle', timeout=30000)
            content = playwright_page.content()
            soup = BeautifulSoup(content, "html.parser")
        except Exception as e:
            logger.warning(f"Playwright failed for {root_url}: {e}")
            r = safe_get(root_url)
            if not r or r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, "html.parser")
    else:
        r = safe_get(root_url)
        if not r or r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
    
    candidates = []
    
    # Look for links with careers-related text or href
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        text = (a.get_text() or "").lower()
        
        # Check if link contains careers patterns
        if any(pattern in href for pattern in CAREERS_PATTERNS) or \
           any(pattern in text for pattern in ["career", "careers", "jobs", "join us", "we're hiring", "we are hiring", "open positions"]):
            url = urljoin(root_url, a["href"])
            candidates.append((url, text))
    
    # Also check for navigation menus
    nav_selectors = ['nav', '.nav', '.navigation', '.menu', '.header', '.main-menu']
    for selector in nav_selectors:
        nav = soup.select_one(selector)
        if nav:
            for a in nav.find_all("a", href=True):
                href = a["href"].lower()
                text = (a.get_text() or "").lower()
                if any(pattern in href for pattern in CAREERS_PATTERNS) or \
                   any(pattern in text for pattern in ["career", "careers", "jobs"]):
                    url = urljoin(root_url, a["href"])
                    candidates.append((url, text))
    
    # Return the first unique candidate
    seen = set()
    for url, text in candidates:
        if url not in seen:
            seen.add(url)
            logger.info(f"Found careers link: {url}")
            return url
    
    return None

def detect_ats(url: str) -> Optional[str]:
    """Detect ATS provider from URL."""
    for name, pattern in COMMON_ATS:
        if pattern.search(url):
            return name
    return None

def extract_jobs_from_ats(url: str, ats_name: str, limit: int = 3, playwright_page: Optional[Page] = None) -> List[Dict]:
    """Extract jobs from known ATS providers."""
    jobs = []
    
    try:
        if playwright_page:
            playwright_page.goto(url, wait_until='networkidle', timeout=30000)
            content = playwright_page.content()
            soup = BeautifulSoup(content, "html.parser")
        else:
            r = safe_get(url)
            if not r or r.status_code != 200:
                return jobs
            soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        logger.warning(f"Failed to load {url}: {e}")
        return jobs
    
    if ats_name == "lever":
        # Lever specific selectors
        selectors = [
            "[data-automation-id='posting']",
            ".posting",
            ".job-posting",
            "[data-qa='posting']"
        ]
        for selector in selectors:
            posts = soup.select(selector)
            if posts:
                for post in posts[:limit]:
                    job = extract_lever_job(post, url)
                    if job:
                        jobs.append(job)
                break
    
    elif ats_name == "greenhouse":
        # Greenhouse specific selectors
        selectors = [
            ".opening",
            ".position",
            "[data-qa='opening']",
            ".job-listing"
        ]
        for selector in selectors:
            posts = soup.select(selector)
            if posts:
                for post in posts[:limit]:
                    job = extract_greenhouse_job(post, url)
                    if job:
                        jobs.append(job)
                break
    
    elif ats_name == "workable":
        # Workable specific selectors
        posts = soup.select(".job-listing, .position, [data-qa='job-item']")
        for post in posts[:limit]:
            job = extract_workable_job(post, url)
            if job:
                jobs.append(job)
    
    elif ats_name == "smartrecruiters":
        # SmartRecruiters specific selectors
        posts = soup.select(".job-item, .position-item, [data-qa='job-card']")
        for post in posts[:limit]:
            job = extract_smartrecruiters_job(post, url)
            if job:
                jobs.append(job)
    
    elif ats_name == "personio":
        # Personio specific selectors
        posts = soup.select(".job-item, .position-item, [data-qa='job-card']")
        for post in posts[:limit]:
            job = extract_personio_job(post, url)
            if job:
                jobs.append(job)
    
    elif ats_name == "teamtailor":
        # Teamtailor specific selectors
        posts = soup.select(".job-item, .position-item, [data-qa='job-card']")
        for post in posts[:limit]:
            job = extract_teamtailor_job(post, url)
            if job:
                jobs.append(job)
    
    elif ats_name == "wellfound":
        # Wellfound specific selectors
        posts = soup.select(".job-item, .position-item, [data-qa='job-card']")
        for post in posts[:limit]:
            job = extract_wellfound_job(post, url)
            if job:
                jobs.append(job)
    
    else:
        # Generic fallback
        jobs = extract_generic_jobs(soup, url, limit)
    
    return jobs[:limit]

def extract_lever_job(post, base_url: str) -> Optional[Dict]:
    """Extract job details from Lever posting."""
    try:
        title_el = post.select_one("[data-automation-id='posting-title']") or \
                   post.select_one("a") or \
                   post.select_one(".posting-title")
        
        title = title_el.get_text(strip=True) if title_el else None
        link = urljoin(base_url, title_el["href"]) if title_el and title_el.has_attr("href") else None
        
        location_el = post.select_one("[data-automation-id='location']") or \
                     post.select_one(".location") or \
                     post.select_one(".posting-location")
        location = location_el.get_text(strip=True) if location_el else None
        
        # Try to get description
        desc_el = post.select_one(".posting-description") or \
                  post.select_one("[data-automation-id='posting-description']")
        description = desc_el.get_text(strip=True)[:200] + "..." if desc_el else ""
        
        return {
            "title": title,
            "url": link,
            "location": location,
            "description": description,
            "date": None
        }
    except Exception as e:
        logger.warning(f"Failed to extract Lever job: {e}")
        return None

def extract_greenhouse_job(post, base_url: str) -> Optional[Dict]:
    """Extract job details from Greenhouse posting."""
    try:
        title_el = post.select_one("a") or post.select_one(".position-title")
        title = title_el.get_text(strip=True) if title_el else None
        link = urljoin(base_url, title_el["href"]) if title_el and title_el.has_attr("href") else None
        
        location_el = post.select_one('.location') or post.select_one('.position-location')
        location = location_el.get_text(strip=True) if location_el else None
        
        desc_el = post.select_one('.position-description') or post.select_one('.description')
        description = desc_el.get_text(strip=True)[:200] + "..." if desc_el else ""
        
        return {
            "title": title,
            "url": link,
            "location": location,
            "description": description,
            "date": None
        }
    except Exception as e:
        logger.warning(f"Failed to extract Greenhouse job: {e}")
        return None

def extract_workable_job(post, base_url: str) -> Optional[Dict]:
    """Extract job details from Workable posting."""
    try:
        title_el = post.select_one("a") or post.select_one(".job-title")
        title = title_el.get_text(strip=True) if title_el else None
        link = urljoin(base_url, title_el["href"]) if title_el and title_el.has_attr("href") else None
        
        location_el = post.select_one('.location') or post.select_one('.job-location')
        location = location_el.get_text(strip=True) if location_el else None
        
        desc_el = post.select_one('.job-description') or post.select_one('.description')
        description = desc_el.get_text(strip=True)[:200] + "..." if desc_el else ""
        
        return {
            "title": title,
            "url": link,
            "location": location,
            "description": description,
            "date": None
        }
    except Exception as e:
        logger.warning(f"Failed to extract Workable job: {e}")
        return None

def extract_smartrecruiters_job(post, base_url: str) -> Optional[Dict]:
    """Extract job details from SmartRecruiters posting."""
    try:
        title_el = post.select_one("a") or post.select_one(".job-title")
        title = title_el.get_text(strip=True) if title_el else None
        link = urljoin(base_url, title_el["href"]) if title_el and title_el.has_attr("href") else None
        
        location_el = post.select_one('.location') or post.select_one('.job-location')
        location = location_el.get_text(strip=True) if location_el else None
        
        desc_el = post.select_one('.job-description') or post.select_one('.description')
        description = desc_el.get_text(strip=True)[:200] + "..." if desc_el else ""
        
        return {
            "title": title,
            "url": link,
            "location": location,
            "description": description,
            "date": None
        }
    except Exception as e:
        logger.warning(f"Failed to extract SmartRecruiters job: {e}")
        return None

def extract_personio_job(post, base_url: str) -> Optional[Dict]:
    """Extract job details from Personio posting."""
    try:
        title_el = post.select_one("a") or post.select_one(".job-title")
        title = title_el.get_text(strip=True) if title_el else None
        link = urljoin(base_url, title_el["href"]) if title_el and title_el.has_attr("href") else None
        
        location_el = post.select_one('.location') or post.select_one('.job-location')
        location = location_el.get_text(strip=True) if location_el else None
        
        return {
            "title": title,
            "url": link,
            "location": location,
            "description": "",
            "date": None
        }
    except Exception as e:
        logger.warning(f"Failed to extract Personio job: {e}")
        return None

def extract_teamtailor_job(post, base_url: str) -> Optional[Dict]:
    """Extract job details from Teamtailor posting."""
    try:
        title_el = post.select_one("a") or post.select_one(".job-title")
        title = title_el.get_text(strip=True) if title_el else None
        link = urljoin(base_url, title_el["href"]) if title_el and title_el.has_attr("href") else None
        
        location_el = post.select_one('.location') or post.select_one('.job-location')
        location = location_el.get_text(strip=True) if location_el else None
        
        return {
            "title": title,
            "url": link,
            "location": location,
            "description": "",
            "date": None
        }
    except Exception as e:
        logger.warning(f"Failed to extract Teamtailor job: {e}")
        return None

def extract_wellfound_job(post, base_url: str) -> Optional[Dict]:
    """Extract job details from Wellfound posting."""
    try:
        title_el = post.select_one("a") or post.select_one(".job-title")
        title = title_el.get_text(strip=True) if title_el else None
        link = urljoin(base_url, title_el["href"]) if title_el and title_el.has_attr("href") else None
        
        location_el = post.select_one('.location') or post.select_one('.job-location')
        location = location_el.get_text(strip=True) if location_el else None
        
        return {
            "title": title,
            "url": link,
            "location": location,
            "description": "",
            "date": None
        }
    except Exception as e:
        logger.warning(f"Failed to extract Wellfound job: {e}")
        return None

def extract_generic_jobs(soup: BeautifulSoup, base_url: str, limit: int) -> List[Dict]:
    """Generic job extraction for unknown ATS providers."""
    jobs = []
    
    # Look for job links with common patterns
    job_patterns = ['apply', 'job', 'careers', 'openings', 'positions', 'opportunities']
    
    anchors = []
    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        text = (a.get_text() or '').lower()
        
        # Skip navigation and general links
        if any(skip in text for skip in ['careers', 'jobs', 'opportunities', 'help', 'support', 'about']):
            continue
            
        if any(pattern in href for pattern in job_patterns) or \
           any(pattern in text for pattern in job_patterns):
            anchors.append(a)
    
    seen = set()
    for a in anchors:
        if len(jobs) >= limit:
            break
            
        href = urljoin(base_url, a['href'])
        if href in seen:
            continue
        seen.add(href)
        
        title = a.get_text(strip=True)
        # Better filtering for job titles
        if title and len(title) > 5 and len(title) < 100 and \
           not any(skip in title.lower() for skip in ['careers', 'jobs', 'opportunities', 'help', 'support', 'about', 'contact']):
            jobs.append({
                "title": title,
                "url": href,
                "location": None,
                "description": "",
                "date": None
            })
    
    return jobs

def find_linkedin_url(company_name: str) -> Optional[str]:
    """Try to construct LinkedIn company URL."""
    clean_name = re.sub(r'[^\w\s]', '', company_name).strip().lower()
    clean_name = re.sub(r'\s+', '-', clean_name)
    return f"https://www.linkedin.com/company/{clean_name}"

# --- Main workflow ---

def enrich_companies(df: pd.DataFrame, max_rows: Optional[int] = None, 
                    start_idx: int = 0, use_playwright: bool = True) -> pd.DataFrame:
    """Main function to enrich company data with job information."""
    out_rows = []
    n = len(df) if max_rows is None else min(max_rows, len(df))
    
    playwright_browser = None
    playwright_page = None
    
    if use_playwright:
        try:
            playwright = sync_playwright().start()
            playwright_browser = playwright.chromium.launch(headless=True)
            playwright_page = playwright_browser.new_page()
            logger.info("Playwright initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Playwright: {e}. Falling back to requests.")
            use_playwright = False
    
    try:
        for idx in tqdm(range(start_idx, start_idx + n), desc="Processing companies"):
            row = df.iloc[idx]
            company = str(row.get('Company', row.get('company', ''))).strip()
            
            if not company:
                out_rows.append({
                    "Company Name": company, 
                    "Company Description": None,
                    "Unnamed: 2": None,
                    "Website URL": None,
                    "Linkedin URL": None,
                    "Careers Page URL": None,
                    "Job listings page URL": None,
                    "job post1 URL": None,
                    "job post1 title": None,
                    "job post2 URL": None,
                    "job post2 title": None,
                    "job post3 URL": None,
                    "job post3 title": None,
                    "Notes": "No company name provided"
                })
                continue
            
            logger.info(f"Processing ({idx+1}/{len(df)}): {company}")
            
            result = {"Company Name": company}
            
            # Add empty columns to match data.xlsx format
            result['Company Description'] = None
            result['Unnamed: 2'] = None
            
            # Find website
            website = find_company_website(company)
            result['Website URL'] = website
            
            # Find LinkedIn
            linkedin = find_linkedin_url(company)
            result['Linkedin URL'] = linkedin
            
            # Find careers page
            careers = None
            if website:
                careers = find_careers_link_from_home(website, playwright_page if use_playwright else None)
            result['Careers Page URL'] = careers
            
            # Set job listings page URL (same as careers page for now)
            result['Job listings page URL'] = careers
            
            # Detect ATS and extract jobs
            ats = None
            jobs = []
            if careers:
                ats = detect_ats(careers)
                
                # Extract jobs
                jobs = extract_jobs_from_ats(careers, ats, limit=3, 
                                           playwright_page=playwright_page if use_playwright else None)
            
            # Add job data to result (matching data.xlsx format)
            for i in range(1, 4):
                job = jobs[i-1] if i <= len(jobs) else {}
                result[f'job post{i} URL'] = job.get('url')
                result[f'job post{i} title'] = job.get('title')
            
            result['Notes'] = f"ATS: {ats}" if ats else "No ATS detected"
            out_rows.append(result)
            
            # Rate limiting
            time.sleep(2)
    
    finally:
        if playwright_page:
            playwright_page.close()
        if playwright_browser:
            playwright_browser.close()
    
    return pd.DataFrame(out_rows)

def create_methodology_sheet() -> pd.DataFrame:
    """Create methodology documentation."""
    methodology_data = {
        'Category': [
            'Tools Used',
            'Search Strategy',
            'ATS Detection',
            'Job Extraction',
            'Rate Limiting',
            'Error Handling',
            'Data Quality',
            'Output Format'
        ],
        'Description': [
            'requests + BeautifulSoup for basic scraping, Playwright for JS-heavy sites',
            'Company name + common TLDs (.com, .co, .org, .net, .io, .ai, .tech)',
            'Pattern matching for 11+ ATS providers (Lever, Greenhouse, Workable, etc.)',
            'ATS-specific selectors with generic fallback for unknown providers',
            '2-second delay between requests to avoid rate limiting',
            'Comprehensive error handling with logging to scraper.log',
            'Manual verification recommended for production use',
            'Matches data.xlsx format with Company Name, Website URL, Linkedin URL, Careers Page URL, Job listings page URL, and job post URLs/titles'
        ]
    }
    return pd.DataFrame(methodology_data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Growth for Impact - Job Listings Scraper')
    parser.add_argument('--input', required=True, help='Input Excel file path')
    parser.add_argument('--output', required=True, help='Output Excel file path')
    parser.add_argument('--rows', type=int, default=50, help='Number of rows to process (default: 50)')
    parser.add_argument('--start', type=int, default=0, help='Starting row index (default: 0)')
    parser.add_argument('--no-playwright', action='store_true', help='Disable Playwright (use only requests)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input file
    in_path = Path(args.input)
    if not in_path.exists():
        logger.error(f"Input file not found: {in_path}")
        raise SystemExit(1)
    
    # Load data
    try:
        df = pd.read_excel(in_path)
        logger.info(f"Loaded {len(df)} rows from {in_path}")
    except Exception as e:
        logger.error(f"Failed to load Excel file: {e}")
        raise SystemExit(1)
    
    # Find company column
    possible = [c for c in df.columns if 'company' in c.lower()]
    if not possible:
        logger.error("No company-like column found. Please ensure there's a column with company names.")
        raise SystemExit(1)
    
    company_col = possible[0]
    df = df.rename(columns={company_col: 'Company'})
    logger.info(f"Using column '{company_col}' as company names")
    
    # Process companies
    logger.info(f"Processing {args.rows} companies starting from row {args.start}")
    out_df = enrich_companies(df, max_rows=args.rows, start_idx=args.start, 
                            use_playwright=not args.no_playwright)
    
    # Create methodology sheet
    methodology_df = create_methodology_sheet()
    
    # Save results
    try:
        with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
            out_df.to_excel(writer, sheet_name='Data', index=False)
            methodology_df.to_excel(writer, sheet_name='Methodology', index=False)
        
        logger.info(f"Results saved to {args.output}")
        logger.info(f"Processed {len(out_df)} companies successfully")
        
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        raise SystemExit(1)
