import json
import time
import gzip
import urllib2
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


  def createBlankStock(self):
    stock = {}
    for key in self.currency_names:
      stock[self.currency_names[key]] = 0
    return stock

  def processStashes(self, stashes):
    for stash in stashes:
      if stash['public']:
        items = stash['items']
        stock = self.createBlankStock()
        for item in items:
          if item['league'] == self.league:
            typeLine = item['typeLine']
            if typeLine in self.currency_names:
              currencyName = self.currency_names[typeLine]
              stock[currencyName] += item['stackSize']
              if 'note' in item:
                notes = item['note'].split(' ')
                if len(notes) == 3 and (notes[0] == '~b/o' or notes[0] == '~price'):
                  values = notes[1].split('/')
                  if len(values) == 1:
                    values.append(1)
                  askingCurrency = notes[2]
                  if askingCurrency in self.currency_rates:
                    askingChaosEquiv = self.currency_rates[askingCurrency] * float(values[0])
                    offeringChaosEquiv = self.currency_rates[currencyName] * float(values[1])
                    if offeringChaosEquiv > askingChaosEquiv:
                      print ''
                      print ''
                      print "Currency selling: " + currencyName + '    Note: ' + item['note']
                      print ' I pay: ' + str(askingChaosEquiv) + " and it's worth: " + str(offeringChaosEquiv) + '   profit: ' + str(offeringChaosEquiv - askingChaosEquiv)
                      print '@' + stash['lastCharacterName'] + " Hi, I'd like to buy your " + str(values[1]) + ' ' + currencyName + ' for my ' + str(values[0]) + ' ' + askingCurrency + ' in ' + self.league

        # print stock

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

      print "Ended session"
      time.sleep(self.delay)

instance = Indexer()
instance.index()




