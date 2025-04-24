# ─── Metro Search ─────────────────────────────────────────────────────────────
else:
    st.header("Metro Search")
    st.sidebar.header("Search Filter")

    # Cluster & Metro selectors
    grp_ms = st.sidebar.selectbox(
        "Cluster Group",
        sorted(df['GroupName'].unique())
    )
    metro = st.sidebar.selectbox(
        "Metro",
        df[df['GroupName'] == grp_ms]['CBSA Title'].sort_values()
    )
    st.markdown(f"## {metro} — {grp_ms}")

    # Fetch the metro’s data row
    r = df[df['CBSA Title'] == metro].iloc[0]

    # Build rows: Value + Share(%) for non–per-capita metrics
    rows = []
    for m in all_metrics:
        val = r[m]
        row = {'Metric': m, 'Value': f"{val:.2f}"}
        if m not in per_capita_metrics:
            total = totals.get(m, 0)
            pct = (val / total * 100) if total else np.nan
            row['Share (%)'] = f"{pct:.1f}%"
        rows.append(row)

    metro_df = pd.DataFrame(rows).set_index('Metric')

    # Simply render the table—global CSS at top handles center alignment
    st.table(metro_df)
