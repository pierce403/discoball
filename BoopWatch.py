import time
from web3 import Web3, HTTPProvider

abi = '''
[
	{
		"constant": false,
		"inputs": [
			{
				"name": "message",
				"type": "string"
			}
		],
		"name": "boop",
		"outputs": [],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"name": "message",
				"type": "string"
			}
		],
		"name": "BoopMsg",
		"type": "event"
	}
]
'''

contract_address = '0xBD838672f10E6b0950D3F28d847cebD4edB03834'

#web3 = Web3(HTTPProvider("https://mainnet.infura.io"))
#web3 = Web3(HTTPProvider("http://127.0.0.1:8545"))
web3 = Web3(Web3.WebsocketProvider("wss://mainnet.infura.io/ws"))

while web3.eth.syncing:
  print("syncing: "+str(web3.eth.syncing))
  time.sleep(10)

boop = web3.eth.contract(abi=abi, address=contract_address)

print("All synced up! Watching for Boops!")

#boops = web3.eth.filter('pending')
#boops = web3.eth.filter({"fromBlock":6293142 ,"address": contract_address})
boops = boop.events.BoopMsg.createFilter(fromBlock=6293142)

for event in boops.get_all_entries():
  #print("old : "+str(event))
  print("old : "+str(event['args']['message']))

for event in boops.get_new_entries():
  print("new : "+str(event['args']['messages']))



