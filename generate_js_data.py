import pandas as pd
import json

# Read raw and cleaned datasets
raw_df = pd.read_csv('student_attendance_dirty_60.csv', dtype=str)
cleaned_df = pd.read_csv('student_attendance_cleaned.csv', dtype=str)
issues_df = pd.read_csv('data_issues_log.csv', dtype=str)

raw_records = raw_df.fillna('').to_dict(orient='records')
cleaned_records = cleaned_df.fillna('').to_dict(orient='records')
issues_records = issues_df.fillna('').to_dict(orient='records')

data = {
    'raw_records': raw_records,
    'cleaned_records': cleaned_records,
    'issues_records': issues_records
}

with open('attendance_data.js', 'w', encoding='utf-8') as f:
    f.write('const ATTENDANCE_DATA = ' + json.dumps(data, ensure_ascii=False, indent=2) + ';\n')

print("Generated attendance_data.js successfully!")

