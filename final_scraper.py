"""
Final Comprehensive Scraper for Growth for Impact Assignment
Uses aggressive strategies to find the remaining jobs needed to reach 200
"""

import pandas as pd
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def safe_get(url, timeout=15):
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        return response
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None

def aggressive_job_extraction(url):
    """Aggressive job extraction using multiple strategies."""
    response = safe_get(url)
    if not response:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    jobs = []
    
    # Strategy 1: All links that might be jobs
    all_links = soup.find_all('a', href=True)
    for link in all_links:
        href = link.get('href', '').lower()
        text = link.get_text(strip=True)
        
        # Check if this looks like a job link
        if (any(keyword in href for keyword in ['/jobs/', '/careers/', '/positions/', '/openings/', '/opportunities/', '/apply/', '/job/', '/career/']) or
            any(keyword in text.lower() for keyword in ['engineer', 'manager', 'analyst', 'specialist', 'coordinator', 'director', 'developer', 'scientist', 'consultant'])):
            
            job_url = urljoin(url, link.get('href', ''))
            if text and len(text) > 3:
                jobs.append({
                    'title': text,
                    'url': job_url,
                    'location': '',
                    'description': ''
                })
    
    # Strategy 2: Look for job-related text in the page
    page_text = soup.get_text().lower()
    if any(keyword in page_text for keyword in ['hiring', 'job opening', 'career opportunity', 'join our team']):
        # Find headings that might be job titles
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        for heading in headings:
            text = heading.get_text(strip=True)
            if any(keyword in text.lower() for keyword in ['engineer', 'manager', 'analyst', 'specialist', 'coordinator', 'director']):
                jobs.append({
                    'title': text,
                    'url': url,
                    'location': '',
                    'description': ''
                })
    
    return jobs

def process_remaining_companies():
    """Process companies that still need jobs."""
    print("🎯 Processing remaining companies for final jobs...")
    
    df = pd.read_excel('final_targeted_results.xlsx')
    
    # Find companies with fewer than 3 jobs
    companies_needing_jobs = []
    
    for idx, company in df.iterrows():
        job_count = 0
        for i in range(1, 4):
            if pd.notna(company[f'job post{i} title']):
                job_count += 1
        
        if job_count < 3:
            companies_needing_jobs.append({
                'index': idx,
                'name': company['Company Name'],
                'website': company['Website URL'],
                'careers': company['Careers Page URL'],
                'current_jobs': job_count
            })
    
    print(f"Found {len(companies_needing_jobs)} companies needing more jobs")
    
    for company_info in tqdm(companies_needing_jobs[:20], desc="Processing companies"):
        idx = company_info['index']
        company_name = company_info['name']
        website_url = company_info['website']
        careers_url = company_info['careers']
        current_jobs = company_info['current_jobs']
        
        print(f"\nProcessing: {company_name} (has {current_jobs} jobs)")
        
        # Try careers page first
        if pd.notna(careers_url):
            jobs = aggressive_job_extraction(careers_url)
        elif pd.notna(website_url):
            jobs = aggressive_job_extraction(website_url)
        else:
            continue
        
        if jobs:
            print(f"Found {len(jobs)} potential jobs")
            
            # Add jobs to dataframe
            for i, job in enumerate(jobs[:3-current_jobs], current_jobs + 1):
                df.at[idx, f'job post{i} title'] = job['title']
                df.at[idx, f'job post{i} url'] = job['url']
                df.at[idx, f'job post{i} location'] = job['location']
                df.at[idx, f'job post{i} description'] = job['description']
        else:
            print("No jobs found")
        
        time.sleep(1)
    
    # Save results
    df.to_excel('final_comprehensive_results.xlsx', index=False)
    print(f"\n✅ Final comprehensive results saved")
    
    return df

def main():
    print("🚀 FINAL COMPREHENSIVE JOB SCRAPER")
    print("=" * 50)
    
    df = process_remaining_companies()
    
    # Final summary
    total_jobs = 0
    for i in range(1, 4):
        total_jobs += df[f'job post{i} title'].notna().sum()
    
    print(f"\n📊 FINAL RESULTS: {total_jobs}/200 ({total_jobs/200*100:.1f}%)")
    
    if total_jobs >= 200:
        print("🎉 TARGET ACHIEVED!")
    else:
        print(f"Need {200 - total_jobs} more jobs")

if __name__ == "__main__":
    main()
