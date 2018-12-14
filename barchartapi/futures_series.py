'''
Created on Dec 13, 2018

get history data for a series of commodity contracts

Example args:
python get_contract_series_history.py /
 --api_key yourkeyfrombarchart /
 --bar_type minutes /
 --interval 1 /
 --commodity CL /
 --beg_yyyymm 201001 /
 --end_yyyymm 201812 

@author: bperlman1
'''
from barchartapi import barchart_api as bcapi
import argparse as ap
import logging
from tqdm import tqdm
import datetime


    
def init_root_logger(logfile,logging_level=None):
    level = logging_level
    if level is None:
        level = logging.DEBUG
    # get root level logger
    logger = logging.getLogger()
    if len(logger.handlers)>0:
        return logger
    logger.setLevel(logging.getLevelName(level))

    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)   
    return logger

def datetime_from_yyyymmdd(yyyymmdd):
    y = int(str(yyyymmdd)[0:4])
    m = int(str(yyyymmdd)[4:6])
    d = int(str(yyyymmdd)[6:8])
    dt = datetime.datetime(y,m,d)
    return dt

def yyyymmdd_from_datetime(dt):
    y = dt.year
    m = dt.month 
    d = dt.day 
    return '%04d%02d%02d' %(y,m,d)

class FuturesSeries():
    def __init__(self,api_key,commodity,beg_yyyymm,end_yyyymm,bar_type=None,interval=1,endpoint_type=None):
        self.commodity = commodity
        self.api_key = api_key
        self.beg_yyyymm = beg_yyyymm
        self.end_yyyymm = end_yyyymm
        self.bar_type = bar_type
        self.interval = interval
        self.endpoint_type = endpoint_type if endpoint_type is not None else 'paid_url'
        self._validate_yyyymms()
        self.bch = bcapi.BcHist(api_key, bar_type=bar_type, interval=interval,endpoint_type = endpoint_type)
        
    def _validate_yyyymms(self):
        if self.beg_yyyymm is None or self.end_yyyymm is None:
            if self.end_yyyymm is not None:
                end_yyyymmdd = int(str(self.end_yyyymm)+'01')
                beg_yyyymmdd = None
                dates_tup = bcapi.calc_dates(beg_yyyymmdd, end_yyyymmdd, self.bar_type, self.interval)
            elif self.beg_yyyymm is not None:
                end_yyyymmdd = None
                beg_yyyymmdd = int(str(self.beg_yyyymm)+'01')
                dates_tup = bcapi.calc_dates(beg_yyyymmdd, end_yyyymmdd, self.bar_type, self.interval)
        else:
            beg_yyyymmdd = int(str(self.beg_yyyymm)+'01')
            end_yyyymmdd = int(str(self.end_yyyymm)+'01')
            dates_tup = bcapi.calc_dates(beg_yyyymmdd, end_yyyymmdd, self.bar_type, self.interval)
            
        beg_yyyymmdd = dates_tup['beg_yyyymmdd']
        end_yyyymmdd = dates_tup['end_yyyymmdd']
        self.beg_yyyymm = int(str(beg_yyyymmdd)[0:6])        
        self.end_yyyymm = int(str(end_yyyymmdd)[0:6])        
    
    def get_contracts(self):
        self.df_final = None
        df_contracts = self.bch.get_contract_short_names(self.commodity, self.beg_yyyymm, self.end_yyyymm)
        
        # STEP 4: loop to get data
        for i in tqdm(range(len(df_contracts))):   
            row = df_contracts.iloc[i]
            contract_last_day_yyyymmdd = self.bch.get_futures_last_day_yyyymmdd(row.contract)
            contract_first_day_yyyymmdd = yyyymmdd_from_datetime(datetime_from_yyyymmdd(contract_last_day_yyyymmdd)- datetime.timedelta(40))
            tup = self.bch.get_history(row.contract, beg_yyyymmdd=contract_first_day_yyyymmdd, end_yyyymmdd=contract_last_day_yyyymmdd)
            df = tup[1]
            if len(df)<1:
                logger.warn('%s: %s' %(row.contract,tup[0]))
            else:
                if self.df_final is None:
                    self.df_final = df.copy()
                else:
                    self.df_final = self.df_final.append(df)
    
    def write_csv(self,output_folder):
        self.df_final.to_csv('%s/%s_%06d_%06d.csv' %(output_folder,commodity,self.beg_yyyymm,self.end_yyyymm),index=False)
        
if __name__ == '__main__':
    parser = ap.ArgumentParser()
    parser.add_argument('--api_key',type=str,help='barchart API KEY')
    parser.add_argument('--endpoint_type',type=str,
                             help='either paid_url or free_url (Default is paid_url',
                             default='paid_url')
    
    parser.add_argument('--bar_type',type=str,help='either daily or minutes (default is minutes)',
                        default='minutes')
    parser.add_argument('--interval',type=int,
                        help='if bar_type = minutes, then either 1,5,15,30 or 60. (default = 1)',
                        default=1)
    parser.add_argument('--commodity',type=str,
                        help='a commodity code like CL or NG or ES')
    parser.add_argument('--beg_yyyymm',type=int,
                        help='a YYYYMM date like 201811 for Nov  2018.  Use this to denote the FIRST contract date of the series',
                        nargs='?')
    parser.add_argument('--end_yyyymm',type=int,
                        help='a YYYYMM date like 201811 for Nov  2018.  Use this to denote the LAST contract date of the series',
                        nargs='?')
    parser.add_argument('--output_folder',type=str,
                             help='folder to write final csv',
                             default='temp_folder')
    args = parser.parse_args()
    api_key = args.api_key # 
    
    bar_type = args.bar_type
    interval = args.interval
    commodity = args.commodity
    beg_yyyymm = args.beg_yyyymm
    end_yyyymm = args.end_yyyymm
    output_folder = args.output_folder
    logger = init_root_logger('logger.log')
    endpoint_type = args.endpoint_type
    
    logger.info('start')
    fc = FuturesSeries(api_key, commodity, beg_yyyymm, end_yyyymm, bar_type, interval, endpoint_type)
    fc.get_contracts()
    fc.write_csv(output_folder)
    logger.info('done')

    
#     # STEP 1: get dates for beg_yyyymm and end_yyyymm 
#     if beg_yyyymm is None or end_yyyymm is None:
#         if end_yyyymm is not None:
#             end_yyyymmdd = int(str(end_yyyymm)+'01')
#             beg_yyyymmdd = None
#             dates_tup = bcapi.calc_dates(beg_yyyymmdd, end_yyyymmdd, bar_type, interval)
#         elif beg_yyyymm is not None:
#             end_yyyymmdd = None
#             beg_yyyymmdd = int(str(beg_yyyymm)+'01')
#             dates_tup = bcapi.calc_dates(beg_yyyymmdd, end_yyyymmdd, bar_type, interval)
#     else:
#         beg_yyyymmdd = int(str(beg_yyyymm)+'01')
#         end_yyyymmdd = int(str(end_yyyymm)+'01')
#         dates_tup = bcapi.calc_dates(beg_yyyymmdd, end_yyyymmdd, bar_type, interval)
#         
#     beg_yyyymmdd = dates_tup['beg_yyyymmdd']
#     end_yyyymmdd = dates_tup['end_yyyymmdd']
#     beg_yyyymm = int(str(beg_yyyymmdd)[0:6])        
#     end_yyyymm = int(str(end_yyyymmdd)[0:6])        
# 
#     # STEP 2: create instance of BcHist
#     bch = bcapi.BcHist(api_key, bar_type=bar_type, interval=interval,endpoint_type = endpoint_type)
#     
#     # STEP 3: create contracts to get
#     df_final = None
#     df_contracts = bch.get_contract_short_names(commodity, beg_yyyymm, end_yyyymm)
#     
#     # STEP 4: loop to get data
#     for i in tqdm(range(len(df_contracts))):   
#         row = df_contracts.iloc[i]
#         contract_last_day_yyyymmdd = bch.get_futures_last_day_yyyymmdd(row.contract)
#         contract_first_day_yyyymmdd = yyyymmdd_from_datetime(datetime_from_yyyymmdd(contract_last_day_yyyymmdd)- datetime.timedelta(40))
#         tup = bch.get_history(row.contract, beg_yyyymmdd=contract_first_day_yyyymmdd, end_yyyymmdd=contract_last_day_yyyymmdd)
#         df = tup[1]
#         if len(df)<1:
#             logger.warn('%s: %s' %(row.contract,tup[0]))
#         else:
#             if df_final is None:
#                 df_final = df.copy()
#             else:
#                 df_final = df_final.append(df)
#     
#     df_final.to_csv('%s/%s_%06d_%06d.csv' %(output_folder,commodity,beg_yyyymm,end_yyyymm),index=False)
#     logger.info('done')
            