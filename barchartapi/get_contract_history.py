'''
Created on Dec 13, 2018

@author: Bill Perlman
'''
from barchartapi import barchart_api as bcapi
import argparse as ap

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
    parser.add_argument('--short_name',type=str,
                        help='a stock name like AAPL, or a commodities contract like CLF19 (NO DEFAULT')
    parser.add_argument('--beg_yyyymmdd',type=int,
                        help='a YYYYMMDD date like 20181101 for Nov 1st, 2018.  This will be the date of the first history bar that you get.  If none, the date is calculated as the last 2 months of a commodities contracts, or 2 months back from today for a stock',
                        nargs='?')
    parser.add_argument('--end_yyyymmdd',type=int,
                        help='a YYYYMMDD date like 20181214 for Dec 14th, 2018.  This will be the date of the last history bar that you getIf none, the date is calculated as the last 2 months of a commodities contracts, or 2 months back from today for a stock',
                        nargs='?')
    args = parser.parse_args()
    
    api_key = args.api_key # 
    endpoint_type = args.endpoint_type
    bar_type = args.bar_type
    interval = args.interval
    short_name = args.short_name
    beg_yyyymmdd = args.beg_yyyymmdd
    end_yyyymmdd = args.end_yyyymmdd
    
    bch = bcapi.BcHist(api_key, bar_type=bar_type, interval=interval,endpoint_type = endpoint_type)
    tup = bch.get_history(short_name, beg_yyyymmdd, end_yyyymmdd)
    print(tup[0])
    print(tup[1])
            