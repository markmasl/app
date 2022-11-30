#!/root/app/env/bin/python3

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

from src.utils.file_utils import initialize_logging, initialize_properties, get_os_variable


config = {
  'user': 'app_username',
  'password': 'app_password',
  'host': 'localhost',
  'database': 'app_db',
  'raise_on_warnings': True,
  'port':'7000'
}

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

#info = [f'{"name": {socket.gethostname()} }, {"id": 2, "name": "Company Two"}']

api = Flask(__name__)

@api.route('/info', methods=['GET'])
def get_info():
  d = os.environ['HOME']
  return jsonify({'podname':d})

def start_api_server():
  api.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)


REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
@REQUEST_TIME.time()
def start_data_producing():
  uname    = fake.name()
  uaddress = fake.address()
  delivery_date = datetime.now().date() + timedelta(days=10)
  data_customer = (uname, uaddress, delivery_date)
  
  print(f"The name is {uname} ")
  print(f"The address is {uaddress} ")
  print(f"The delivery date is {delivery_date}")

  cnx = mysql.connector.connect(**config)
  cursor = cnx.cursor()
  
  try:
    cursor.execute(add_customer,data_customer)
    cnx.commit()
  except mysql.connector.Error as err:
    print(err.msg)
  else:
    cursor.close()
    cnx.close()

def check_db():
  try:
    cnx = mysql.connector.connect(**config)
  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      print("Database does not exist")
    else:
      print(err)
  else:
    create_tables_db()

def create_tables_db():
  cnx = mysql.connector.connect(**config)
  cursor = cnx.cursor()
  
  for table_name in TABLES:
    table_description = TABLES[table_name]
    try:
        print("Creating table {}: ".format(table_name), end='')
        cursor.execute(table_description)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("already exists.")
        else:
            print(err.msg)
    else:
        print("OK")
  cursor.close()
  cnx.close()

def main():
  check_db()
  create_tables_db()
  
  start_http_server(8000)
  threading.Thread(target=start_api_server, daemon=True).start()

  while True:
    start_data_producing()
    sleep(1)

if __name__ == "__main__":
  main()

