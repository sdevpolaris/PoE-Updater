CREATE TABLE currencyDeals (
  league varchar,
  charName varchar,
  currencyName varchar,
  offeringAmount float(10),
  askingCurrency varchar,
  askingAmount float(10),
  offeringEquiv float(10),
  askingEquiv float(10),
  profit float(10),
  stock int,
  note varchar,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE itemDeals (
  league varchar,
  charName varchar,
  itemName varchar,
  mods varchar,
  askingPrice float(10),
  avgPrice float(10),
  profit float(10),
  stock int,
  note varchar,
  stashName varchar,
  x int,
  y int,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);