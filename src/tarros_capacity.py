import pyodbc
import pandas as pd
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

class Calculator:

    def __init__(self):
        self.hoydia = datetime.today()
        self.dmr_path = os.getenv('PATH_DMR')
        self.segmentos_path = os.getenv('PATH_SEGMENTOS')
        self.output_path = os.getenv('PATH_OUTPUT')
        server = os.getenv('DB_SERVER')
        database = os.getenv('DB_DATABASE')
        self.connecta = pyodbc.connect(
    'Driver={SQL Server};'
    'Server={server};'
    'Database={database};'
    'Trusted_Connection=yes;'
)
        self.data = {'container_type':['20\' Standard Dry','40\' High Cube Dry','40\' High Cube Non Operating Reefer','40\' Standard Dry'],'Capacity':[33.2
,76,76,67.7]}
        
    def database_connection(self):
        cursors = self.connecta.cursor()
        query = pd.read_sql_query('SELECT * FROM CBK_MCA.dbo.Master_CBK_MCA',self.connecta)
        return query
    
    def volume(self,query):
        Capacidades = pd.DataFrame(self.data)
        #calcular metros cúbicos por sku
        query['Volume'] = (query['Lenght_of_the_Sale_Unit_Cm'] * query['Width_of_the_Sale_Unit_Cm'] * query['Height_of_the_Sale_Unit_Cm']) /1000000
        dmr = pd.read_excel(self.dmr_path)

        #DF con exclusivamente columnas requeridas
        dmr1 = dmr[['shipment_id','Part Number','Product Description','line_quantity','inco1','product_line','origin_country_code','final_destination_country_code','container_number','container_type','Est. Arrival at Destination Port']]
        #dmr1 = dmr1[(dmr1['shipment_id'].str.startswith('80'))]
        #dmr1 = dmr1[(dmr1['inco1'].str.contains('DAP|DDP|DAT|DDU',na=False))]
        #dmr1 = dmr1[(dmr1['final_destination_country_code'].str.contains('AR|BO|CL|PE|CO|PA|US|UY|PY',na=False))]
        dmr1 = dmr1[(dmr1['container_number'].str.match(r'^[A-Z]{4}')==True)]

        dmr2 = dmr1
        dmr2 = dmr2.merge(query[['Material','Volume']],how='left',left_on='Part Number',right_on='Material')
        dmr2['Total Volume'] = dmr2['Volume'] * dmr2['line_quantity']
        dmr3 =dmr2.groupby(['container_number']).sum().reset_index()

        segmentos = pd.read_excel(self.segmentos_path,sheet_name='Segmento')
        contenedoresSacar = dmr2.loc[dmr2.Volume.isnull()]['container_number'].unique()
        pd.DataFrame(contenedoresSacar)
        dmr1 = dmr1.merge(segmentos[['PL','Business Unit']],left_on='product_line',right_on='PL',how='left')
        cosaSegments = dmr1.groupby('container_number')['Business Unit'].nunique().reset_index()
        dmr1 = dmr1.merge(cosaSegments,left_on='container_number',right_on='container_number',how='left')
        dmr1['BU'] = np.where(dmr1['Business Unit_y']>1,'Mixto',dmr1['Business Unit_x'])

        datas = dmr1.drop_duplicates(subset='container_number',keep='first')

        #Obtener contenedores que tienen alguna linea sin volumen
        contenedoresOK = dmr2.loc[~dmr2['container_number'].isin(contenedoresSacar)]
        contenedoresOK = contenedoresOK.groupby(['container_number']).sum().reset_index()
        contenedoresOK = contenedoresOK.merge(datas,left_on='container_number',right_on='container_number',how='left')
        contenedoresOK = contenedoresOK.merge(Capacidades,left_on='container_type',right_on='container_type')
        contenedoresOK['Used Capacity'] = contenedoresOK['Total Volume'] / contenedoresOK['Capacity']
        contenedoresOK = contenedoresOK[['container_number','line_quantity_x','Total Volume','origin_country_code','final_destination_country_code','container_type','Est. Arrival at Destination Port','BU','Capacity','Used Capacity']]

        contenedoresOK['Alertar'] = np.where(((contenedoresOK['Est. Arrival at Destination Port']>=self.hoydia)&(contenedoresOK['Used Capacity']<0.6)),'Alertar','No Alertar')

        sobreutilizados = contenedoresOK.loc[contenedoresOK['Used Capacity'] >=1]
        contenedoresnotOK = dmr2.loc[dmr2['container_number'].isin(contenedoresSacar)]
        listaPNSVol = contenedoresnotOK
        contenedoresOK = contenedoresOK.loc[(contenedoresOK['Used Capacity'] <1) & (contenedoresOK['Used Capacity'] > 0)]

        promedioPL = query.groupby('PL').mean()['Volume'].reset_index()
        promedioPL.PL = promedioPL.PL.str.strip()
        contenedoresnotOK = contenedoresnotOK.merge(promedioPL,left_on='product_line',right_on='PL',how='left')

        contenedoresOK['Semaforo'] = "Calculo correcto"
        sobreutilizados['Semaforo'] = "Sobreutilizado"
        totalcontenedores = contenedoresOK.append(sobreutilizados)

        contenedoresnotOK['EV'] = np.where(contenedoresnotOK['Volume_x'].isnull(),contenedoresnotOK['Volume_y'],contenedoresnotOK['Volume_x'])
        contenedoresnotOK['TEV'] = contenedoresnotOK['EV'] * contenedoresnotOK['line_quantity']
        contenedoresnotOK = contenedoresnotOK.groupby(['container_number']).sum().reset_index()
        contenedoresnotOK = contenedoresnotOK.merge(datas,left_on='container_number',right_on='container_number',how='left')
        contenedoresnotOK = contenedoresnotOK.merge(Capacidades,left_on='container_type',right_on='container_type')
        contenedoresnotOK['Used Capacity'] = contenedoresnotOK['TEV'] / contenedoresnotOK['Capacity']
        contenedoresnotOK = contenedoresnotOK[['container_number','line_quantity_x','TEV','origin_country_code','final_destination_country_code','container_type','Est. Arrival at Destination Port','BU','Capacity','Used Capacity']]
        contenedoresnotOK.rename(columns={'TEV':'Total Volume'},inplace=True)
        contenedoresnotOK['Semaforo'] = "Volumen Estimado"
        totalcontenedores = totalcontenedores.append(contenedoresnotOK)

        return totalcontenedores, contenedoresOK, contenedoresnotOK, sobreutilizados,listaPNSVol
    

    def outputreport(self,totalcontenedores, contenedoresOK, contenedoresnotOK, sobreutilizados, listaPNSVol):
        with pd.ExcelWriter(self.output_path) as writer:
            totalcontenedores.to_excel(writer, sheet_name='Utilizacion',index=False)
            contenedoresOK.to_excel(writer, sheet_name='En Rango',index=False)
            contenedoresnotOK.to_excel(writer, sheet_name='Volumen 0',index=False)
            sobreutilizados.to_excel(writer, sheet_name='Sobreutilizado',index=False)
            listaPNSVol.to_excel(writer, sheet_name='PN Pendientes', index=False)
        self.connecta.close()


if __name__ == '__main__':
    app = Calculator()
    q = app.database_connection()
    results = app.volume(q)
    app.outputreport(*results)
        