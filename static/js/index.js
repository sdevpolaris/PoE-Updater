(function() {

  'use strict';

  var autoRefreshEnabled = false;

  function createDealTile(deal, list) {
    var _template = $('<div class="alert alert-success deal-row" role="alert"><div class="deal-info-section"><div id="league-note"></div><div id="equivalence"></div><div id="stock"></div><div id="charName"></div></div><input class="form-control purchase-msg-text" type="text" id="single-purchase-msg"><input class="form-control purchase-msg-text" type="text" id="stock-purchase-msg"></div>');
    $('#league-note', _template).html('League: ' + deal['league'] + ', Currency: ' + deal['currencyname'] + ', Note: ' + deal['note']);
    $('#equivalence', _template).html('Paying: ' + deal['askingamount'] + ' ' + deal['askingcurrency'] + ' (' + deal['askingequiv'] + 'c), Getting: ' + deal['offeringamount'] + ' ' + deal['currencyname'] + ' (' + deal['offeringequiv'] + 'c), Profit: ' + deal['profit'] + 'c');
    $('#stock', _template).html('Stock: ' + deal['stock'] + ' ' + deal['currencyname']);
    $('#charName', _template).html('Character Name: ' + deal['charname']);

    $('#single-purchase-msg', _template).val("@" + deal['charname'] + " Hi, I'd like to buy your " + deal['offeringamount'] + " " + deal['currencyname'] + " for my " + deal['askingamount'] + " " + deal['askingcurrency'] + " in " + deal['league'] + ".");
    $('#single-purchase-msg', _template).on("click", function() {
      $(this).select();
    });

    var multiplier = Math.floor(deal['stock'] / deal['offeringamount']);
    var multi_offeringamount = deal['offeringamount'] * multiplier;
    var multi_askingamount = deal['askingamount'] * multiplier;

    $('#stock-purchase-msg', _template).val("@" + deal['charname'] + " Hi, I'd like to buy your " + multi_offeringamount + " " + deal['currencyname'] + " for my " + multi_askingamount + " " + deal['askingcurrency'] + " in " + deal['league'] + ".");
    $('#stock-purchase-msg', _template).on("click", function() {
      $(this).select();
    });

    list.prepend(_template);
  }

  function reloadDealsList(result) {
    var dealsList = $('#deals-container');
    if (dealsList.children().length > 40) {
      dealsList.children().slice(-20).remove();
    }
    var deals = result;
    for (var i = 0; i < deals.length; i++) {
      var deal = deals[i][0]
      createDealTile(deal, dealsList);
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
    setTimeout(requestLatestAuto, 30000);
  }

  function requestInitFeed() {
    requestFeed('init');
    setTimeout(requestLatestAuto, 30000);
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