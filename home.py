from flask import Flask, render_template, jsonify
import psycopg2
import json
app = Flask(__name__)

dbinfo = {}

with open('dbinfo.json') as db_file:
  dbinfo = json.load(db_file)

@app.route('/')
def index():
  return render_template("index.html")

@app.route('/latest')
def latest():
  dbconn = psycopg2.connect("dbname=" + dbinfo['dbname'] +
                             " user=" + dbinfo['username'] +
                             " password= " + dbinfo['password'] +
                             " host= " + dbinfo['host'] +
                             " port=" + dbinfo['port'])
  cursor = dbconn.cursor()
  cursor.execute("SELECT row_to_json(c) FROM currencyDeals c WHERE c.created > CURRENT_TIMESTAMP - interval '21 seconds';")
  result = cursor.fetchall()
  cursor.close()
  dbconn.close()
  return jsonify(result)

@app.route('/init')
def initfeed():
  dbconn = psycopg2.connect("dbname=" + dbinfo['dbname'] +
                             " user=" + dbinfo['username'] +
                             " password= " + dbinfo['password'] +
                             " host= " + dbinfo['host'] +
                             " port=" + dbinfo['port'])
  cursor = dbconn.cursor()
  cursor.execute("SELECT row_to_json(c) FROM currencyDeals c WHERE c.created > CURRENT_TIMESTAMP - interval '10 minutes';")
  result = cursor.fetchall()
  cursor.close()
  dbconn.close()
  return jsonify(result)

if __name__ == "__main__":
  app.run()