#!/usr/bin/python

# Commitment of Traders (http://www.cftc.gov) data handling

from google.appengine.ext import db
import csv
import sys
import httplib
import datetime
import utils
from cacher import *


def fetch_cftc_file (path):
    """
    Downloads file from CFTC site
    """
    conn = httplib.HTTPConnection ("www.cftc.gov")
    res = None
    try:
        conn.request ("GET", path)
        r = conn.getresponse ()
        res = r.read ()
    finally:
        conn.close ();
    return res;



class COT_Record (db.Model):
    # GOLD, EUR, MEAT, etc
    symbol = db.StringProperty (required = True)
    date = db.DateProperty (required = True)
    # Open Interest
    oi = db.IntegerProperty (required = True)
    # Non Commercial
    pos_non_comm_long = db.IntegerProperty (required = True)
    pos_non_comm_short = db.IntegerProperty (required = True)
    pos_non_comm_spread = db.IntegerProperty (required = True)
    # Commercial
    pos_comm_long = db.IntegerProperty (required = True)
    pos_comm_short = db.IntegerProperty (required = True)
    # Non reportable
    pos_non_rep_long = db.IntegerProperty (required = True)
    pos_non_rep_short = db.IntegerProperty (required = True)
    # count of traders
    count_non_comm_long = db.IntegerProperty (required = True)
    count_non_comm_short = db.IntegerProperty (required = True)
    count_non_comm_spread = db.IntegerProperty (required = True)
    count_comm_long = db.IntegerProperty (required = True)
    count_comm_short = db.IntegerProperty (required = True)

    def exists (self):
        """
        Returns true if value with such symbol and date is already exists
        """
        q = COT_Record.gql ("WHERE symbol = :1 and date = :2", self.symbol, self.date)
        if len (q.fetch (10)) > 0:
            return True
        else:
            return False



class COT_Last (db.Model):
    date = db.DateProperty (required = True)


class COT_Last_Provider:
    def get (self):
        # download http://cftc.gov/dea/newcot/deacit.txt, and check first line and third CSV value
        try:
            res = fetch_cftc_file ("/dea/newcot/deacit.txt")
            for row in csv.reader ([res.split ('\n')[0]], delimiter=',', quotechar='"'):
                if row[2] == '':
                    return None
                return utils.parseIsoDate (row[2])
        except:
            pass
        return None



def last_cot_report_date ():
    """
    Return date of latest COT report. If report cannot be downloaded, return None
    """
    return Cacher (COT_Last_Provider (), "last_cot", 60*60).get ()


def update_last_cot_report (date):
    for last in COT_Last.all ().fetch (100):
        last.delete ()
    last = COT_Last (date = date)
    last.put ()


def process_last_cot_report ():
    """
    Sub loads and processes latest COT report
    """
    skipped = count = 0
    try:
        res = fetch_cftc_file ("/dea/newcot/deacom.txt")
        date = last_cot_report_date ()
        for row in csv.reader (res.split ('\n'), delimiter=',', quotechar='"'):
            if row == []:
                continue
            rec = row_to_record (row)
            if rec != None:
                # verify that rec is single
                if rec.exists ():
                    print rec.symbol, rec.date
                    skipped = skipped + 1
                else:
                    rec.put ()
                    count = count + 1
                if date == None or date < rec.date:
                    date = rec.date
        update_last_cot_report (date)
    except:
        raise

    return "Processed %d entries, %d skipped" % (count, skipped)



def row_to_record (row):
    """
    Converts row of CSV file to COT_Record data object

    Arguments:
    - `row`: - array of CSV values
    """
    sym = name_to_symbol (row[0])
    if sym == None:
        return None
    return COT_Record (symbol = sym,
                       date = utils.parseIsoDate (row[2]),
                       oi = long (row[7]),
                       pos_non_comm_long = long (row[8]),
                       pos_non_comm_short = long (row[9]),
                       pos_non_comm_spread = long (row[10]),
                       pos_comm_long = long (row[11]),
                       pos_comm_short = long (row[12]),
                       pos_non_rep_long = long (row[15]),
                       pos_non_rep_short = long (row[16]),
                       count_non_comm_long = long (row[78]),
                       count_non_comm_short = long (row[79]),
                       count_non_comm_spread = long (row[80]),
                       count_comm_long = long (row[81]),
                       count_comm_short = long (row[82]))

def name_to_symbol (name):
    dict = {
        'GOLD'  : ['GOLD - '],
        'SILVER' : ['SILVER - '],
        'CHF' : ['SWISS FRANC - '],
        'EUR' : ['EURO FX - '],
        'GBP' : ['BRITISH POUND STERLING - '],
        'JPY' : ['JAPANESE YEN - '],
        'CAD' : ['CANADIAN DOLLAR - '],
        }
    for key in dict.keys ():
        for v in dict[key]:
            if name.find (v) == 0:
                return key
    return None
