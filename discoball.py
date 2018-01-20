from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'discoball.db'
db = SQLAlchemy(app)

class Bribe(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  end_date = db.Column(db.Integer, primary_key=True)
  address = db.Column(db.String(50), nullable=False)
  ipfs = db.Column(db.String(50), nullable=False)
  ipfs_size = db.Column(db.String(50), nullable=False)

  rate # updated when new payouts come in 

class Node(db.Model)
  node_id  = db.Column(db.String(50), nullable=False)
  eth_addr = db.Column(db.String(50), nullable=False)

@app.route('/')
def hello_world():
  return 'Hello, World!'
    
@app.route('/bribe')
def bribe():

# cron get bump tx to destination, read data
# list bumps
# pay out registered nodes
