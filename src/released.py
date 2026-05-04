from selenium import webdriver
import selenium
from selenium.webdriver.common import by
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
from datetime import datetime
from datetime import date, timedelta
import pandas as pd
import pyautogui as pya
import pyperclip as pc
import os
from dotenv import load_dotenv
load_dotenv()

class ReleaseBot:
    def __init__(self):
        self.driver = os.getenv('PATH_DRIVER')
        self.dlvfalabella = os.getenv('PATH_DELIVERIES')
        self.s4url = os.getenv('URL_S4')
        self.outputreport = os.getenv('PATH_OUTPUT')
    
    def released(self):
        df1 = pd.read_excel(self.dlvfalabella)
        df1.drop_duplicates(inplace=True)
        Dlv_stock=list(df1['Deliveries'])
        sales_org=list(df1['Sales org'])
        fechaf=datetime.today().strftime('%m/%d/%y')
        fechaanterior=datetime.today()-timedelta(days=365)
        fechai = fechaanterior.strftime('%m/%d/%y')
        sales_pais=sales_org[1:2]
        driver = webdriver.Chrome(executable_path = self.driver)
        driver.implicitly_wait(30)
        driver.maximize_window()
        driver.get(self.s4url)         
        time.sleep(15)
        driver.switch_to.frame(driver.find_element_by_tag_name("iframe"))
        sales_organization=WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,'//*[@id="M0:46:::1:34"]')))
        sales_organization.send_keys(sales_pais)
        delivery_created_on_initial = driver.find_element(By.ID, 'M0:46:::8:34')
        delivery_created_on_initial.send_keys(fechai)
        delivery_created_on_final = driver.find_element(By.ID, 'M0:46:::8:59')
        delivery_created_on_final.send_keys(fechaf)
        time.sleep(2)
        insert = driver.find_element(By.ID, 'M0:46:::7:78')
        insert.click()
        for d in Dlv_stock[:]:
            packging1 = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,f"//input[contains(@id,'[1,2]_c')]")))
            packging1.send_keys(d)
            adicionar=driver.find_element(By.XPATH, '//*[@id="M1:48::btn[13]"]')
            adicionar.click()
            time.sleep(2)
        aceptar=driver.find_element(By.XPATH, '//*[@id="M1:48::btn[8]"]')
        aceptar.click()
        time.sleep(2)
        aceptar2 = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,'//*[@id="M0:50::btn[8]"]')))
        aceptar2.click()
        time.sleep(5)
        select_all = WebDriverWait(driver, 50).until(EC.visibility_of_element_located((By.ID,'102_toolbar_btn2')))
        select_all.click()
        time.sleep(2)
        driver.find_element_by_xpath('/html/body/table/tbody/tr/td/div/form/table/tbody/tr[2]/td[1]/div/div[1]/div/div/table/tbody[1]/tr[1]/td[2]/div/div/table/tbody/tr/th[5]').click()
        pc.copy("")
        pya.hotkey('ctrl','c')
        time.sleep(2)
        la = pd.read_clipboard()
        print(la)

    def outputreport(self,la):
        la.to_excel(self.outputreport) 

if __name__ == '__main__':
    ReleaseBot.released()
    ReleaseBot.outputreport()