# 🪩 Discoball
IPFS mirror bribery

## Architecture

A decentralized system for website mirroring that reduces server load and ensures content accessibility through community-driven IPFS mirrors.

**Core Components:**
- **Smart Contracts**: On-chain registry for verified mirrors
- **Mirror Providers**: Community members who capture and host website snapshots
- **IPFS Storage**: Decentralized content storage
- **DNS Authorization**: Domain owners authorize mirroring via DNS records

## Smart Contracts

The DiscoBall registry is built on Ethereum-compatible chains (deployed on Base) and provides:

- **Decentralized Registry**: Anyone can publish domain/path/IPFS mirror triples
- **Efficient Querying**: Fast lookups by domain, publisher, path, or combinations
- **Historical Records**: Complete audit trail of all mirror publications
- **Gas Optimized**: Pagination and efficient data structures

### Quick Start

```solidity
import "./src/DiscoBallRegistry.sol";

DiscoBallRegistry registry = DiscoBallRegistry(0x...);

// Publish a mirror
registry.publishMirror("example.com", "/page", "QmYourIPFSHash");

// Get latest mirror for a domain
DiscoBallRegistry.MirrorEntry memory latest = registry.getLatestByDomain("example.com");
```

### Development

```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install dependencies
forge install

# Run tests
forge test

# Deploy to testnet
forge script script/Deploy.s.sol --rpc-url base_sepolia --broadcast
```

See [CONTRACTS.md](./CONTRACTS.md) for complete documentation.

## For Ethereum Developers

```solidity
import "./discoball.sol";

discoball = DiscoBall("0xPOTATO");
discoball.insert(string ipfshash, string description);
```

## For Node Runners (maybe not in v1?)

(run on server running IPFS node)

```bash
./discoball-node.py
```

will generate a private key (if not already generated)
will deploy a node contract (if not already deployed)

## For Data Farmers

(run on server running IPFS node)

```bash
./discoball-farmer.py
```

will query nodes looking for IPFS data to pin

## Contributing

This is an open source project welcoming contributions from developers and decentralization enthusiasts. Visit our [GitHub repository](https://github.com/pierce403/discoball) to get involved!

## License

MIT License - see [LICENSE](./LICENSE) for details.
