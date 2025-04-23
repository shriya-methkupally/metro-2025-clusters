import streamlit as st
import pandas as pd
import numpy as np

# ─── Page config & CSS ─────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Metro Dashboard", layout="wide", page_icon="🤖")
st.markdown("""
<style>
  .stApp { background-color: #F2F3F4 !important; }
  [data-testid="stSidebar"] { background-color: #FFFFFF !important; }
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stRadio label,
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stCheckbox label { color: #000000 !important; }
  .stMarkdown h1, .stMarkdown p, .stMarkdown span { color: #000000 !important; }
  .stTable, .stTable td, .stTable th { 
    margin-left:auto !important; margin-right:auto !important;
    color: #000000 !important; background-color: #FFFFFF !important;
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
    'Nascent AI Adopters': "Medium strength across at least two indicators (≥ two Ms, no Ts)",
    'Others':              "Low strength across at least two indicators (≥ two Bs, no Ts)",
    'Small metros':        "Not assigned to T/M/B tiers"
}

# ─── Define metrics ────────────────────────────────────────────────────────────
count_metrics = ['Job Postings','AI Startups','VC Funding']
firm_metrics  = ['Firm AI Use','Firm Data Readiness','Firm Cloud Readiness','Occupational Exposure to AI']
talent_metrics = ["Science and Engineering Bachelor's",'Phd','Profiles']
innovation_metrics = ['Publications','Patents','Contracts','HPC']
all_metrics = count_metrics + firm_metrics + talent_metrics + innovation_metrics

# ─── Load & prepare data ───────────────────────────────────────────────────────
df = pd.read_csv('SHRIYA_updated raw data_v4_clusters.csv', encoding='latin1')
cluster_info = pd.read_excel('cluster_groupings.xlsx', sheet_name=0)
df = df.merge(
    cluster_info[['Code','Combination','Group']],
    left_on='CBSA Code', right_on='Code', how='left'
)
df['Group2']    = df['Group'].fillna(0).astype(int)
name_map = {1:'AI Superstars',2:'Star AI Hubs',3:'Emerging AI Centers',
            4:'Focused AI Scalers',5:'Nascent AI Adopters',6:'Others',0:'Small metros'}
df['GroupName'] = df['Group2'].map(name_map)

for c in all_metrics:
    df[c] = pd.to_numeric(df[c], errors='coerce')
totals = {m: df[m].sum(skipna=True) for m in count_metrics}

# ─── Build summary_df ─────────────────────────────────────────────────────────
records = []
for grp, gdf in df.groupby('GroupName'):
    for m in all_metrics:
        vals = gdf[m].dropna()
        if vals.empty: continue
        rec = {
            'Group': grp, 'Metric': m,
            'Mean': vals.mean(), 'Min': vals.min(),
            'Max': vals.max(), 'Range': vals.max()-vals.min(),
            'Best Metro': gdf.loc[vals.idxmax(),'CBSA Title'],
            'Worst Metro':gdf.loc[vals.idxmin(),'CBSA Title']
        }
        if m in count_metrics:
            rec['Sum']       = vals.sum()
            rec['Share (%)'] = rec['Sum']/totals[m]*100 if totals[m] else np.nan
        records.append(rec)
summary_df = pd.DataFrame(records)

# ─── Sidebar: View Mode ────────────────────────────────────────────────────────
mode = st.sidebar.radio("View", ["Group Overviews","Group Comparison","Metro Search"])

# ─── Group Overviews ──────────────────────────────────────────────────────────
if mode == "Group Overviews":
    st.sidebar.header("Filters")
    grp = st.sidebar.selectbox("Cluster Group", sorted(summary_df['Group'].unique()))
    m = st.sidebar.selectbox("Metric", summary_df[summary_df['Group']==grp]['Metric'].unique())

    st.markdown(f"<h1 style='color:{group_colors[grp]};'>{m} — {grp}</h1>", unsafe_allow_html=True)
    st.markdown(f"*{group_defs[grp]}*")

    cnt = df[df['GroupName']==grp].shape[0]
    row = summary_df[(summary_df['Group']==grp)&(summary_df['Metric']==m)].iloc[0]

    cols = st.columns(5)
    stats = [
        ('Count', cnt), ('Mean', row['Mean']),
        ('Min', row['Min']), ('Max', row['Max']),
        ('Range', row['Range'])
    ]
    for box,(lbl,val) in zip(cols, stats):
        box.metric(lbl, f"{val:,.2f}")

    if m in count_metrics:
        st.metric("Share (%)", f"{row['Share (%)']:.2f}%")

    st.markdown("### Top Metros")
    top = df[df['GroupName']==grp][['CBSA Title',m]].nlargest(5, m)
    for i,(mt,vl) in enumerate(zip(top['CBSA Title'], top[m]), 1):
        st.write(f"{i}. {mt} — {vl:,.2f}")

    st.markdown("### Bottom Metros")
    bot = df[df['GroupName']==grp][['CBSA Title',m]].nsmallest(5, m)
    for i,(mt,vl) in enumerate(zip(bot['CBSA Title'], bot[m]), 1):
        st.write(f"{i}. {mt} — {vl:,.2f}")

    st.markdown("### Strength & Weakness Profile")
    comb = df[df['GroupName']==grp]['Combination'].value_counts()
    pct = (comb/comb.sum()*100).round(1)
    st.table(pd.DataFrame({'Count':comb,'Share (%)':pct}))

# ─── Group Comparison ─────────────────────────────────────────────────────────
elif mode == "Group Comparison":
    st.header("Group Comparison")
    st.markdown("Select clusters to compare metrics:")

    check_cols = st.columns(3)
    selected = [g for i,g in enumerate(group_colors) if check_cols[i%3].checkbox(g)]
    if not selected:
        st.warning("Select at least one cluster.")
    else:
        rows = []
        metrics_to_compare = count_metrics + firm_metrics + talent_metrics + innovation_metrics
        for m in metrics_to_compare:
            if m in count_metrics:
                total_sel = summary_df[
                    (summary_df['Group'].isin(selected)) & (summary_df['Metric']==m)
                ]['Sum'].sum()
                val = total_sel / totals[m] * 100 if totals[m] else np.nan
            else:
                val = df[df['GroupName'].isin(selected)][m].mean()
            rows.append({'Metric': m, 'Value': val})
        comp_df = pd.DataFrame(rows).set_index('Metric')
        st.table(comp_df.style.format({'Value':'{:.2f}' + ('%' if m in count_metrics else '')}))

# ─── Metro Search ─────────────────────────────────────────────────────────────
else:
    st.header("Metro Search")
    st.sidebar.header("Filters")
    grp_ms = st.sidebar.selectbox("Cluster Group", sorted(df['GroupName'].unique()))
    metro = st.sidebar.selectbox("Metro", df[df['GroupName']==grp_ms]['CBSA Title'].sort_values())

    st.markdown(f"## {metro} — {grp_ms}")
    r = df[df['CBSA Title']==metro].iloc[0]
    rows = []
    for m in all_metrics:
        val = r[m]
        pct = (val/totals[m]*100) if m in count_metrics else np.nan
        rows.append({'Metric': m, 'Value': val, 'Share (%)': pct})
    metro_df = pd.DataFrame(rows).set_index('Metric')
    st.table(metro_df.style.format({'Value':'{:.2f}','Share (%)':'{:.2f}%'}))
