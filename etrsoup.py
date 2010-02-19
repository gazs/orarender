#!/usr/bin/env python
#-*- coding:utf-8 -*-


from BeautifulSoup import BeautifulSoup
from datetime import datetime
from icalendar import UTC, Calendar, Event, vRecur





felev_eleje = datetime(2010,2,8,8,0,0,tzinfo=UTC) #feb 8 2010. hétfő
felev_vege = datetime(2010,5,14,0,10,0,tzinfo=UTC) #május 14 2010. péntek


ahetnapjai = ["fixme", "mo", "tu", "we", "th", "fr"]

def beolvas(soup, gomoku=False):
  title = soup.h3.contents[0]
  orarend = soup.body.p.table.tbody.tr.td.table.tbody.contents
  napoz = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
  orak = []
  import logging
  negyzetracs = ""
  for sor in orarend[1:]:
    napok = range(0,6)
    napok[0] = sor.tt.string
    ervenyes_napoz = napoz.copy()
    for egyora in sor("font"):
      oszlop = sor.contents.index(egyora.parent) # 1-5: 1: hétfő 5: péntek
      if len(sor) < 6: # csúszás van érvényben
        csusztass = 0
        for nullaigvisszaszamol in range(oszlop+1):
          if ervenyes_napoz[nullaigvisszaszamol]: csusztass += 1
        oszlop = oszlop + csusztass
      if oszlop > 5: print "5+!"; oszlop = 5
      try:
        napoz[oszlop] = int(egyora.parent['rowspan'])
      except KeyError:
        napoz[oszlop] = 1
      orak.append({
        "nap": ahetnapjai[oszlop], 
        "ido": egyora.contents[0], 
        "hely": egyora.contents[2], 
        "kurzus": egyora.contents[4]})
      # sárga, ugyanakkor kezdődő kurzusokhoz
      # nem így kéne, hanem valahogy úgy, hogy len(egyora)//5 <- sorok száma, len(egyora)%5 <- emiatt hányat kell csúsztatni.
      try:
	orak.append({
          "nap": ahetnapjai[oszlop],
          "ido": egyora.contents[6],
          "hely": egyora.contents[8],
          "kurzus": egyora.contents[10]})
      except IndexError:
        pass
    # este és reggel, következő sor: csökkentsük mindegyik csúszását
    if gomoku:
      if sor("font"):
        negyzetracs += "<b>"
      negyzetracs += str(napok[0]) + " " + str(napoz[1]) + " " + str(napoz[2]) + " " + str(napoz[3]) + " " + str(napoz[4]) + " " + str(napoz[5]) + " # " + str(len(sor)) + "<br>"
      if sor("font"):
        negyzetracs += "</b>"
    for nap, csuszas in napoz.iteritems():
      if csuszas > 0: napoz[nap] = csuszas-1
  if gomoku:
    return negyzetracs
  if not gomoku:
    return title, orak

def orarender(beolvasott):
  cal = Calendar()
  cal.add('version', '2.0')
  cal.add('prodid', '-//Orarender//bergengocia.net//')
  cal['summary'] = beolvasott[0]
  cal['X-WR-CALNAME'] = beolvasott[0]
  print beolvasott[1]
  for ora in beolvasott[1]:
    cal.add_component(kurzusize(ora['nap'], idopontize(ora['ido']), ora['hely'], ora['kurzus']))
#  import tempfile, os
#  directory = tempfile.mkdtemp()
#  f = open('/home/gazs/Desktop/orarend.ics', 'wb')
#  f.write(cal.as_string())
#  f.close()
  return cal.as_string(), beolvasott


def idopontize(nyers):
  darabos = [int (y) for x in nyers.split("-") for y in x.split(":")]
  return darabos

def kurzusize(nap, darabos, hely, kurzus):
  event = Event()
  event.add('summary', kurzus)
  # 0: vasárnap, hogy könnyen tudjuk felpakolni az első hétre az eseményeket.
  # darabos óra + 1? időzóna, my friend. utc-ben dolgozunk, mert különben kéne időzónát gyártani,
  # viszont errefelé utc+1/utc+2 van. szerencsére nem kavar be a márciusvégi időszámítás-váltás,
  # a hozzáadáskori időzónához igazodik a kliens, ha jól nézem.
  hozzaadando= ahetnapjai.index(nap)
  event.add('dtstart', datetime(2010,2,7+hozzaadando,darabos[0]-1,darabos[1],0,tzinfo=UTC))
  event.add('dtend', datetime(2010,2,7+hozzaadando,darabos[2]-1,darabos[3],0,tzinfo=UTC))
  event.add('dtstamp', datetime(2010,1,29,0,10,0,tzinfo=UTC)) # "mikor adták hozzá vagy módosították az eseményt". lényegtelen, de kell.
  event.add('location', hely)
  recur = vRecur(freq='weekly', byday=nap, count=15) # kézzel számoltam, vigyázz!
  event.add('rrule', recur)
  return event


