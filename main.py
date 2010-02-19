#!/usr/bin/env python
#-*- coding:utf-8 -*-

#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from BeautifulSoup import BeautifulSoup
import etrsoup
import hashlib

class Orarend(db.Model):
    title = db.StringProperty()
    html = db.TextProperty()
    icalendar = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    preview = db.TextProperty()
    bugzik = db.BooleanProperty()
    megjegyzes = db.TextProperty()


class DebugView(webapp.RequestHandler):
  def get(self):
    if not self.request.get("i"):
      azorarendek = Orarend.all()
      self.response.out.write("<table>")
      for azorarend in azorarendek:
	self.response.out.write("""
	<tr><td>""" + str(azorarend.key()) + """</td><td>""" + unicode(azorarend.title) + """</td><td>""" + str(azorarend.bugzik) + """</td></tr>
	""" )
      self.response.out.write("</table>")

    else:
      key = self.request.get("i")
      orarend = db.get(key)
      tempvaltozo = BeautifulSoup(orarend.html)
      gomoku = etrsoup.beolvas(tempvaltozo, gomoku=True)
      template_values = {"title": orarend.title, "preview": orarend.preview, "key": key, "megjegyzes": orarend.megjegyzes, "gomoku": gomoku}
      path = os.path.join(os.path.dirname(__file__), 'templates/debug.html')
      self.response.out.write(template.render(path, template_values))
  def post(self):
    resetgomb = self.request.get("resetgomb")
    if resetgomb:
      key = self.request.get("i")
      orarend = db.get(key)
      path = os.path.join(os.path.dirname(__file__), 'templates/preview.html')
#      self.response.out.write("key")
      soup = BeautifulSoup(orarend.html)
      bla = etrsoup.beolvas(soup)
      template_values = {"ical": bla[1]}
      orarend.icalendar = db.Text(etrsoup.orarender(bla)[0], encoding="utf-8")
      orarend.preview = db.Text(template.render(path, template_values), encoding="utf-8")
      orarend.put()
      self.redirect("/debug?i="+str(key))



class TagSoup(webapp.RequestHandler):
  def get(self):
    key = self.request.get("i")
    orarend = db.get(key)
    self.response.headers['Content-Type'] = "text/html; charset=UTF-8"
    self.response.out.write(orarend.html)


class TextCalendar(webapp.RequestHandler):
  def get(self):
    key = self.request.get("i")
    orarend = db.get(key)
    self.response.headers['Content-Type'] = "text/calendar; charset=UTF-8"
    self.response.headers['Content-Disposition'] = 'attachment; filename="orarend-2009-2010-2.ics"'
    self.response.out.write(orarend.icalendar)

class HibaHandler(webapp.RequestHandler):
  def get(self):
    key = self.request.get("i")
    orarend = db.get(key)
    template_values = {"message": "Sajnálom, hogy nem sikerült tökéletesre a feldolgozás, de tök örülök, hogy segítesz megtalálni a hiba okát. A lenti dobozba kérlek írd le, hogy is kéne kinéznie az órarendednek az ETR alapján!", "title": orarend.title, "preview": orarend.preview, "key": key, "megjegyzes": orarend.megjegyzes}
    path = os.path.join(os.path.dirname(__file__), 'templates/hibajelento.html')
    self.response.out.write(template.render(path, template_values))
  def post(self):
    key = self.request.get("i")
    orarend = db.get(key)
    orarend.bugzik = True
    orarend.megjegyzes = db.Text(self.request.get("megjegyzes"))
    orarend.put()
    
    template_values = {"message": "<b>Köszönöm, meg fogom nézni mi nem stimmel</b>. Ha gondolod, itt módosíthatod az üzeneted.", "title": orarend.title, "preview": orarend.preview, "key": key, "megjegyzes": orarend.megjegyzes}
    path = os.path.join(os.path.dirname(__file__), 'templates/hibajelento.html')
    self.response.out.write(template.render(path, template_values))

class CheckHandler(webapp.RequestHandler):
  def get(self):
    key = self.request.get("i")
    result = db.get(key)  

    template_values = {"title": result.title, "preview": result.preview, "key": key}
    path = os.path.join(os.path.dirname(__file__), 'templates/feldolgozott.html')
    self.response.out.write(template.render(path, template_values))        

class MainHandler(webapp.RequestHandler):
  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    try:
      fajl = self.request.get("etrfile")
      soup = BeautifulSoup(fajl)
      bla = etrsoup.beolvas(soup)
      
      path = os.path.join(os.path.dirname(__file__), 'templates/preview.html')
      template_values = {"ical": bla[1]}
      orarend = Orarend()
      orarend.title = db.Text(bla[0])
      orarend.html = db.Text(fajl, encoding="iso-8859-2")
      orarend.icalendar = db.Text(etrsoup.orarender(bla)[0], encoding="utf-8")
      orarend.preview = db.Text(template.render(path, template_values), encoding="utf-8")
      orarend.put()
      key = orarend.key()
      
      self.redirect("/check?i="+str(key))
    except AttributeError:
      self.response.clear()
      self.response.set_status(400)
      self.response.out.write("Szerintem rossz fájlt küldtél át. Legalábbis ebben nem látom az órarendet. <a href='/'>Próbáld újra, ok?</a>")
  
#    template_values = {"title": bla[0], "ical": bla[1]}
#    path = os.path.join(os.path.dirname(__file__), 'templates/feldolgozott.html')
#    self.response.out.write(template.render(path, template_values))    
#    self.response.headers['Content-Type'] = "text/calendar"
#    self.response.out.write(etrsoup.orarender(bla)[0])

def main():
  application = webapp.WSGIApplication([('/', MainHandler), 
                                       ('/check', CheckHandler),
                                       ('/cal', TextCalendar),
                                       ('/hiba', HibaHandler),
                                       ('/tagsoup', TagSoup),
                                       ('/debug', DebugView),],
                                       debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
