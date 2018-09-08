import time
from web3 import Web3, HTTPProvider

abi = '''
[
	{
		"constant": false,
		"inputs": [
			{
				"name": "target",
				"type": "uint256"
			}
		],
		"name": "bump",
		"outputs": [],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": false,
		"inputs": [
			{
				"name": "hash",
				"type": "string"
			},
			{
				"name": "description",
				"type": "string"
			}
		],
		"name": "insert",
		"outputs": [],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": false,
		"inputs": [
			{
				"name": "target",
				"type": "uint256"
			}
		],
		"name": "stomp",
		"outputs": [],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"name": "publisher",
				"type": "address"
			},
			{
				"indexed": false,
				"name": "hash",
				"type": "string"
			},
			{
				"indexed": false,
				"name": "description",
				"type": "string"
			},
			{
				"indexed": false,
				"name": "count",
				"type": "uint256"
			}
		],
		"name": "DiscoMsg",
		"type": "event"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "discoData",
		"outputs": [
			{
				"name": "",
				"type": "address"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	}
]
'''

contract_address = '0x1Ca0eb599d249e1930BD6DE0A55E39Adc1C132b5'

import requests

def pin_stuff(hash):
	#http://127.0.0.1:5001/api/v0/ls/QmSV87hzPYKxo8Go7A2JCsfCVXPqV8poovGk9tFrVJmdNr
    try:
      lscheck = requests.get('http://127.0.0.1:5001/api/v0/pin/add/'+hash,timeout=10)
      print("pinned "+hash)
    except:
      print("failed to pin "+hash)


#web3 = Web3(HTTPProvider("https://mainnet.infura.io"))
#web3 = Web3(HTTPProvider("http://127.0.0.1:8545"))
web3 = Web3(Web3.WebsocketProvider("wss://mainnet.infura.io/ws"))

while web3.eth.syncing:
  print("syncing: "+str(web3.eth.syncing))
  time.sleep(10)

discoBall = web3.eth.contract(abi=abi, address=contract_address)

# data_address = discoBall.discoData;
# discoData = web3.eth.contract(abi=abi, address=contract_address)
#
# print("number of hashes so far: "+str(DiscoData.count()))
#
# for x in range(0,discoData.count()):
#
#
# print("All synced up! Watching for Boops!")

#boops = web3.eth.filter('pending')
#boops = web3.eth.filter({"fromBlock":6293142 ,"address": contract_address})
boops = discoBall.events.DiscoMsg.createFilter(fromBlock=6293142)

for event in boops.get_all_entries():
  #print("old : "+str(event))
  print("old : "+str(event['args']['hash']+" "+event['args']['description']))
  pin_stuff(event['args']['hash'])

while True:
  for event in boops.get_new_entries():
    print("new : "+str(event['args']['hash']+" "+event['args']['description']))
    pin_stuff(event['args']['hash'])
