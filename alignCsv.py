import re
#--------------------------------------------------------------------------------------------------------------------
def getEncoding(filename:str) -> str:
    import chardet
    with open(filename, 'rb') as f:  # Öffnen im Binärmodus
        rawdata = f.read()
    result = chardet.detect(rawdata)
    encoding = result['encoding']
    print("Encoding = ", encoding)
    return encoding
#--------------------------------------------------------------------------------------------------------------------
pattern = r',(?=(?:[^"]*"[^"]*")*[^"]*$)'
def count_delimiters(text:str, s:str=","):
    matches = re.findall(pattern, text)
    nrs = len(matches)
    return nrs
#--------------------------------------------------------------------------------------------------------------------
def alignSeparators(file_path, output_file, encoding):
    with open(file_path, 'r', encoding=encoding) as file:
        lines = file.readlines()

    max_separators = max(count_delimiters(line) for line in lines)
    # Jede Zeile auf die maximale Anzahl an Separatoren auffüllen
    aligned_lines = []
    for line in lines:
        current_separators = count_delimiters(line)
        aligned_lines.append(line.strip() + ',' * (max_separators - current_separators) + '\n')
    with open(output_file, 'w', encoding='utf-8') as file:
        file.writelines(aligned_lines)
    return output_file
