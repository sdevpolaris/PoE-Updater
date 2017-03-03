(function() {

  'use strict';

  var autoRefreshEnabled = true;

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

    var multiplier = deal['stock'] / deal['offeringamount'];
    var multi_offeringamount = deal['offeringamount'] * multiplier;
    var multi_askingamount = deal['askingamount'] * multiplier;

    $('#stock-purchase-msg', _template).val("@" + deal['charname'] + " Hi, I'd like to buy your " + multi_offeringamount + " " + deal['currencyname'] + " for my " + multi_askingamount + " " + deal['askingcurrency'] + " in " + deal['league'] + ".");
    $('#stock-purchase-msg', _template).on("click", function() {
      $(this).select();
    });

    list.append(_template);
  }

  function reloadDealsList(result) {
    var dealsList = $('#deals-container');
    dealsList.empty();
    var deals = result;
    for (var i = 0; i < deals.length; i++) {
      var deal = deals[i][0]
      createDealTile(deal, dealsList);
    }
    if (deals.length === 0) {
      dealsList.html("There doesn't seem to be anything here...");
    }
  }

  function requestLatest() {
    $.ajax({
      url: '/latest',
      success: function(data) {
        reloadDealsList(data);
      }
    });
  }

  function requestLatestAuto() {
    if (autoRefreshEnabled) {
      requestLatest();
    }
    setTimeout(requestLatestAuto, 10000);
  }

  $('#refresh').click(function() {
    requestLatest();
  });

  $('#auto-refresh').click(function() {
    if (autoRefreshEnabled) {
      $('#auto-refresh').html('Enable Auto Refresh');
    } else {
      $('#auto-refresh').html('Disable Auto Refresh');
    }
    autoRefreshEnabled = !autoRefreshEnabled;
  });

  requestLatestAuto();
  
})();