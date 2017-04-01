(function() {

  'use strict';

  var autoRefreshEnabled = false;

  var notifySound = document.getElementById('notifySound');

  function createItemDealTile(deal, list) {
    var _template = $('#itemDealTile').clone();
    _template.removeAttr('id');
    _template.removeClass('hidden');
    $('#league-note', _template).html('League: ' + deal['league'] + ', Character Name: ' + deal['charname']);
    $('#item', _template).html(deal['itemname']);
    $('#mods', _template).html(deal['mods']);
    $('#price', _template).html('Price: ' + deal['askingprice'] + ' , Market: ' + deal['avgprice'] + ' , Profit: ' + deal['profit']);
    $('#stock', _template).html('Stacksize: ' + deal['stock']);

    $('#single-purchase-msg', _template).val('@' + deal['charname'] + ' Hi, I would like to buy your ' + deal['itemname'] + ' for ' + Math.floor(deal['askingprice']) + ' chaos in ' + deal['league'] + ' (stash tab "' + deal['stashname'] + '"; position: left ' + deal['x'] + ', top ' + deal['y'] + ')');
    $('#single-purchase-msg', _template).on("click", function() {
      $(this).select();
      document.execCommand('copy');
    });

    $('#closeDeal', _template).on('click', function() {
      _template.remove();
    });

    list.prepend(_template);
  }

  function createCurrencyDealTile(deal, list) {
    var _template = $('#currencyDealTile').clone();
    _template.removeAttr('id');
    _template.removeClass('hidden');
    $('#league-note', _template).html('League: ' + deal['league'] + ', Currency: ' + deal['currencyname'] + ', Note: ' + deal['note']);
    $('#equivalence', _template).html('Paying: ' + deal['askingamount'] + ' ' + deal['askingcurrency'] + ' (' + deal['askingequiv'] + 'c), Getting: ' + deal['offeringamount'] + ' ' + deal['currencyname'] + ' (' + deal['offeringequiv'] + 'c), Profit: ' + deal['profit'] + 'c');
    $('#stock', _template).html('Stock: ' + deal['stock'] + ' ' + deal['currencyname']);
    $('#charName', _template).html('Character Name: ' + deal['charname']);

    $('#single-purchase-msg', _template).val("@" + deal['charname'] + " Hi, I'd like to buy your " + deal['offeringamount'] + " " + deal['currencyname'] + " for my " + deal['askingamount'] + " " + deal['askingcurrency'] + " in " + deal['league'] + ".");
    $('#single-purchase-msg', _template).on("click", function() {
      $(this).select();
      document.execCommand('copy');
    });

    var multiplier = Math.floor(deal['stock'] / deal['offeringamount']);
    var multi_offeringamount = deal['offeringamount'] * multiplier;
    var multi_askingamount = deal['askingamount'] * multiplier;

    $('#stock-purchase-msg', _template).val("@" + deal['charname'] + " Hi, I'd like to buy your " + multi_offeringamount + " " + deal['currencyname'] + " for my " + multi_askingamount + " " + deal['askingcurrency'] + " in " + deal['league'] + ".");
    $('#stock-purchase-msg', _template).on("click", function() {
      $(this).select();
      document.execCommand('copy');
    });

    $('#closeDeal', _template).on('click', function() {
      _template.remove();
    });

    list.prepend(_template);
  }

  function reloadDealsList(result) {
    var dealsList = $('#deals-container');
    if (dealsList.children().length > 40) {
      dealsList.children().slice(-20).remove();
    }

    var currencyDeals = result['currencies'];
    var itemDeals = result['items'];

    if (currencyDeals.length > 0 || itemDeals.length > 0) {
      notifySound.play();
      var separator = $('<hr />');
      dealsList.prepend(separator);
    }

    for (var i = 0; i < currencyDeals.length; i++) {
      var deal = currencyDeals[i][0]
      createCurrencyDealTile(deal, dealsList);
    }

    for (var j = 0; j < itemDeals.length; j++) {
      var deal = itemDeals[j][0]
      createItemDealTile(deal, dealsList);
    }

    $('#refresh-spinner').addClass('hidden');
  }

  function requestFeed(type) {
    $.ajax({
      url: '/' + type,
      success: function(data) {
        reloadDealsList(data);
      }
    });
    $('#refresh-spinner').removeClass('hidden');
  }

  function requestLatestAuto() {
    if (autoRefreshEnabled) {
      requestFeed('latest');
    }
    setTimeout(requestLatestAuto, 20000);
  }

  function requestInitFeed() {
    requestFeed('init');
    setTimeout(requestLatestAuto, 20000);
  }

  $('#refresh').click(function() {
    requestFeed('latest');
  });

  $('#auto-refresh').click(function() {
    if (autoRefreshEnabled) {
      $('#auto-refresh').html('Enable Auto Refresh');
    } else {
      $('#auto-refresh').html('Disable Auto Refresh');
    }
    autoRefreshEnabled = !autoRefreshEnabled;
  });

  requestInitFeed();
  
})();