"""
    The MIT License (MIT)

    Copyright (c) 2014 Vivek Jha

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
import ast 
import re
import json
import zipfile
import io
import requests
from dateutil import parser
from datetime import datetime as dt 
from nsetools.bases import AbstractBaseExchange
from nsetools.utils import byte_adaptor
from nsetools.utils import js_adaptor
from nsetools.utils import byte_adaptor, js_adaptor
from nsetools.datemgr import mkdate
from nsetools import urls

class Nse(AbstractBaseExchange):
    """
    class which implements all the functionality for
    National Stock Exchange
    """
    __CODECACHE__ = None

    def __init__(self, session_refresh_interval=120):
        self.session_refresh_interval = session_refresh_interval 
        self.create_session()

    def get_stock_codes(self, cached=True, as_json=False):
        """
        returns a dictionary with key as stock code and value as stock name.
        It also implements cache functionality and hits the server only
        if user insists or cache is empty
        :return: dict
        """
        url = urls.STOCKS_CSV_URL
        req = "Request(url, None, self.headers)"
        res_dict = {}
        if cached is not True or self.__CODECACHE__ is None:
            # raises HTTPError and URLError
            res = self.opener.open(req)
            if res is not None:
                # for py3 compat covert byte file like object to
                # string file like object
                res = byte_adaptor(res)
                for line in res.read().split('\n'):
                    if line != '' and re.search(',', line):
                        (code, name) = line.split(',')[0:2]
                        res_dict[code] = name
                    # else just skip the evaluation, line may not be a valid csv
            else:
                raise Exception('no response received')
            self.__CODECACHE__ = res_dict
        return self.render_response(self.__CODECACHE__, as_json)

    def is_valid_code(self, code):
        """
        :param code: a string stock code
        :return: Boolean
        """
        if code:
            stock_codes = self.get_stock_codes()
            if code.upper() in stock_codes.keys():
                return True
            else:
                return False

    def get_quote(self, code, all_data=False):
        """
        gets the quote for a given stock code
        :param code:
        :return: dict or None
        :raises: HTTPError
        """
        code = code.upper()
        # TODO: implement if the code is valid
        res = self.fetch(urls.QUOTE_API_URL % code)
        res = res.json()['priceInfo'] if all_data is False else res.json()
        return self.cast_intfloat_string_values_to_intfloat(res)
    
    def get_top_gainers(self, index=None):
        """
        :return: a list of dictionaries containing top gainers of the day for all indices
        """
        url = urls.TOP_GAINERS_URL
        res = self.fetch(url)
        res_dict = res.json()
        if index is None:
            return self.cast_intfloat_string_values_to_intfloat(res_dict)
        else:
            res_dict = res_dict[index]
            return res_dict['data']


    def get_top_losers(self, index=None):
        """
        :return: a list of dictionaries containing top losers of the day for all indices
        """
        url = urls.TOP_LOSERS_URL
        res = self.fetch(url)
        res_dict = res.json()
        if index is None:
            return self.cast_intfloat_string_values_to_intfloat(res_dict)
        else:
            res_dict = res_dict[index]
            return res_dict['data']
    
    def get_advances_declines(self, code='nifty 50'):
        """
        :return: a list of dictionaries with advance decline data
        :raises: URLError, HTTPError
        """
        # fixing this
        code = code.upper()
        code = ' '.join(code.split())
        url = urls.EQUITY_STOCK_INDICES_URL % code
        response = self.fetch(url).json()['advance']
        return self.cast_intfloat_string_values_to_intfloat(response)
    

    def get_top_fno_gainers(self, as_json=False):
        """
        :return: a list of dictionaries containing top gainers in fno of the day
        """
        url = urls.TOP_FNO_GAINER_URL
        req = "Request(url, None, self.headers)"
        # this can raise HTTPError and URLError
        res = self.opener.open(req)
        # for py3 compat covert byte file like object to
        # string file like object
        res = byte_adaptor(res)
        res_dict = json.load(res)
        # clean the output and make appropriate type conversions
        res_list = [self.clean_server_response(item) for item in res_dict['data']]
        return self.render_response(res_list, as_json)
    
    def get_fno_lot_sizes(self, cached=True, as_json=False):
        """
        returns a dictionary with key as stock code and value as stock name.
        It also implements cache functionality and hits the server only
        if user insists or cache is empty
        :return: dict
        """
        url = urls.FNO_LOT_SIZE_URL
        req = "Request(url, None, self.headers)"
        res_dict = {}
        if cached is not True or self.__CODECACHE__ is None:
            # raises HTTPError and URLError
            res = self.opener.open(req)
            if res is not None:
                # for py3 compat covert byte file like object to
                # string file like object
                res = byte_adaptor(res)
                for line in res.read().split('\n'):
                    if line != '' and re.search(',', line) and (line.casefold().find('symbol') == -1):
                        (code, name) = [x.strip() for x in line.split(',')[1:3]]
                        res_dict[code] = int(name)
                    # else just skip the evaluation, line may not be a valid csv
            else:
                raise Exception('no response received')
            self.__CODECACHE__ = res_dict
        return self.render_response(self.__CODECACHE__, as_json)


    def get_top_fno_losers(self, as_json=False):
        """
        :return: a list of dictionaries containing top losers of the day
        """
        url = urls.TOP_FNO_LOSER_URL
        req = "Request(url, None, self.headers)"
        # this can raise HTTPError and URLError
        res = self.opener.open(req)
        # for py3 compat covert byte file like object to
        # string file like object
        res = byte_adaptor(res)
        res_dict = json.load(res)
        # clean the output and make appropriate type conversions
        res_list = [self.clean_server_response(item)
                    for item in res_dict['data']]
        return self.render_response(res_list, as_json)

    def cast_intfloat_string_values_to_intfloat(self, d):
        d = d.copy()
        for keys in d:
            if type(d[keys]) == str:
                try:
                    d[keys] = int(d[keys])
                except:
                    try:
                        d[keys] = float(d[keys])
                    except:
                        # given string value is neither string nor float ..
                        # do nothing in such cases
                        pass 
        return d

    def get_index_list(self):
        """ get list of indices and codes
        returns: a list | json of index codes
        """
        return [ i['indexSymbol'] for i in self.get_all_index_quote()]
    
    def get_index_quote(self, code):
        """
        params:
            code : string index code
        returns:
            dict 
        """
        url = urls.ALL_INDICES_URL
        all_index_quote = self.get_all_index_quote()
        index_list = [ i['indexSymbol'] for i in all_index_quote]
        code = code.upper()
        code = ' '.join(code.split())
        if code in index_list:
            response = list(filter(lambda idx: idx['indexSymbol'] == code, all_index_quote))[0]
            return self.cast_intfloat_string_values_to_intfloat(response)
        else:
            raise Exception('Wrong index code')
    
    def get_all_index_quote(self):
        """
        Gets information of all indices and one go
        returns:
            list of dicts
        """
        url = urls.ALL_INDICES_URL
        res = self.fetch(url)
        return res.json()['data']

    def nse_headers(self):
        """
        Builds right set of headers for requesting http://nseindia.com
        :return: a dict with http headers
        """
        return {"Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.5",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest"
                }

    
    def build_url_for_quote(self, code):
        """
        builds a url which can be requested for a given stock code
        :param code: string containing stock code.
        :return: a url object
        """
        pass 

    def clean_server_response(self, resp_dict):
        """cleans the server reponse by replacing:
            '-'     -> None
            '1,000' -> 1000
        :param resp_dict:
        :return: dict with all above substitution
        """

        # change all the keys from unicode to string
        pass 
    
    def download_index_copy(self, d):
        """returns index copy file"""
        pass

    def create_session(self):
        home_url = "https://nseindia.com"
        self._session = requests.Session()
        self._session.headers.update(self.nse_headers())
        self._session.get(urls.NSE_HOME)
        self._session_init_time = dt.now()
        
    
    def fetch(self, url):
        time_diff = dt.now() - self._session_init_time
        if time_diff.seconds < self.session_refresh_interval:
            print("time diff is ", time_diff.seconds)
            return self._session.get(url)
        else:
            print("time diff is ", time_diff.seconds)
            print("re-initing the session because of expiry")
            self.create_session()
            return self._session.get(url)

    def get_active_monthly(self, as_json=False):
        pass 

    def get_year_high(self, as_json=False):
        pass

    def get_year_low(self, as_json=False):
        pass
    
    def get_preopen_nifty(self, as_json=False):
        pass

    def get_preopen_niftybank(self, as_json=False):
        pass

    def get_preopen_fno(self, as_json=False):
        pass 

    def _get_json_response_from_url(self, url, as_json):
        """
        :return: a list of dictionaries containing the response got back from url
        """
        pass 
    
    def __str__(self):
        """
        string representation of object
        :return: string
        """
        return 'Driver Class for National Stock Exchange (NSE)'


if __name__ == "__main__":
    n = Nse()
    # data = n.download_bhavcopy("14th Dec")
    n.get_quote('reliance')

# TODO: get_most_active()
# TODO: get_top_volume()
# TODO: get_peer_companies()
# TODO: is_market_open()
# TODO: concept of portfolio for fetching price in a batch and field which should be captured
# TODO: Concept of session, just like as in sqlalchemy
