import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
from dotenv import load_dotenv
import datetime
import csv
load_dotenv()

CAPTCHA_API_KEY = os.getenv('CAPTCHA_API_KEY')
BIRTHDAY = os.getenv('BIRTHDAY')
IDCARD = os.getenv('IDCARD')

def solve_captcha(image_path):
    # 上傳圖片給2captcha
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'key': CAPTCHA_API_KEY}
        print(data)
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

def book_registration(date: str, doctor: str):
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
    driver.save_screenshot('result.png')
    # 完成可加line/email通知
    print('已自動掛號完成')
    driver.quit()

def read_appointments(csv_file):
    appointments = []
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 預設 doctor 欄位必填
            date = datetime.datetime.strptime(row['date'], '%Y-%m-%d').date()
            doctor = row['doctor']
            appointments.append({'date': date, 'doctor': doctor})
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
            print(f"今天要幫 {doctor} 預約 {target_date}，啟動自動掛號流程...")
            # TODO: 呼叫你的自動掛號主流程並指定醫師
            book_registration(target_date, doctor)
    else:
        print(f"今天沒有需要掛號的目標日（{target_date}）")


if __name__ == "__main__":
    check_and_book('appointments.csv')
