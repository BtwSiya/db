import json
import re

def guess_data_type(text, index):
    if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', text):
        return "email"
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}', text):
        return "date_extra"
    if re.match(r'^(http|https)://', text):
        return "link"
    if re.match(r'^[a-zA-Z0-9_.+-]+$', text) and len(text) > 6:
        return f"possible_password_or_username_{index}"
    return f"extra_text_{index}"

def convert_all(input_file, output_file):
    base_keys = ["phone", "fb_id", "first_name", "last_name", "gender", "current_city", "hometown", "relationship", "work", "timestamp"]
    
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as fin, open(output_file, 'w', encoding='utf-8') as fout:
        fout.write('[\n')
        
        is_first = True
        for line in fin:
            parts = line.strip().split(':')
            if len(parts) < 2:
                continue
                
            record = {}
            for i, val in enumerate(parts):
                if not val:
                    continue
                    
                if i < len(base_keys):
                    record[base_keys[i]] = val
                else:
                    key_name = guess_data_type(val, i)
                    record[key_name] = val
            
            if not is_first:
                fout.write(',\n')
            else:
                is_first = False
                
            fout.write(json.dumps(record, ensure_ascii=False))
            
        fout.write('\n]')

convert_all('db.txt', 'db.json')

