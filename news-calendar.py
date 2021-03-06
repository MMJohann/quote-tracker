#!/usr/bin/python
# -*- coding: utf-8 -*-

print 'Content-Type: text/calendar; charset=UTF-8'
print 'Cache-Control: no-cache, must-revalidate'
print 'Expires: Sat, 26 Jul 1997 05:00:00 GMT'
print ''

from icalendar import Calendar, Event, UTC
from icalendar.prop import vText
import time
import datetime
import cgi
from google.appengine.ext import db

from tracker import news

curr_filter = cgi.FieldStorage ().getlist ('curr')
curr_filter = map (lambda a: a.upper (), curr_filter)

if 'imp' in cgi.FieldStorage ():
    imp = int (cgi.FieldStorage ()['imp'].value)
else:
    imp = 0

if imp < 0:
    imp = 0
elif imp > 2:
    imp = 2

d_from = datetime.date.today ()
d_to = d_from + datetime.timedelta (days = 7)

cal = Calendar ()
cal['version'] = "2.0"
cal['prodid'] = "-//Shmuma//FX News 0.1//EN"
cal['x-wr-timezone'] = "UTC"

f_str = "\\, ".join (curr_filter)
if imp > 0:
    f_str += "\\, imp > %d" % imp
if curr_filter:
    cal['x-wr-calname'] = "Forex News (" + f_str + ")"
    cal['x-wr-caldesc'] = "Upcoming financial news. Filtered by " + f_str + "."
else:
    cal['x-wr-calname'] = "Forex News"
    cal['x-wr-caldesc'] = "Upcoming financial news."
cal['x-published-ttl'] = "P1H"


def norm_str (str, vis = 0):
    if vis == 0:
        if str == None:
            return "-"
        return str.strip ()
    else:
        if str == None:
            return ""
        return str.strip ()

# Filter is a list of currencies
# Curr is a comma-separated list of currenclies.
def check_filter (filter, curr):
    if len (filter) == 0:
        return True
    if not curr:
        return True
    for item in curr.split (","):
        if item.upper () in filter:
            return True
    return False

# generate importance filter string
imp_list = []
for i in xrange(imp, 3):
    imp_list.append ("%d" % i)
imp_filter = "(" + ",".join (imp_list) + ")"

q = db.GqlQuery ("select * from News_Record_v2 where when > :1 and when < :2 and importance in %s order by when" % imp_filter, d_from, d_to)
id = 0
for ev in q:
    if not check_filter (curr_filter, ev.curr):
        continue
    event = Event ()
    event['uid'] = "%d-%d@quote-tracker.appspot.ru" % (id, time.mktime (ev.when.timetuple ()))
    event['summary'] = vText (u"%s, Imp: %s" % (norm_str (ev.title), news.val2imp (ev.importance)))
    event['description'] = vText ("Prev: %s\\, Fore: %s" % (norm_str (ev.pred), norm_str (ev.fore)))
    event['dtstamp'] = ev.when.strftime ("%Y%m%dT%H%M%SZ")
    event['dtstart'] = ev.when.strftime ("%Y%m%dT%H%M%SZ")
    event['dtend'] = (ev.when + datetime.timedelta (minutes = 10)).strftime ("%Y%m%dT%H%M%SZ")
    event['priority'] = 0
    cal.add_component (event)
    id += 1


print cal.as_string (),
