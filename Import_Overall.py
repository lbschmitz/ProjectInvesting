import json
from datetime import date
from qtrade import Questrade
from decimal import Decimal
from forex_python.converter import CurrencyRates
import mysql.connector
from mysql.connector import Error
qtrade = Questrade(token_yaml='/home/ec2-user/token.yaml')
qtrade.refresh_access_token(from_yaml=True)
account_ids = qtrade.get_account_id()
positions = []


for account in account_ids:
    print(account)
    temp = qtrade.get_account_positions(account_id=account)
    positions = positions + temp 