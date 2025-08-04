import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
from dotenv import load_dotenv
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

def book_registration():
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

if __name__ == "__main__":
    book_registration()
