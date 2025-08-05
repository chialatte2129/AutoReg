import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
from dotenv import load_dotenv
import datetime
import csv
import re
load_dotenv()

CAPTCHA_API_KEY = os.getenv('CAPTCHA_API_KEY')
BIRTHDAY = os.getenv('BIRTHDAY')
IDCARD = os.getenv('IDCARD')
LINE_TOKEN = os.getenv("LINE_TOKEN")

def solve_captcha(image_path):
    # 上傳圖片給2captcha
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'key': CAPTCHA_API_KEY}
        r = requests.post('http://2captcha.com/in.php', files=files, params=data)
    if 'OK|' not in r.text:
        raise Exception('2Captcha上傳失敗:' + r.text)
    captcha_id = r.text.split('|')[1]
    # 等待並取得答案
    for i in range(20):
        res = requests.get(f"http://2captcha.com/res.php?key={CAPTCHA_API_KEY}&action=get&id={captcha_id}")
        if 'OK|' in res.text:
            return res.text.split('|')[1]
        time.sleep(5)
    raise Exception('2Captcha等候超時')

def book_registration(date: str,section: str, doctor: str):
    roc_date = to_roc_date_string(date)
    driver = webdriver.Chrome()
    driver.get('https://webreg.timing-pharmacy.com/MobileReg.aspx?code=3805340179&FormType=1')
    # ...填入基本資料的自動化...
    # 選擇診別(初診/複診)
    driver.find_element(By.ID, 'ImageButton1').click()  # 根據實際ID或選項

    #等待頁面跳轉
    time.sleep(2)  # 等待頁面加載

    # 輸入身分證
    driver.find_element(By.ID, 'txtIdentityCard').send_keys(IDCARD)

    # 輸入生日
    driver.find_element(By.ID, 'txtBirthDay').send_keys(BIRTHDAY)

    # 下載驗證碼圖片
    captcha_img = driver.find_element(By.ID, 'captcha')  # 根據實際ID
    captcha_img.screenshot('captcha.png')

    # 解驗證碼
    captcha_text = solve_captcha('captcha.png')
    print('驗證碼答案:', captcha_text)

    # 輸入驗證碼
    driver.find_element(By.ID, 'TextBox5').send_keys(captcha_text)  # 根據實際ID

    
    # 提交表單
    driver.find_element(By.ID, 'ImageButton3').click()

    time.sleep(2)  # 建議加一點延遲，等畫面跳轉/結果出現

    # 選擇醫師
    # 從 table id=GridList 中選擇日期為設定日期 民國年/月/日的行
    # 根據section的值 "早上":2, "下午":3, "晚上":4
    # 尋找第一個與 doctor 名稱匹配的醫師，醫師物件是一個<a>元素 value是doctor名稱
    section_map = {'早上': 2, '下午': 3, '晚上': 4}
    section_index = section_map.get(section, 3)  # 預設為早上

    # 找到日期欄位對應的那一列
    rows = driver.find_elements(By.XPATH, '//table[@id="GridList"]/tbody/tr')
    target_row = None
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        if not cols:
            continue
        if cols[0].text.strip() == roc_date:
            target_row = cols
            break

    if not target_row:
        print(f"未找到日期 {roc_date} 的資料列")
        driver.quit()
        return

    # 在指定時段欄位找醫師
    doctor_found = False
    try:
        cell = target_row[section_index]
        print("單元格", cell)
        a_tags = cell.find_elements(By.TAG_NAME, 'a')
        for a in a_tags:
            if a.text.strip() == doctor:  # doctor 例如 '3診-洪頌宏'
                a.click()
                doctor_found = True
                break
    except Exception:
        pass

    time.sleep(5)
    
    if not doctor_found:
        print(f"未找到醫師 {doctor} 在 {roc_date} 的 {section} 時段")
        driver.quit()
        return
    print(f"找到醫師 {doctor} 在 {roc_date} 的 {section} 時段，進行預約中...")

    panel = driver.find_element(By.ID, 'Panel5')
    rows = panel.find_elements(By.XPATH, './/table//tr')

    

    message = "預約成功!! \n\n"
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        if len(cols) >= 2:
            key = clean_text(cols[0].text)
            value = clean_text(cols[1].text)
            message+=f"{key}：{value}\n"
    
    # 確定預約掛號
    driver.find_element(By.ID, 'ImageButton4').click()

    send_line_message(message)

    time.sleep(6)  # 建議加一點延遲，等畫面跳轉/結果出現
    # 完成可加line/email通知
    print('已自動掛號完成')
    driver.quit()

def clean_text(text):
    return re.sub(r'[\r\n\t\u3000]+', '', text).strip()

def send_line_message(message):
    BROADCAST_URL = 'https://api.line.me/v2/bot/message/broadcast'
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    response = requests.post(BROADCAST_URL, headers=headers, json=payload)
    if response.status_code == 200:
        print("✅ 群發成功")
    else:
        print(f"❌ 發送失敗：{response.status_code} - {response.text}")
        
def to_roc_date_string(d: datetime.date) -> str:
    roc_year = d.year - 1911
    return f"{roc_year}/{d.month:02d}/{d.day:02d}"

def read_appointments(csv_file):
    appointments = []
    with open(csv_file, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(row)
            # 預設 doctor 欄位必填
            date = datetime.datetime.strptime(row['date'], '%Y/%m/%d').date()
            section = row['section']
            doctor = row['doctor']
            appointments.append({'date': date,'section':section, 'doctor': doctor})
    return appointments

def check_and_book(csv_file):
    today = datetime.date.today()
    target_date = today + datetime.timedelta(days=30)
    appointments = read_appointments(csv_file)

    # 找出所有今天需要掛號的醫師（可能有多筆）
    targets = [a for a in appointments if a['date'] == target_date]

    if targets:
        for item in targets:
            doctor = item['doctor']
            section = item['section']
            print(f"今天要幫 {doctor} 預約 {target_date}，啟動自動掛號流程...")
            # TODO: 呼叫你的自動掛號主流程並指定醫師
            book_registration(target_date, section, doctor)
    else:
        print(f"今天沒有需要掛號的目標日（{target_date}）")


if __name__ == "__main__":
    check_and_book('appointments.csv')
