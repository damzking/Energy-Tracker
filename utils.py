import pandas as pd


def load_emissions(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # ensure types
    df['emissions_mtco2'] = pd.to_numeric(df['emissions_mtco2'], errors='coerce').fillna(0)
    return df


def top_categories_by_country(df: pd.DataFrame, country: str = None):
    if country and country != 'All':
        sub = df[df['country'] == country]
    else:
        sub = df
    agg = sub.groupby('category', as_index=False)['emissions_mtco2'].sum()
    agg = agg.sort_values('emissions_mtco2', ascending=False)
    return agg


def country_totals(df: pd.DataFrame):
    return df.groupby('country', as_index=False)['emissions_mtco2'].sum().sort_values('emissions_mtco2', ascending=False)
