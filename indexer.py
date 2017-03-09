import json
import time
import gzip
import urllib2
import psycopg2
import datetime
from StringIO import StringIO

DEBUG = False

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

  def dealExists(self, cursor, deal):
    cursor.execute("SELECT * from currencyDeals where charName = %s and currencyName = %s and stock = %s and note = %s",
      (deal['charName'], deal['currencyName'], deal['stock'], deal['note']))
    return cursor.fetchone() is not None

  def storeDeals(self):
    dbconn = psycopg2.connect("dbname=" + self.dbinfo['dbname'] +
                             " user=" + self.dbinfo['username'] +
                             " password= " + self.dbinfo['password'] +
                             " host= " + self.dbinfo['host'] +
                             " port=" + self.dbinfo['port'])

    cursor = dbconn.cursor()
    for deal in self.deals:
      if not self.dealExists(cursor, deal):
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

  def removeOldDeals(self):
    dbconn = psycopg2.connect("dbname=" + self.dbinfo['dbname'] +
                             " user=" + self.dbinfo['username'] +
                             " password= " + self.dbinfo['password'] +
                             " host= " + self.dbinfo['host'] +
                             " port=" + self.dbinfo['port'])

    cursor = dbconn.cursor()

    # Remove all rows in the table that were created more than 30 minutes ago
    cursor.execute("DELETE FROM currencyDeals c WHERE created < CURRENT_TIMESTAMP - interval '30 minutes';")
    dbconn.commit()
    cursor.close()
    dbconn.close()

  def processStashes(self, stashes):
    for stash in stashes:
      if stash['public']:
        items = stash['items']

        # For each separate stash we need a stock object to keep count of every currency type

        stock = self.createBlankStock()
        deals = []

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

                    # Ignore any false deals, aka asking for 0 currencies

                    if int(values[0]) == 0:
                      continue
                    values.append(1)
                  askingCurrency = notes[2]
                  if askingCurrency in self.currency_rates:

                    # Convert all currencies to chaos equivalent amounts

                    askingChaosEquiv = self.currency_rates[askingCurrency] * float(values[0])
                    offeringChaosEquiv = self.currency_rates[currencyName] * float(values[1])
                    if (offeringChaosEquiv > askingChaosEquiv) and (offeringChaosEquiv - askingChaosEquiv > self.threshold):

                      if DEBUG:
                        print ''
                        print ''
                        print "Currency selling: " + currencyName + '    Note: ' + item['note']
                        print ' I pay: ' + str(askingChaosEquiv) + " and it's worth: " + str(offeringChaosEquiv) + '   profit: ' + str(offeringChaosEquiv - askingChaosEquiv)
                        print ' stock: ' + str(stock[currencyName])
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
                      new_deal['stock'] = stock[currencyName]
                      new_deal['note'] = item['note']
                      deals.append(new_deal)

        for deal in deals:
          deal['stock'] = stock[deal['currencyName']]
        self.deals = self.deals + deals

  def index(self):
    lastCleanoffTime = datetime.datetime.now()
    while True:
      currentTime = datetime.datetime.now()
      timeDiff = currentTime - lastCleanoffTime

      # Every 1800 seconds or 30 minutes we would like to purge old currency deals

      if timeDiff.total_seconds() > 1800:
        self.removeOldDeals()
        lastCleanoffTime = datetime.datetime.now()
        print "Purged entries at : " + str(lastCleanoffTime)

      apiUrlModified = self.apiUrl if self.changeId == None else self.apiUrl + '?id=' + self.changeId
      if DEBUG:
        print "Request: " + apiUrlModified
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
      time.sleep(self.delay)

instance = Indexer()
instance.index()