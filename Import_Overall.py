
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
Totalforpercent = 0
Totalforpercent2 = 0  
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
            Totalforpercent2 = Totalforpercent2 + item['currentMarketValue']
            if ismorethanone >= 2 and item['openQuantity'] != checkitem['openQuantity']: #if to sum the doubles
                item
                placeitem = item.copy()
                placeitem['openQuantity'] = placeitem['openQuantity'] + checkitem['openQuantity']
                placeitem['totalCost'] = placeitem['totalCost'] + checkitem['totalCost']
                placeitem['averageEntryPrice'] = placeitem['totalCost'] / placeitem['openQuantity'] 
                placeitem['currentMarketValue'] = placeitem['currentMarketValue'] + checkitem['currentMarketValue']
                placeitem['openPnl'] = placeitem['openPnl'] + checkitem['openPnl']
                doubleadded = 'yes'
    print ("Total amount of money is 22222   ", Totalforpercent2)
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
        print("UPDATED DOUBLES", placeitem['symbol'], placeitem['openQuantity'], placeitem['totalCost'])
        Totalforpercent = Totalforpercent + placeitem['currentMarketValue']
    if ismorethanone >= 2 and doubleadded == 'no' or doubleadded == 'yes':
        print ("doubled and nothing happends")
    else:     
        sqlstuff = "UPDATE Positions SET Shares = %s, CostBasis =%s, CostperShare =%s, CurrentPrice =%s, MarketValue =%s, PLMarket =%s WHERE Ticker = %s"
        record1 = (item['openQuantity'], item['totalCost'], item['averageEntryPrice'], item['currentPrice'], item['currentMarketValue'], item['openPnl'], item['symbol'])
        mycursor.execute(sqlstuff, record1)
        db.commit()
        print("UPDATED SINGLES", item['symbol'], item['openQuantity'], item['totalCost'])
        Totalforpercent = Totalforpercent + item['currentMarketValue']


print ("this is the total market valeu", Totalforpercent)
#UPDATING CURRENT POSITIONS TABLE -----------end
#UPDATING OPERATIONS-----------------------------
import datetime
activities = []
today = date.today()
today = today.strftime("%Y-%m-%d")

for account in account_ids:
    print(account)
    activities = qtrade.get_account_activities(account, today, today) + activities

mycursor.execute("select * from Operations")
dbactivities = mycursor.fetchall()

i=1
for item in activities:
    opitem = 0
    dateitem = []
    dateitem = item['tradeDate']
    dateitem = datetime.datetime.strptime(dateitem, "%Y-%m-%dT%H:%M:%S.%f-05:00")
    dateitem = datetime.datetime.date(dateitem)
    for dbitem in dbactivities:
        netdbitem = dbitem[9]
        netdbitem = float(netdbitem)
        if item['netAmount'] == netdbitem and item['symbol'] == dbitem[3] and item['quantity'] == dbitem[5] and dateitem == dbitem[1]:
            opitem = 1
    if opitem == 0:
        print ("\n The symbol is", item['symbol'], "and the total amount is", item['netAmount'],"the quantity is", item['quantity'], "and number #", i, "and the date is:", dateitem)
        print ("Add to the database")
        sqlstuff = "INSERT INTO Operations (TransactionDate, Action, Symbol, Description, Quantity, Price, GrossAmount, Commission, NetAmount, Currency, ActivityType) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        record1 = (item['tradeDate'], item['action'], item['symbol'],item['description'],item['quantity'],item['price'],item['grossAmount'],item['commission'],item['netAmount'],item['currency'],item['type'])
        mycursor.execute(sqlstuff, record1)
        db.commit()
    i = i + 1
today = date.today()
today = today.strftime("%Y-%m-%d")