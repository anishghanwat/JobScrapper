import pandas as pd

# Load the submission file
df = pd.read_excel('submission_results.xlsx')

# Calculate totals
total_jobs = 0
for i in range(1, 4):
    total_jobs += df[f'job post{i} title'].notna().sum()

print("=== FINAL ASSIGNMENT STATUS ===")
print(f"📊 Job postings collected: {total_jobs}/200 ({total_jobs/200*100:.1f}%)")
print(f"🏢 Companies processed: {len(df)}")
print(f"🌐 Companies with websites: {df['Website URL'].notna().sum()}")
print(f"💼 Companies with careers pages: {df['Careers Page URL'].notna().sum()}")

if total_jobs >= 200:
    print("🎉 TARGET ACHIEVED!")
else:
    print(f"📈 Need {200 - total_jobs} more jobs to reach target")

print("\n✅ READY FOR SUBMISSION!")
print("📁 Submit: submission_results.xlsx")
