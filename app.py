import re
import unicodedata

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils import load_emissions, top_categories_by_country, country_totals

DATA_SAMPLE = "data/sample_emissions.csv"
DATA_EDGAR = "data/GHG_totals_by_country.csv"
DATA_EDGAR_XLSX = "EDGAR_2026_GHG_booklet_2026.xlsx"

AFRICA_COUNTRY_ALIASES = {
    'Algeria': ['Algeria'],
    'Angola': ['Angola'],
    'Benin': ['Benin'],
    'Botswana': ['Botswana'],
    'Burkina Faso': ['Burkina Faso'],
    'Burundi': ['Burundi'],
    'Cabo Verde': ['Cabo Verde', 'Cape Verde'],
    'Cameroon': ['Cameroon'],
    'Central African Republic': ['Central African Republic', 'Central African Rep.', 'Central African Rep'],
    'Chad': ['Chad'],
    'Comoros': ['Comoros'],
    'Congo': ['Congo', 'Congo-Brazzaville'],
    'Democratic Republic of the Congo': ['Democratic Republic of the Congo', 'DR Congo', 'D R Congo', 'Congo, Dem. Rep.'],
    'Cote d\'Ivoire': ['Cote d\'Ivoire', "Côte d'Ivoire", 'Cote d Ivoire', 'Ivory Coast'],
    'Djibouti': ['Djibouti'],
    'Egypt': ['Egypt'],
    'Equatorial Guinea': ['Equatorial Guinea'],
    'Eritrea': ['Eritrea'],
    'Eswatini': ['Eswatini', 'Swaziland'],
    'Ethiopia': ['Ethiopia'],
    'Gabon': ['Gabon'],
    'Gambia': ['Gambia'],
    'Ghana': ['Ghana'],
    'Guinea': ['Guinea'],
    'Guinea-Bissau': ['Guinea-Bissau', 'Guinea Bissau'],
    'Kenya': ['Kenya'],
    'Lesotho': ['Lesotho'],
    'Liberia': ['Liberia'],
    'Libya': ['Libya'],
    'Madagascar': ['Madagascar'],
    'Malawi': ['Malawi'],
    'Mali': ['Mali'],
    'Mauritania': ['Mauritania'],
    'Mauritius': ['Mauritius'],
    'Morocco': ['Morocco'],
    'Mozambique': ['Mozambique'],
    'Namibia': ['Namibia'],
    'Niger': ['Niger'],
    'Nigeria': ['Nigeria'],
    'Rwanda': ['Rwanda'],
    'Sao Tome and Principe': ['Sao Tome and Principe', 'São Tomé & Príncipe', 'Sao Tome and Principe', 'Sao Tome & Principe'],
    'Senegal': ['Senegal'],
    'Seychelles': ['Seychelles'],
    'Sierra Leone': ['Sierra Leone'],
    'Somalia': ['Somalia'],
    'South Africa': ['South Africa'],
    'South Sudan': ['South Sudan'],
    'Sudan': ['Sudan'],
    'Tanzania': ['Tanzania'],
    'Togo': ['Togo'],
    'Tunisia': ['Tunisia'],
    'Uganda': ['Uganda'],
    'Zambia': ['Zambia'],
    'Zimbabwe': ['Zimbabwe'],
}

GAS_LOOKUP = {
    'co2': {'label': 'Fossil CO2', 'substance': 'CO2', 'color': '#374151'},
    'ch4': {'label': 'Methane (CH4)', 'substance': 'GWP_100_AR5_CH4', 'color': '#d97706'},
    'n2o': {'label': 'Nitrous Oxide (N2O)', 'substance': 'GWP_100_AR5_N2O', 'color': '#059669'},
    'f_gases': {'label': 'F-gases', 'substance': 'GWP_100_AR5_F-gases', 'color': '#7c3aed'},
}


def normalize_country_name(value):
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace('&', ' and ')
    text = text.replace('.', '').replace('-', ' ').replace("'", '').replace(',', '').replace('’', '')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def is_africa_country(country_name):
    if pd.isna(country_name):
        return False
    norm = normalize_country_name(country_name)
    for canonical, aliases in AFRICA_COUNTRY_ALIASES.items():
        for alias in aliases:
            if normalize_country_name(alias) == norm:
                return True
    return False


def drop_global_total(df, country_col='Country'):
    if df.empty or country_col not in df.columns:
        return df.copy()
    mask = ~df[country_col].astype(str).str.strip().str.upper().str.contains('GLOBAL TOTAL|WORLD TOTAL', case=False, na=False)
    return df.loc[mask].copy()


def render_filter_bar(df, year_col="year", country_col="country"):
    """Returns the selected year, Africa-only flag, and a filtered dataframe."""
    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        years = sorted(pd.Series(df[year_col].dropna().unique()).astype(str).tolist())
        try:
            years = sorted(pd.to_numeric(df[year_col], errors='coerce').dropna().unique().tolist())
        except Exception:
            pass
        selected_year = st.selectbox("Year", years, index=len(years) - 1)

    with col2:
        africa_only = st.checkbox("🌍 Show Africa Only")

    with col3:
        st.caption("Use the year and regional filters to focus the chart.")

    filtered = df[df[year_col] == selected_year].copy()
    if africa_only:
        filtered = filtered[filtered[country_col].apply(is_africa_country)]

    return selected_year, africa_only, filtered


def render_country_totals(scope, title_override=None):
    df_totals = pd.read_csv(DATA_EDGAR)
    years = df_totals.columns.tolist()[2:]
    year = st.sidebar.selectbox("Select year", years, index=len(years) - 1)

    df_year = df_totals[['EDGAR Country Code', 'Country', *years]].copy()
    df_year = df_year.melt(id_vars=['EDGAR Country Code', 'Country'], var_name='year', value_name='value')
    df_year['year'] = pd.to_numeric(df_year['year'], errors='coerce')
    df_year['value'] = pd.to_numeric(df_year['value'], errors='coerce').fillna(0)

    africa_only = scope == 'Africa'
    if africa_only:
        df_year = df_year[df_year['Country'].apply(is_africa_country)]

    selected_year = int(year)
    filtered = df_year[df_year['year'] == selected_year].copy()
    filtered = drop_global_total(filtered, country_col='Country')
    if filtered.empty:
        st.info('No data for the selected year and scope.')
        return selected_year

    total = filtered['value'].sum()
    top_row = filtered.sort_values('value', ascending=False).iloc[0]
    trend_df = drop_global_total(df_year.copy(), country_col='Country').groupby('year', as_index=False)['value'].sum().sort_values('year')

    c1, c2, c3 = st.columns(3)
    c1.metric("Top Emitter", str(top_row['Country']), f"{top_row['value']:,.0f} Mt")
    c2.metric("Countries Shown", len(filtered))
    c3.metric("Selected Year", selected_year)

    fig_trend = px.line(trend_df, x='year', y='value', markers=True,
                        title='Emissions Trend Over Time')
    fig_trend.update_traces(line_color='#1e3a5f', line_width=3)
    fig_trend.update_layout(template='plotly_white', height=360, margin=dict(t=60, l=30, r=20, b=30))
    st.plotly_chart(fig_trend, use_container_width=True)

    heading = title_override or "Top 30 emitters"
    st.subheader(f"{heading} — {selected_year}")
    st.caption("Showing the 30 highest emitting countries for the selected year. Values (Mt CO2e) are shown on the bars.")

    top30 = filtered.sort_values('value', ascending=False).head(30).copy()
    top30['value_str'] = top30['value'].map(lambda v: f"{v:,.1f}")
    top30_sorted = top30.sort_values('value', ascending=True)
    fig = px.bar(top30_sorted, x='value', y='Country', orientation='h', text='value_str',
                 labels={'value': 'Emissions (Mt CO2e)', 'Country': 'Country'},
                 title=f"Top 30 emitting countries in {selected_year}")
    fig.update_traces(textposition='outside', marker_color='#1f77b4')
    fig.update_layout(template='plotly_white', height=700, margin=dict(l=160, r=40, t=80, b=40))
    fig.update_xaxes(tickformat=',.0f')
    st.plotly_chart(fig, use_container_width=True)
    return selected_year


def render_ghg_totals_view(scope):
    st.title("GHG Totals by Country")
    st.caption("Full ranked breakdown, filtered by year and region.")

    df_totals = pd.read_csv(DATA_EDGAR)
    years = [c for c in df_totals.columns if c not in ['EDGAR Country Code', 'Country']]
    df = df_totals[['Country', *years]].copy()
    df = df.melt(id_vars=['Country'], var_name='year', value_name='value')
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['value'] = pd.to_numeric(df['value'], errors='coerce').fillna(0)
    df = df.rename(columns={'Country': 'country'})

    selected_year, africa_only, filtered = render_filter_bar(df, year_col='year', country_col='country')
    chart_df = drop_global_total(filtered.copy(), country_col='country')

    if chart_df.empty:
        st.info('No country-level data for the selected year and region.')
        return

    limit = 50 if africa_only else 10
    top_n = chart_df.sort_values('value', ascending=False).head(limit)

    fig = px.bar(top_n, x='country', y='value',
                 title=f"{('Africa' if africa_only else 'Global')} GHG Totals — {selected_year}",
                 color_discrete_sequence=['#1e3a5f'])
    fig.update_layout(xaxis_tickangle=-45, height=500, template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Full Data Table")
    display_df = filtered.sort_values('value', ascending=False).reset_index(drop=True)
    display_df.index = range(1, len(display_df) + 1)
    st.dataframe(
        display_df.rename(columns={'country': 'Country', 'value': 'GHG Total (Mt)'}),
        use_container_width=True
    )

    st.caption(f"⚠️ Showing {len(chart_df)} {'African' if africa_only else ''} countries for {selected_year}.")


def render_per_capita_view(scope):
    st.title("GHG Per Capita by Country")
    st.caption("Country-level emissions intensity per person, filtered by year and region. Units are t CO2e per person.")

    df_capita = pd.read_excel(DATA_EDGAR_XLSX, sheet_name='GHG_per_capita_by_country', engine='openpyxl')
    years = [c for c in df_capita.columns if c not in ['EDGAR Country Code', 'Country']]
    df = df_capita[['Country', *years]].copy()
    df = df.melt(id_vars=['Country'], var_name='year', value_name='value')
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['value'] = pd.to_numeric(df['value'], errors='coerce').fillna(0)
    df = df.rename(columns={'Country': 'country'})

    selected_year, africa_only, filtered = render_filter_bar(df, year_col='year', country_col='country')
    chart_df = drop_global_total(filtered.copy(), country_col='country')

    if chart_df.empty:
        st.info('No country-level per-capita data for the selected year and region.')
        return

    limit = 50 if africa_only else 10
    top_n = chart_df.sort_values('value', ascending=False).head(limit)

    fig = px.bar(
        top_n,
        x='country',
        y='value',
        title=f"{('Africa' if africa_only else 'Global')} GHG per Capita — {selected_year} (t CO2e per person)",
        color_discrete_sequence=['#8b5cf6'],
        labels={'value': 'GHG per capita (t CO2e/person)', 'country': 'Country'}
    )
    fig.update_layout(xaxis_tickangle=-45, height=500, template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Full Data Table")
    display_df = chart_df.sort_values('value', ascending=False).reset_index(drop=True)
    display_df.index = range(1, len(display_df) + 1)
    st.dataframe(
        display_df.rename(columns={'country': 'Country', 'value': 'GHG per capita (t CO2e/person)'}),
        use_container_width=True
    )

    st.caption(f"⚠️ Showing {len(chart_df)} {'African' if africa_only else ''} countries for {selected_year}. Units are t CO2e per person.")


def load_sector_gas_data(substance_filter=None):
    """Load the EDGAR sector-by-country sheet and optionally filter to one or more substances."""
    try:
        edgar_sheet = pd.read_excel(DATA_EDGAR_XLSX, sheet_name='GHG_by_sector_and_country', engine='openpyxl')
    except Exception as e:
        st.error(f"Failed to read EDGAR sheet: {e}")
        return pd.DataFrame()

    year_cols = [c for c in edgar_sheet.columns if (isinstance(c, int) or (isinstance(c, str) and c.isdigit()))]
    id_cols = [c for c in edgar_sheet.columns if c not in year_cols]
    df_long = edgar_sheet.melt(id_vars=id_cols, value_vars=year_cols, var_name='year', value_name='value')
    df_long['year'] = pd.to_numeric(df_long['year'], errors='coerce')
    df_long['value'] = pd.to_numeric(df_long['value'], errors='coerce').fillna(0)
    df_long = df_long.rename(columns={'Country': 'country', 'Sector': 'sector', 'Substance': 'substance'})

    if substance_filter is None:
        return df_long

    if isinstance(substance_filter, str):
        substance_filter = [substance_filter]

    substance_filter = {str(s).strip() for s in substance_filter}
    if not substance_filter:
        return df_long

    df_long = df_long[df_long['substance'].astype(str).isin(substance_filter)].copy()
    return df_long


def render_gas_tab(gas_key, gas_label, gas_color, gas_df):
    gas_df = gas_df.copy()
    year_values = sorted(gas_df['year'].dropna().astype(int).unique().tolist())
    if not year_values:
        st.info(f'No year data available for {gas_label}.')
        return

    col1, col2, col3 = st.columns([1.2, 1.5, 2])
    with col1:
        selected_year = st.selectbox('Year', year_values, index=len(year_values) - 1)
    with col2:
        countries = ['All'] + sorted(gas_df['country'].dropna().astype(str).unique().tolist())
        selected_country = st.selectbox('Country', countries, index=0)
    with col3:
        africa_only = st.checkbox('🌍 Africa Only', value=False)

    filtered = gas_df[gas_df['year'] == selected_year].copy()
    filtered = drop_global_total(filtered.copy(), country_col='country')

    if selected_country != 'All':
        filtered = filtered[filtered['country'] == selected_country]
    if africa_only:
        filtered = filtered[filtered['country'].apply(is_africa_country)]

    if filtered.empty:
        st.info(f'No country-level data for {gas_label} in the selected year and region.')
        return

    country_totals = filtered.groupby('country', as_index=False)['value'].sum().sort_values('value', ascending=False)
    total = country_totals['value'].sum()
    top_row = country_totals.iloc[0]

    c1, c2 = st.columns(2)
    c1.metric(f"{gas_label} Total", f"{total:,.0f}")
    c2.metric("Top Source Country", top_row['country'], f"{top_row['value']:,.0f}")

    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        limit = 50 if africa_only else 10
        top_n = country_totals.head(limit)
        fig = px.bar(top_n, x='value', y='country', orientation='h', color_discrete_sequence=[gas_color],
                     title=f"{gas_label} totals — {selected_year}")
        fig.update_layout(height=max(350, limit * 20), template='plotly_white', margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        sector_df = gas_df[gas_df['year'] == selected_year].copy()
        sector_df = drop_global_total(sector_df, country_col='country')
        if selected_country != 'All':
            sector_df = sector_df[sector_df['country'] == selected_country]
        if africa_only:
            sector_df = sector_df[sector_df['country'].apply(is_africa_country)]
        sector_df = sector_df.groupby('sector', as_index=False)['value'].sum().sort_values('value', ascending=False)
        if sector_df.empty:
            st.info('No sector breakdown for this selection.')
            return

        total_sector = sector_df['value'].sum()
        if total_sector > 0:
            sector_df['value'] = (sector_df['value'] / total_sector) * 100
        else:
            sector_df['value'] = 0.0

        sector_df = sector_df.sort_values('value', ascending=False).head(8)
        heat = go.Figure(data=go.Heatmap(
            z=[sector_df['value'].tolist()],
            x=sector_df['sector'].tolist(),
            y=["Share of total"],
            colorscale=[[0, '#f8fafc'], [0.3, '#dbeafe'], [0.7, gas_color], [1, '#0f172a']],
            zmin=0,
            zmax=max(100, sector_df['value'].max() * 1.2),
            text=[[f"{v:.1f}%" for v in sector_df['value']]],
            texttemplate='%{text}',
            hovertemplate='Sector: %{x}<br>Share: %{z:.1f}%<extra></extra>',
            showscale=True,
            colorbar=dict(title='Share %', len=0.7, thickness=12)
        ))
        heat.update_xaxes(tickangle=-35, tickfont=dict(size=10), side='bottom')
        heat.update_yaxes(showticklabels=False, ticks='')
        heat.update_layout(
            title=f"{gas_label} sector share — {selected_year}",
            template='plotly_white',
            height=260,
            margin=dict(l=25, r=20, t=60, b=60),
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        st.plotly_chart(heat, use_container_width=True)


def render_sector_view(scope):
    try:
        edgar_sheet = pd.read_excel(DATA_EDGAR_XLSX, sheet_name='GHG_by_sector_and_country', engine='openpyxl')
    except Exception as e:
        st.error(f"Failed to read EDGAR sheet: {e}")
        edgar_sheet = None

    if edgar_sheet is None:
        return

    year_cols = [c for c in edgar_sheet.columns if (isinstance(c, int) or (isinstance(c, str) and c.isdigit()))]
    id_cols = [c for c in edgar_sheet.columns if c not in year_cols]
    df_long = edgar_sheet.melt(id_vars=id_cols, value_vars=year_cols, var_name='year', value_name='emissions_mtco2')
    df_long['year'] = df_long['year'].astype(int)
    df_long['emissions_mtco2'] = pd.to_numeric(df_long['emissions_mtco2'], errors='coerce').fillna(0)

    countries_all = sorted(df_long['Country'].dropna().astype(str).unique().tolist())
    africa_defaults = [c for c in countries_all if is_africa_country(c)]
    sectors_all = sorted(df_long['Sector'].dropna().unique().tolist())
    substances_all = sorted(df_long['Substance'].dropna().unique().tolist())
    years_all = sorted(df_long['year'].dropna().astype(int).unique().tolist())

    st.markdown('### Sector filters')
    filter_cols = st.columns(4)
    with filter_cols[0]:
        selected_year = st.selectbox('Year', years_all, index=len(years_all) - 1)
    with filter_cols[1]:
        selected_sector = st.selectbox('Sector', ['All'] + sectors_all, index=0)
    with filter_cols[2]:
        country_options = ['All'] + countries_all
        default_country_index = 0 if scope == 'Global' else (0 if not africa_defaults else 0)
        selected_country = st.selectbox('Country', country_options, index=default_country_index)
    with filter_cols[3]:
        selected_substance = st.selectbox('Substance', ['All'] + substances_all, index=0)

    df_year = df_long[df_long['year'] == selected_year].copy()
    if scope == 'Africa':
        df_year = df_year[df_year['Country'].apply(is_africa_country)]
    df_year = df_year.rename(columns={'Country': 'country', 'Sector': 'sector', 'Substance': 'substance', 'emissions_mtco2': 'emissions_mtco2'})

    if selected_sector != 'All':
        df_year = df_year[df_year['sector'] == selected_sector]
    if selected_substance != 'All':
        df_year = df_year[df_year['substance'] == selected_substance]
    if selected_country != 'All':
        df_sel = df_year[df_year['country'] == selected_country].copy()
    else:
        df_sel = df_year.copy()

    df_sel = drop_global_total(df_sel.copy(), country_col='country')

    st.subheader(f"GHG by sector and substance — {selected_year}")
    if df_sel.empty:
        st.info('No data for this selection.')
        return

    sector_totals = df_sel.groupby('sector', as_index=False)['emissions_mtco2'].sum().sort_values('emissions_mtco2', ascending=False)
    sector_totals['value_label'] = sector_totals['emissions_mtco2'].map(lambda v: f"{v:,.1f}")
    top_sector = sector_totals.iloc[0]
    total_sector = sector_totals['emissions_mtco2'].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric('Total GHG', f"{total_sector:,.0f} Mt")
    c2.metric('Top Sector', str(top_sector['sector']))
    c3.metric('Top Sector Total', f"{top_sector['emissions_mtco2']:,.0f} Mt")

    st.caption(f"Sector analysis for {selected_year}: {top_sector['sector']} contributes the largest share of total emissions in this dataset. Units shown are Mt CO2e for the selected year and filters.")

    fig_sector = px.bar(
        sector_totals.sort_values('emissions_mtco2', ascending=True),
        x='emissions_mtco2',
        y='sector',
        orientation='h',
        text='value_label',
        labels={'emissions_mtco2': 'GHG Total (Mt CO2e)', 'sector': 'Sector'},
        title=f"GHG totals by sector — {selected_year} (Mt CO2e)",
        color_discrete_sequence=['#1f77b4']
    )
    fig_sector.update_traces(textposition='outside', cliponaxis=False)
    fig_sector.update_layout(template='plotly_white', height=max(420, len(sector_totals) * 30), margin=dict(l=150, r=40, t=60, b=30))
    fig_sector.update_xaxes(tickformat=',.0f')
    st.plotly_chart(fig_sector, use_container_width=True)

    fig_sb = px.sunburst(df_sel, path=['substance', 'sector', 'country'], values='emissions_mtco2', title=f"Substance → Sector → Country — {selected_year} (Mt CO2e)")
    fig_sb.update_layout(template='plotly_white', margin=dict(t=50, l=0, r=0, b=0))
    fig_sb.update_traces(textinfo='label+percent parent')
    st.plotly_chart(fig_sb, use_container_width=True)

    agg = df_sel.groupby(['country', 'sector'], as_index=False)['emissions_mtco2'].sum()
    pivot = agg.pivot(index='country', columns='sector', values='emissions_mtco2').fillna(0)
    fig_stacked = px.bar(pivot, y=pivot.index, x=pivot.columns, orientation='h', title=f"Country totals by sector — {selected_year} (Mt CO2e)")
    fig_stacked.update_layout(template='plotly_white', height=600, margin=dict(l=160, r=40, t=60, b=40))
    fig_stacked.update_xaxes(title_text='Emissions (Mt CO2e)')
    fig_stacked.update_yaxes(title_text='Country')
    st.plotly_chart(fig_stacked, use_container_width=True)

    st.markdown('---')
    st.subheader('Top country contributors')
    country_totals_bar = df_sel.groupby('country', as_index=False)['emissions_mtco2'].sum().sort_values('emissions_mtco2', ascending=False).head(20)
    country_totals_bar['value_str'] = country_totals_bar['emissions_mtco2'].map(lambda v: f"{v:,.1f}")
    fig_country = px.bar(country_totals_bar.sort_values('emissions_mtco2', ascending=True),
                         x='emissions_mtco2', y='country', orientation='h', text='value_str',
                         labels={'emissions_mtco2': 'Emissions (Mt CO2e)', 'country': 'Country'},
                         title=f"Top country contributors — {selected_year} (Mt CO2e)")
    fig_country.update_traces(textposition='outside', marker_color='#8c564b')
    fig_country.update_layout(template='plotly_white', height=600, margin=dict(l=160, r=40, t=60, b=40))
    st.plotly_chart(fig_country, use_container_width=True)
    st.download_button('Download CSV', data=df_sel.to_csv(index=False).encode('utf-8'), file_name=f'ghg_by_sector_country_{selected_year}.csv')


def render_sheet_content(active_sheet, scope):
    sheet_label = {
        'overview': 'Overview',
        'ghg_totals': 'GHG Totals by Country',
        'co2': 'Fossil CO2',
        'ch4': 'Methane (CH4)',
        'n2o': 'Nitrous Oxide (N2O)',
        'f_gases': 'F-gases',
        'per_capita': 'Per Capita Emissions',
        'sector': 'Sector Breakdown',
    }

    if active_sheet == 'overview':
        st.subheader('EDGAR overview')
        render_country_totals(scope, 'Overview')
        return

    if active_sheet == 'ghg_totals':
        render_ghg_totals_view(scope)
        return

    if active_sheet == 'per_capita':
        render_per_capita_view(scope)
        return

    if active_sheet == 'sector':
        render_sector_view(scope)
        return

    if active_sheet in GAS_LOOKUP:
        gas_cfg = GAS_LOOKUP[active_sheet]
        gas_df = load_sector_gas_data(gas_cfg['substance'])
        if not gas_df.empty:
            render_gas_tab(active_sheet, gas_cfg['label'], gas_cfg['color'], gas_df)
            return

    st.info(f"{sheet_label.get(active_sheet, 'This sheet')} is currently mapped to the country totals view until the specific EDGAR sheet is loaded.")
    render_country_totals(scope, sheet_label.get(active_sheet, 'Country totals'))


def main():
    st.set_page_config(page_title="Africa Emissions Tracker", layout='wide')

    st.sidebar.title("🌍 EDGAR GHG")
    st.sidebar.caption("2026 Booklet Dashboard")

    sheet_options = {
        "📊 Overview": "overview",
        "🌍 GHG Totals by Country": "ghg_totals",
        "🏭 Fossil CO2": "co2",
        "💨 Methane (CH4)": "ch4",
        "⚗️ Nitrous Oxide (N2O)": "n2o",
        "🧪 F-gases": "f_gases",
        "👤 Per Capita Emissions": "per_capita",
        "🏗️ Sector Breakdown": "sector",
    }
    selected_label = st.sidebar.radio("Navigate", list(sheet_options.keys()))
    active_sheet = sheet_options[selected_label]

    col1, col2 = st.columns([8, 2])
    with col1:
        st.title("Africa Emissions Tracker")
    with col2:
        scope = st.radio('Scope', ['Global', 'Africa'], index=1)

    st.sidebar.markdown("---")
    render_sheet_content(active_sheet, scope)


if __name__ == '__main__':
    main()
