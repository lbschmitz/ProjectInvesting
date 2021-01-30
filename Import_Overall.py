
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
dboverall = None
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
if dboverall == None:
    sqlstuff = "INSERT INTO Overall (Date, BookValue, MarketValue, MarketPL) VALUES (%s,%s,%s,%s)"
    record1 = (d1, Bookvalue, MarketValue, PL)
    mycursor.execute(sqlstuff, record1)
    db.commit()
else: 
    print ("Daily Overall has been added already.")
#----/Check if record has been added
       
