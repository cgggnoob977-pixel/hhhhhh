import pandas as pd
import numpy as np

# Load raw dataset
df_raw = pd.read_csv('student_attendance_dirty_60.csv', dtype=str)

print(f"Total raw rows: {len(df_raw)}")

# Check duplicate
duplicates = df_raw[df_raw.duplicated(keep=False)]
print("Duplicate rows:")
print(duplicates)

# Analyze each condition
issues = []

# Keep track of duplicate occurrences
seen_records = set()
seen_keys = set()

for idx, row in df_raw.iterrows():
    rec_id = row['รหัสบันทึก']
    date = row['วันที่']
    student_id = row['รหัสนักเรียน']
    room = row['ห้องเรียน']
    subject = row['วิชา']
    status = row['สถานะเข้าเรียน']
    late_min_str = row['นาทีที่สาย']
    hours_str = row['ชั่วโมงเรียน']
    submission = row['สถานะส่งงาน']
    
    key = (date, student_id, subject)
    
    # 1. Duplicate check
    is_duplicate = False
    if rec_id in seen_records or key in seen_keys:
        is_duplicate = True
        issues.append({
            'รหัสรายการ': rec_id,
            'คอลัมน์': 'รหัสบันทึก / วันที่+รหัสนักเรียน+วิชา',
            'ค่าที่พบ': f"รหัส {rec_id}, {key}",
            'เหตุผล': 'ข้อมูลซ้ำซ้อน ทั้งรหัสบันทึกและวัน-นักเรียน-วิชาเดียวกับรายการก่อนหน้า',
            'วิธีจัดการ': 'ตัดออกจากการคำนวณเพื่อนับเพียง 1 ครั้ง แต่บันทึกหลักฐานการซ้ำไว้',
            'ผลกระทบ': 'กระทบทุกตัวชี้วัดหากไม่ตัด (ตัดออก 1 แถว เหลือ 59 แถวที่ไม่ซ้ำ)'
        })
    else:
        seen_records.add(rec_id)
        seen_keys.add(key)
        
    # Check whitespace
    for col in ['สถานะเข้าเรียน', 'สถานะส่งงาน', 'วิชา', 'ห้องเรียน', 'รหัสนักเรียน', 'รหัสบันทึก']:
        val = row[col]
        if pd.notna(val) and val != val.strip():
            issues.append({
                'รหัสรายการ': rec_id,
                'คอลัมน์': col,
                'ค่าที่พบ': f"'{val}'",
                'เหตุผล': 'มีช่องว่างเกิน (Leading/Trailing Whitespace)',
                'วิธีจัดการ': 'ตัดช่องว่างส่วนเกิน (Trim Whitespace) เพื่อให้ข้อมูลมาตรฐาน',
                'ผลกระทบ': 'ไม่กระทบการตัดทิ้ง แต่ต้อง Trim ก่อนนำไปจับคู่สถานะ'
            })
            
    # Check null / missing
    if pd.isna(submission) or str(submission).strip() == '' or str(submission).lower() == 'nan':
        issues.append({
            'รหัสรายการ': rec_id,
            'คอลัมน์': 'สถานะส่งงาน',
            'ค่าที่พบ': 'ค่าว่าง (Missing / Null)',
            'เหตุผล': 'ไม่มีข้อมูลสถานะส่งงาน ห้ามเดาหรือถือว่ายังไม่ส่งโดยอัตโนมัติตามนิยามโจทย์',
            'วิธีจัดการ': 'แยกเป็นรายการรอตรวจสอบ ไม่นำมารวมในตัวหารของอัตราส่งงาน',
            'ผลกระทบ': 'ไม่ถูกนำไปคำนวณในอัตราส่งงาน (ทั้งรวมและผู้เข้าเรียน) แต่ยังคงนับในอัตราเข้าเรียนได้ตามปกติ'
        })
        
    # Check late minutes
    try:
        late_min = int(late_min_str)
        if late_min < 0:
            issues.append({
                'รหัสรายการ': rec_id,
                'คอลัมน์': 'นาทีที่สาย',
                'ค่าที่พบ': str(late_min),
                'เหตุผล': 'นาทีที่สายติดลบ ขัดกับนิยามที่ระบุว่านาทีที่สายต้องไม่ติดลบ',
                'วิธีจัดการ': 'แยกเป็นรายการรอตรวจสอบนาทีที่สาย ไม่นำไปคำนวณในนาทีที่สายเฉลี่ย',
                'ผลกระทบ': 'ตัดออกจากตัวหารและผลรวมของ "นาทีที่สายเฉลี่ย" แต่สถานะเข้าเรียนยังเป็น "สาย" นับในอัตราเข้าเรียนได้'
            })
        clean_status = str(status).strip()
        if clean_status == 'สาย' and late_min <= 0:
            issues.append({
                'รหัสรายการ': rec_id,
                'คอลัมน์': 'นาทีที่สาย / สถานะเข้าเรียน',
                'ค่าที่พบ': f"สถานะ={clean_status}, นาที={late_min}",
                'เหตุผล': 'สถานะสายต้องมีนาทีที่สายมากกว่า 0 แต่พบเป็น 0',
                'วิธีจัดการ': 'แยกเป็นรายการรอตรวจสอบนาทีที่สาย ไม่นำไปคำนวณในนาทีที่สายเฉลี่ย',
                'ผลกระทบ': 'ตัดออกจากตัวหารและผลรวมของ "นาทีที่สายเฉลี่ย" แต่ยังนับสถานะสายในอัตราเข้าเรียน'
            })
        if clean_status != 'สาย' and late_min != 0:
            issues.append({
                'รหัสรายการ': rec_id,
                'คอลัมน์': 'นาทีที่สาย',
                'ค่าที่พบ': f"สถานะ={clean_status}, นาที={late_min}",
                'เหตุผล': 'สถานะอื่นที่ไม่ใช่สายต้องมีนาทีที่สายเป็น 0',
                'วิธีจัดการ': 'ตรวจสอบและปรับเป็น 0 หรือรอตรวจสอบ',
                'ผลกระทบ': 'ไม่มี'
            })
    except Exception as e:
        issues.append({
            'รหัสรายการ': rec_id,
            'คอลัมน์': 'นาทีที่สาย',
            'ค่าที่พบ': str(late_min_str),
            'เหตุผล': f'แปลงเป็นตัวเลขไม่ได้: {e}',
            'วิธีจัดการ': 'รอตรวจสอบ',
            'ผลกระทบ': 'ตัดออกจากนาทีที่สายเฉลี่ย'
        })

    # Check study hours
    try:
        hours = int(hours_str)
        if hours <= 0 or hours > 8:
            issues.append({
                'รหัสรายการ': rec_id,
                'คอลัมน์': 'ชั่วโมงเรียน',
                'ค่าที่พบ': str(hours),
                'เหตุผล': 'ชั่วโมงเรียนต่อคาบต้องมากกว่า 0 และไม่เกิน 8 ชั่วโมง (พบ 25 ชั่วโมง ผิดเงื่อนไข)',
                'วิธีจัดการ': 'บันทึกเป็นข้อผิดพลาดรอตรวจสอบชั่วโมงเรียน แต่เนื่องจากการคำนวณการเข้าเรียนนับเป็นครั้งต่อคาบ ไม่ใช้ผลรวมชั่วโมง จึงไม่กระทบตัวชี้วัดเข้าเรียนและส่งงาน',
                'ผลกระทบ': 'ไม่กระทบอัตราเข้าเรียนและส่งงาน (เนื่องจากนับต่อครั้ง/คาบ) แต่เป็นข้อผิดพลาดโครงสร้างตารางเรียนที่ต้องส่งให้ครูผู้สอนแก้ไข'
            })
    except Exception as e:
        issues.append({
            'รหัสรายการ': rec_id,
            'คอลัมน์': 'ชั่วโมงเรียน',
            'ค่าที่พบ': str(hours_str),
            'เหตุผล': f'แปลงตัวเลขไม่ได้: {e}',
            'วิธีจัดการ': 'รอตรวจสอบ',
            'ผลกระทบ': 'บันทึกเป็นปัญหา'
        })

issues_df = pd.DataFrame(issues)
print("=== ISSUES FOUND ===")
print(issues_df.to_string())

# Save issues to CSV
issues_df.to_csv('data_issues_log.csv', index=False, encoding='utf-8-sig')

