
import json
from datetime import date
from qtrade import Questrade
from decimal import Decimal
from forex_python.converter import CurrencyRates
import mysql.connector
from mysql.connector import Error
import config 

#---connect to questrade
qtrade = Questrade(token_yaml='/home/ec2-user/token.yaml')
qtrade.refresh_access_token(from_yaml=True)
account_ids = qtrade.get_account_id()
positions = []
#---/connect to questrade

#----Connect to DB
db = mysql.connector.connect(
    host=config.DATABASE_CONFIG['host'],
    user=config.DATABASE_CONFIG['user'],
    passwd=config.DATABASE_CONFIG['password'],
    database=config.DATABASE_CONFIG['database']
)
mycursor = db.cursor()
#----/Connect to DB

#----Get info from Questrade

for account in account_ids:
    print(account)
    temp = qtrade.get_account_positions(account_id=account)
    positions = positions + temp 
#----/Get info from Questrade

#---------------------getday
today = date.today()
d1 = today.strftime("%Y-%m-%d")
#---------------------import sql

#----get latest date from DB
dboverall = []
sqlstuff = ("SELECT * FROM Overall "
         "WHERE Date = %s and BookValue >= %s")
d2 = 0
record1 = (d1, d2)
mycursor.execute(sqlstuff, record1)
dboverall = mycursor.fetchall()
#----------------------

#----Get Overal info
c = CurrencyRates()
Bookvalue = 0
MarketValue = 0
substring = '.TO'
for item in positions:
    if substring in item["symbol"]:
        Bookvalue = Bookvalue + item["totalCost"] 
        MarketValue = MarketValue + item["currentMarketValue"]
    else:
        Bookvalue = c.convert('USD', 'CAD', item['currentMarketValue']) + Bookvalue
        MarketValue = c.convert('USD', 'CAD', item['currentMarketValue']) + MarketValue

PL = MarketValue - Bookvalue
#----/Get Overal info
#----Check if record has been added
if not dboverall:
    sqlstuff = "INSERT INTO Overall (Date, BookValue, MarketValue, MarketPL) VALUES (%s,%s,%s,%s)"
    record1 = (d1, Bookvalue, MarketValue, PL)
    mycursor.execute(sqlstuff, record1)
    db.commit()
else: 
    print ("Daily Overall has been added already.")
#----/Check if record has been added


#UPDATING CURRENT POSITIONS TABLE
#----Search current positions table
mycursor.execute("select * from Positions")
dbpositions = mycursor.fetchall()
for item in dbpositions:
    item[0]       
#----/Search current positions table
for item in positions: 
    test = item['symbol']
    inthetable = 'no' #placeholder to see if a new stock has been added
    ismorethanone = 0
    doubleadded = 'no'
    for checkitem in positions: #Check if I have the same security in more than one account
        if item['symbol'] == checkitem['symbol']:
            ismorethanone = ismorethanone + 1
            doubleadded = 'no'
            if ismorethanone >= 2 and item['openQuantity'] != checkitem['openQuantity']: #if to sum the doubles
                item
                placeitem = item.copy()
                placeitem['openQuantity'] = placeitem['openQuantity'] + checkitem['openQuantity']
                placeitem['totalCost'] = placeitem['totalCost'] + checkitem['totalCost']
                placeitem['averageEntryPrice'] = placeitem['totalCost'] / placeitem['openQuantity'] 
                placeitem['currentMarketValue'] = placeitem['currentMarketValue'] + checkitem['currentMarketValue']
                placeitem['openPnl'] = placeitem['openPnl'] + checkitem['openPnl']
                doubleadded = 'yes'
    for dbitem in dbpositions:
        test2 = dbitem[0]
        if test == test2:
            #print("Found")
            inthetable = 'yes'
    if inthetable == 'no': #in case the stock is new!
        print("This stock", item['symbol'], "isn't on the table, we need to add")
        sqlstuff = "INSERT INTO Positions (Ticker, Shares) VALUES (%s,%s)"
        record1 = (item['symbol'], item['openQuantity'])
        mycursor.execute(sqlstuff, record1)
        db.commit()
        if inthetable != 'yes':
            print("This stock", item['symbol'], "wasn't on the tabel, so we added!")
    #print (item['symbol'], "has showed up", ismorethanone)
    #print (item['symbol'], doubleadded)
    #input()
    if ismorethanone >= 2 and doubleadded == 'yes':
        sqlstuff = "UPDATE Positions SET Shares = %s, CostBasis =%s, CostperShare =%s, CurrentPrice =%s, MarketValue =%s, PLMarket =%s WHERE Ticker = %s"
        record1 = (placeitem['openQuantity'], placeitem['totalCost'], placeitem['averageEntryPrice'], placeitem['currentPrice'], placeitem['currentMarketValue'], placeitem['openPnl'], placeitem['symbol'])
        mycursor.execute(sqlstuff, record1)
        db.commit()
        print("UPDATED DOUBLES", placeitem['openQuantity'], placeitem['totalCost'])
    if ismorethanone >= 2 and doubleadded == 'no' or doubleadded == 'yes':
        print ("doubled and nothing happends")
    else:     
        sqlstuff = "UPDATE Positions SET Shares = %s, CostBasis =%s, CostperShare =%s, CurrentPrice =%s, MarketValue =%s, PLMarket =%s WHERE Ticker = %s"
        record1 = (item['openQuantity'], item['totalCost'], item['averageEntryPrice'], item['currentPrice'], item['currentMarketValue'], item['openPnl'], item['symbol'])
        mycursor.execute(sqlstuff, record1)
        db.commit()
        print("UPDATED SINGLES", item['openQuantity'], item['totalCost'])

#UPDATING CURRENT POSITIONS TABLE -----------end


