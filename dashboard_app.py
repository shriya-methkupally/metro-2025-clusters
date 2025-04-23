import streamlit as st
import pandas as pd
import numpy as np

# ─── Page config & styling ─────────────────────────────────────────────────────
st.set_page_config(page_title="AI Metro Dashboard", layout="wide", page_icon="🤖")
st.markdown("""
<style>
  /* App background */
  .stApp { background-color: #F2F3F4 !important; }
  /* Sidebar */
  [data-testid="stSidebar"] { background-color: #FFFFFF !important; }
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stRadio label,
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stCheckbox label {
    color: #000000 !important;
  }
  /* Main text */
  [data-testid="stMarkdownContainer"] * { color: #000000 !important; }
  /* Tables */
  .stTable td, .stTable th {
    color: #000000 !important;
    background-color: #FFFFFF !important;
    text-align: center !important;
  }
</style>
""", unsafe_allow_html=True)

# ─── Cluster colors & definitions ──────────────────────────────────────────────
group_colors = {
    'AI Superstars':'#003a70','Star AI Hubs':'#FF9E1B','Emerging AI Centers':'#8BB8E8',
    'Focused AI Scalers':'#F2CD00','Nascent AI Adopters':'#B1B3B3','Others':'#A569BD',
    'Small metros':'#58D68D'
}
group_defs = {
    'AI Superstars':       "Bay Area (unique cluster with highest capacity)",
    'Star AI Hubs':        "Strength across all indicators (TTT)",
    'Emerging AI Centers': "Strength across at least two indicators (at least two Ts)",
    'Focused AI Scalers':  "Focused strength along one indicator (only one T)",
    'Nascent AI Adopters': "Medium strength along at least two indicators (at least two Ms, no Ts)",
    'Others':              "Low strength across at least two indicators (two or more Bs, no Ts)",
    'Small metros':        "Not assigned to T/M/B tiers"
}

# ─── Pillar metric mapping ─────────────────────────────────────────────────────
talent_metrics = [
    "Science and Engineering Bachelor's",
    'Phd',
    'Profiles'
]
innovation_metrics = [
    'Publications','Patents','Contracts','HPC'
]
adoption_metrics = [
    'Job Postings','AI Startups','VC Funding',
    'Firm AI Use','Firm Data Readiness','Firm Cloud Readiness','Occupational Exposure to AI'
]
per_capita_metrics = [
    'Firm AI Use','Firm Data Readiness','Firm Cloud Readiness','Occupational Exposure to AI'
]
all_metrics = talent_metrics + innovation_metrics + adoption_metrics

# ─── Load & prepare data ───────────────────────────────────────────────────────
df = pd.read_csv('SHRIYA_updated raw data_v4_clusters.csv', encoding='latin1')
cluster_info = pd.read_excel('cluster_groupings.xlsx', sheet_name=0)

# merge on CBSA Code → Code
df = df.merge(
    cluster_info[['Code','Combination','Group']],
    left_on='CBSA Code', right_on='Code',
    how='left'
)
... (rest of original code unchanged) ...

# ─── Group Overviews ──────────────────────────────────────────────────────────
if mode == "Group Overviews":
    ...
    # stats cards
    cnt = df[df['GroupName']==grp].shape[0]
    row = summary_df[(summary_df['Group']==grp)&(summary_df['Metric']==m)].iloc[0]
    cols = st.columns(4)
    stats = [
        ('Count',cnt),
        ('Mean',row['Mean']),('Min',row['Min']),
        ('Max',row['Max'])
    ]
    for box,(lbl,val) in zip(cols,stats):
        box.markdown(
            f"<div style='background-color:{group_colors[grp]};"
            f"padding:10px;border-radius:8px;'>"
            f"<h4 style='color:white;margin:0'>{lbl}</h4>"
            f"<p style='color:white;font-size:20px;margin:0'>{val:.2f}</p>"
            "</div>",
            unsafe_allow_html=True
        )

    # only show sum/share for non-per-capita adoption metrics
    if m in adoption_metrics and m not in per_capita_metrics:
        c5,c6 = st.columns(2)
        c5.metric("Sum",f"{row['Sum']:.0f}")
        c6.metric("Share (%)",f"{row['Share (%)']:.1f}%")

    st.markdown("### Top Metros")
    ...
    st.markdown("### Strength & Weakness Profile")
    comb = df[df['GroupName']==grp]['Combination'].value_counts()
    pct  = (comb/comb.sum()*100).round(1)
    profile_df = pd.DataFrame({'Count':comb,'Share (%)':pct})
    st.table(profile_df.style.set_table_styles([
        {'selector': 'th, td', 'props': [('text-align', 'center')]}
    ]))

# ─── Group Comparison ─────────────────────────────────────────────────────────
elif mode == "Group Comparison":
    st.header("Group Comparison")
    st.markdown("Select clusters to view either combined share (%) or average value for each adoption metric.")
    cols = st.columns(3)
    sel = [grp for i,grp in enumerate(group_colors) if cols[i%3].checkbox(grp)]
    if not sel:
        st.warning("Select at least one cluster.")
    else:
        rows=[]
        for m in adoption_metrics:
            if m in per_capita_metrics:
                # average of group means
                means = summary_df[(summary_df['Group'].isin(sel)) & (summary_df['Metric']==m)]['Mean']
                val = means.mean() if not means.empty else np.nan
                rows.append({'Metric':m,'Average':val})
            else:
                total_sel = summary_df[
                    (summary_df['Group'].isin(sel)) & (summary_df['Metric']==m)
                ]['Sum'].sum()
                pct = total_sel / totals[m] * 100 if totals[m] else np.nan
                rows.append({'Metric':m,'Share (%)':pct})
        comp_df = pd.DataFrame(rows).set_index('Metric')
        st.table(comp_df.style.format({
            'Average':'{:.2f}','Share (%)':'{:.1f}%'
        }).set_table_styles([
            {'selector': 'th, td', 'props': [('text-align', 'center')]}
        ]))

# ─── Metro Search ─────────────────────────────────────────────────────────────
else:
    st.header("Metro Search")
    ...
    metro_df = pd.DataFrame(rows).set_index('Metric')
    st.table(metro_df.style.format({
        'Value':'{:.2f}','Share (%)':'{:.1f}%'
    }).set_table_styles([
        {'selector': 'th, td', 'props': [('text-align', 'center')]}
    ]))
