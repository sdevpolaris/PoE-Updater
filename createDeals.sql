CREATE TABLE currencyDeals (
  league varchar(30),
  charName varchar(100),
  currencyName varchar(30),
  offeringAmount float(10),
  askingCurrency varchar(30),
  askingAmount float(10),
  offeringEquiv float(10),
  askingEquiv float(10),
  profit float(10),
  stock int,
  note varchar(100),
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);