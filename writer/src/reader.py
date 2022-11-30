#!/root/app/env/bin/python3

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

config = {
  'user': 'app_username',
  'password': 'app_password',
  'host': 'localhost',
  'database': 'app_db',
  'raise_on_warnings': True,
  'port':'7000'
}

query = ("SELECT COUNT(*) FROM customers;")

api = Flask(__name__)

@api.route('/info', methods=['GET'])
def get_info():
  d = os.environ['HOME']
  return jsonify({'podname':d})

def start_api_server():
  api.run(debug=True, use_reloader=False, host='0.0.0.0', port=8080)

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
@REQUEST_TIME.time()
def start_data_reading():
  
  cnx = mysql.connector.connect(**config)
  cursor = cnx.cursor(buffered=True)
#  delay = randint(1,2)
#  sleep(delay) 

  try:
    cursor.execute(query)
    result = cursor.fetchall()
    return result
    print(f"There are {result[(0)]} row(s) in the table")
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
    cnx.close()

def main():
  check_db()
  
  start_http_server(8000)
  threading.Thread(target=start_api_server, daemon=True).start()
    
  while True:
    start_data_reading()
    sleep(1)

if __name__ == "__main__":
  main()

