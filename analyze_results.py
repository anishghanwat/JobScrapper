import pandas as pd
import numpy as np

def analyze_results():
    print("=== GROWTH FOR IMPACT - RESULTS ANALYSIS ===\n")
    
    # Load the complete results
    df = pd.read_excel('complete_results.xlsx')
    
    print(f"📊 CURRENT STATUS:")
    print(f"Total companies: {len(df)}")
    print(f"Companies with websites: {df['Website URL'].notna().sum()}")
    print(f"Companies with careers pages: {df['Careers Page URL'].notna().sum()}")
    
    # Count job postings
    job1_count = df['job post1 title'].notna().sum()
    job2_count = df['job post2 title'].notna().sum()
    job3_count = df['job post3 title'].notna().sum()
    total_jobs = job1_count + job2_count + job3_count
    
    print(f"Job postings collected: {total_jobs}")
    print(f"Target: 200")
    print(f"Remaining needed: {200 - total_jobs}")
    
    print(f"\n🔍 OPPORTUNITIES FOR MORE JOBS:")
    
    # Companies with careers pages but no jobs
    careers_no_jobs = df[(df['Careers Page URL'].notna()) & (df['job post1 title'].isna())]
    print(f"Companies with careers pages but no jobs: {len(careers_no_jobs)}")
    if len(careers_no_jobs) > 0:
        print("Examples:")
        for i, company in careers_no_jobs.head(5).iterrows():
            print(f"  - {company['Company Name']}: {company['Careers Page URL']}")
    
    # Companies with websites but no careers pages
    website_no_careers = df[(df['Website URL'].notna()) & (df['Careers Page URL'].isna())]
    print(f"\nCompanies with websites but no careers pages: {len(website_no_careers)}")
    if len(website_no_careers) > 0:
        print("Examples:")
        for i, company in website_no_careers.head(5).iterrows():
            print(f"  - {company['Company Name']}: {company['Website URL']}")
    
    # Companies with no website found
    no_website = df[df['Website URL'].isna()]
    print(f"\nCompanies with no website found: {len(no_website)}")
    if len(no_website) > 0:
        print("Examples:")
        for i, company in no_website.head(5).iterrows():
            print(f"  - {company['Company Name']}")
    
    # Companies with only 1 job (could get 2 more)
    one_job = df[(df['job post1 title'].notna()) & (df['job post2 title'].isna())]
    print(f"\nCompanies with only 1 job (could get 2 more): {len(one_job)}")
    potential_jobs = len(one_job) * 2
    
    # Companies with only 2 jobs (could get 1 more)
    two_jobs = df[(df['job post2 title'].notna()) & (df['job post3 title'].isna())]
    print(f"Companies with only 2 jobs (could get 1 more): {len(two_jobs)}")
    potential_jobs += len(two_jobs)
    
    print(f"\n🎯 POTENTIAL ADDITIONAL JOBS:")
    print(f"From companies with careers but no jobs: {len(careers_no_jobs)} * 3 = {len(careers_no_jobs) * 3}")
    print(f"From companies with 1 job: {len(one_job)} * 2 = {len(one_job) * 2}")
    print(f"From companies with 2 jobs: {len(two_jobs)} * 1 = {len(two_jobs)}")
    print(f"Total potential: {len(careers_no_jobs) * 3 + len(one_job) * 2 + len(two_jobs)}")
    
    print(f"\n📈 STRATEGY TO REACH 200:")
    needed = 200 - total_jobs
    print(f"Need {needed} more jobs")
    
    if len(careers_no_jobs) * 3 >= needed:
        print(f"Focus on companies with careers pages but no jobs: need ~{needed//3 + 1} companies")
    elif len(careers_no_jobs) * 3 + len(one_job) * 2 >= needed:
        print(f"Focus on careers_no_jobs + companies with 1 job")
    else:
        print(f"Need to improve website discovery for companies without websites")
    
    # Save analysis results
    analysis_results = {
        'total_companies': len(df),
        'companies_with_websites': df['Website URL'].notna().sum(),
        'companies_with_careers': df['Careers Page URL'].notna().sum(),
        'total_jobs': total_jobs,
        'jobs_needed': 200 - total_jobs,
        'careers_no_jobs': len(careers_no_jobs),
        'website_no_careers': len(website_no_careers),
        'no_website': len(no_website),
        'one_job_companies': len(one_job),
        'two_job_companies': len(two_jobs),
        'potential_additional_jobs': len(careers_no_jobs) * 3 + len(one_job) * 2 + len(two_jobs)
    }
    
    return analysis_results, careers_no_jobs, one_job, two_jobs

if __name__ == "__main__":
    analyze_results()
