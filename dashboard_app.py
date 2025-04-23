import streamlit as st
import pandas as pd
import numpy as np

# ─── Page config & styling ─────────────────────────────────────────────────────
st.set_page_config(page_title="AI Metro Dashboard", layout="wide", page_icon="🤖")
st.markdown(
    """
    <style>
      .stApp {
        background-color: #F2F3F4;  /* light grey */
        color: #1B2631;             /* dark text */
      }
      .stSidebar {
        background-color: #FFFFFF;  /* keep sidebar white */
      }
    </style>
    """,
    unsafe_allow_html=True
)

# ─── Define cluster colors ─────────────────────────────────────────────────────
group_colors = {
    'AI Superstars':        '#003a70',
    'Star AI Hubs':         '#FF9E1B',
    'Emerging AI Centers':  '#8BB8E8',
    'Focused AI Scalers':   '#F2CD00',
    'Nascent AI Adopters':  '#B1B3B3',
    'Others':               '#A569BD'
}

# ─── Load & prepare data ───────────────────────────────────────────────────────
raw   = pd.read_csv('SHRIYA_updated raw data_v1_clusters.csv', encoding='latin1')
check = pd.read_excel('gpt check.xlsx', sheet_name=0)

df = pd.merge(
    raw,
    check[['Code','Combination','Group']],
    left_on='CBSA Code', right_on='Code',
    how='left'
)
df['Group2']    = df['Group'].fillna(0).astype(int)
group_names    = {1: 'AI Superstars', 2: 'Star AI Hubs', 3: 'Emerging AI Centers',
                  4: 'Focused AI Scalers', 5: 'Nascent AI Adopters', 6: 'Others', 0: 'Small metros'}
df['GroupName'] = df['Group2'].map(group_names)

# ─── Metrics lists ─────────────────────────────────────────────────────────────
count_metrics = ['Job Postings','AI Startups','VC Funding']
firm_metrics  = ['Firm AI Use','Firm Data Readiness','Firm Cloud Readiness','Occupational Exposure to AI']
other_metrics = ["Science and Engineering Bachelor's",'Phd','Profiles','Publications','Patents','Contracts','HPC']
all_metrics   = count_metrics + firm_metrics + other_metrics

# convert to numeric
for c in all_metrics:
    df[c] = pd.to_numeric(df[c], errors='coerce')

# precompute totals for share %
totals = {m: df[m].sum(skipna=True) for m in count_metrics}

# build summary_df
records = []
for grp, grp_df in df.groupby('GroupName'):
    for metric in all_metrics:
        arr = grp_df[metric].dropna()
        if arr.empty: continue
        rec = {
            'Group': grp, 'Metric': metric,
            'Mean': arr.mean(), 'Min': arr.min(), 'Max': arr.max(),
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

# ─── Sidebar: choose mode ──────────────────────────────────────────────────────
mode = st.sidebar.radio("View Mode", ["📊 Stats", "🔍 Compare Groups"])

if mode == "📊 Stats":
    # ─── Stats mode ────────────────────────────────────────────────────────────
    st.sidebar.header("Filter by Group & Metric")
    group  = st.sidebar.selectbox("Cluster Group", summary_df['Group'].unique())
    metrics_available = summary_df[summary_df['Group']==group]['Metric'].unique()
    metric = st.sidebar.selectbox("Metric", metrics_available)

    # Header
    st.markdown(
        f"<h1 style='color:{group_colors.get(group,'#000')};'>"
        f"🔸 {metric} — {group}</h1>",
        unsafe_allow_html=True
    )

    # summary stats boxes
    row = summary_df[(summary_df['Group']==group)&(summary_df['Metric']==metric)].iloc[0]
    cols = st.columns(4)
    stats = [('Mean',row['Mean']),('Min',row['Min']),('Max',row['Max']),('Range',row['Range'])]
    for col_box,(label,val) in zip(cols, stats):
        col_box.markdown(
            f"<div style='background-color:{group_colors[group]};"
            f"padding:10px;border-radius:8px;'>"
            f"<h4 style='color:white;margin-bottom:2px'>{label}</h4>"
            f"<p style='color:white;font-size:20px;margin:0'>{val:.2f}</p>"
            "</div>",
            unsafe_allow_html=True
        )

    # extra for counts
    if metric in count_metrics:
        c5, c6 = st.columns(2)
        c5.metric("Sum",   f"{row['Sum']:.0f}")
        c6.metric("Share", f"{row['Share (%)']:.1f}%")

    # top / bottom lists
    st.markdown("### 🔝 Top 5 Metros")
    top5 = df[df['GroupName']==group][['CBSA Title',metric]].dropna().nlargest(5,metric)
    for i,(m,v) in enumerate(zip(top5['CBSA Title'],top5[metric]),1):
        st.write(f"{i}. **{m}** — {v:.2f}")

    st.markdown("### 🔽 Bottom 5 Metros")
    bot5 = df[df['GroupName']==group][['CBSA Title',metric]].dropna().nsmallest(5,metric)
    for i,(m,v) in enumerate(zip(bot5['CBSA Title'],bot5[metric]),1):
        st.write(f"{i}. **{m}** — {v:.2f}")

else:
    # ─── Comparison mode ─────────────────────────────────────────────────────
    st.header("🔍 Compare Cluster Groups")
    st.markdown("Select one or more clusters to see their **aggregate share** of each count metric.")

    cols = st.columns(3)
    compare_groups = list(group_colors.keys())
    selected = []
    for idx, grp in enumerate(compare_groups):
        if cols[idx % 3].checkbox(grp):
            selected.append(grp)

    if not selected:
        st.warning("▶️ Select at least one cluster above.")
    else:
        data = []
        for m in count_metrics:
            total_sel = summary_df[
                (summary_df['Group'].isin(selected)) & (summary_df['Metric']==m)
            ]['Sum'].sum()
            pct = total_sel / totals[m] * 100 if totals[m] else np.nan
            data.append({'Metric': m, 'Share (%)': pct})
        comp_df = pd.DataFrame(data).set_index('Metric')
        st.table(comp_df.style.format("{:.1f}%"))
