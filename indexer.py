import json
import time
import gzip
import urllib2
import psycopg2
from StringIO import StringIO

class Indexer:
  def __init__(self):

    # Read config file

    with open('config.json') as config_file:
      configs = json.load(config_file)
      self.apiUrl = configs['apiUrl']
      self.changeId = configs['changeId']
      self.league = configs['league']
      self.threshold = configs['threshold']
      self.delay = configs['delay']

    # Read predefined market rates for currency (Sell values)

    with open('currency_rates.json') as rates_file:
      self.currency_rates = json.load(rates_file)

    # Read predefined currency names

    with open('currency_names.json') as names_file:
      self.currency_names = json.load(names_file)

    # Read database info
    with open('dbinfo.json') as db_file:
      self.dbinfo = json.load(db_file)

    self.deals = []

  def createBlankStock(self):
    stock = {}
    for key in self.currency_names:
      stock[self.currency_names[key]] = 0
    return stock

  def storeDeals(self):
    dbconn = psycopg2.connect("dbname=" + self.dbinfo['dbname'] +
                             " user=" + self.dbinfo['username'] +
                             " password= " + self.dbinfo['password'] +
                             " host= " + self.dbinfo['host'] +
                             " port=" + self.dbinfo['port'])

    cursor = dbconn.cursor()
    for deal in self.deals:
      cursor.execute("""INSERT INTO currencyDeals (league, charName, currencyName, offeringAmount, askingCurrency, askingAmount, offeringEquiv, askingEquiv, profit, stock, note)
                  VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                  (deal['league'],
                   deal['charName'],
                   deal['currencyName'],
                   deal['offeringAmount'],
                   deal['askingCurrency'],
                   deal['askingAmount'],
                   deal['offeringEquiv'],
                   deal['askingEquiv'],
                   deal['profit'],
                   deal['stock'],
                   deal['note']))

    dbconn.commit()
    cursor.close()
    dbconn.close()


  def processStashes(self, stashes):
    for stash in stashes:
      if stash['public']:
        items = stash['items']

        # For each separate stash we need a stock object to keep count of every currency type

        stock = self.createBlankStock()

        for item in items:

          # Only match items belonging to the specified league

          if item['league'] == self.league:

            # typeLine is the displaying name of the item, in this case the currency's official name in-game

            typeLine = item['typeLine']
            if typeLine in self.currency_names:
              currencyName = self.currency_names[typeLine]
              stock[currencyName] += item['stackSize']
              if 'note' in item:
                notes = item['note'].split(' ')

                # Only care about buyouts or fixed priced items

                if len(notes) == 3 and (notes[0] == '~b/o' or notes[0] == '~price'):
                  values = notes[1].split('/')

                  # First value is the amount of currency buyer needs to give, second value is the amount of currency seller needs to sell off
                  # If there is no second value, then it means seller is only selling one of the currency type

                  if len(values) == 1:
                    values.append(1)
                  askingCurrency = notes[2]
                  if askingCurrency in self.currency_rates:

                    # Convert all currencies to chaos equivalent amounts

                    askingChaosEquiv = self.currency_rates[askingCurrency] * float(values[0])
                    offeringChaosEquiv = self.currency_rates[currencyName] * float(values[1])
                    if offeringChaosEquiv > askingChaosEquiv:
                      print ''
                      print ''
                      print "Currency selling: " + currencyName + '    Note: ' + item['note']
                      print ' I pay: ' + str(askingChaosEquiv) + " and it's worth: " + str(offeringChaosEquiv) + '   profit: ' + str(offeringChaosEquiv - askingChaosEquiv)
                      print '@' + stash['lastCharacterName'] + " Hi, I'd like to buy your " + str(values[1]) + ' ' + currencyName + ' for my ' + str(values[0]) + ' ' + askingCurrency + ' in ' + self.league
                      new_deal = {}
                      new_deal['league'] = self.league
                      new_deal['charName'] = stash['lastCharacterName']
                      new_deal['currencyName'] = currencyName
                      new_deal['offeringAmount'] = values[1]
                      new_deal['askingCurrency'] = askingCurrency
                      new_deal['askingAmount'] = values[0]
                      new_deal['offeringEquiv'] = offeringChaosEquiv
                      new_deal['askingEquiv'] = askingChaosEquiv
                      new_deal['profit'] = offeringChaosEquiv - askingChaosEquiv
                      new_deal['stock'] = 1
                      new_deal['note'] = item['note']
                      self.deals.append(new_deal)

  def index(self):
    while True:
      apiUrlModified = self.apiUrl if self.changeId == None else self.apiUrl + '?id=' + self.changeId
      print apiUrlModified
      request = urllib2.Request(apiUrlModified)
      request.add_header('Accept-encoding', 'gzip')
      resp = urllib2.urlopen(request)
      status = resp.getcode()
      if status == 200 and resp.info().get('Content-Encoding') == 'gzip':
        buf = StringIO(resp.read())
        f = gzip.GzipFile(fileobj=buf)
        data = f.read()

        stashJson = json.loads(data)
        if 'next_change_id' in stashJson:
          self.changeId = stashJson['next_change_id']
        if 'stashes' in stashJson:  
          stashes = stashJson['stashes']
          self.processStashes(stashes)
      else:
        print "Connection failed. Retrying"

      if len(self.deals) > 0:
        self.storeDeals()
      self.deals = []
      print "Ended session"
      time.sleep(self.delay)

instance = Indexer()
instance.index()