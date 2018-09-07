# discoball
IPFS mirror bribery


# Architecture

# For Ethereum Developers

import "./discoball.sol";
discoball = DiscoBall("0xPOTATO");
discoball.insert(string ipfshash,string description,);

# For Node Runners (maybe not in v1?)

(run on server running IPFS node)
./discoball-node.py
will generate a private key (if not already generated)
will deploy a node contract (if not already deployed)


# For Data Farmers

(run on server running IPFS node)
./discoball-farmer.py
will query nodes looking for IPFS data to pin
