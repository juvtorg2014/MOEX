import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

headers = {
    "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36",
    "Accept" : "text/plain, */*; q=0.01",
    "Content-Type" : "application/x-www-form-urlencoded",
    "X-Requested-With" : "XMLHttpRequest"}
URL = 'https://www.moex.com/ru/contract.aspx?code='


def download(url):
    url_tiker = URL + url
    driver = webdriver.Firefox()
    driver.get(url_tiker)
    if driver:
        text = driver.page_source
    else:
        print(f" Нет ответа от сервера {url_tiker}")
        exit()
    driver.maximize_window()
    time.sleep(5)
    content = driver.find_element(By.CLASS_NAME, 'disclaimer__buttons')
    button = driver.find_elements('div', class_ = "btn2 btn2-primary")
    button.click()
    print(text)
    driver.close()
if __name__ == '__main__':
    download('Si-6.23')

