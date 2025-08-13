"""
Targeted Scraper for Growth for Impact Assignment
Focuses on specific companies and uses different strategies to find more jobs
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

def safe_get(url, timeout=15):
    """Safely make HTTP request."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        return response
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None

def extract_jobs_generic(url):
    """Generic job extraction that tries multiple strategies."""
    response = safe_get(url)
    if not response:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    jobs = []
    
    # Strategy 1: Look for job links with common patterns
    job_patterns = [
        'a[href*="/jobs/"]',
        'a[href*="/careers/"]',
        'a[href*="/positions/"]',
        'a[href*="/openings/"]',
        'a[href*="/opportunities/"]',
        'a[href*="/apply/"]',
        'a[href*="/job/"]',
        'a[href*="/career/"]'
    ]
    
    for pattern in job_patterns:
        links = soup.select(pattern)
        for link in links:
            href = link.get('href', '')
            job_url = urljoin(url, href)
            title = link.get_text(strip=True)
            
            if title and len(title) > 5 and title.lower() not in ['apply', 'careers', 'jobs', 'join us']:
                jobs.append({
                    'title': title,
                    'url': job_url,
                    'location': '',
                    'description': ''
                })
    
    # Strategy 2: Look for job titles in headings
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
    for heading in headings:
        text = heading.get_text(strip=True)
        if any(keyword in text.lower() for keyword in ['engineer', 'manager', 'analyst', 'specialist', 'coordinator', 'director']):
            # Look for nearby links
            parent = heading.parent
            if parent:
                links = parent.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if any(keyword in href.lower() for keyword in ['/jobs/', '/careers/', '/apply/']):
                        job_url = urljoin(url, href)
                        jobs.append({
                            'title': text,
                            'url': job_url,
                            'location': '',
                            'description': ''
                        })
    
    # Strategy 3: Look for job cards or sections
    job_sections = soup.find_all(['div', 'section'], class_=re.compile(r'job|career|position|opening', re.I))
    for section in job_sections:
        title_elem = section.find(['h1', 'h2', 'h3', 'h4'])
        if title_elem:
            title = title_elem.get_text(strip=True)
            link = section.find('a', href=True)
            if link:
                job_url = urljoin(url, link.get('href', ''))
                jobs.append({
                    'title': title,
                    'url': job_url,
                    'location': '',
                    'description': ''
                })
    
    return jobs

def process_specific_companies():
    """Process specific companies that might have been missed."""
    print("🎯 Processing specific companies for additional jobs...")
    
    df = pd.read_excel('final_enhanced_results.xlsx')
    
    # Companies to target specifically
    target_companies = [
        {
            'name': 'Willow',
            'url': 'https://wellfound.com/company/willowdotco',
            'strategy': 'wellfound'
        },
        {
            'name': 'Tandem',
            'url': 'https://calendly.com/tandemteam/quick-tandem-overview',
            'strategy': 'calendly'
        },
        {
            'name': 'Landis+Gyr',
            'url': 'https://careers.landisgyr.com',
            'strategy': 'generic'
        },
        {
            'name': 'Einride',
            'url': 'https://careers.einride.tech',
            'strategy': 'generic'
        },
        {
            'name': 'Aerobotics',
            'url': 'https://aerobotics.com/careers',
            'strategy': 'generic'
        },
        {
            'name': 'Scout Motors',
            'url': 'https://scoutmotors.com/careers',
            'strategy': 'generic'
        },
        {
            'name': 'Outrider',
            'url': 'https://outrider.com/our-team',
            'strategy': 'generic'
        },
        {
            'name': 'Base Power Company',
            'url': 'https://basepowercompany.com/careers',
            'strategy': 'generic'
        },
        {
            'name': 'Greenlight Biosciences',
            'url': 'https://greenlightbiosciences.com/team',
            'strategy': 'generic'
        },
        {
            'name': 'Plus',
            'url': 'https://plus.co',
            'strategy': 'generic'
        },
        {
            'name': 'Encamp',
            'url': 'https://encamp.com/join-us/',
            'strategy': 'generic'
        },
        {
            'name': 'Bird',
            'url': 'https://bird.com/careers',
            'strategy': 'generic'
        },
        {
            'name': 'C&D Technologies',
            'url': 'https://cdtechnologies.com',
            'strategy': 'generic'
        },
        {
            'name': 'Power Factors',
            'url': 'https://www.powerfactors.com/about/#meet-the-team',
            'strategy': 'generic'
        }
    ]
    
    for company_info in tqdm(target_companies, desc="Processing specific companies"):
        company_name = company_info['name']
        url = company_info['url']
        strategy = company_info['strategy']
        
        print(f"\nProcessing: {company_name} - {url}")
        
        # Find the company in the dataframe
        company_row = df[df['Company Name'] == company_name]
        if company_row.empty:
            print(f"Company {company_name} not found in dataframe")
            continue
        
        idx = company_row.index[0]
        
        # Check if company already has jobs
        existing_jobs = 0
        for i in range(1, 4):
            if pd.notna(company_row.iloc[0][f'job post{i} title']):
                existing_jobs = i
        
        if existing_jobs >= 3:
            print(f"Company already has {existing_jobs} jobs")
            continue
        
        # Extract jobs based on strategy
        if strategy == 'wellfound':
            jobs = extract_wellfound_jobs(url)
        elif strategy == 'calendly':
            jobs = extract_calendly_jobs(url)
        else:
            jobs = extract_jobs_generic(url)
        
        if jobs:
            print(f"Found {len(jobs)} jobs")
            
            # Add jobs to dataframe
            for i, job in enumerate(jobs[:3-existing_jobs], existing_jobs + 1):
                df.at[idx, f'job post{i} title'] = job['title']
                df.at[idx, f'job post{i} url'] = job['url']
                df.at[idx, f'job post{i} location'] = job['location']
                df.at[idx, f'job post{i} description'] = job['description']
        else:
            print("No jobs found")
        
        time.sleep(2)
    
    # Save updated results
    df.to_excel('targeted_results.xlsx', index=False)
    print(f"\n✅ Targeted results saved to targeted_results.xlsx")
    
    return df

def extract_wellfound_jobs(url):
    """Extract jobs from Wellfound (AngelList) company page."""
    # Wellfound often redirects to a different URL structure
    # Try to find the actual jobs page
    base_url = url.replace('/company/', '/jobs/')
    
    response = safe_get(base_url)
    if not response:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    jobs = []
    
    # Look for job listings
    job_links = soup.find_all('a', href=re.compile(r'/jobs/'))
    for link in job_links:
        title = link.get_text(strip=True)
        if title and len(title) > 5:
            job_url = urljoin(url, link.get('href', ''))
            jobs.append({
                'title': title,
                'url': job_url,
                'location': '',
                'description': ''
            })
    
    return jobs

def extract_calendly_jobs(url):
    """Extract jobs from Calendly company page."""
    # Calendly is usually for scheduling, but might have job info
    response = safe_get(url)
    if not response:
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    jobs = []
    
    # Look for any job-related content
    text_content = soup.get_text()
    if any(keyword in text_content.lower() for keyword in ['job', 'career', 'position', 'hiring']):
        # Try to find job information in the page
        headings = soup.find_all(['h1', 'h2', 'h3'])
        for heading in headings:
            text = heading.get_text(strip=True)
            if any(keyword in text.lower() for keyword in ['engineer', 'manager', 'analyst', 'specialist']):
                jobs.append({
                    'title': text,
                    'url': url,
                    'location': '',
                    'description': ''
                })
    
    return jobs

def find_additional_companies():
    """Find additional companies that might have been missed."""
    print("🔍 Looking for additional companies...")
    
    df = pd.read_excel('targeted_results.xlsx')
    
    # Companies with websites but no careers pages
    website_no_careers = df[(df['Website URL'].notna()) & (df['Careers Page URL'].isna())]
    
    print(f"Found {len(website_no_careers)} companies with websites but no careers pages")
    
    for idx, company in tqdm(website_no_careers.head(10).iterrows(), desc="Processing additional companies"):
        website_url = company['Website URL']
        print(f"\nProcessing: {company['Company Name']} - {website_url}")
        
        # Try to find careers page on the website
        response = safe_get(website_url)
        if not response:
            continue
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for careers links
        careers_links = soup.find_all('a', href=True)
        careers_url = None
        
        for link in careers_links:
            href = link.get('href', '').lower()
            text = link.get_text(strip=True).lower()
            
            if any(keyword in href or keyword in text for keyword in ['career', 'job', 'join', 'team', 'work']):
                careers_url = urljoin(website_url, link.get('href', ''))
                break
        
        if careers_url:
            print(f"Found careers page: {careers_url}")
            
            # Extract jobs from careers page
            jobs = extract_jobs_generic(careers_url)
            
            if jobs:
                print(f"Found {len(jobs)} jobs")
                
                # Update careers page URL and add jobs
                df.at[idx, 'Careers Page URL'] = careers_url
                
                for i, job in enumerate(jobs[:3], 1):
                    df.at[idx, f'job post{i} title'] = job['title']
                    df.at[idx, f'job post{i} url'] = job['url']
                    df.at[idx, f'job post{i} location'] = job['location']
                    df.at[idx, f'job post{i} description'] = job['description']
            else:
                print("No jobs found")
        
        time.sleep(2)
    
    # Save final results
    df.to_excel('final_targeted_results.xlsx', index=False)
    print(f"\n✅ Final targeted results saved to final_targeted_results.xlsx")
    
    return df

def main():
    print("🎯 GROWTH FOR IMPACT - TARGETED JOB SCRAPER")
    print("=" * 50)
    
    # Step 1: Process specific companies
    df1 = process_specific_companies()
    
    # Step 2: Find additional companies
    df2 = find_additional_companies()
    
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
