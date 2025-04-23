import streamlit as st
import pandas as pd
import numpy as np

# ─── Page config & styling ─────────────────────────────────────────────────────
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
  /* Sidebar radio & checkbox labels */
  .stSidebar .stRadio label, 
  .stSidebar .stCheckbox label {
    color: #1B2631 !important;
  }
  /* Tables */
  .stTable td, .stTable th {
    color: #1B2631 !important;
    background-color: #FFFFFF !important;
  }
</style>
""", unsafe_allow_html=True)

# ─── Cluster colors ────────────────────────────────────────────────────────────
group_colors = {
    'AI Superstars':       '#003a70',
    'Star AI Hubs':        '#FF9E1B',
    'Emerging AI Centers': '#8BB8E8',
    'Focused AI Scalers':  '#F2CD00',
    'Nascent AI Adopters': '#B1B3B3',
    'Others':              '#A569BD',
    'Small metros':        '#58D68D'
}

# ─── Group definitions ─────────────────────────────────────────────────────────
group_defs = {
    'AI Superstars':       "Bay Area (unique cluster with highest capacity)",
    'Star AI Hubs':        "Strength across all indicators (TTT)",
    'Emerging AI Centers': "Strength across at least two indicators (at least two Ts)",
    'Focused AI Scalers':  "Focused strength along one indicator (only one T)",
    'Nascent AI Adopters': "Medium strength along at least two indicators (at least two Ms, no Ts)",
    'Others':              "Low strength across at least two indicators (two or more Bs, no Ts)",
    'Small metros':        "Not assigned to T/M/B tiers"
}

# ─── Load & prepare data ───────────────────────────────────────────────────────
raw = pd.read_csv('SHRIYA_updated raw data_v1_clusters.csv', encoding='latin1')
chk = pd.read_excel('gpt check.xlsx', sheet_name=0)
df  = pd.merge(
    raw, chk[['Code','Combination','Group']],
    left_on='CBSA Code', right_on='Code', how='left'
)
df['Group2']    = df['Group'].fillna(0).astype(int)
names = {
    1:'AI Superstars',2:'Star AI Hubs',3:'Emerging AI Centers',
    4:'Focused AI Scalers',5:'Nascent AI Adopters',6:'Others',0:'Small metros'
}
df['GroupName'] = df['Group2'].map(names)

# ─── Define metrics ───────────────────────────────────────────────────────────
firm_metrics  = [
    'Firm AI Use','Firm Data Readiness',
    'Firm Cloud Readiness','Occupational Exposure to AI'
]
share_metrics = [
    'Job Postings','AI Startups','VC Funding',
    "Science and Engineering Bachelor's",'Phd','Profiles',
    'Publications','Patents','Contracts','HPC'
]
all_metrics   = firm_metrics + share_metrics

for c in all_metrics:
    df[c] = pd.to_numeric(df[c], errors='coerce')

totals = {m: df[m].sum(skipna=True) for m in share_metrics}

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
            'Min': arr.min(),
            'Max': arr.max(),
            'Range': arr.max() - arr.min(),
            'Best Metro': gdf.loc[arr.idxmax(),'CBSA Title'],
            'Worst Metro': gdf.loc[arr.idxmin(),'CBSA Title']
        }
        if m in share_metrics:
            rec['Sum'] = arr.sum()
            rec['Share (%)'] = rec['Sum'] / totals[m] * 100 if totals[m] else np.nan
        records.append(rec)
summary_df = pd.DataFrame(records)

# ─── Sidebar: select view ──────────────────────────────────────────────────────
mode = st.sidebar.radio(
    "View",
    ["Group Overviews", "Group Comparison", "Metro Search"]
)

# ─── Group Overviews ──────────────────────────────────────────────────────────
if mode == "Group Overviews":
    st.sidebar.header("Overview Filter")
    grp = st.sidebar.selectbox("Cluster Group", summary_df['Group'].unique())
    m   = st.sidebar.selectbox(
        "Metric",
        summary_df[summary_df['Group']==grp]['Metric'].unique()
    )

    # Header + definition
    st.markdown(
        f"<h1 style='color:{group_colors[grp]};'>{m} — {grp}</h1>"
        f"<p><em>{group_defs.get(grp)}</em></p>",
        unsafe_allow_html=True
    )

    # Count of metros
    cnt = df[df['GroupName']==grp].shape[0]
    row = summary_df[
        (summary_df['Group']==grp)&(summary_df['Metric']==m)
    ].iloc[0]

    # Stat cards: Count, Mean, Min, Max, Range
    cols = st.columns(5)
    stats = [
        ('Count', cnt),
        ('Mean',  row['Mean']),
        ('Min',   row['Min']),
        ('Max',   row['Max']),
        ('Range', row['Range'])
    ]
    for col_box,(label,val) in zip(cols,stats):
        col_box.markdown(
            f"<div style='background-color:{group_colors[grp]};"
            f"padding:10px;border-radius:8px;'>"
            f"<h4 style='color:white;margin:0'>{label}</h4>"
            f"<p style='color:white;font-size:20px;margin:0'>{val:.2f}</p>"
            "</div>",
            unsafe_allow_html=True
        )

    # Sum & Share
    if m in share_metrics:
        c5,c6 = st.columns(2)
        c5.metric("Sum", f"{row['Sum']:.0f}")
        c6.metric("Share (%)", f"{row['Share (%)']:.1f}%")

    # Top / Bottom Metros
    st.markdown("### 🔝 Top Metros")
    top = df[df['GroupName']==grp][['CBSA Title', m]] \
            .nlargest(5, m)
    for i,(metro,val) in enumerate(zip(top['CBSA Title'], top[m]),1):
        st.write(f"{i}. **{metro}** — {val:.2f}")

    st.markdown("### 🔽 Bottom Metros")
    bot = df[df['GroupName']==grp][['CBSA Title', m]] \
            .nsmallest(5, m)
    for i,(metro,val) in enumerate(zip(bot['CBSA Title'], bot[m]),1):
        st.write(f"{i}. **{metro}** — {val:.2f}")

    # Strength & Weakness (TMB combos)
    st.markdown("### Strength & Weakness Profile")
    comb = df[df['GroupName']==grp]['Combination'].value_counts()
    comb_pct = comb / comb.sum() * 100
    comb_df = pd.DataFrame({
        'Count': comb,
        'Share (%)': comb_pct.round(1)
    })
    st.table(comb_df)

# ─── Group Comparison ─────────────────────────────────────────────────────────
elif mode == "Group Comparison":
    st.header("Group Comparison")
    st.markdown("Select clusters to view combined share (%) for each count metric.")

    cols = st.columns(3)
    selected = [
        grp for idx, grp in enumerate(group_colors.keys())
        if cols[idx%3].checkbox(grp)
    ]

    if not selected:
        st.warning("Select at least one cluster.")
    else:
        rows = []
        for m in share_metrics:
            total_sel = summary_df[
                (summary_df['Group'].isin(selected)) &
                (summary_df['Metric']==m)
            ]['Sum'].sum()
            pct = total_sel / totals[m] * 100 if totals[m] else np.nan
            rows.append({'Metric': m, 'Share (%)': pct})
        comp_df = pd.DataFrame(rows).set_index('Metric')
        st.table(comp_df)

# ─── Metro Search ─────────────────────────────────────────────────────────────
else:
    st.header("Metro Search")
    st.sidebar.header("Search Filter")
    grp_ms = st.sidebar.selectbox("Cluster Group", sorted(df['GroupName'].unique()))
    metro  = st.sidebar.selectbox(
        "Metro",
        df[df['GroupName']==grp_ms]['CBSA Title'].sort_values()
    )

    st.markdown(f"## {metro} — {grp_ms}")
    r = df[df['CBSA Title']==metro].iloc[0]

    rows = []
    for m in all_metrics:
        val   = r[m]
        pct   = (val/totals[m]*100) if m in share_metrics and totals[m] else np.nan
        rows.append({'Metric': m, 'Value': val, 'Share (%)': pct})
    metro_df = pd.DataFrame(rows).set_index('Metric')
    st.table(metro_df.style.format({
        'Value': '{:.2f}',
        'Share (%)': '{:.1f}%'
    }))
