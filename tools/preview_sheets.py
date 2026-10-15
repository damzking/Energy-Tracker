import sys
import zipfile
import xml.etree.ElementTree as ET


def preview_with_pandas(path, sheet, n=5):
    import pandas as pd
    df = pd.read_excel(path, sheet_name=sheet)
    print(f"--- Sheet: {sheet} (pandas) ---")
    print(df.head(n).to_csv(index=False))


def parse_shared_strings(z):
    try:
        with z.open('xl/sharedStrings.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            strings = [ ''.join(t.itertext()) for t in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si') ]
            return strings
    except KeyError:
        return []


def preview_with_stdlib(path, sheet_name, n=5):
    with zipfile.ZipFile(path, 'r') as z:
        ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        # map sheet name -> sheet file
        with z.open('xl/workbook.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            sheets = root.findall('ns:sheets/ns:sheet', ns)
            name_to_rid = {s.attrib['name']: s.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id') for s in sheets}

        rels = {}
        try:
            with z.open('xl/_rels/workbook.xml.rels') as f:
                tree = ET.parse(f)
                for rel in tree.getroot():
                    rid = rel.attrib.get('Id')
                    target = rel.attrib.get('Target')
                    rels[rid] = target
        except KeyError:
            pass

        target = rels.get(name_to_rid.get(sheet_name))
        if not target:
            print(f"Could not find worksheet file for sheet {sheet_name}")
            return
        # normalize target
        target_path = 'xl/' + target

        shared = parse_shared_strings(z)

        with z.open(target_path) as f:
            tree = ET.parse(f)
            root = tree.getroot()
            rows = root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
            print(f"--- Sheet: {sheet_name} (stdlib) ---")
            for i, r in enumerate(rows[:n]):
                vals = []
                for c in r.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                    t = c.attrib.get('t')
                    v = c.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                    if v is None:
                        vals.append('')
                    else:
                        text = v.text
                        if t == 's':
                            try:
                                vals.append(shared[int(text)])
                            except Exception:
                                vals.append(text)
                        else:
                            vals.append(text)
                print(','.join(vals))


def main():
    if len(sys.argv) < 2:
        print('usage: python preview_sheets.py path/to/file.xlsx')
        sys.exit(1)
    path = sys.argv[1]

    # list sheets
    with zipfile.ZipFile(path, 'r') as z:
        with z.open('xl/workbook.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            sheets = [s.attrib.get('name') for s in root.findall('ns:sheets/ns:sheet', ns)]

    for s in sheets:
        try:
            preview_with_pandas(path, s)
        except Exception:
            preview_with_stdlib(path, s)


if __name__ == '__main__':
    main()
