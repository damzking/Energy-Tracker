import sys
import pandas as pd

def export(path, sheet, out):
    df = pd.read_excel(path, sheet_name=sheet)
    df.to_csv(out, index=False)
    print(df.head().to_csv(index=False))

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('usage: python export_sheet.py workbook.xlsx sheet_name out.csv')
        sys.exit(1)
    export(sys.argv[1], sys.argv[2], sys.argv[3])
