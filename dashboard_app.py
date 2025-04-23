import streamlit as st
import pandas as pd
import numpy as np

# Page styling
st.set_page_config(page_title="AI Metro Dashboard", layout="wide", page_icon="🤖")
st.markdown("""
<style>
  .stApp {
    background-color: #F2F3F4;
    color: #1B2631;
  }
  .stSidebar {
    background-color: #FFFFFF;
  }
  .dataframe td, .dataframe th {
    color: #1B2631 !important;
    background-color: #FFFFFF !important;
  }
</style>
""", unsafe_allow_html=True)

# Cluster colors
group_colors = {
  'AI Superstars':'#003a70',
  'Star AI Hubs':'#FF9E1B',
  'Emerging AI Centers':'#8BB8E8',
  'Focused AI Scalers':'#F2CD00',
  'Nascent AI Adopters':'#B1B3B3',
  'Others':'#A569BD',
  'Small metros':'#58D68D'
}

# Load data
raw = pd.read_csv('SHRIYA_updated raw data_v1_clusters.csv', encoding='latin1')
chk = pd.read_excel('gpt check.xlsx', sheet_name=0)

df = pd.merge(
    raw,
    chk[['Code','Group']],
    left_on='CBSA Code',
    right_on='Code',
    how='left'
)
df['Group2'] = df['Group'].fillna(0).astype(int)
names = {
    1:'AI Superstars', 2:'Star AI Hubs', 3:'Emerging AI Centers',
    4:'Focused AI Scalers', 5:'Nascent AI Adopters', 6:'Others', 0:'Small metros'
}
df['GroupName'] = df['Group2'].map(names)

# Define metrics
firm_metrics  = [
    'Firm AI Use',
    'Firm Data Readiness',
    'Firm Cloud Readiness',
    'Occupational Exposure to AI'
]
share_metrics = [
    'Job Postings',
    'AI Startups',
    'VC Funding',
    "Science and Engineering Bachelor's",
    'Phd',
    'Profiles',
    'Publications',
    'Patents',
    'Contracts',
    'HPC'
]
all_metrics = firm_metrics + share_metrics

# Convert to numeric and compute totals for share metrics
for c in all_metrics:
    df[c] = pd.to_numeric(df[c], errors='coerce')
totals = {m: df[m].sum(skipna=True) for m in share_metrics}

# Build summary_df
records = []
for grp, gdf in df.groupby('GroupName'):
    for m in all_metrics:
        arr = gdf[m].dropna()
        if arr.empty: continue
        rec = {
            'Group': grp,
            'Metric': m,
            'Mean': arr.mean(),
            'Min': arr.min(),
            'Max': arr.max(),
            'Range': arr.max() - arr.min(),
            'Best Metro': gdf.loc[arr.idxmax(), 'CBSA Title'],
            'Best Value': arr.max(),
            'Worst Metro': gdf.loc[arr.idxmin(), 'CBSA Title'],
            'Worst Value': arr.min()
        }
        if m in share_metrics:
            rec['Sum'] = arr.sum()
            rec['Share (%)'] = rec['Sum'] / totals[m] * 100 if totals[m] else np.nan
        records.append(rec)

summary_df = pd.DataFrame(records)

# Sidebar: mode
mode = st.sidebar.radio("Mode", ["📊 Stats", "🔍 Compare Groups", "🔎 Metro Search"])

if mode == "📊 Stats":
    st.sidebar.header("Stats Filter")
    grp = st.sidebar.selectbox("Group", summary_df['Group'].unique())
    m = st.sidebar.selectbox(
        "Metric",
        summary_df[summary_df['Group'] == grp]['Metric'].unique()
    )

    st.markdown(
        f"<h1 style='color:{group_colors[grp]};'>🔸 {m} — {grp}</h1>",
        unsafe_allow_html=True
    )

    row = summary_df[
        (summary_df['Group'] == grp) & (summary_df['Metric'] == m)
    ].iloc[0]

    cols = st.columns(4)
    stats = [
        ('Mean', row['Mean']),
        ('Min', row['Min']),
        ('Max', row['Max']),
        ('Range', row['Range'])
    ]
    for cb, (lab, val) in zip(cols, stats):
        cb.markdown(
            f"<div style='background-color:{group_colors[grp]};padding:10px;border-radius:8px;'>"
            f"<h4 style='color:white'>{lab}</h4>"
            f"<p style='color:white;font-size:20px;margin:0'>{val:.2f}</p></div>",
            unsafe_allow_html=True
        )

    if m in share_metrics:
        c5, c6 = st.columns(2)
        c5.metric("Sum", f"{row['Sum']:.0f}")
        c6.metric("Share (%)", f"{row['Share (%)']:.1f}%")

    st.markdown("### 🔝 Top 5")
    top5 = df[df['GroupName'] == grp][['CBSA Title', m]].nlargest(5, m)
    for i, (nm, v) in enumerate(zip(top5['CBSA Title'], top5[m]), 1):
        st.write(f"{i}. **{nm}** — {v:.2f}")

    st.markdown("### 🔽 Bottom 5")
    bot5 = df[df['GroupName'] == grp][['CBSA Title', m]].nsmallest(5, m)
    for i, (nm, v) in enumerate(zip(bot5['CBSA Title'], bot5[m]), 1):
        st.write(f"{i}. **{nm}** — {v:.2f}")

elif mode == "🔍 Compare Groups":
    st.header("Compare Groups")
    st.markdown("Select clusters to view share % for count metrics.")
    cols = st.columns(3)
    sel = [
        grp for i, grp in enumerate(group_colors)
        if cols[i % 3].checkbox(grp)
    ]
    if not sel:
        st.warning("Select at least one cluster.")
    else:
        rows = []
        for m in share_metrics:
            total_sel = summary_df[
                (summary_df['Group'].isin(sel)) &
                (summary_df['Metric'] == m)
            ]['Sum'].sum()
            pct = total_sel / totals[m] * 100 if totals[m] else np.nan
            rows.append({'Metric': m, 'Share (%)': pct})
        dfc = pd.DataFrame(rows).set_index('Metric').sort_index()
        st.dataframe(
            dfc.style.format("{:.1f}%").set_properties(color="#1B2631", background="#FFFFFF"),
            use_container_width=True
        )

else:
    st.header("Metro Search")
    st.sidebar.header("Search Filter")
    grp_ms = st.sidebar.selectbox("Group", sorted(df['GroupName'].unique()))
    metro = st.sidebar.selectbox(
        "Metro",
        df[df['GroupName'] == grp_ms]['CBSA Title'].sort_values()
    )

    st.markdown(f"## {metro} — {grp_ms}")
    r = df[df['CBSA Title'] == metro].iloc[0]
    rows = []
    for m in all_metrics:
        val = r[m]
        pct = val / totals[m] * 100 if m in share_metrics and totals[m] else np.nan
        rows.append({'Metric': m, 'Value': val, 'Share (%)': pct})
    dfrm = pd.DataFrame(rows).set_index('Metric')
    st.dataframe(
        dfrm.style.format({"Value": "{:.2f}", "Share (%)": "{:.1f}%"}),
        use_container_width=True
    )
