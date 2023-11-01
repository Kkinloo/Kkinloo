import re
import random
import requests
import subprocess
import pandas as pd
import time
import pyperclip
from playwright.sync_api import sync_playwright

def get_holding(address):
    # Initialize a list to store the results with both address and balance
    all_results = []

    def get_user_holding(address, page_start=None):
        url = f"https://prod-api.kosetto.com/users/{address}/token-holdings"
        if page_start is not None:
            url += f"?pageStart={page_start}"

        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print("kosetto api did not respond")
            return None

    # Initial page start (None for the first page)
    page_start = None

    while True:
        result = get_user_holding(address, page_start)

        if result is None:
            print("Error fetching data. result is none")
            return None

        # Extract addresses and balances from this page and add to all_results
        for entry in result['users']:
            addr = entry['address']
            bal = entry['balance']
            xname = entry['twitterName']

            # Ensure we're not adding the original address to the results
            if addr.lower() != address.lower():
                all_results.append({'address': addr, 'balance': bal, 'twitterName': xname})

        # Check if there is a next page or if we've reached the end
        if 'nextPageStart' in result and result['nextPageStart'] is not None and len(result['users']) > 0:
            page_start = result['nextPageStart']
        else:
            break

    # Convert the results to a DataFrame
    df = pd.DataFrame(all_results)

    return df
def clean_username(username):
    words = re.findall(r'\w+', username)
    vocal_fillers = ['The', 'A', 'An']
    words = [word for word in words if word not in vocal_fillers]
    return words[0] if words else ''

chrome_path='chrome.exe' #最好把chrome加到系统的path里面，否则要填完整的文件地址

sentences_df = pd.read_csv('sentences.csv') #在这个文件里面填入句子
sentences_list = sentences_df.iloc[:, 0].tolist()

#Playwright控制的浏览器
print("启动Chrome，确保路径设置正确")
subprocess.Popen([chrome_path, '--remote-debugging-port=9222', '--user-data-dir=D:\\playwright_chrome'])
time.sleep(1)
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://localhost:9222/')
    page = browser.contexts[0].pages[0]
    page.goto("https://www.friend.tech/")
    print("已经连接上", page.title())
    input("手动完成登录步骤，进入到主页后，输入Y继续...")
    page.click('xpath=//*[@id="top-nav"]/div[2]/div/span[2]',timeout=5000)
    page.click('img[src="/copyIconOutline.svg"]',timeout=5000)
    YOUR_ADDRESS = pyperclip.paste()
    df = get_holding(YOUR_ADDRESS)
    df.drop_duplicates(inplace=True)
    df['cleanedName'] = df['twitterName'].apply(clean_username)
    df.to_csv('my_holding.csv', index=False)

    for _, row in df.iterrows():
        shares_subject = row['address']
        username=row['cleanedName']
        print(f"going to {username}'s room: {shares_subject}...")
        page.goto(f"https://www.friend.tech/rooms/{shares_subject}")
        time.sleep(3)
        random_sentence = random.choice(sentences_list)
        message = f"GM {username}. Remember: {random_sentence}"
        page.fill('textarea#message-input', message)
        page.click('img[src="/sendMessageIcon.svg"]')