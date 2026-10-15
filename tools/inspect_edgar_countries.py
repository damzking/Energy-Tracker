import pandas as pd
xl='EDGAR_2026_GHG_booklet_2026.xlsx'
ed=pd.read_excel(xl, sheet_name='GHG_by_sector_and_country', engine='openpyxl')
year_cols = [c for c in ed.columns if (isinstance(c,int) or (isinstance(c,str) and c.isdigit()))]
id_cols = [c for c in ed.columns if c not in year_cols]
df_long = ed.melt(id_vars=id_cols, value_vars=year_cols, var_name='year', value_name='emissions_mtco2')
arr = df_long['Country'].unique()
print('len unique', len(arr))
print('types sample:', [type(x) for x in arr[:30]])
print('values sample:', arr[:30])
print('any null?', df_long['Country'].isnull().any())
print('first 10 rows Country types:', [type(x) for x in df_long['Country'].head(20)])