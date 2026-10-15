import pandas as pd
import sys

def main(path='data/GHG_totals_by_country.csv'):
    df = pd.read_csv(path)
    rows = len(df)
    cols = df.columns.tolist()
    years = cols[2:]
    latest = years[-1]

    print(f'rows_count: {rows}')
    print(f'years_range: {years[0]} - {latest}')
    print('\nfirst_10_countries:')
    print(df[['EDGAR Country Code','Country']].head(10).to_string(index=False))

    # show top 15 emitters in latest year
    df_latest = df[['EDGAR Country Code','Country', latest]].copy()
    df_latest[latest] = pd.to_numeric(df_latest[latest], errors='coerce').fillna(0)
    top = df_latest.sort_values(latest, ascending=False).head(15)
    print(f"\nTop 15 emitters in {latest} (by total):")
    print(top.to_string(index=False))

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'data/GHG_totals_by_country.csv'
    main(path)
