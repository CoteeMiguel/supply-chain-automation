import time
from xml.dom.minidom import Element
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import os
from datetime import datetime, date, timedelta
import pandas as pd
from datetime import datetime,timedelta
import workdays
import win32com.client as win32
from dotenv import load_dotenv
load_dotenv()

class ControlFreak:
    def __init__(self):
        #parameters
        self.dayspan = 100
        self.hoydia = datetime.today()

        #paths
        self.driver = os.getenv('PATH_DRIVER')
        self.newdir = os.getenv('PATH_NEWDIR')
        self.znetcoreport = os.getenv('PATH_ZNETCO')
        self.statusagregado = os.getenv('PATH_STATUS')
        self.bbdd = os.getenv('PATH_BBDD')
        self.outputreport = os.getenv('PATH_OUTPUT')

        #urls
        self.s4url = os.getenv('URL_S4')

        #emails
        self.lspemail = os.getenv('EMAIL_LSP')
        self.colleagues = os.getenv('EMAIL_HP')

    def s4reportextraction(self):

        diahoy = "%02d" %self.hoydia.day
        meshoy = "%02d" %self.hoydia.month
        anohoy = "%04d" %self.hoydia.year
        dianterior = self.hoydia - timedelta(days=self.dayspan)
        fechahasta = meshoy + "/" + diahoy + "/" + anohoy
        diaantes = "%02d" %dianterior.day
        mesantes = "%02d" %dianterior.month
        anoantes = "%04d" %dianterior.year
        fechadesde = mesantes + "/" + diaantes + "/" + anoantes

        driver = webdriver.Chrome(self.driver)
        driver.get(self.s4url)
        time.sleep(60)
        driver.find_element_by_xpath("//*[@id='__tile13']").click()
        time.sleep(15)
        driver.switch_to.window(driver.window_handles[1])
        driver.switch_to.frame(driver.find_element_by_xpath('//*[@id="application-Shell-startGUI-iframe"]'))
        driver.find_element_by_xpath('//*[@id="M0:46:::1:34"]').send_keys('{}'.format(fechadesde))
        driver.find_element_by_xpath('//*[@id="M0:46:::1:59"]').send_keys('{}'.format(fechahasta))
        driver.find_element_by_xpath('//*[@id="M0:46:::2:34"]').send_keys('CL11')
        driver.find_element_by_xpath('//*[@id="M0:46:::3:34"]').send_keys('*')
        driver.find_element_by_xpath('//*[@id="M0:50::btn[8]"]').click()

        time.sleep(25)
        
        driver.find_element_by_xpath('/html').send_keys(Keys.SHIFT,Keys.F9)
        time.sleep(20)
        driver.find_element_by_xpath('//*[@id="UpDownDialogChoose"]').click()

        time.sleep(10)
        os.chdir(self.newdir)
        filename = sorted(os.listdir(os.getcwd()),key=os.path.getctime)[-1]
        filename = os.path.abspath(filename)
        os.remove(self.znetcoreport)
        os.rename(filename,self.znetcoreport)

    def instructionreport(self):
        znetco = pd.read_excel(self.znetcoreport)
        znetco = znetco.loc[(znetco.Delivery.notnull())&((znetco['Sales Document Type']=='ZOR1')|(znetco['Sales Document Type']=='ZFD1'))]
        znetco.Delivery = znetco.Delivery.astype(str)
        znetco.Delivery = znetco.Delivery.str[:-2]
        statustms = pd.read_excel(self.statusagregado,parse_dates=['FECHA ENTREGADO','FECHA DESPACHO'],dayfirst=True)
        znetcolocales = znetco[znetco.Plant!='CL01']
        peles = pd.read_excel(self.bbdd)

        statustms2 = statustms[(statustms['NRO. PEDIDO'].str.startswith('80'))]
        statustms2.drop(statustms2[(statustms2['ESTADO']=='ENTREGADO')&(statustms2['FECHA ENTREGADO'].isnull())].index,inplace=True)
        statustms2.drop_duplicates(['NRO. PEDIDO'],keep='last',inplace=True)
        statustms2 = statustms2[['NRO. PEDIDO','ESTADO','STATUS DE INCIDENTE','OBSERVACION DEL INCIDENTE','FECHA ENTREGADO','FECHA DESPACHO','TIPO VIAJE']]
        dlvlocalmat = znetcolocales[['Delivery','Plant','Status','Customer Reference','Sold To Name','Del.Created On','Actual Quant Delvrd','Net Value','Material','Ship To Name']]
        dlvlocalmat['agingdlv'] = dlvlocalmat.apply(lambda row: self.agingcalculator(row['Del.Created On']),axis=1)
        dlvlocalmat = dlvlocalmat.merge(peles,how='left',left_on='Material',right_on='PN')
        dlvlocalmat = dlvlocalmat.merge(statustms2,how='left',left_on='Delivery',right_on='NRO. PEDIDO')
        dlvlocalmat = dlvlocalmat[['Delivery','Plant','Status','Customer Reference','Sold To Name','Del.Created On','Actual Quant Delvrd','Net Value','Material','agingdlv','PL','Ship To Name','NRO. PEDIDO','ESTADO','STATUS DE INCIDENTE','OBSERVACION DEL INCIDENTE','FECHA ENTREGADO','FECHA DESPACHO','TIPO VIAJE']]
        dlvlocalmat['FECHA DESPACHO'] = dlvlocalmat['FECHA DESPACHO'].astype('datetime64[h]')
        #dlvlocalmat['FECHA ENTREGADO'] = dlvlocalmat['FECHA ENTREGADO'].astype('datetime64[h]')
        #dlvlocalmat['ESTADO'].fillna(0)

        dlvlocalmat['AlertaDHL'] = dlvlocalmat.apply(self.condiciones,axis=1)

        return dlvlocalmat
        
    def agingcalculator(fechaGeneracion):
        return workdays.networkdays(fechaGeneracion,datetime.today())-1
    
    def condiciones(self,zao):
        if (zao['ESTADO'] == 'ENTREGADO' and zao['Status'] == 'INVOICED') or (zao['ESTADO'] == 'ENTREGADO' and zao['Status'] == 'PGI'):
            return 'ok'
        elif (zao['ESTADO'] == 'CANCELADO' and zao['Status']=='INVOICED'):
            return 'ok'
        elif (zao['ESTADO'] == 'SIN STOCK'):
            return 'ok'
        elif (zao['ESTADO'] == 'MERCADERIA RECIBIDA' and zao['Status'] == 'PGI'):
            return 'ok'
        elif (zao['ESTADO'] == 'EN VIAJE' and zao['Status'] == 'INVOICED') or (zao['ESTADO'] == 'EN VIAJE' and zao['Status'] == 'PGI'):
            if (zao['TIPO VIAJE'] == 'ENTREGA LTL REGIONES' and (self.hoydia-zao['FECHA DESPACHO']).days<=3) or ((self.hoydia-zao['FECHA DESPACHO']).days<=1):
                return 'ok'
            else:
                return 'not ok'
        elif (zao['ESTADO'] == 'ASIGNADO' and zao['Status'] == 'CREATED') or (zao['ESTADO'] == 'ASIGNADO' and zao['Status'] == 'PACKING') or (zao['ESTADO'] == 'ASIGNADO' and zao['Status'] == 'PGI') or (zao['ESTADO'] == 'ASIGNADO' and zao['Status'] == 'INVOICED'):
            if (zao['FECHA DESPACHO']- self.hoydia).days>=-1:
                return 'ok'
            else:
                return 'not ok'
        elif (zao['ESTADO'] == 'PENDIENTE'):
            if (zao['Plant'] == 'CL20' and zao['agingdlv']>=7 and zao['Status']=='CREATED' and str(zao['STATUS DE INCIDENTE']).__contains__('HP')): #no eliminar los que tienen cita solicitada
                return 'Eliminar dlv'
            elif (pd.isna(zao['STATUS DE INCIDENTE'])):
                return 'asignar incidente'
            elif (str(zao['STATUS DE INCIDENTE']).__contains__('TURNO') and zao['agingdlv']>=3):
                return 'ayuda csr'
            else:
                return 'check'
        elif (zao['ESTADO'] == 'NO ENTREGADO' and zao['Status'] == 'INVOICED'):
            return 'ok'
        elif (pd.isna(zao.ESTADO) and zao.agingdlv == 0):
            return 'ok'
        else:
            return 'not ok'
        
    def outputreport(self,dlvlocalmat):
        dlvlocalmat.to_excel(self.outputreport,index=False)
        print("Okidoki")        

    def reportdeliver(self):
        source = self.znetcoreport
        source2 = self.outputreport

        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.To = self.lspemail
        mail.Subject = 'Revisar delivery'
        mail.Body = 'Hola Seba te adjunto el archivo znetco 100 días'
        mail.Attachments.Add(source)
        #mail.HTMLBody = chao #this field is optional

        # To attach a file to the email (optional):
        #attachment  = "Path to the attachment"
        #mail.Attachments.Add(attachment)
        mail.Send()

        mail = outlook.CreateItem(0)
        mail.To = self.colleagues
        mail.Subject = 'Cote Status'
        mail.Body = 'Hola Les adjunto el reporte que lleva mi bello nombre'
        mail.Attachments.Add(source2)
        #mail.HTMLBody = chao #this field is optional

        # To attach a file to the email (optional):
        #attachment  = "Path to the attachment"
        #mail.Attachments.Add(attachment)
        mail.Send()    
        
if __name__ == '__main__':
    app = ControlFreak()
    app.s4reportextraction()
    result = app.instructionreport()
    app.outputreport(result)
    app.reportdeliver()
