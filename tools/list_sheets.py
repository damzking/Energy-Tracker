import zipfile
import xml.etree.ElementTree as ET
import sys

def list_sheets(xlsx_path):
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        with z.open('xl/workbook.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            # find sheets
            ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            sheets = [s.attrib.get('name') for s in root.findall('ns:sheets/ns:sheet', ns)]
            return sheets

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: python list_sheets.py path/to/file.xlsx')
        sys.exit(1)
    path = sys.argv[1]
    for s in list_sheets(path):
        print(s)
