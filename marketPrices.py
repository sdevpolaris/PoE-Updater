import json
import time
import urllib2
import datetime

class ItemList:

  def __init__(self):
    with open('config.json') as config_file:
      configs = json.load(config_file)
      self.ninjaRatesPropheciesUrl = configs['ninjaRatesProphecies']
      self.ninjaRatesDivCardsUrl = configs['ninjaRatesDivCards']
      self.ninjaRatesUniqueMapsUrl = configs['ninjaRatesUniqueMaps']
      self.ninjaRatesMapsUrl = configs['ninjaRatesMaps']
      self.ninjaRatesUniqueJewelsUrl = configs['ninjaRatesUniqueJewels']

  def retrieveRates(self, ratesUrl, itemList, date):
    ratesUrlModified = ratesUrl + date if not (date == None) else ratesUrl
    print ratesUrlModified
    request = urllib2.Request(ratesUrlModified)
    resp = urllib2.urlopen(request)
    status = resp.getcode()
    if status == 200:
      ratesJson = json.load(resp)
      for line in ratesJson['lines']:

        # Only care about items with 2.0 or higher chaos market price

        if line['chaosValue'] > 2.0:
          itemName = line['name']
          itemList[itemName] = line['chaosValue']

  # Retrieve a dict of all wanted items and their market average prices

  def getAllItems(self):
    itemList = {}
    currentDate = time.strftime('%Y-%m-%d', time.gmtime())
    self.retrieveRates(self.ninjaRatesPropheciesUrl, itemList, currentDate)
    self.retrieveRates(self.ninjaRatesDivCardsUrl, itemList, currentDate)
    self.retrieveRates(self.ninjaRatesUniqueMapsUrl, itemList, None)
    self.retrieveRates(self.ninjaRatesMapsUrl, itemList, currentDate)
    self.retrieveRates(self.ninjaRatesUniqueJewelsUrl, itemList, None)
    return itemList