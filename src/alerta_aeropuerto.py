import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

class Notifier:
    def __init__(self):
        self.dailyreport = os.getenv('DAILYREP_PATH')
        self.airportarrivals = os.getenv('AIRPORTREP_PATH')
        self.output_path = os.getenv('PATH_OUTPUT')

        self.ListaDespachos = []

    def createlist(self):
        ReporteDiario = pd.read_excel(self.dailyreport)
        RetirosAeropuerto = pd.read_excel(self.airportarrivals)

        ReporteDiario = ReporteDiario.loc[ReporteDiario.Modal=='AIR']
        ReporteDiario = ReporteDiario.loc[ReporteDiario['BU']=='FGI']


        ReporteDiario = ReporteDiario[(ReporteDiario.ATA.notnull()) &
                                      (ReporteDiario['Retiro /Entrega'].isnull()) &
                                      (ReporteDiario.Emisor.str.contains('EXPRESS')==False)]
        
        ReporteDiario['DiasArribado'] = datetime.today()-ReporteDiario['ATA']
        ReporteDiario = ReporteDiario[ReporteDiario.DiasArribado.dt.days>=1]


        ListaBroker = ReporteDiario[['Broker Internal Order','ATA']]

        RetirosAeropuerto = RetirosAeropuerto[['Despacho','Fecha del Retiro']]
        ListaBroker = ListaBroker.loc[ListaBroker['Fecha del Retiro'].isnull()]
        ListaBroker = ListaBroker.merge(RetirosAeropuerto,how='left',left_on='Broker Internal Order',right_on='Despacho')

        self.ListaDespachos = ListaBroker['Broker Internal Order']

    def postlist(self):
        f = open(self.output_path,'w+')

        lista = list(self.ListaDespachos)

        f.write(str(lista))

        f.close()

if __name__ == '__main__':
    app = Notifier()
    app.createlist()
    app.postlist()
