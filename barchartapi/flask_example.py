'''
Created on Jan 7, 2019

Toy example of using a Flask server to serve data from barchart api.

The method dataframe_return(df,is_error=None) allows you to return pandas
  DataFrames to the caller, as either html, a csv file, a json file or a zip file.

@author: Bill Perlman
'''
import argparse as ap
import flask as fl
from flask import make_response
from flask import send_file
import io 
import pandas as pd
import json
from barchartapi.barchart_api import BcHist


app = fl.Flask(__name__)
app.secret_key = 'development key'

qba = None
logger = None


@app.route("/bchist",methods=('GET', 'POST'))
def bchist():
    '''
    Example:
    Daily bar examples:
        for csv printed in browser:
        http://127.0.0.1:5300/bchist?contract=CLZ20&beg_yyyymmdd=20180901&end_yyyymmdd=20181130
        for csv download:
        http://127.0.0.1:5300/bchist?contract=CLZ20&beg_yyyymmdd=20180901&end_yyyymmdd=20181130&return_csv=True
        for json:
        http://127.0.0.1:5300/bchist?contract=CLZ20&beg_yyyymmdd=20180901&end_yyyymmdd=20181130&return_json=True

    Minute bar example
        http://127.0.0.1:5300/bchist?contract=CLZ20&beg_yyyymmdd=20180901&end_yyyymmdd=20181130&interval=1&bartype=minutes
    '''
    contract = fl.request.args.get('contract')
    beg_yyyymmdd = fl.request.args.get('beg_yyyymmdd')
    end_yyyymmdd = fl.request.args.get('end_yyyymmdd')
    interval =  fl.request.args.get('interval')
    if interval is None:
        interval = 1
    else:
        interval = int(interval)
    
    bartype =  fl.request.args.get('bartype')
    if bartype is None:
        bartype = 'daily'
    
    api_key = open('temp_folder/free_api_key.txt','r').read()
    bc = BcHist(api_key, bartype, interval, 'free_url')
    resp = bc.get_history(contract, beg_yyyymmdd, end_yyyymmdd)
    if resp[1] is None:
        return dataframe_return(pd.DataFrame({'ERROR':[resp[0]]}))
    df = resp[1]
    return dataframe_return(df)


def dataframe_return(df,is_error=False):
    """
    This method will create an http response variable that can be used to return from a route.
    If return_json = true, then the response will be a json object as follows (assume that 215 csv lines, including the header, are returned:
        {"result":
            {
                "0":"active_parcel,record_id,update_id,upf_ltd",
                "1":"2009-0178-0000-0019-0000,668681,1515891000540,130.00",
                "2":"2009-0178-0000-0019-0000,663672,1515890999758,1221.00",
                "3":"2009-0178-0000-0019-0000,648645,1515890994821,3878.22",
                ...
                "214":"2009-0178-0000-0019-0000,648645,1515890994821,3878.22"
            }
        }
    
    If return_zip = true, a zip file of the inner csv will be returned
    
    otherwise, the csv file will be returned 

    :param df:
    """
    # return a csv of the Dataframe
    return_zip = fl.request.args.get('return_zip')
    if return_zip is not None:
        # df_for_workato is really a memory_file of io.BytesIO()
        memory_file = df
        memory_file.seek(0)
        return send_file(memory_file, attachment_filename=return_zip, as_attachment=True)


    return_json = fl.request.args.get('return_json')
    if return_json is not None and str(return_json).lower()=='true':
        # create string array imbedded in DataFrame for workato csv return
        s = io.StringIO()
        df.to_csv(s,index=False)
        arr = s.getvalue().split('\n')    
        main_key = 'result'
        if str(is_error).lower()=='true':
            main_key = 'ERROR'
        df_for_workato =  pd.DataFrame({main_key:arr})
        s = io.StringIO()
        df_for_workato.to_json(s)
        records_string = s.getvalue()
        output = make_response(records_string)
        output.headers["Content-Disposition"] = "attachment; filename=export.csv"
        output.headers["Content-type"] = "json"
        return output
    
    return_csv = fl.request.args.get('return_csv')
    if return_csv is not None and str(return_csv).lower()=='true':
        s = io.StringIO()
        df.to_csv(s,index=False)
        records_string = s.getvalue()
        output = make_response(records_string)
        output.headers["Content-Disposition"] = "attachment; filename=export.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    # default case
    html_of_df = df.to_html()
    return fl.render_template('show_dataframe.html', html_to_display=html_of_df)


if __name__ == '__main__':
    parser = ap.ArgumentParser()
    parser.add_argument('--host_url',type=str,help='host url (or ip).  Default is 127.0.0.1',default='127.0.0.1')
    parser.add_argument('--port',type=str,help='port',default='5300')
    args = parser.parse_args()
    host_url = args.host_url 
    port = args.port
    print('hi there from flask_example.py')
    app.run(host=host_url, port=port)
