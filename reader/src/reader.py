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

query = ("SELECT COUNT(*) FROM customers;")

"""
Initialize api server, set info path
"""
api = Flask(__name__)

@api.route('/info', methods=['GET'])
def get_info():
  p = os.environ['MY_POD_NAME','defaultname']
  return jsonify({'podname':p})
#  return jsonify({'podname':p, 'rowsintable':r})

def start_api_server():
  api.run(debug=True, use_reloader=False, host='0.0.0.0', port=8080)

REQUEST_TIME = Summary('data_reading_seconds', 'Time spent for quering data in database')
@REQUEST_TIME.time()
def start_data_reading(config):
  """
  Connecting to db and running query
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
      cursor.execute(query)
      result = cursor.fetchall()
      logging.info(f"There are {result[(0)]} row(s) in the table")
    except mysql.connector.Error as err:
      logging.info(err.msg)
    else:
      cursor.close()
      cnx.close()
      return result

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

  start_http_server(server_exporter_port)
  threading.Thread(target=start_api_server, daemon=True).start()
    
  while True:
    start_data_reading(config)
    sleep(1)

if __name__ == "__main__":
  main()

