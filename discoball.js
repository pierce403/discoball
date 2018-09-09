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
  if (netId != 3) {
    $("#netwarn").html("Please switch MetaMask to the <b>Ropsten</b> network.")
  }
})

if (!web3.eth.defaultAccount) {
  $("#msg").html("Please unlock MetaMask");
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

discoBall.discoData(function (err, result) {
  console.log(err, result);
  discoData = DiscoData.at(result);
  console.log("discoData is "+discoData)
  discoData.count(function (err, result){
    console.log("count is "+result);
    var count = result;
    for(var x=0;x<count;++x)
    {
	    console.log(x)
	    discoData.hashes(x,function(err,res){
		    console.log(res);
	    }
			     
	    
	    //console.log(discoData.descriptions(x));
    }
  });
});

function search() {
  console.log("search.. " + $("#search").val());
  $("#name").text($("#search").val());

  var result = cryptoMe.get($("#search").val(), function(err, res) {
    if (err) {
      console.log(err);
      return;
    }

    console.log("BOOM")
    console.log(res);

    if (res[0] === "") {
      $("#name").text($("#search").val() + " (user not found)");
    } else {
      $("#name").text($("#search").val());
      location.hash = $("#search").val();
    }
    $("#addr").text(res[1]);
    $("#email").text(res[2]);
    $("#ipfs").text(res[3]);
  });
  //console.log(result);
}

function register() {
  console.log("called!")

  var name = $("#newname").val();

  var result = cryptoMe.register(name, function(err, res) {
    console.log(res);
  });

  console.log("register result:");
  console.log(result);
  $('#reg-modal').modal('hide');
}

function update() {
  console.log("called!")

  var email = $("#updatedemail").val();
  var ipfs = $("#updatedipfs").val();

  var result = cryptoMe.update(email, ipfs, function(err, res) {
    console.log(res);
  });

  console.log("update result:");
  console.log(result);
  $('#update-modal').modal('hide');
}
