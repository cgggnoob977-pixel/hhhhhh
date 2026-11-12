import pandas as pd
import numpy as np

# Load raw dataset
df_raw = pd.read_csv('student_attendance_dirty_60.csv')
print(f"Total raw records: {len(df_raw)}")

# 1. Clean whitespace
for col in df_raw.select_dtypes(include='object').columns:
    df_raw[col] = df_raw[col].astype(str).str.strip()

# Replace 'nan' with actual NaN
df_raw['สถานะส่งงาน'] = df_raw['สถานะส่งงาน'].replace(['nan', 'None', ''], np.nan)

# 2. Check duplicate: drop duplicate keeping first, but keep evidence
df_dedup = df_raw.drop_duplicates(subset=['รหัสบันทึก'], keep='first').copy()
# Also verify subset=['วันที่', 'รหัสนักเรียน', 'วิชา']
df_dedup2 = df_raw.drop_duplicates(subset=['วันที่', 'รหัสนักเรียน', 'วิชา'], keep='first').copy()
print(f"Dedup by ID count: {len(df_dedup)}, Dedup by Date+Student+Subject count: {len(df_dedup2)}")

df_clean = df_dedup.copy()
print(f"Records after dedup: {len(df_clean)}")

# Let's verify metrics on df_clean (59 records):
# Total unique students:
unique_students = df_clean['รหัสนักเรียน'].nunique()
print(f"1. Unique students: {unique_students}")

# Attendance Rate:
# อัตราเข้าเรียน = (จำนวนครั้งมาเรียน + สาย) ÷ รายการสถานะถูกต้อง × 100
# ตัวหารอัตราเข้าเรียนรวมทั้ง มาเรียน สาย ขาด และลา หลังจัดการข้อมูลซ้ำ
valid_attendance_statuses = ['มาเรียน', 'สาย', 'ขาด', 'ลา']
df_valid_att = df_clean[df_clean['สถานะเข้าเรียน'].isin(valid_attendance_statuses)]
present_late_count = df_valid_att['สถานะเข้าเรียน'].isin(['มาเรียน', 'สาย']).sum()
att_rate = (present_late_count / len(df_valid_att)) * 100
print(f"2. Attendance Rate: {att_rate:.2f}% ({present_late_count} / {len(df_valid_att)})")

# Breakdown of Attendance Status:
status_counts = df_clean['สถานะเข้าเรียน'].value_counts()
print("Attendance status counts:")
print(status_counts)

# Submission Rate (Overall):
# อัตราส่งงานรวม = รายการส่งแล้ว ÷ รายการที่ทราบสถานะส่งงาน × 100
# อัตราส่งงานรวมให้นับขาด/ลาที่ระบุยังไม่ส่งด้วย ตามนิยามงานในคาบ
known_sub = df_clean[df_clean['สถานะส่งงาน'].notna() & df_clean['สถานะส่งงาน'].isin(['ส่งแล้ว', 'ยังไม่ส่ง'])]
submitted_count = (known_sub['สถานะส่งงาน'] == 'ส่งแล้ว').sum()
sub_rate_total = (submitted_count / len(known_sub)) * 100
print(f"3. Overall Submission Rate: {sub_rate_total:.2f}% ({submitted_count} / {len(known_sub)})")

# Submission Rate (Attended only):
# อัตราส่งงานของผู้เข้าเรียน = ส่งแล้วในกลุ่มมาเรียน/สาย ÷ รายการมาเรียน/สายที่ทราบสถานะส่งงาน × 100
attended = df_clean[df_clean['สถานะเข้าเรียน'].isin(['มาเรียน', 'สาย'])]
attended_known_sub = attended[attended['สถานะส่งงาน'].notna() & attended['สถานะส่งงาน'].isin(['ส่งแล้ว', 'ยังไม่ส่ง'])]
attended_submitted = (attended_known_sub['สถานะส่งงาน'] == 'ส่งแล้ว').sum()
sub_rate_attended = (attended_submitted / len(attended_known_sub)) * 100
print(f"4. Attended Submission Rate: {sub_rate_attended:.2f}% ({attended_submitted} / {len(attended_known_sub)})")

# Average Late Minutes:
# นาทีที่สายเฉลี่ย = ผลรวมนาทีที่สายที่ถูกต้อง ÷ จำนวนรายการสายที่นาทีถูกต้อง
# สถานะสายต้องมีนาทีที่สายมากกว่า 0
late_records = df_clean[df_clean['สถานะเข้าเรียน'] == 'สาย']
print(f"Total late records: {len(late_records)}")
print(late_records[['รหัสบันทึก', 'รหัสนักเรียน', 'วิชา', 'นาทีที่สาย']])

# Filter valid late minutes: late_min > 0 and late_min <= hours * 60
valid_late = late_records[(late_records['นาทีที่สาย'] > 0) & (late_records['นาทีที่สาย'] <= late_records['ชั่วโมงเรียน'] * 60)]
print(f"Valid late records: {len(valid_late)}")
print(valid_late[['รหัสบันทึก', 'รหัสนักเรียน', 'วิชา', 'นาทีที่สาย']])
avg_late_minutes = valid_late['นาทีที่สาย'].mean()
print(f"5. Average Late Minutes: {avg_late_minutes:.2f} mins (Sum: {valid_late['นาทีที่สาย'].sum()} / {len(valid_late)})")

print("\n--- ANSWERING QUESTIONS ---")
# Q1: ห้องใดมีอัตราเข้าเรียนสูงกว่า และใช้ข้อมูลกี่รายการ?
for room, group in df_clean.groupby('ห้องเรียน'):
    g_valid = group[group['สถานะเข้าเรียน'].isin(valid_attendance_statuses)]
    g_pres = g_valid['สถานะเข้าเรียน'].isin(['มาเรียน', 'สาย']).sum()
    rate = (g_pres / len(g_valid)) * 100
    print(f"Room {room}: Att Rate = {rate:.2f}% ({g_pres}/{len(g_valid)}) Total records used: {len(g_valid)}")

# Q2: วิชาใดมีอัตราสายสูงกว่า? ใช้จำนวนสายหารรายการสถานะถูกต้องของวิชานั้น
for subj, group in df_clean.groupby('วิชา'):
    g_valid = group[group['สถานะเข้าเรียน'].isin(valid_attendance_statuses)]
    g_late = (g_valid['สถานะเข้าเรียน'] == 'สาย').sum()
    rate = (g_late / len(g_valid)) * 100
    print(f"Subject {subj}: Late Rate = {rate:.2f}% ({g_late}/{len(g_valid)}) Total valid records: {len(g_valid)}")

# Q3: นักเรียนคนใดควรติดตามเรื่องขาดเรียนหรือยังไม่ส่งงาน เพราะอะไร?
print("\nStudent breakdown:")
student_summary = []
for s_id, group in df_clean.groupby('รหัสนักเรียน'):
    room = group['ห้องเรียน'].iloc[0]
    total_classes = len(group)
    absent_cnt = (group['สถานะเข้าเรียน'] == 'ขาด').sum()
    leave_cnt = (group['สถานะเข้าเรียน'] == 'ลา').sum()
    late_cnt = (group['สถานะเข้าเรียน'] == 'สาย').sum()
    present_cnt = (group['สถานะเข้าเรียน'] == 'มาเรียน').sum()
    not_sub_cnt = (group['สถานะส่งงาน'] == 'ยังไม่ส่ง').sum()
    sub_cnt = (group['สถานะส่งงาน'] == 'ส่งแล้ว').sum()
    unknown_sub = group['สถานะส่งงาน'].isna().sum()
    student_summary.append({
        'รหัสนักเรียน': s_id,
        'ห้องเรียน': room,
        'จำนวนคาบ': total_classes,
        'มาเรียน': present_cnt,
        'สาย': late_cnt,
        'ขาด': absent_cnt,
        'ลา': leave_cnt,
        'ยังไม่ส่งงาน': not_sub_cnt,
        'ส่งแล้ว': sub_cnt,
        'ไม่ทราบสถานะส่ง': unknown_sub
    })
stud_df = pd.DataFrame(student_summary)
print(stud_df.to_string())

# Save cleaned CSV as requested
df_clean.to_csv('student_attendance_cleaned.csv', index=False, encoding='utf-8-sig')

