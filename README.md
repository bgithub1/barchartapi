## barchartapi facilitates python access to Barchart's paid API (https://www.barchart.com/ondemand/api)
*The following examples  assume that you have launched a jupyter notebook or a python module from the folder YOUR_WORKSPACE/barchartapi/barchartapi*

___
## Structure:
* **project name**: *barchartapi*
* **main package**: *barchartapi/barchartapi*
* **main module**: *barchartapi/barchartapi/barchart_api.py*
* **main class**: *barchartapi/barchartapi/barchart_api.BcHist*


___ 
## For stocks and other non futures:  
(See jupyter notebook **get_history_stocks.ipynb** )

### Example: get one minute bars for SPY  

##### Import pandas and sys  
```
import pandas as pd
import sys
```

##### Add references to your sys.path, that barchartapi uses
```
WORKSPACE_DIR = '../..' 
PROJECT_DIR = f'{WORKSPACE_DIR}/barchartapi' 
WORKING_DIR = f'{PROJECT_DIR}/barchartapi' 
if WORKING_DIR not in sys.path:
    sys.path.append(WORKING_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)
if WORKSPACE_DIR not in sys.path:
    sys.path.append(WORKSPACE_DIR)
import barchart_api as bcapi
```

##### Create an instance of BsHist
```
api_key = "YOUR_FREE_OR_PAID_API_KEY"
bar_type='minutes'
interval=30
key_is_paid=False
endpoint_type=  'paid_url' if key_is_paid else 'free_url'
bch = bcapi.BcHist(api_key, bar_type=bar_type, interval=interval,endpoint_type = endpoint_type)
```

#### Get data
```
beg_yyyymmdd = 20180601
end_yyyymmdd = 20181231
return_tuple = bch.get_history(short_name, beg_yyyymmdd, end_yyyymmdd)
df_history = tup[1]
df_history.head(20)
```

___
## Get Futures Data for a series of contracts
(See the jupyter notebook futures_series.ipynb)

#### Import futures_series
```
# make sure you have executed the previous exports and 
#   added the previous folders to sys.path
import futures_series as futs
```

#### Define date and bar type parameters
```
bar_type = 'minutes'
interval = 1
output_folder = temp_folder
logger = futs.init_root_logger('logger.log')
start_year = 2008
end_year = 2018
years = np.linspace(start_year,end_year,end_year-start_year+1,dtype=int)
days = 40
```

#### Create a loop that uses instances of the class FuturesSeries
```
for y in years:
    beg_yyyymm = int(f'{y}01')
    end_yyyymm = int(f'{y}12')
    logger.info(f'begin:{beg_yyyymm}, end:{end_yyyymm}')
    fc = futs.FuturesSeries(api_key, commodity, beg_yyyymm, end_yyyymm, bar_type, 
                            interval, endpoint_type,logger)
    logger.info(f'BEGIN Fetching Data for year: {y}')
    fc.get_contracts(trading_days_to_get=days,month_code_list=month_codes)
    logger.info(f'BEGIN Writing Data for year: {y}')
    fc.write_csv(output_folder)
    logger.info(f'END Writing Data for year: {y}')
```


