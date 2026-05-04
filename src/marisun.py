import requests as r
import pandas as pd
from datetime import date, timedelta
import os
from dotenv import load_dotenv
load_dotenv()

class MarisunETL:
    def __init__(self):
        #credenciales
        self.user = os.getenv('TMS_USER')
        self.password = os.getenv('TMS_PASSWORD')

        #rutas
        self.dayspan = 100
        self.tturl = os.getenv('TTURL_login')
        self.ttreport = os.getenv('TTURL_filter')
        self.htmlreport = os.getenv('PATH_HTMLREPORT')
        self.statusagregado = os.getenv('PATH_STATUS')
        self.outputreport = os.getenv('PATH_OUTPUT')
        self.request_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36"
}

    def reportextraction(self):

        hoydia = date.today()
        diadehoy = "%02d" %hoydia.day
        mesdehoy = "%02d" %hoydia.month
        anodehoy = "%02d" %hoydia.year
        fechainicio = hoydia - timedelta(days= self.dayspan)
        diaantes = "%02d" %fechainicio.day
        mesantes = "%02d" %fechainicio.month
        anoantes = "%02d" %fechainicio.year

        payload = { "envio": "1", "from": "", "username": self.user, "password": self.password }

        with r.Session() as s:
            s.headers.update(self.request_headers)
            print("conectando ...")
            get_1 = s.get(self.tturl)
            post_1 = s.post(self.tturl, data=payload)
            #hasta aca es el login
            print("solicitando reporte")
            filtro = {
                "dd_desde": diaantes,
                "mm_desde": mesantes,
                "aaaa_desde": anoantes,
                "dd_hasta": diadehoy,
                "mm_hasta": mesdehoy,
                "aaaa_hasta": anodehoy,
            }
            page = s.get(self.ttreport.format(**filtro))

            nombre_archivo=self.htmlreport
            if page.status_code == 200:
                print("escribiendo reporte a {}".format(nombre_archivo))
                with open(nombre_archivo, "w+") as report:
                    report.write(page.text)
                print("done!")
            else:
                print("Error en conexión!")

    def reportgeneration(self):
        #load data
        status = pd.read_excel(self.statusagregado)
        tms = pd.read_html(self.htmlreport)[0]
        tms = tms[1:]
        titulos = list(tms.iloc[0])
        tms.columns = titulos
        tms.drop([1],inplace=True)

        #generate new report
        tms = tms.merge(status[["ESTADO","Status agregado"]],how="left", on=["ESTADO"])
        tms.loc[(tms["ESTADO"]=="PENDIENTE") & (tms["STATUS DE INCIDENTE"].isnull().values.any()),"Status agregado"] = "In Process"
        tms.loc[(tms["ESTADO"]=="PENDIENTE") & (tms["STATUS DE INCIDENTE"].str.contains("ESPERA CONFIRMACION DE TURNO")),"Status agregado"] = "Waiting for Appointment"
        tms.loc[(tms["ESTADO"]=="PENDIENTE") & (tms["STATUS DE INCIDENTE"].str.contains("(HP)")),"Status agregado"] = "Waiting SC instruction"

        return tms

    def reportoutput(self,tms):
        tms.to_excel(self.reportoutput,sheet_name="Chile",index=False)

if __name__ == '__main__':
    app = MarisunETL()
    app.reportextraction()
    output = app.reportgeneration()
    app.reportoutput(output)