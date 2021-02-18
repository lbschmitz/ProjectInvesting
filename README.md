# ProjectInvesting
 AWS_Python_MySQL

- Goals

-Create a data history value and return of a stock portfolio at Questrade

-Monitor daily dividends 

-Converting currencies


Environment:
App layer: EC2(t2.micro) instance
Data layer: RDS MySQL 

Using the brokerage API site to authenticate and getting current possions and value
CRON Job running a python script to colect, parse and insert data into a MySQL database

Using grafana to create a dashboard

Things to be improved:
-hourly update on Overall table
-Create horly update on Snapshots
-Add "N" to dividend table
-Improve Dividend Track per month
