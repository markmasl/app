from faker import Faker

from random import randint
from time import sleep
from datetime import date, datetime, timedelta

import mysql.connector
from mysql.connector import errorcode

from prometheus_client import start_http_server, Summary
import time

from flask import Flask, jsonify
import threading

import socket
import os

import logging
import logging.config

from src.utils.file_utils import initialize_logging, initialize_properties

DB_NAME = 'app_db'

TABLES = {}
TABLES['customers'] = (
    "CREATE TABLE `customers` ("
    "  `emp_id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `name` varchar(30) NOT NULL,"
    "  `address` varchar(120) NOT NULL,"
    "  `from_date` date NOT NULL,"
    "  PRIMARY KEY (`emp_id`)"
    ") ENGINE=InnoDB")

add_customer = ("INSERT INTO customers "
               "(name, address, from_date) "
               "VALUES (%s, %s, %s)")

fake = Faker()

"""
Initialize api server, set info path
"""
api = Flask(__name__)

@api.route('/info', methods=['GET'])
def get_info():
  p = os.environ.get('MY_POD_NAME', 'defaultvalue')
  return jsonify({ 'podname': p})

def start_api_server():
  api.run(debug=True, use_reloader=False, host='0.0.0.0', port=8080)

"""
Measure processing time
"""
REQUEST_TIME = Summary('data_producing_seconds', 'Time spent for data producing and commiting to database')
@REQUEST_TIME.time()
def start_data_producing(config):
  """
  Generate random data
  """
  uname    = fake.name()
  uaddress = fake.address()
  delivery_date = datetime.now().date() + timedelta(days=10)
  data_customer = (uname, uaddress, delivery_date)
  
  logging.info(f"Generated name is {uname} ")
  logging.info(f"Generated address is {uaddress} ")
  logging.info(f"Generated delivery date is {delivery_date}")
  """
  Commit data to db
  """
  try:
    cnx = mysql.connector.connect(**config)
  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      logging.error("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      logging.error("Database does not exist")  
    else:
      logging.error(err)
  else:
    try:
      cursor = cnx.cursor()
      logging.info(f"Commiting data {uname}, {uaddress}, {delivery_date} to database")
      cursor.execute(add_customer,data_customer)
      cnx.commit()
    except mysql.connector.Error as err:
      logging.error(err.msg)
    else:
      cursor.close()
      cnx.close()

def create_tables_db(config):
  """
  Create table
  """
  cnx = mysql.connector.connect(**config)
  cursor = cnx.cursor()
  
  for table_name in TABLES:
    table_description = TABLES[table_name]
    try:
        logging.info("Creating table {}: ".format(table_name))
        cursor.execute(table_description)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            logging.info("Table already exists.")
        else:
            logging.info(err.msg)
    else:
        logging.info("OK")
  cursor.close()
  cnx.close()

def main():
  
  initialize_logging()
  properties = initialize_properties()
  """
  Configure settings
  """
  server_api_port = properties.get('server',{}).get('api_port','8080')
  server_exporter_port = properties.get('server',{}).get('exporter_port','9000')

  mysql_host = properties.get('mysql',{}).get('host','localhost')
  mysql_user = properties.get('mysql',{}).get('user','app_username')
  mysql_password = properties.get('mysql',{}).get('password','app_password')
  mysql_db = properties.get('mysql',{}).get('database','app_db')
  mysql_port = properties.get('mysql',{}).get('port','7000')

  config = {
  'user': mysql_user,
  'password': mysql_password,
  'host': mysql_host,
  'database': mysql_db,
  'raise_on_warnings': True,
  'port': mysql_port
  }

  create_tables_db(config)
  
  start_http_server(server_exporter_port)
  threading.Thread(target=start_api_server, daemon=True).start()

  while True:
    start_data_producing(config)
    sleep(1)

if __name__ == "__main__":
  main()
