
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

#---------------------getdaytoda
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
MarketPLPercent = (PL * 100) / Bookvalue
print ("Bookvalue", Bookvalue)
print ("PL", PL)
print ("MarketPL", MarketPLPercent)
#----/Get Overal info
#----Check if record has been added
if not dboverall:
    sqlstuff = "INSERT INTO Overall (Date, BookValue, MarketValue, MarketPL, MarketPLPercent) VALUES (%s,%s,%s,%s,%s)"
    record1 = (d1, Bookvalue, MarketValue, PL, MarketPLPercent)
    mycursor.execute(sqlstuff, record1)
    db.commit()
else: 
    print ("Daily Overall has been added already. so we updated!")
    sqlstuff = "UPDATE Overall SET BookValue = %s, MarketValue = %s, MarketPL = %s, MarketPLPercent = %s  WHERE Date = %s"
    record1 = (Bookvalue, MarketValue, PL, MarketPLPercent, d1)
    mycursor.execute(sqlstuff, record1)
    db.commit()
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
    divcalc = 0
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
            dbitem[0]
            dbitem[9]
            divcalc = dbitem[9]
            if not divcalc:
                print("If not divcalc")
            else:
                divcalc = float(divcalc)
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
        if substring in item["symbol"]: #CHECK IF STOCK IS CAD/USD
            bookcad = placeitem['totalCost'] 
            marketcad = placeitem['currentMarketValue'] 
        else:
            bookcad = c.convert('USD', 'CAD', placeitem['totalCost'])
            marketcad = c.convert('USD', 'CAD', placeitem['currentMarketValue'])
        itempercent = marketcad * 100 /MarketValue
        plpercent = ((divcalc+placeitem['openPnl']) * 100) / placeitem['totalCost']
        print ("percentage is", itempercent)
        print ("prince in cad is", marketcad)
        print("UPDATED DOUBLES", placeitem['symbol'], placeitem['openQuantity'], placeitem['totalCost'])
        sqlstuff = "UPDATE Positions SET Shares = %s, CostBasis =%s, CostperShare =%s, CurrentPrice =%s, MarketValue =%s, PLMarket =%s, PLPercentage = %s, TotalPercentage = %s, BookCad = %s, MarketCad = %s WHERE Ticker = %s"
        record1 = (placeitem['openQuantity'], placeitem['totalCost'], placeitem['averageEntryPrice'], placeitem['currentPrice'], placeitem['currentMarketValue'], placeitem['openPnl'], plpercent, itempercent, bookcad, marketcad, placeitem['symbol'])
        mycursor.execute(sqlstuff, record1)
        db.commit()
    if ismorethanone >= 2 and doubleadded == 'no' or doubleadded == 'yes':
        print ("doubled and nothing happends")
    else:     
        if substring in item["symbol"]:
            bookcad = item['totalCost'] 
            marketcad = item['currentMarketValue'] 
        else:
            bookcad = c.convert('USD', 'CAD', item['totalCost'])
            marketcad = c.convert('USD', 'CAD', item['currentMarketValue'])
        itempercent = marketcad * 100 /MarketValue
        if not divcalc:
            print("If not divcalc")
        else:
            plpercent = ((divcalc+item['openPnl']) * 100) / item['totalCost']
            print ("percentage is", itempercent)
            print ("prince in cad is", marketcad)
            sqlstuff = "UPDATE Positions SET Shares = %s, CostBasis =%s, CostperShare =%s, CurrentPrice =%s, MarketValue =%s, PLMarket =%s, PLPercentage = %s, TotalPercentage = %s, BookCad = %s, MarketCad = %s  WHERE Ticker = %s"
            record1 = (item['openQuantity'], item['totalCost'], item['averageEntryPrice'], item['currentPrice'], item['currentMarketValue'], item['openPnl'], plpercent, itempercent, bookcad, marketcad, item['symbol'])
            mycursor.execute(sqlstuff, record1)
            db.commit()
            print("UPDATED SINGLES", item['symbol'], item['openQuantity'], item['totalCost'])
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
        ne 
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
#------------------------------------------------------
#--------Check Dividends and import them
currentpositions = []
sqlstuff = ("SELECT Ticker FROM Positions") #SELECT TO CHECK HOW MANY SECURITIES I HAVE 
mycursor.execute(sqlstuff)
currentpositions = mycursor.fetchall()
for positionitem in currentpositions: #FOR TO SEARCH HOW MANY DIVIDENDS PER SHARE WITH THE N MARK
    currentdiv = 0
    sqloperations = ("SELECT TransactionID, Symbol, NetAmount FROM Operations "
    "where Symbol = %s and InPositions = %s and ActivityType = %s")
    Ticker = positionitem[0]
    InDB = 'N'
    Dividends = 'Dividends'
    record1 = (Ticker, InDB, Dividends)
    mycursor.execute(sqloperations, record1)
    divlist = mycursor.fetchall()
    #divlist
    for divitem in divlist:
        #print ("The stock symbol is", divitem[0], "and the total amount of money paid is", divitem[1])
        sqlpositions = ("select Ticker, DividendIncome from Positions "
        "where Ticker = %s") 
        Ticker = divitem[1]
        record1 = Ticker, 
        mycursor.execute(sqlpositions, record1)
        divposi = mycursor.fetchall()
        divposi = divposi[0]
        divposi = divposi[1]
        print ("Total of dividends received by", divitem[1], "is", divposi, "and adding", divitem[2])
        currentdiv = divposi + divitem[2]
        sqlstuff = "UPDATE Positions SET DividendIncome = %s  WHERE Ticker = %s"
        record1 = (currentdiv, divitem[1])
        mycursor.execute(sqlstuff, record1)
        db.commit()
        print ("Transaction ID", divitem[0], "Ticker", divitem[1], "Amount", divitem[2], "has been marked as ADDED")
        sqlstuff = "UPDATE Operations SET InPositions = %s  WHERE Symbol = %s"
        inposition = 'Y'
        record1 = (inposition, divitem[1])
        mycursor.execute(sqlstuff, record1)
        db.commit()
#--------Check Dividends and import them end
#--------Snapshots!
import datetime
today = date.today()
today = today.strftime("%Y-%m-%d")
sqloperations = ("SELECT * from Positions")
mycursor.execute(sqloperations)
positions = mycursor.fetchall()
for item in positions:
    snaps = []
    item[0]
    item[14]
    sqlstuff = ("SELECT id, Ticker FROM snapshots "
        "WHERE Date = %s and Ticker = %s")
    record1 = (today, item[0])
    mycursor.execute(sqlstuff, record1)
    snaps = mycursor.fetchall()
    snaps
    if not snaps:
        print("I should insert")
        sqlstuff = "INSERT INTO snapshots (Date,Ticker,Shares,CostBasis,CostperShare,CurrentPrice,MarketValue,PLMarket,DividendIncome,PLTotal,PLPercentage,TotalPercentage,BookCad,MarketCad,MarketDividends,DividendCad,PLCad) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        record1 = (today, item[0], item[3], item[4],item[5],item[6],item[7],item[8],item[9],item[10],item[11],item[12],item[13],item[14],item[15],item[16],item[17])
        mycursor.execute(sqlstuff, record1)
        db.commit()
    else: 
        print("I should update")
        sqlstuff = "UPDATE snapshots SET Shares=%s,CostBasis=%s,CostperShare=%s,CurrentPrice=%s,MarketValue=%s,PLMarket=%s,DividendIncome=%s,PLTotal=%s,PLPercentage=%s,TotalPercentage=%s,BookCad=%s,MarketCad=%s,MarketDividends=%s,DividendCad=%s,PLCad=%s WHERE Date = %s and Ticker = %s"
        record1 = (item[3], item[4],item[5],item[6],item[7],item[8],item[9],item[10],item[11],item[12],item[13],item[14],item[15],item[16],item[17], today, item[0])
        mycursor.execute(sqlstuff, record1)
        db.commit()
        

