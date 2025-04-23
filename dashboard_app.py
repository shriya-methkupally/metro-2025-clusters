import streamlit as st
import pandas as pd
import numpy as np

# Define colors for each group
group_colors = {
    'AI Superstars': '#003a70',
    'Star AI Hubs': '#FF9E1B',
    'Emerging AI Centers': '#8BB8E8',
    'Focused AI Scalers': '#F2CD00',
    'Nascent AI Adopters': '#B1B3B3',
    'Others': '#A569BD',
    'Small metros': '#58D68D'
}

# Load data
raw = pd.read_csv('SHRIYA_updated raw data_v1_clusters.csv', encoding='latin1')
check = pd.read_excel('gpt check.xlsx', sheet_name=0)

df = pd.merge(raw, check[['Code','Combination','Group']],
              left_on='CBSA Code', right_on='Code', how='left')
df['Group2'] = df['Group'].fillna(0).astype(int)
group_names = {
    1: 'AI Superstars', 2: 'Star AI Hubs', 3: 'Emerging AI Centers',
    4: 'Focused AI Scalers', 5: 'Nascent AI Adopters',
    6: 'Others', 0: 'Small metros'
}
df['GroupName'] = df['Group2'].map(group_names)

# Ensure numeric metrics
count_metrics = ['Job Postings','AI Startups','VC Funding']
firm_metrics = [
    'Firm AI Use','Firm Data Readiness',
    'Firm Cloud Readiness','Occupational Exposure to AI'
]
other_metrics = [
    "Science and Engineering Bachelor's",'Phd','Profiles',
    'Publications','Patents','Contracts','HPC'
]
all_metrics = count_metrics + firm_metrics + other_metrics
for col in all_metrics:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Precompute totals for share %
totals = {m: df[m].sum(skipna=True) for m in count_metrics}

# Build summary DataFrame
records = []
for grp, grp_df in df.groupby('GroupName'):
    for metric in all_metrics:
        arr = grp_df[metric].dropna()
        if arr.empty:
            continue
        rec = {
            'Group': grp,
            'Metric': metric,
            'Mean': arr.mean(),
            'Min': arr.min(),
            'Max': arr.max(),
            'Range': arr.max() - arr.min(),
            'Best Metro': grp_df.loc[arr.idxmax()]['CBSA Title'],
            'Best Value': arr.max(),
            'Worst Metro': grp_df.loc[arr.idxmin()]['CBSA Title'],
            'Worst Value': arr.min()
        }
        if metric in count_metrics:
            rec['Sum'] = arr.sum()
            rec['Share (%)'] = rec['Sum'] / totals[metric] * 100 if totals[metric] else np.nan
        records.append(rec)

summary_df = pd.DataFrame(records)

# Sidebar controls
st.sidebar.header("Filter by Group & Metric")
group = st.sidebar.selectbox("Cluster Group", summary_df['Group'].unique())
metrics = summary_df[summary_df['Group']==group]['Metric'].unique()
metric = st.sidebar.selectbox("Metric", metrics)

# Header with group color
st.markdown(
    f"<h1 style='color:{group_colors[group]};'>🔸 {metric} — {group}</h1>",
    unsafe_allow_html=True
)

# Display summary stats in colored boxes
row = summary_df[
    (summary_df['Group']==group) &
    (summary_df['Metric']==metric)
].iloc[0]

col1, col2, col3, col4 = st.columns(4)
stats = [
    ('Mean', row['Mean']),
    ('Min', row['Min']),
    ('Max', row['Max']),
    ('Range', row['Range'])
]
for col_box, (label, value) in zip((col1, col2, col3, col4), stats):
    col_box.markdown(
        f"<div style='background-color:{group_colors[group]};"
        f"padding:10px;border-radius:8px'>"
        f"<h4 style='color:white;text-align:center;margin:0'>{label}</h4>"
        f"<p style='color:white;text-align:center;font-size:20px;"
        f"margin:0'>{value:.2f}</p>"
        "</div>",
        unsafe_allow_html=True
    )

# Additional stats for count metrics
if metric in count_metrics:
    col5, col6 = st.columns(2)
    col5.markdown(
        f"<div style='background-color:{group_colors[group]};"
        f"padding:10px;border-radius:8px'>"
        f"<h4 style='color:white;text-align:center;margin:0'>Sum</h4>"
        f"<p style='color:white;text-align:center;font-size:20px;"
        f"margin:0'>{row['Sum']:.0f}</p>"
        "</div>",
        unsafe_allow_html=True
    )
    col6.markdown(
        f"<div style='background-color:{group_colors[group]};"
        f"padding:10px;border-radius:8px'>"
        f"<h4 style='color:white;text-align:center;margin:0'>Share (%)</h4>"
        f"<p style='color:white;text-align:center;font-size:20px;"
        f"margin:0'>{row['Share (%)']:.2f}</p>"
        "</div>",
        unsafe_allow_html=True
    )

# Top & Bottom lists
st.markdown("### 🔝 Top 5 Metros")
top5 = df[df['GroupName']==group][['CBSA Title', metric]] \
    .dropna().sort_values(by=metric, ascending=False).head(5)
for i, (metro, val) in enumerate(zip(top5['CBSA Title'], top5[metric]), 1):
    st.markdown(f"{i}. **{metro}** — {val:.2f}")

st.markdown("### 🔽 Bottom 5 Metros")
bot5 = df[df['GroupName']==group][['CBSA Title', metric]] \
    .dropna().sort_values(by=metric).head(5)
for i, (metro, val) in enumerate(zip(bot5['CBSA Title'], bot5[metric]), 1):
    st.markdown(f"{i}. **{metro}** — {val:.2f}")
