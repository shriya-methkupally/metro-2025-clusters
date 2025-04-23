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
  .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
  .stMarkdown p, .stMarkdown span { color: #000000 !important; }
  .stTable td, .stTable th { color: #000000 !important; background-color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# ─── Cluster colors & descriptions ─────────────────────────────────────────────
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

# ─── Pillar metrics ────────────────────────────────────────────────────────────
talent_metrics = [
    "Science and Engineering Bachelor's", 'Phd', 'Profiles'
]
innovation_metrics = ['Publications','Patents','Contracts','HPC']
adoption_metrics = [
    'Job Postings','AI Startups','VC Funding',
    'Firm AI Use','Firm Data Readiness','Firm Cloud Readiness','Occupational Exposure to AI'
]
all_metrics = talent_metrics + innovation_metrics + adoption_metrics

# ─── Load data & merge cluster info ─────────────────────────────────────────────
df = pd.read_csv('SHRIYA_updated raw data_v4_clusters.csv', encoding='latin1')
cluster_info = pd.read_excel('cluster_groupings.xlsx', sheet_name='Sheet1')

df = df.merge(
    cluster_info[['Code','Combination','Group','talent_score','innovation_score','adoption_score']],
    left_on='CBSA Code', right_on='Code', how='left'
)
df['Group2'] = df['Group'].fillna(0).astype(int)
name_map = {
    1:'AI Superstars',2:'Star AI Hubs',3:'Emerging AI Centers',
    4:'Focused AI Scalers',5:'Nascent AI Adopters',6:'Others',0:'Small metros'
}
df['GroupName'] = df['Group2'].map(name_map)

# ensure numeric
for col in all_metrics + ['talent_score','innovation_score','adoption_score']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# precompute totals for adoption metrics
totals = {m: df[m].sum(skipna=True) for m in adoption_metrics}

# ─── Build summary_df ─────────────────────────────────────────────────────────
records = []
for grp, gdf in df.groupby('GroupName'):
    for m in all_metrics:
        arr = gdf[m].dropna()
        if arr.empty: continue
        rec = {
            'Group': grp, 'Metric': m,
            'Mean':       arr.mean(),
            'Min':        arr.min(),
            'Max':        arr.max(),
            'Range':      arr.max()-arr.min(),
            'Best Metro': gdf.loc[arr.idxmax(),'CBSA Title'],
            'Worst Metro':gdf.loc[arr.idxmin(),'CBSA Title']
        }
        if m in adoption_metrics:
            rec['Sum']       = arr.sum()
            rec['Share (%)'] = rec['Sum']/totals[m]*100 if totals[m] else np.nan
        records.append(rec)
summary_df = pd.DataFrame(records)

# ─── Sidebar: Mode & Pillar filter ─────────────────────────────────────────────
mode = st.sidebar.radio("Dashboard View",
    ["Group Overviews","Group Comparison","Metro Search"]
)

# ─── Group Overviews ──────────────────────────────────────────────────────────
if mode == "Group Overviews":
    st.sidebar.header("Overview Filters")
    pillar = st.sidebar.radio("Pillar",
        ["📊 All","🎓 Talent","🔬 Innovation","🤖 Adoption"]
    )
    grp = st.sidebar.selectbox("Cluster Group", sorted(summary_df['Group'].unique()))
    if pillar=="🎓 Talent":
        mets = [m for m in talent_metrics if m in summary_df['Metric'].unique()]
    elif pillar=="🔬 Innovation":
        mets = [m for m in innovation_metrics if m in summary_df['Metric'].unique()]
    elif pillar=="🤖 Adoption":
        mets = [m for m in adoption_metrics if m in summary_df['Metric'].unique()]
    else:
        mets = summary_df[summary_df['Group']==grp]['Metric'].unique().tolist()
    m = st.sidebar.selectbox("Metric", mets)

    # ─ KPI Row ─
    group_df = df[df['GroupName']==grp]
    count_metros = group_df.shape[0]
    t_score = group_df['talent_score'].mean()
    i_score = group_df['innovation_score'].mean()
    a_score = group_df['adoption_score'].mean()
    k1,k2,k3,k4 = st.columns([1,1,1,1])
    k1.metric("Count",      f"{count_metros:,}")
    k2.metric("Talent",     f"{t_score:0.00}")
    k3.metric("Innovation", f"{i_score:0.00}")
    k4.metric("Adoption",   f"{a_score:0.00}")

    # ─ Callout Panel ─
    arr = group_df[m].dropna()
    best_val = arr.max(); best_metro = group_df.loc[arr.idxmax(),'CBSA Title']
    worst_val= arr.min(); worst_metro= group_df.loc[arr.idxmin(),'CBSA Title']
    spread   = best_val - worst_val
    st.success(f"🏆 Top Metro: {best_metro} — {best_val:0.00}")
    st.error  (f"⚠️ Biggest Spread: {best_val:0.00} vs {worst_val:0.00} (Δ {spread:0.00})")

    # ─ Stat Cards ─
    row = summary_df[(summary_df['Group']==grp)&(summary_df['Metric']==m)].iloc[0]
    c1,c2,c3,c4,c5 = st.columns(5)
    cards = [('Mean',row['Mean']),('Min',row['Min']),('Max',row['Max']),('Range',row['Range'])]
    for col_box,(lbl,val) in zip([c1,c2,c3,c4], cards):
        col_box.metric(lbl, f"{val:0.00}")
    if m in adoption_metrics:
        c5.metric("Share (%)", f"{row['Share (%)']:0.00}%")

    # ─ Top/Bottom Metros ─
    st.markdown("### Top Metros")
    for i,(mt,vl) in enumerate(zip(*group_df[['CBSA Title',m]].nlargest(5,m).values.T),1):
        st.markdown(f"{i}. {mt} — {vl:0.00}")
    st.markdown("### Bottom Metros")
    for i,(mt,vl) in enumerate(zip(*group_df[['CBSA Title',m]].nsmallest(5,m).values.T),1):
        st.markdown(f"{i}. {mt} — {vl:0.00}")

    # ─ Strength & Weakness Heatmap ─
    comb = group_df['Combination'].value_counts()
    pct  = (comb/comb.sum()*100).round(1)
    comb_df = pd.DataFrame({'Count':comb,'Share (%)':pct})
    st.dataframe(
        comb_df.style.background_gradient(cmap='Blues')
               .format({'Share (%)':'{:.2f}%'}),
        use_container_width=True
    )

# ─── Group Comparison ─────────────────────────────────────────────────────────
elif mode == "Group Comparison":
    st.header("Group Comparison")
    st.markdown("Select clusters to compare their adoption shares:")
    cols = st.columns(3)
    selected = [grp for i,grp in enumerate(group_colors) if cols[i%3].checkbox(grp)]
    if not selected:
        st.warning("Please select at least one cluster.")
    else:
        rows=[]
        for m in adoption_metrics:
            total_sel = summary_df[
                (summary_df['Group'].isin(selected)) & (summary_df['Metric']==m)
            ]['Sum'].sum()
            pct = total_sel/totals[m]*100 if totals[m] else np.nan
            rows.append({'Metric':m,'Share (%)':pct})
        cmp_df = pd.DataFrame(rows).set_index('Metric')
        st.dataframe(
            cmp_df.style.format('{:.2f}%')
                  .set_properties(color="#000000",background="#FFFFFF"),
            use_container_width=True
        )

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
        pct = (val/totals[m]*100) if m in adoption_metrics else np.nan
        rows.append({'Metric':m,'Value':val,'Share (%)':pct})
    metro_df = pd.DataFrame(rows).set_index('Metric')
    st.dataframe(
        metro_df.style.format({'Value':'{:.2f}','Share (%)':'{:.2f}%'}),
        use_container_width=True
    )
