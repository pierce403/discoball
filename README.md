# 🪩 Discoball

**Discoball** is an open-source, decentralized mirroring solution designed to help websites facing traffic and scraping pressures from AI companies. It enables communities to host verified, trusted mirrors of content, reducing costs for original content providers and ensuring the availability and resilience of web resources.

## 🌟 Core Concept

Discoball allows any domain owner to explicitly authorize community-driven mirrors through simple DNS TXT records. Snapshots of website URLs are securely stored on IPFS, linked to the domain, path, publisher public key, and timestamp on-chain via smart contracts.

The playful "Discoball" name evokes the concept of multiple mirrors reflecting the original content, maintaining authenticity and reliability.

## 🔑 Key Features

- **DNS-Based Verification**: Domain owners explicitly authorize mirrors by setting a TXT record containing a public Ethereum-compatible address.
- **Decentralized & Transparent**: Snapshots and metadata are decentralized via IPFS and recorded on-chain.
- **Historical Snapshots**: Maintains a record of historical snapshots with no guarantee of permanent IPFS storage, encouraging community-driven data persistence.
- **Flexible & Extensible**: Designed without immediate token incentives but with flexibility for future enhancements like token rewards.

## 🛠️ How It Works

### For Domain Owners:

1. Generate an Ethereum-compatible key pair.
2. Publish the public key in your DNS as a TXT record:

```
discoball-site-verification=0xYourPublicEthereumAddress
```

### For Mirror Providers:

1. Capture and upload website snapshots to IPFS.
2. Submit the snapshot metadata (domain, URL path, IPFS hash, timestamp, publisher signature) to the Discoball smart contract on Base.

### Verification & Usage:

- Users verify mirrors against the publisher's DNS TXT record.
- Verified snapshots provide higher trust and reliability.

## 📋 Smart Contracts

The DiscoBall registry is deployed on Base and provides a decentralized registry for website mirrors:

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

### Development & Testing

```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install dependencies
forge install

# Compile contracts
forge build

# Run tests (15 comprehensive test cases)
forge test

# Run tests with gas reporting
forge test --gas-report

# Deploy to Base Sepolia testnet
forge script script/Deploy.s.sol --rpc-url base_sepolia --broadcast --verify

# Deploy to Base mainnet
forge script script/Deploy.s.sol --rpc-url base --broadcast --verify
```

**Environment Variables for Deployment:**
- `PRIVATE_KEY`: Deployer private key
- `BASESCAN_API_KEY`: For contract verification

See [CONTRACTS.md](./CONTRACTS.md) for complete smart contract documentation and API reference.

## 🚨 Considerations

- No permanent storage guarantee for IPFS snapshots—communities are encouraged to pin and maintain their own persistent copies.
- DNS spoofing or misconfigurations may temporarily affect verification; DNSSEC is recommended for stronger security.

## 🌐 Frontend & Community

A user-friendly frontend will make it easy for anyone to mirror content, check snapshot authenticity, and visualize domain "discoball maturity" scores.

## 📈 Roadmap

- **Initial Launch**: Core decentralized verification and snapshot submission system.
- **Future Enhancements**:
  - zkTLS integration for trustless verification.
  - Community reputation scoring.
  - Optional token-based incentive models.

## 🙌 Join Us

Discoball is an open project welcoming contributions from developers, content creators, and decentralization enthusiasts. Visit our [GitHub repository](https://github.com/pierce403/discoball) to get involved!

Let's reflect the future, one mirror at a time! 🪩✨
