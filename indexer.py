import json
import time
import gzip
import urllib2
import psycopg2
import datetime
import math
from StringIO import StringIO
from marketPrices import ItemList

def isfloat(values):
  try:
    for value in values:
      float(value)
    return True
  except ValueError:
    return False

class Indexer:
  def __init__(self):

    # Read config file

    with open('config.json') as config_file:
      configs = json.load(config_file)
      self.apiUrl = configs['apiUrl']
      self.changeId = None
      self.ninjaApiUrl = configs['ninjaApiUrl']
      self.ninjaRatesUrl = configs['ninjaRatesUrl']
      self.league = configs['league']
      self.threshold = configs['threshold']
      self.delay = configs['delay']

    # Read predefined market rates for currency (Sell values)

    with open('currency_rates.json') as rates_file:
      self.currency_rates = json.load(rates_file)

    # Read predefined currency names

    with open('currency_names.json') as names_file:
      self.currency_names = json.load(names_file)

    # Read predefined leaguestone rates

    with open('leaguestones.json') as stones_file:
      self.leaguestones = json.load(stones_file)

    # Read database info
    with open('dbinfo.json') as db_file:
      self.dbinfo = json.load(db_file)

    self.deals = []
    self.itemDeals = []

    # Request for the latest rates

    self.itemList = ItemList()
    self.updateWithNinjaRates()

    # Update rates that have shared keys

    self.updateSharedCurrencyRates()

    # Request for the latest changeId from poe.ninja

    request = urllib2.Request(self.ninjaApiUrl)
    resp = urllib2.urlopen(request)
    status = resp.getcode()
    if status == 200:
      ninjaJson = json.load(resp)
      self.changeId = ninjaJson['nextChangeId']
      print "ChangeId received from poe.ninja: " + self.changeId

      # Start indexing

      self.index()

  def updateSharedCurrencyRates(self):
    sharedPerandus = ['coins', 'shekel', 'perandus']
    for shared in sharedPerandus:
      self.currency_rates[shared] = self.currency_rates['coin']

  def updateWithNinjaRates(self):

    self.itemPrices = self.itemList.getAllItems()
    self.itemPrices.update(self.leaguestones)

    self.currentDate = time.strftime('%Y-%m-%d', time.gmtime())
    ratesUrlModified = self.ninjaRatesUrl + self.currentDate
    request = urllib2.Request(ratesUrlModified)
    resp = urllib2.urlopen(request)
    status = resp.getcode()
    if status == 200:
      ratesJson = json.load(resp)
      for line in ratesJson['lines']:
        currencyTypeName = line['currencyTypeName']
        if (currencyTypeName in self.currency_names) and line['receive']:
          self.currency_rates[self.currency_names[currencyTypeName]] = line['receive']['value']
      print "Updated currency rates with poe.ninja at: " + str(datetime.datetime.now())

  def createBlankStock(self):
    stock = {}
    for key in self.currency_names:
      stock[self.currency_names[key]] = 0
    return stock

  def dealExists(self, cursor, deal):
    cursor.execute("SELECT * from currencyDeals where charName = %s and currencyName = %s and stock = %s and note = %s",
      (deal['charName'], deal['currencyName'], deal['stock'], deal['note']))
    return cursor.fetchone() is not None

  def itemDealExists(self, cursor, deal):
    cursor.execute("SELECT * from itemDeals where charName = %s and itemName = %s and stashName = %s and x = %s and y = %s",
      (deal['charName'], deal['itemName'], deal['stashName'], deal['x'], deal['y']))
    return cursor.fetchone() is not None

  def storeDeals(self):
    if len(self.deals) == 0 and len(self.itemDeals) == 0:
      return

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

    for deal in self.itemDeals:
      if not self.itemDealExists(cursor, deal):
        cursor.execute("""INSERT INTO itemDeals (league, charName, itemName, mods, askingPrice, avgPrice, profit, stock, note, stashName, x, y)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                    (deal['league'],
                     deal['charName'],
                     deal['itemName'],
                     deal['mods'],
                     deal['askingPrice'],
                     deal['avgPrice'],
                     deal['profit'],
                     deal['stock'],
                     deal['note'],
                     deal['stashName'],
                     deal['x'],
                     deal['y']))

    dbconn.commit()
    cursor.close()
    dbconn.close()
    self.deals = []
    self.itemDeals = []

  def removeOldDeals(self):
    dbconn = psycopg2.connect("dbname=" + self.dbinfo['dbname'] +
                             " user=" + self.dbinfo['username'] +
                             " password= " + self.dbinfo['password'] +
                             " host= " + self.dbinfo['host'] +
                             " port=" + self.dbinfo['port'])

    cursor = dbconn.cursor()

    # Remove all rows in the table that were created more than 30 minutes ago
    cursor.execute("DELETE FROM currencyDeals c WHERE created < CURRENT_TIMESTAMP - interval '30 minutes';")
    cursor.execute("DELETE FROM itemDeals c WHERE created < CURRENT_TIMESTAMP - interval '30 minutes';")
    dbconn.commit()
    cursor.close()
    dbconn.close()

  # Returns the listed price of an item, returns 0.0 if no prices are listed

  def getItemPrice(self, item, stash):
    askingPrice = 0.0

    # First check stash global buyout price

    stashTokens = stash['stash'].split(' ')

    if len(stashTokens) == 3 and (stashTokens[0] == '~b/o' or stashTokens[0] == '~price') and stashTokens[2] == 'chaos':
      amount = stashTokens[1]

      if not isfloat(amount):
        return askingPrice

      askingPrice = float(amount)

    # Second check item buyout price. If it exists it will overwrite stash buyout

    if 'note' in item:
      notes = item['note'].split(' ')

      if len(notes) == 3 and (notes[0] == '~b/o' or notes[0] == '~price') and notes[2] == 'chaos':
        amount = notes[1]

        if not isfloat(amount):
          return askingPrice

        askingPrice = float(amount)

    return askingPrice

  def processItem(self, typeLine, extended, stash, item, itemDeals):
    typeLineTokens = typeLine.split(' ')
    if 'Leaguestone' in typeLineTokens:
      typeIndex = typeLineTokens.index('Leaguestone')
      typeLine = typeLineTokens[typeIndex - 1] + ' ' + 'Leaguestone'

    if typeLine in self.itemPrices:
      askingPrice = self.getItemPrice(item, stash)

      if askingPrice == 0.0:
        return

      # Modifying properties so that placeholder %x strings are replaced with actual values

      modifiedProperties = []
      if 'properties' in item:
        for prop in item['properties']:

          # If the leaguestones have these mods, skip them

          if prop['name'].startswith('Can only be used in Areas with Monster Level') and prop['name'].endswith('or below'):
            return
          if prop['name'].startswith('Can only be used in Areas with Monster Level between'):
            return

          propString = ''
          if 'values' in prop and len(prop['values']) > 0:

            # If there is only one property and the value cannot be placed in a placeholder, simply append value to the end

            if not ('%' in prop['name']) and len(prop['values']) == 1:
              propString = prop['name'] + ': ' + prop['values'][0][0]
            else:
              nameTokens = prop['name'].split(' ')
              modTokens = []
              index = 0
              for token in nameTokens:
                if token.startswith('%'):
                  modTokens.append(prop['values'][index][0])
                  index += 1
                else:
                  modTokens.append(token)
              propString = ' '.join(modTokens)
          else:
            propString = prop['name']
          modifiedProperties.append(propString)

      # Mod object will contain all modifiers information on the item

      mods = {}
      mods['implicitMods'] = item['implicitMods'] if 'implicitMods' in item else []
      mods['properties'] = modifiedProperties
      mods['explicitMods'] = item['explicitMods'] if 'explicitMods' in item else []
      mods['prophecyText'] = item['prophecyText'] if 'prophecyText' in item else ''
      mods['prophecyDiffText'] = item['prophecyDiffText'] if 'prophecyDiffText' in item else ''

      askingPrice = float(askingPrice)
      avgPrice = self.itemPrices[typeLine]

      # For leaguestones we want to buy at average price, for other items we want a better margin

      if (askingPrice <= avgPrice and 'Leaguestone' in typeLine) or (askingPrice < avgPrice and avgPrice - askingPrice >= 1.0):
        finalName = ' '.join(typeLineTokens)
        new_deal = {}
        new_deal['league'] = self.league
        new_deal['charName'] = stash['lastCharacterName']
        new_deal['itemName'] = finalName if extended == None else finalName + ' ' + extended
        new_deal['mods'] = json.dumps(mods)
        new_deal['askingPrice'] = askingPrice
        new_deal['avgPrice'] = avgPrice
        new_deal['profit'] = avgPrice - askingPrice
        new_deal['stock'] = item['stackSize'] if 'stackSize' in item else 1
        new_deal['note'] = item['note'] if 'note' in item else ''
        new_deal['stashName'] = stash['stash']
        new_deal['x'] = item['x'] + 1
        new_deal['y'] = item['y'] + 1
        self.itemDeals.append(new_deal)

  def processStashes(self, stashes):
    for stash in stashes:
      if stash['public']:
        items = stash['items']

        # For each separate stash we need a stock object to keep count of every currency type

        stock = self.createBlankStock()
        deals = []
        itemDeals = []

        for item in items:

          # Only match items belonging to the specified league and not corrupted

          if item['league'] == self.league and not item['corrupted']:

            # typeLine is the displaying name of the item, in this case the currency's official name in-game

            typeLine = item['typeLine']
            itemName = item['name']

            # Remove the added string in typeLine if it exists
            typeLinePrefix = '<<set:MS>><<set:M>><<set:S>>'
            if typeLine.startswith(typeLinePrefix) and len(itemName) == 0:
              typeLine = typeLine[len(typeLinePrefix):]
              self.processItem(typeLine, None, stash, item, itemDeals)
            if len(itemName) > 0:
              if itemName.startswith(typeLinePrefix):
                itemName = itemName[len(typeLinePrefix):]
              self.processItem(itemName, typeLine, stash, item, itemDeals)

            if typeLine in self.currency_names:
              currencyName = self.currency_names[typeLine]

              # Some items do not have a stack size, default to 1

              stackSize = 1
              if item['stackSize']:
                stackSize = item['stackSize']
              stock[currencyName] += stackSize
              if 'note' in item:
                notes = item['note'].split(' ')

                # Only care about buyouts or fixed priced items

                if len(notes) == 3 and (notes[0] == '~b/o' or notes[0] == '~price'):
                  values = notes[1].split('/')

                  if not isfloat(values):
                    continue

                  # First value is the amount of currency buyer needs to give, second value is the amount of currency seller needs to sell off
                  # If there is no second value, then it means seller is only selling one of the currency type

                  if len(values) == 1:

                    # Ignore any false deals, aka asking for 0 currencies

                    if float(values[0]) == 0.0:
                      continue
                    values.append(1)
                  askingCurrency = notes[2]
                  if askingCurrency in self.currency_rates:

                    # Convert all currencies to chaos equivalent amounts

                    askingChaosEquiv = self.currency_rates[askingCurrency] * float(values[0])
                    offeringChaosEquiv = self.currency_rates[currencyName] * float(values[1])

                    if (offeringChaosEquiv > askingChaosEquiv) and (offeringChaosEquiv - askingChaosEquiv >= self.threshold):
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
    print "Indexing beginning at: " + str(lastCleanoffTime)
    while True:
      currentTime = datetime.datetime.now()
      timeDiff = currentTime - lastCleanoffTime

      # Every 1800 seconds or 30 minutes we would like to purge old currency deals and update rates from poe.ninja

      if timeDiff.total_seconds() > 1800:
        self.removeOldDeals()
        lastCleanoffTime = datetime.datetime.now()
        print "Purged entries at : " + str(lastCleanoffTime)
        self.updateWithNinjaRates()

      apiUrlModified = self.apiUrl if self.changeId == None else self.apiUrl + '?id=' + self.changeId
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

      # Store deals that were found in the current batch of stash tab data
      self.storeDeals()

      time.sleep(self.delay)

instance = Indexer()