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

@author: Bill Perlman
'''

import math
from barchartapi import barchart_api as bcapi
import argparse as ap
import logging
from tqdm import tqdm
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_finance import candlestick_ohlc
import matplotlib.dates as mdates
from matplotlib import ticker


    
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
    index_columns = ['cyear','cmonth','symbol','year','month','day','hour','minute','tyear','tmonth','tday','yyyymmddhhmm']
    
    scale_functions = {'close':'mean', 'high':'max','low':'min', 
                       'open':'mean', 'volume':'sum','last_yyyymmddhhmm':'max','dte':'max'}    

    
    def __init__(self,api_key,commodity,beg_yyyymm,end_yyyymm,bar_type=None,interval=1,endpoint_type=None,logger=None):
        self.logger = logger if logger is not None else  init_root_logger('logger.log')
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
    
    
    def get_contracts(self,trading_days_to_get=40,month_code_list=None):
        '''
        Get data from Barchart, and add extra informative columns
        :param trading_days_to_get:
        '''
        # STEP 1: get list of contracts and their yyyy and mm
        self.df_final = None
        df_contracts = self.bch.get_contract_short_names(self.commodity, self.beg_yyyymm, self.end_yyyymm)
        if month_code_list is not None:
            df_contracts['month_code'] = df_contracts.contract.apply(lambda c: c[-3:][0])
            df_contracts = df_contracts[df_contracts.month_code.isin(month_code_list)]

        # STEP 2: loop to get data
        for i in tqdm(range(len(df_contracts))):   
            row = df_contracts.iloc[i]
            contract_last_day_yyyymmdd = self.bch.get_last_trading_day(row.contract)
            contract_first_day_yyyymmdd = yyyymmdd_from_datetime(datetime_from_yyyymmdd(contract_last_day_yyyymmdd)- datetime.timedelta(trading_days_to_get))
            tup = self.bch.get_history(row.contract, beg_yyyymmdd=contract_first_day_yyyymmdd, end_yyyymmdd=contract_last_day_yyyymmdd)
            df = tup[1]
            if len(df)<1:
                self.logger.warn('%s: %s' %(row.contract,tup[0]))
            else:
                if self.df_final is None:
                    self.df_final = df.copy()
                else:
                    self.df_final = self.df_final.append(df)
        
#         # STEP 3: add informative columns
#         self.df_final = proc_df(self.df_final)
    
    def write_csv(self,output_folder):
        self.df_final.to_csv('%s/%s_%06d_%06d.csv' %(output_folder,self.commodity,self.beg_yyyymm,self.end_yyyymm),index=False)

def proc_df(df,is_commodity=True):
    '''
    Add important columns to Barchart csv data
    :param df:
    '''
    
    # Create year, month, day, hour minute, tyear, tmonth and tday
    tss = df['timestamp'].as_matrix()
    fyear = [int(s[0:4]) for s in tss]
    fmon =  [int(s[5:7]) for s in tss]
    fday =  [int(s[8:10]) for s in tss]
    fhour =  [int(s[11:13]) for s in tss]
    fminute =  [int(s[14:16]) for s in tss]
    df['year'] = fyear
    df['month'] = fmon
    df['day'] = fday
    df['hour'] = fhour
    df['minute'] = fminute        

    if is_commodity:
        month_nums = {'F':1,'G':2,'H':3,'J':4,'K':5,'M':6,'N':7,'Q':8,'U':9,'V':10,'X':11,'Z':12}
        syms = df['symbol'].as_matrix()
        cmon = [int(month_nums[s[-3:][0]]) for s in syms]
        cyear =  [int(s[-2:]) + 2000 for s in syms]
        df['cyear'] = cyear
        df['cmonth'] = cmon
    else:
        df['cyear'] = df['year']
        df['cmonth'] = df['month']
        
    tds = df['tradingDay'].as_matrix()
    fyear = [int(s[0:4]) for s in tds]
    fmon =  [int(s[5:7]) for s in tds]
    fday =  [int(s[8:10]) for s in tds]
    df['tyear'] = fyear
    df['tmonth'] = fmon
    df['tday'] = fday

    # drop any rows where the contract year is less than the trading date year
    df = df.drop(df[(df.cyear<df.year) ].index)

    # Define method to create yyyymmddhhmm
    def _yyyymmddhhmm(s):
        y = int(s[0:4])
        mon = int(s[5:7])
        d = int(s[8:10])
        h = int(s[11:13])
        mnt = int(s[14:16])
        return int('%04d%02d%02d%02d%02d' %(y,mon,d,h,mnt))   
    df['yyyymmddhhmm'] = df.timestamp.apply(_yyyymmddhhmm)

    
    # create dte
    df_max = df[['symbol','yyyymmddhhmm']].groupby('symbol',as_index=False).max()
    df_max = df_max.rename(columns={'yyyymmddhhmm':'last_yyyymmddhhmm'})
    df_with_max = df.merge(df_max,how='inner',on='symbol')
    y = np.array(df_with_max.tyear)
    m = np.array(df_with_max.tmonth)
    d = np.array(df_with_max.tday)
    last_year = np.array(df_with_max.last_yyyymmddhhmm.apply(lambda i:str(i)[0:4]).astype(int))
    last_month = np.array(df_with_max.last_yyyymmddhhmm.apply(lambda i:str(i)[4:6]).astype(int))
    last_day = np.array(df_with_max.last_yyyymmddhhmm.apply(lambda i:str(i)[6:8]).astype(int))
    zips = zip(last_year,last_month,last_day,y,m,d)
    
    dte = np.array([(datetime.datetime(ly,lm,ld)-datetime.datetime(cy,cm,cd)).days for ly,lm,ld,cy,cm,cd in list(zips)])
    df_with_max['dte'] = dte
    
    # save df_final
    scale_columns = list(FuturesSeries.scale_functions.keys())
    df_final = df_with_max[FuturesSeries.index_columns+scale_columns]
    return df_final

def scale_df(df_minute_data,scale_factor=15):
    '''
    Create a new version of minute bars, scaled to some less granular time frame.
    :param df:
    :param scale_factor:
    '''
    #scale bars
    df_scaled = df_minute_data.copy()
    scale_columns = list(FuturesSeries.scale_functions.keys())
    df_scaled['minute_scaled'] = df_scaled.minute.apply(lambda i: (int(str(i)[-2:])//scale_factor)*scale_factor)
    index_columns_to_use = list(set(FuturesSeries.index_columns+['minute_scaled']) - set(['minute','yyyymmddhhmm']))
    df_scaled = df_scaled.groupby(index_columns_to_use,as_index=False).agg(FuturesSeries.scale_functions)
    df_scaled = df_scaled.rename(columns={'minute_scaled':'minute'})
    df_scaled['yyyymmddhhmm'] = df_scaled.apply(lambda r: '%04d%02d%02d%02d%02d' %(r.year,r.month,r.day,r.hour,r.minute),axis=1)
    df_scaled = df_scaled.sort_values(FuturesSeries.index_columns)
    df_scaled.index = range(len(df_scaled))
    df_scaled = df_scaled[FuturesSeries.index_columns+scale_columns]
    return df_scaled


def plot_candles(dfcv):
    '''
    Plot candlesticks with volume
    :param dfcv:
    '''
    def _dts(row):
        return datetime.datetime(int(row.year),
                                 int(row.month),
                                 int(row.day),
                                 int(row.hour),
                                 int(row.minute))
    
    fig, ax1 = plt.subplots(1, 1, figsize=(14, 12))
    plt.grid()
    min_yyyymmddhhmm = int('%04d%02d%02d0000' %(min(dfcv.tyear),min(dfcv.tmonth),min(dfcv.tday)))
    print(min_yyyymmddhhmm)
#     yyyymm000000 =  math.trunc(min(dfcv.yyyymmddhhmm)/1000000)*1000000
    xall = np.array(dfcv.yyyymmddhhmm)
#     x = xall[xall>=min_yyyymmddhhmm]
    t = np.array(dfcv.apply(_dts,axis=1))
    t = t[xall>=min_yyyymmddhhmm]
    t = mdates.date2num(t)
    y1c = np.array(dfcv.close)
    y1c = y1c[xall>=min_yyyymmddhhmm]
    y1o = np.array(dfcv.open)
    y1o = y1o[xall>=min_yyyymmddhhmm]
    y1h = np.array(dfcv.high)
    y1h = y1h[xall>=min_yyyymmddhhmm]
    y1l = np.array(dfcv.low)
    y1l = y1l[xall>=min_yyyymmddhhmm]
    plt.xticks(rotation=70)
    quotes = zip(t,y1o,y1h,y1l,y1c)
    candlestick_ohlc(ax1,quotes,width=.6/(24*60)*2, colorup='#77d879', colordown='#db3f3f',)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M'))
    ax1.xaxis.set_major_locator(ticker.MaxNLocator(10))
    
    fig, ax1 = plt.subplots(1, 1, figsize=(14, 2))
    plt.xticks(rotation=70)
    y2 = np.array(dfcv.volume)
    y2 = y2[xall>=min_yyyymmddhhmm]
    ax1.grid()
    ax1.plot(t,y2) 
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M'))
    ax1.xaxis.set_major_locator(ticker.MaxNLocator(10))

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

            