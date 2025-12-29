import pandas as pd
import os
from odf.style import Style, TableColumnProperties, TextProperties, TableCellProperties
from odf.table import Table, TableColumn, TableRow, TableCell
from odf.opendocument import load

def exportToOds(filename: str, sheetsData: dict):
    """
    Exports data to an Open Document Spreadsheet (.ods).
    sheetsData: dict where key is Sheet Name and value is a list of items to write.
                 Items can be DataFrames, dicts (key-value pairs), or strings (titles).
    """
    
    if os.path.exists(filename):
        os.remove(filename)

    with pd.ExcelWriter(filename, engine="odf") as writer:
        for sheetName, contentList in sheetsData.items():
            if not contentList:
                pd.DataFrame().to_excel(writer, sheet_name=sheetName)
                continue

            # Accumulate all content into a single grid (list of lists)
            sheetRows = []
            
            def cleanVal(val, decimals=3):
                 if isinstance(val, float):
                     return round(val, decimals)
                 return val

            for item in contentList:
                if isinstance(item, str):
                    # Add title row
                    sheetRows.append([item])
                    # Add spacing
                    sheetRows.append([])

                elif isinstance(item, pd.DataFrame):
                    if not item.empty:
                        # Make positive (except 'Gewinn [€]')
                        item_copy = item.copy()
                        numeric_cols = item_copy.select_dtypes(include=['number']).columns
                        for col in numeric_cols:
                            if col != 'Gewinn [€]':
                                item_copy[col] = item_copy[col].abs()
                        item = item_copy

                        # Add headers
                        cols = list(item.columns)
                        sheetRows.append(cols)
                        
                        # Find USDEUR index
                        usdEurIdx = -1
                        if "USDEUR" in cols:
                             usdEurIdx = cols.index("USDEUR")
                        
                        # Add values
                        for row in item.values.tolist():
                            newRow = []
                            for i, val in enumerate(row):
                                if i == usdEurIdx:
                                    newRow.append(cleanVal(val, 5))
                                else:
                                    newRow.append(cleanVal(val, 3))
                            sheetRows.append(newRow)
                    else:
                        sheetRows.append(["No Data"])
                    
                    # Add spacing
                    sheetRows.append([])
                    sheetRows.append([]) # Add an extra line for better separation

                elif isinstance(item, dict):
                    # Add items
                    for k, v in item.items():
                        sheetRows.append([k, cleanVal(v, 3)])
                    # Add spacing
                    sheetRows.append([])

                elif isinstance(item, list):
                    # Add a custom row
                    cleanRow = [cleanVal(x, 3) for x in item]
                    sheetRows.append(cleanRow)
                    # Add spacing
                    sheetRows.append([])

                elif isinstance(item, (int, float)):
                    sheetRows.append([cleanVal(item, 3)])
                    sheetRows.append([])

            # Special logic for Steuer Übersicht
            if sheetName == "Steuer Übersicht":
                # User requested moves: B20 -> B4, B38 -> B5, B29 -> B3
                # Indices (0-based): 19 -> 3, 37 -> 4, 28 -> 2
                def get_b_val(row_idx):
                    if len(sheetRows) > row_idx and len(sheetRows[row_idx]) > 1:
                        return sheetRows[row_idx][1]
                    return None

                v20 = get_b_val(19)
                v38 = get_b_val(37)
                v29 = get_b_val(28)

                if v29 is not None and len(sheetRows) > 2: sheetRows[2][1] = v29
                if v20 is not None and len(sheetRows) > 3: sheetRows[3][1] = v20
                if v38 is not None and len(sheetRows) > 4: sheetRows[4][1] = v38

                # Delete from row 14 (Index 13)
                if len(sheetRows) > 13:
                    sheetRows = sheetRows[:13]

                # Round Column B to 2 decimals
                for row in sheetRows:
                    if len(row) > 1:
                        try:
                            # Try converting to float and round
                            val = pd.to_numeric(row[1], errors='coerce')
                            if pd.notnull(val):
                                row[1] = round(float(val), 2)
                        except:
                            pass

            # Create a single DataFrame from the grid
            if sheetRows:
                # We do not want a header for the main dataframe, and we don't know column names roughly
                # So we simply write it without header and index
                # Pad rows? Pandas DataFrame constructor handles list of lists with different lengths
                
                finalDf = pd.DataFrame(sheetRows)
                # Round numeric columns (or cells) to 3 decimal places
                # Done during accumulation now to handle column-specific rounding
                finalDf.to_excel(writer, sheet_name=sheetName, index=False, header=False)
            else:
                 pd.DataFrame().to_excel(writer, sheet_name=sheetName)

    # Apply formatting after pandas has closed the file
    styleOds(filename, sheetsData)

def styleOds(filename, sheetsData):
    try:
        doc = load(filename)
        
        # 1. Define Styles
        # Column A (4.5cm)
        styleColA = Style(name="coA", family="table-column")
        styleColA.addElement(TableColumnProperties(columnwidth="4.5cm"))
        doc.automaticstyles.addElement(styleColA)

        # Column Symbol (1.6cm)
        styleColSym = Style(name="coSym", family="table-column")
        styleColSym.addElement(TableColumnProperties(columnwidth="1.6cm"))
        doc.automaticstyles.addElement(styleColSym)

        # Column Menge (1.94cm)
        styleColMen = Style(name="coMen", family="table-column")
        styleColMen.addElement(TableColumnProperties(columnwidth="1.94cm"))
        doc.automaticstyles.addElement(styleColMen)

        # Column Optionen (4.5cm)
        styleColOpt = Style(name="coOpt", family="table-column")
        styleColOpt.addElement(TableColumnProperties(columnwidth="4.5cm"))
        doc.automaticstyles.addElement(styleColOpt)

        # Wrap Style
        wrapStyleName = "wrap1"
        wrapStyle = Style(name=wrapStyleName, family="table-cell")
        wrapStyle.addElement(TableCellProperties(wrapoption="wrap"))
        doc.automaticstyles.addElement(wrapStyle)

        # Header Style (Bold, Light Gray, Wrap)
        headerStyleName = "header1"
        headerStyle = Style(name=headerStyleName, family="table-cell")
        headerStyle.addElement(TextProperties(fontweight="bold"))
        headerStyle.addElement(TableCellProperties(backgroundcolor="#e6e6e6", wrapoption="wrap"))
        doc.automaticstyles.addElement(headerStyle)

        # 2. Iterate Sheets to apply styles
        tables = {t.getAttribute("name"): t for t in doc.spreadsheet.getElementsByType(Table)}

        for sheetName, contentList in sheetsData.items():
            if sheetName not in tables:
                continue
            
            table = tables[sheetName]
            
            # --- Column Width Logic ---
            # Identify which columns need which style
            colStyles = {0: "coA"} # Default Col A width
            
            # Scan content for headers to find "Symbol" and "Menge"
            for item in contentList:
                if isinstance(item, pd.DataFrame):
                    cols = list(item.columns)
                    # Use simple string matching or exact match? Exact match based on user request.
                    for i, colName in enumerate(cols):
                        if colName == "Symbol":
                            colStyles[i] = "coSym"
                        elif colName == "Menge":
                            colStyles[i] = "coMen"
                        elif colName == "Optionen":
                            colStyles[i] = "coOpt"
            
            # Apply styles to columns
            # We need to ensure explicit TableColumn elements exist for the max index we need to style
            if colStyles:
                maxIdx = max(colStyles.keys())
                
                # Get existing columns
                existingCols = table.getElementsByType(TableColumn)
                currentCount = len(existingCols)
                
                # We assume no complex 'number-columns-repeated' logic from pandas for now
                # If pandas generated no columns, we create them
                # Structure: <Table> <TableColumn>... <TableColumn> ... <TableRow> ...
                
                # Insert missing columns
                params = []
                for i in range(maxIdx + 1):
                    # Check if we have a style for this column
                    sName = colStyles.get(i, None)
                    
                    if i < currentCount:
                        # Update existing
                        if sName:
                            existingCols[i].setAttribute("stylename", sName)
                    else:
                        # Create new
                        tc = TableColumn()
                        if sName:
                            tc.setAttribute("stylename", sName)
                        
                        # Where to insert?
                        # If existingCols is not empty, after the last one.
                        # If empty, at start of table.
                        if existingCols:
                             # Append after the last known column (which updates as we add)
                             # Easier: insert before first row?
                             # Or just append to table if no rows?
                             # Correct way: use insertBefore with reference node.
                             # If we have current columns, ref is next sibling of last col.
                             pass
                        
                        # Simplification: Collect all column nodes to be ensured/created
                        # Managing DOM 'insertBefore' directly is tedious with mixed content.
                        # Let's find the First Row to use as reference for insertion
                        rows = table.getElementsByType(TableRow)
                        refNode = rows[0] if rows else None
                        table.insertBefore(tc, refNode)
                        
                        # Note: logical order of columns matters. The above insertBefore puts it before the first row,
                        # effectively appending to the list of columns (since existing columns are also before rows).
                        # Wait, if I have [Col0, Col1] and I insert Col2 before Row0, it becomes [Col0, Col1, Col2, Row0]. Correct.

                # Re-fetch/Re-verify order?
                # We relied on 'appending' via inserting before the first row. 
                # This assumes existingCols come before rows.
                pass

            # --- Cell Wrap Logic (Global first) ---
            rows = table.getElementsByType(TableRow)
            for row in rows:
                for cell in row.getElementsByType(TableCell):
                    cell.setAttribute("stylename", wrapStyleName)

            # --- Header Logic ---
            currentRowIndex = 0
            
            for item in contentList:
                if isinstance(item, str):
                    currentRowIndex += 2
                elif isinstance(item, pd.DataFrame):
                    if not item.empty:
                        # Header
                        if currentRowIndex < len(rows):
                            row = rows[currentRowIndex]
                            for cell in row.getElementsByType(TableCell):
                                cell.setAttribute("stylename", headerStyleName)
                        currentRowIndex += 1
                        # Values
                        currentRowIndex += len(item)
                    else:
                        currentRowIndex += 1
                    currentRowIndex += 2
                elif isinstance(item, dict):
                    currentRowIndex += len(item)
                    currentRowIndex += 1
                elif isinstance(item, list):
                    currentRowIndex += 2
                elif isinstance(item, (int, float)):
                    currentRowIndex += 2

        doc.save(filename)
    except Exception as e:
        print(f"Warning: Could not apply styles: {e}")

