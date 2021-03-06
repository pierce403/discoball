// DiscoBall ABI
const discoBallABI = [{
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

const discoDataABI=[
	{
		"constant": true,
		"inputs": [],
		"name": "count",
		"outputs": [
			{
				"name": "",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "view",
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
		"outputs": [
			{
				"name": "",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [
			{
				"name": "",
				"type": "uint256"
			}
		],
		"name": "scores",
		"outputs": [
			{
				"name": "",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "view",
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
		"constant": true,
		"inputs": [
			{
				"name": "",
				"type": "uint256"
			}
		],
		"name": "hashes",
		"outputs": [
			{
				"name": "",
				"type": "string"
			}
		],
		"payable": false,
		"stateMutability": "view",
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
		"name": "bump",
		"outputs": [],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [
			{
				"name": "",
				"type": "uint256"
			}
		],
		"name": "descriptions",
		"outputs": [
			{
				"name": "",
				"type": "string"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [
			{
				"name": "",
				"type": "uint256"
			}
		],
		"name": "publishers",
		"outputs": [
			{
				"name": "",
				"type": "address"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "constructor"
	}
]

console.log("this is strange");

try {
  console.log("HI! your default account is " + web3.eth.defaultAccount);
} catch (e) {
  $("#msg").html("The distributed web requires the <b>MetaMask</b> browser extension. Please go install it now.");
  console.log("o no..")
}

web3.version.getNetwork((err, netId) => {
  if (netId != 1) {
    $("#netwarn").html("Please switch MetaMask to the <b>MainNet</b> network.")
  }
})

if (!web3.eth.defaultAccount) {
  //$("#msg").html("Please unlock MetaMask");
} else {
  web3.eth.getBalance(web3.eth.defaultAccount, function(error, result) {
    console.log(result)
    console.log(result.c[0] + " " + result.c[1]);

    // print balance:
    balance = result.c[0] / 10000;
    console.log("balance is " + balance);

    if (balance === 0) {
      $("#msg").html("Looks like you could use some ETH.");
    }
  })
}

const address = '0x1ca0eb599d249e1930bd6de0a55e39adc1c132b5'; // yay mainnet

//alert('come on now');

// creation of contract object
var DiscoBall = web3.eth.contract(discoBallABI);
var DiscoData = web3.eth.contract(discoDataABI);

// initiate contract for an address
var discoBall = DiscoBall.at(address);
var discoData;
console.log("discoBall is "+discoBall);

discoTable = document.getElementById("discoTable");

discoBall.discoData(function (err, result) {
  console.log(err, result);
  discoData = DiscoData.at(result);
  console.log("discoData is "+discoData)
  discoData.count(function (err, result){
    console.log("count is "+result);
    let count = result;
    for(let x=0;x<count;++x)
    {
	    let row=discoTable.insertRow(-1);
	    row.insertCell().innerText=x;
	    row.insertCell().innerText="";
	    row.insertCell().innerText="";
	    row.insertCell().innerText="";
    }
	  
    for(let x=0;x<count;++x)
    {
	    discoData.hashes(x,function(err,res){
		    console.log(x+": "+res);
		    if(res=="")return;
		    discoTable.rows[x+1].cells[1].innerText=res;
	    });
	    
	    discoData.descriptions(x,function(err,res){
		    console.log(x+": "+res);
		    if(res=="")return;
		    discoTable.rows[x+1].cells[2].innerText=res;
	    });
	    
	    discoData.publishers(x,function(err,res){
		    console.log(x+": "+res);
		    if(res=="0x0000000000000000000000000000000000000000")return;
		    discoTable.rows[x+1].cells[3].innerText=res;
	    });	    
    }
  });
});

function insert() {
  console.log("insert called!")

  let ipfshash = $("#ipfshash").val();
  let description = $("#description").val();

  var result = discoBall.insert(ipfshash, description, function(err, res) {
    console.log(res);
  });

  console.log("update result:");
  console.log(result);
  $('#update-modal').modal('hide');
}
