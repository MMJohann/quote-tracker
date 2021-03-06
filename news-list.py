#!/usr/bin/python

import os
import datetime
import time
import string

from tracker import utils
from tracker import news

from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


def norm_str (str, vis = 0):
    if vis == 0:
        if str == None:
            return "-"
        return str.strip ()
    else:
        if str == None:
            return ""
        return str.strip ()



class NewsPage (webapp.RequestHandler):
    def get (self):
        d_from = utils.parseIsoDate (self.request.get ("from"))
        if d_from == None:
            d_from = datetime.date.today ()
        d_to = utils.parseIsoDate (self.request.get ("to"))
        if d_to == None:
            d_to = d_from + datetime.timedelta (days = 7)
        q = db.GqlQuery ("select * from News_Record_v2 where when > :1 and when < :2 order by when", d_from, d_to)
        if self.request.get ("csv"):
            self.response.headers['Content-Type'] = 'text/plain; charset=cp1251'
            self.response.out.write ("timestamp,importance,title,curr,prev,fore\n")
            for ev in q:
                self.response.out.write (("%d,%s,%s,%s,%s,%s\n" % (time.mktime (ev.when.timetuple ()),
                                                                            ev.importance, norm_str (ev.title),
                                                                            norm_str (ev.curr),
                                                                            norm_str (ev.pred), norm_str (ev.fore))))
        else:
            res = []
            index = 1
            for ev in q:
                ev.index = index
                ev.imp = news.val2imp (ev.importance)
                ev.date = ev.when.date ().isoformat ()
                ev.time = ev.when.time ().isoformat ()
                ev.title = norm_str (ev.title, 1)
                ev.pred =  norm_str (ev.pred, 1)
                ev.fore =  norm_str (ev.fore, 1)
                ev.curr =  norm_str (ev.curr, 1)
                index = index + 1
                res.append (ev)
            path = os.path.join (os.path.dirname (__file__), "tmpl/news-list.html")

            ub_day = (d_from - datetime.timedelta (days = 7)).isoformat ()
            lb_day = (d_from - datetime.timedelta (days = 1)).isoformat ()           
            back_url = "/news?from=%s&to=%s" % (ub_day, lb_day)

            ub_day = (d_to + datetime.timedelta (days = 1)).isoformat ()
            lb_day = (d_to + datetime.timedelta (days = 7)).isoformat ()           
            forward_url = "/news?from=%s&to=%s" % (ub_day, lb_day)
            self.response.out.write (template.render (path, { "news" : res,
                                                              "back" : back_url,
                                                              "forward" : forward_url}))

app = webapp.WSGIApplication ([('/news', NewsPage)], debug=True)

def main ():
    run_wsgi_app (app)

if __name__ == "__main__":
    main ()
