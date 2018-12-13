'''
Created on Dec 12, 2018

implement the barchart python api: https://www.barchart.com/ondemand/api/getHistory
@author: bperlman1
'''
import ondemand
import pandas as pd
import pandas_summary as pds
import datetime
import argparse as ap

class BcHist():
    def __init__(self,
                 api_key,
                 bar_type='minutes',
                 interval= 1):
        self.api_key = api_key
        self.bar_type = bar_type
        self.interval = interval
        self.bars_per_day = 60*24 if bar_type != 'daily'  else 1 
        self.od =  ondemand.OnDemandClient(api_key=api_key, end_point='https://marketdata.websol.barchart.com/')

    
    def get_history(self,short_name,beg_yyyymmdd=None,end_yyyymmdd=None):
        date_dict = calc_dates(beg_yyyymmdd, end_yyyymmdd, self.bar_type, self.interval)
        resp = self.od.history(short_name, self.bar_type, 
                          maxRecords=date_dict['max_records'], 
                          interval=self.interval,
                          startDate=date_dict['beg_yyyymmdd'])
        status = resp['status']
        results = resp['results']
        df = pd.DataFrame(results) 
        return (status,df)  
   
def calc_dates(beg_yyyymmdd=None,end_yyyymmdd=None,
                     bar_type='minutes',interval=1):
    if beg_yyyymmdd is not None:            
        ds = str(beg_yyyymmdd)
        byyyy = int(ds[0:4])
        bmm = int(ds[4:6])
        bdd = int(ds[6:8])
    if end_yyyymmdd is not None:
        ds = str(end_yyyymmdd)
        eyyyy = int(ds[0:4])
        emm = int(ds[4:6])
        edd = int(ds[6:8])

    if beg_yyyymmdd is None:
        if end_yyyymmdd is not None:
            dt_end = datetime.datetime(eyyyy,emm,edd)
            dt_beg = dt_end - datetime.timedelta(40)
        else:
            dt_end = datetime.datetime.now()
            dt_beg = dt_end - datetime.timedelta(40)
    else:
        dt_beg = datetime.datetime(byyyy,bmm,bdd)
        if end_yyyymmdd is not None:
            dt_end = datetime.datetime(eyyyy,emm,edd)
        else:
            dt_end = dt_beg + datetime.timedelta(40)
        
    
    diff = dt_end - dt_beg
    days = diff.days
    max_records  = 1 * days 
    if bar_type != 'daily':
        max_records = 24*60 * days // interval
    b_yyyymmdd = '%04d%02d%02d' %(dt_beg.year,dt_beg.month,dt_beg.day)
    e_yyyymmdd = '%04d%02d%02d' %(dt_end.year,dt_end.month,dt_end.day)
    return {'max_records':max_records,'beg_yyyymmdd':b_yyyymmdd,'end_yyyymmdd':e_yyyymmdd}
         
if __name__ == '__main__':
    parser = ap.ArgumentParser()
    parser.add_argument('--api_key',type=str,help='barchart API KEY')
    parser.add_argument('--bar_type',type=str,help='either daily or minutes (default is minutes)',
                        default='minutes')
    parser.add_argument('--interval',type=int,help='if bar_type = minutes, then either 1,5,15,30 or 60. (default = 1)',
                        default=1)
    parser.add_argument('--short_name',type=str,help='a stock name like AAPL, or a commodities contract like CLF19 (NO DEFAULT')
    parser.add_argument('--beg_yyyymmdd',type=int,
                        help='a YYYYMMDD date like 20181101 for Nov 1st, 2018.  This will be the date of the first history bar that you get.  If none, the date is calculated as the last 2 months of a commodities contracts, or 2 months back from today for a stock',
                        nargs='?')
    parser.add_argument('--end_yyyymmdd',type=int,
                        help='a YYYYMMDD date like 20181214 for Dec 14th, 2018.  This will be the date of the last history bar that you getIf none, the date is calculated as the last 2 months of a commodities contracts, or 2 months back from today for a stock',
                        nargs='?')
    args = parser.parse_args()
    api_key = args.api_key # '99125d367af268ca234144d64583a5e7'
    
    bar_type = args.bar_type
    interval = args.interval
    short_name = args.short_name
    beg_yyyymmdd = args.beg_yyyymmdd
    end_yyyymmdd = args.end_yyyymmdd
    bch = BcHist(api_key, bar_type=bar_type, interval=interval)
    tup = bch.get_history('CLG19', beg_yyyymmdd, end_yyyymmdd)
    print(tup[0])
    print(tup[1])
            