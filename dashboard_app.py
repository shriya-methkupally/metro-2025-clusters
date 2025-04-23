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
df['Group2']    = df['Group'].fillna(0).astype(int)
names = {
    1:'AI Superstars',2:'Star AI Hubs',3:'Emerging AI Centers',
    4:'Focused AI Scalers',5:'Nascent AI Adopters',6:'Others',0:'Small metros'
}
df['GroupName'] = df['Group2'].map(names)

# convert metrics to numeric
for c in all_metrics:
    df[c] = pd.to_numeric(df[c], errors='coerce')

# precompute totals for shares
totals = {m: df[m].sum(skipna=True) for m in adoption_metrics}

# ─── Build summary_df ─────────────────────────────────────────────────────────
records = []
for grp, gdf in df.groupby('GroupName'):
    for m in all_metrics:
        arr = gdf[m].dropna()
        if arr.empty:
            continue
        rec = {
            'Group': grp,
            'Metric': m,
            'Mean': arr.mean(),
            'Min':  arr.min(),
            'Max':  arr.max(),
            'Range': arr.max() - arr.min(),
            'Best Metro': gdf.loc[arr.idxmax(),'CBSA Title'],
            'Worst Metro':gdf.loc[arr.idxmin(),'CBSA Title']
        }
        if m in adoption_metrics:
            rec['Sum']       = arr.sum()
            rec['Share (%)'] = rec['Sum'] / totals[m] * 100 if totals[m] else np.nan
        records.append(rec)
summary_df = pd.DataFrame(records)

# ─── Sidebar: select view ──────────────────────────────────────────────────────
mode = st.sidebar.radio("View", ["Group Overviews","Group Comparison","Metro Search"])

# ─── Group Overviews ──────────────────────────────────────────────────────────
if mode == "Group Overviews":
    st.sidebar.header("Overview Filter")
    pillar = st.sidebar.selectbox("Pillar", ["All","Talent","Innovation","Adoption"])
    grp = st.sidebar.selectbox("Cluster Group", summary_df['Group'].unique())
    if pillar == "Talent":
        mets = [m for m in talent_metrics if m in summary_df['Metric'].unique()]
    elif pillar == "Innovation":
        mets = [m for m in innovation_metrics if m in summary_df['Metric'].unique()]
    elif pillar == "Adoption":
        mets = [m for m in adoption_metrics if m in summary_df['Metric'].unique()]
    else:
        mets = summary_df[summary_df['Group']==grp]['Metric'].unique().tolist()
    m = st.sidebar.selectbox("Metric", mets)

    # header + definition
    st.markdown(
        f"<h1 style='color:{group_colors[grp]};'>{m} — {grp}</h1>"
        f"<p><em>{group_defs[grp]}</em></p>",
        unsafe_allow_html=True
    )

    # stats cards
    cnt = df[df['GroupName']==grp].shape[0]
    row = summary_df[(summary_df['Group']==grp)&(summary_df['Metric']==m)].iloc[0]
    cols = st.columns(5)
    stats = [
        ('Count',cnt),
        ('Mean',row['Mean']),('Min',row['Min']),
        ('Max',row['Max']),('Range',row['Range'])
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

    if m in adoption_metrics:
        c5,c6 = st.columns(2)
        c5.metric("Sum",f"{row['Sum']:.0f}")
        c6.metric("Share (%)",f"{row['Share (%)']:.1f}%")

    st.markdown("### Top Metros")
    top = df[df['GroupName']==grp][['CBSA Title',m]].nlargest(5,m)
    for i,(mt,vl) in enumerate(zip(top['CBSA Title'],top[m]),1):
        st.markdown(f"<span style='color:#000000'>{i}. {mt} — {vl:.2f}</span>", unsafe_allow_html=True)

    st.markdown("### Bottom Metros")
    bot = df[df['GroupName']==grp][['CBSA Title',m]].nsmallest(5,m)
    for i,(mt,vl) in enumerate(zip(bot['CBSA Title'],bot[m]),1):
        st.markdown(f"<span style='color:#000000'>{i}. {mt} — {vl:.2f}</span>", unsafe_allow_html=True)

    st.markdown("### Strength & Weakness Profile")
    comb = df[df['GroupName']==grp]['Combination'].value_counts()
    pct  = (comb/comb.sum()*100).round(1)
    st.table(pd.DataFrame({'Count':comb,'Share (%)':pct}))

# ─── Group Comparison ─────────────────────────────────────────────────────────
elif mode == "Group Comparison":
    st.header("Group Comparison")
    st.markdown("Select clusters to view combined share (%) for each adoption metric.")
    cols = st.columns(3)
    sel = [grp for i,grp in enumerate(group_colors) if cols[i%3].checkbox(grp)]
    if not sel:
        st.warning("Select at least one cluster.")
    else:
        rows=[]
        for m in adoption_metrics:
            total_sel = summary_df[
                (summary_df['Group'].isin(sel)) & (summary_df['Metric']==m)
            ]['Sum'].sum()
            pct = total_sel / totals[m] * 100 if totals[m] else np.nan
            rows.append({'Metric':m,'Share (%)':pct})
        st.table(pd.DataFrame(rows).set_index('Metric'))

# ─── Metro Search ─────────────────────────────────────────────────────────────
else:
    st.header("Metro Search")
    st.sidebar.header("Search Filter")
    grp_ms = st.sidebar.selectbox("Cluster Group", sorted(df['GroupName'].unique()))
    metro  = st.sidebar.selectbox("Metro", df[df['GroupName']==grp_ms]['CBSA Title'].sort_values())
    st.markdown(f"## {metro} — {grp_ms}")
    r = df[df['CBSA Title']==metro].iloc[0]
    rows=[]
    for m in all_metrics:
        val = r[m]
        pct = (val/totals[m]*100) if m in adoption_metrics and totals[m] else np.nan
        rows.append({'Metric':m,'Value':val,'Share (%)':pct})
    metro_df = pd.DataFrame(rows).set_index('Metric')
    st.table(metro_df.style.format({'Value':'{:.2f}','Share (%)':'{:.1f}%'}))

