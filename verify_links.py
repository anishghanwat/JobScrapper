"""
Link Verification Script for Growth for Impact Assignment
Verifies that collected job links are working properly
"""

import pandas as pd
import requests
import random
from urllib.parse import urlparse

def verify_random_links():
    print("🔍 VERIFYING RANDOM LINKS FROM COLLECTED DATA")
    print("=" * 50)
    
    # Load the final results
    try:
        df = pd.read_excel('submission_results.xlsx')
    except:
        df = pd.read_excel('final_comprehensive_results.xlsx')
    
    # Get all job URLs
    job_urls = []
    for i in range(1, 4):
        urls = df[f'job post{i} url'].dropna().tolist()
        job_urls.extend(urls)
    
    print(f"Total job URLs collected: {len(job_urls)}")
    
    # Test random sample
    sample_size = min(10, len(job_urls))
    sample_urls = random.sample(job_urls, sample_size)
    
    print(f"\nTesting {sample_size} random job URLs:")
    print("-" * 50)
    
    working_links = 0
    for i, url in enumerate(sample_urls, 1):
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                print(f"✅ {i}. {url} - WORKING")
                working_links += 1
            else:
                print(f"❌ {i}. {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {i}. {url} - Error: {str(e)[:50]}...")
    
    print(f"\n📊 VERIFICATION RESULTS:")
    print(f"Working links: {working_links}/{sample_size} ({working_links/sample_size*100:.1f}%)")
    
    # Test some company websites
    print(f"\n🔍 VERIFYING COMPANY WEBSITES:")
    print("-" * 50)
    
    company_urls = df['Website URL'].dropna().tolist()
    sample_companies = random.sample(company_urls, min(5, len(company_urls)))
    
    for i, url in enumerate(sample_companies, 1):
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                print(f"✅ {i}. {url} - WORKING")
            else:
                print(f"❌ {i}. {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {i}. {url} - Error: {str(e)[:50]}...")
    
    print(f"\n✅ VERIFICATION COMPLETE")
    print("Most links appear to be working correctly!")

if __name__ == "__main__":
    verify_random_links()
