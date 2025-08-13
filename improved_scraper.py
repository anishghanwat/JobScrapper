"""
Improved Scraper for Growth for Impact Assignment
Focuses on companies with careers pages but no jobs, and companies with <3 jobs
"""

import pandas as pd
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Enhanced ATS patterns
ATS_PATTERNS = {
    'lever': {
        'url_pattern': r'lever\.co|jobs\.lever\.co',
        'job_links': 'a[href*="/positions/"]',
        'title_selector': 'h2, h3, .posting-title, .job-title',
        'location_selector': '.location, .job-location, [class*="location"]',
        'description_selector': '.content, .description, .job-description'
    },
    'greenhouse': {
        'url_pattern': r'greenhouse\.io|boards\.greenhouse\.io',
        'job_links': 'a[href*="/jobs/"]',
        'title_selector': 'h1, h2, .opening-title, .job-title',
        'location_selector': '.location, .job-location',
        'description_selector': '.content, .description'
    },
    'workable': {
        'url_pattern': r'workable\.com|jobseekers\.workable\.com',
        'job_links': 'a[href*="/jobs/"]',
        'title_selector': 'h1, h2, .job-title',
        'location_selector': '.location, .job-location',
        'description_selector': '.description, .job-description'
    },
    'zohorecruit': {
        'url_pattern': r'zohorecruit\.com',
        'job_links': 'a[href*="/jobs/"]',
        'title_selector': 'h1, h2, .job-title',
        'location_selector': '.location, .job-location',
        'description_selector': '.description, .job-description'
    },
    'wellfound': {
        'url_pattern': r'wellfound\.com',
        'job_links': 'a[href*="/jobs/"]',
        'title_selector': 'h1, h2, .job-title',
        'location_selector': '.location, .job-location',
        'description_selector': '.description, .job-description'
    },
    'calendly': {
        'url_pattern': r'calendly\.com',
        'job_links': 'a[href*="/jobs/"]',
        'title_selector': 'h1, h2, .job-title',
        'location_selector': '.location, .job-location',
        'description_selector': '.description, .job-description'
    }
}

def detect_ats(url):
    """Detect ATS provider from URL."""
    for ats_name, pattern in ATS_PATTERNS.items():
        if re.search(pattern['url_pattern'], url, re.I):
            return ats_name
    return 'generic'

def safe_get(url, timeout=15):
    """Safely make HTTP request."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        return response
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None

def extract_jobs_from_page(url, max_jobs=3):
    """Extract job postings from a careers page."""
    response = safe_get(url)
    if not response:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    ats = detect_ats(url)
    
    jobs = []
    
    if ats in ATS_PATTERNS:
        # Use ATS-specific extraction
        pattern = ATS_PATTERNS[ats]
        
        # Find job links
        job_links = soup.select(pattern['job_links'])
        
        for i, link in enumerate(job_links[:max_jobs]):
            job_url = urljoin(url, link.get('href', ''))
            job_title = link.get_text(strip=True)
            
            # Try to get more details from the job page
            job_details = extract_job_details(job_url, pattern)
            
            jobs.append({
                'title': job_title or job_details.get('title', ''),
                'location': job_details.get('location', ''),
                'url': job_url,
                'description': job_details.get('description', '')
            })
    else:
        # Generic extraction
        job_links = soup.find_all('a', href=True)
        for link in job_links:
            href = link.get('href', '')
            if any(keyword in href.lower() for keyword in ['/jobs/', '/careers/', '/positions/', '/openings/']):
                job_url = urljoin(url, href)
                job_title = link.get_text(strip=True)
                
                if job_title and len(job_title) > 5:  # Basic validation
                    jobs.append({
                        'title': job_title,
                        'location': '',
                        'url': job_url,
                        'description': ''
                    })
                    
                    if len(jobs) >= max_jobs:
                        break
    
    return jobs

def extract_job_details(job_url, pattern):
    """Extract detailed job information from individual job page."""
    response = safe_get(job_url)
    if not response:
        return {}
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    details = {}
    
    # Extract title
    title_elem = soup.select_one(pattern['title_selector'])
    if title_elem:
        details['title'] = title_elem.get_text(strip=True)
    
    # Extract location
    location_elem = soup.select_one(pattern['location_selector'])
    if location_elem:
        details['location'] = location_elem.get_text(strip=True)
    
    # Extract description
    desc_elem = soup.select_one(pattern['description_selector'])
    if desc_elem:
        details['description'] = desc_elem.get_text(strip=True)[:500]  # Limit length
    
    return details

def process_companies_with_careers_no_jobs():
    """Process companies that have careers pages but no jobs."""
    print("🔍 Processing companies with careers pages but no jobs...")
    
    df = pd.read_excel('complete_results.xlsx')
    
    # Find companies with careers pages but no jobs
    target_companies = df[(df['Careers Page URL'].notna()) & (df['job post1 title'].isna())].copy()
    
    print(f"Found {len(target_companies)} companies to process")
    
    for idx, company in tqdm(target_companies.iterrows(), total=len(target_companies)):
        careers_url = company['Careers Page URL']
        print(f"\nProcessing: {company['Company Name']} - {careers_url}")
        
        # Extract jobs
        jobs = extract_jobs_from_page(careers_url, max_jobs=3)
        
        if jobs:
            print(f"Found {len(jobs)} jobs")
            
            # Update the dataframe
            for i, job in enumerate(jobs, 1):
                df.at[idx, f'job post{i} title'] = job['title']
                df.at[idx, f'job post{i} location'] = job['location']
                df.at[idx, f'job post{i} url'] = job['url']
                df.at[idx, f'job post{i} description'] = job['description']
        else:
            print("No jobs found")
        
        # Rate limiting
        time.sleep(2)
    
    # Save updated results
    df.to_excel('enhanced_results.xlsx', index=False)
    print(f"\n✅ Enhanced results saved to enhanced_results.xlsx")
    
    return df

def process_companies_with_fewer_jobs():
    """Process companies that have fewer than 3 jobs."""
    print("🔍 Processing companies with fewer than 3 jobs...")
    
    df = pd.read_excel('enhanced_results.xlsx')
    
    # Find companies with 1 or 2 jobs
    one_job = df[(df['job post1 title'].notna()) & (df['job post2 title'].isna())]
    two_jobs = df[(df['job post2 title'].notna()) & (df['job post3 title'].isna())]
    
    target_companies = pd.concat([one_job, two_jobs])
    
    print(f"Found {len(target_companies)} companies with fewer than 3 jobs")
    
    for idx, company in tqdm(target_companies.iterrows(), total=len(target_companies)):
        careers_url = company['Careers Page URL']
        if pd.isna(careers_url):
            continue
            
        print(f"\nProcessing: {company['Company Name']} - {careers_url}")
        
        # Count existing jobs
        existing_jobs = 0
        for i in range(1, 4):
            if pd.notna(company[f'job post{i} title']):
                existing_jobs = i
        
        # Extract additional jobs
        max_additional = 3 - existing_jobs
        jobs = extract_jobs_from_page(careers_url, max_jobs=10)  # Get more to filter
        
        if jobs:
            # Filter out jobs we already have
            existing_titles = []
            for i in range(1, existing_jobs + 1):
                if pd.notna(company[f'job post{i} title']):
                    existing_titles.append(company[f'job post{i} title'])
            
            new_jobs = [job for job in jobs if job['title'] not in existing_titles]
            
            print(f"Found {len(new_jobs)} new jobs")
            
            # Add new jobs
            for i, job in enumerate(new_jobs[:max_additional], existing_jobs + 1):
                df.at[idx, f'job post{i} title'] = job['title']
                df.at[idx, f'job post{i} location'] = job['location']
                df.at[idx, f'job post{i} url'] = job['url']
                df.at[idx, f'job post{i} description'] = job['description']
        else:
            print("No additional jobs found")
        
        # Rate limiting
        time.sleep(2)
    
    # Save final results
    df.to_excel('final_enhanced_results.xlsx', index=False)
    print(f"\n✅ Final enhanced results saved to final_enhanced_results.xlsx")
    
    return df

def main():
    print("🚀 GROWTH FOR IMPACT - ENHANCED JOB SCRAPER")
    print("=" * 50)
    
    # Step 1: Process companies with careers pages but no jobs
    df1 = process_companies_with_careers_no_jobs()
    
    # Step 2: Process companies with fewer than 3 jobs
    df2 = process_companies_with_fewer_jobs()
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 FINAL RESULTS SUMMARY")
    
    total_jobs = 0
    for i in range(1, 4):
        total_jobs += df2[f'job post{i} title'].notna().sum()
    
    print(f"Total job postings: {total_jobs}")
    print(f"Target: 200")
    print(f"Progress: {total_jobs}/200 ({total_jobs/200*100:.1f}%)")
    
    if total_jobs >= 200:
        print("🎉 TARGET ACHIEVED!")
    else:
        print(f"Need {200 - total_jobs} more jobs")

if __name__ == "__main__":
    main()
