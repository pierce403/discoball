# 🪩 DiscoBall Smart Contracts

This directory contains the smart contracts for the DiscoBall decentralized website mirroring system.

## Overview

The DiscoBall smart contracts provide a decentralized registry for website mirrors stored on IPFS. The system allows anyone to publish mirror snapshots of websites while maintaining a transparent, queryable record on-chain.

## Contracts

### DiscoBallRegistry.sol

The main registry contract that stores and manages website mirror entries.

#### Core Features

- **Decentralized Publishing**: Anyone can publish mirror entries for any domain/path combination
- **Efficient Querying**: Multiple indexing strategies for fast lookups by domain, publisher, path, or combinations
- **Historical Records**: Complete history of all mirror publications with timestamps
- **Gas Optimized**: Efficient data structures and pagination to minimize gas costs

#### Data Structure

Each mirror entry contains:
- `domain`: The domain being mirrored (e.g., "example.com")
- `path`: The path being mirrored (e.g., "/article/123")
- `ipfsHash`: The IPFS hash of the mirror content
- `publisher`: Address of who published the mirror
- `timestamp`: When the mirror was published
- `entryId`: Unique identifier for the entry

#### Key Functions

##### Publishing
- `publishMirror(domain, path, ipfsHash)`: Publish a new mirror entry

##### Latest Lookups
- `getLatestByDomain(domain)`: Get the most recent mirror for a domain
- `getLatestByDomainPath(domain, path)`: Get the most recent mirror for a specific domain/path

##### Paginated Queries
- `getEntriesByDomain(domain, offset, limit)`: Get all mirrors for a domain
- `getEntriesByPublisher(publisher, offset, limit)`: Get all mirrors by a publisher
- `getEntriesByPath(path, offset, limit)`: Get all mirrors for a path
- `getEntriesByPublisherDomain(publisher, domain, offset, limit)`: Combined query
- `getEntriesByPublisherPath(publisher, path, offset, limit)`: Combined query
- `getEntriesByDomainPath(domain, path, offset, limit)`: Combined query

##### Statistics
- `getEntryCountByDomain(domain)`: Count of entries for a domain
- `getEntryCountByPublisher(publisher)`: Count of entries by a publisher
- `getEntryCountByPath(path)`: Count of entries for a path

#### Events

```solidity
event MirrorPublished(
    uint256 indexed entryId,
    string indexed domain,
    string path,
    string ipfsHash,
    address indexed publisher,
    uint256 timestamp
);
```

## Development

### Prerequisites

- [Foundry](https://getfoundry.sh/)

### Setup

```bash
# Install dependencies
forge install

# Compile contracts
forge build

# Run tests
forge test

# Run tests with gas reporting
forge test --gas-report
```

### Testing

The test suite covers:
- ✅ Basic mirror publishing
- ✅ Input validation
- ✅ Latest entry queries
- ✅ Paginated queries
- ✅ Combined queries (publisher + domain, etc.)
- ✅ Entry counting
- ✅ Pagination edge cases
- ✅ Empty state handling
- ✅ Multi-publisher scenarios

Run tests with:
```bash
forge test -v
```

### Deployment

#### Base Sepolia (Testnet)
```bash
forge script script/Deploy.s.sol --rpc-url base_sepolia --broadcast --verify
```

#### Base Mainnet
```bash
forge script script/Deploy.s.sol --rpc-url base --broadcast --verify
```

**Environment Variables Required:**
- `PRIVATE_KEY`: Deployer private key
- `BASESCAN_API_KEY`: For contract verification

## Architecture Decisions

### Why These Data Structures?

The contract uses multiple mapping strategies to enable efficient O(1) lookups:

1. **Latest Entry Tracking**: Separate mappings for `latestEntryByDomain` and `latestEntryByDomainPath` provide instant access to the most recent mirrors
2. **Array-based Indexing**: Arrays like `entriesByDomain[]` enable pagination and historical browsing
3. **Combined Indexes**: Nested mappings like `entriesByPublisherDomain` enable complex queries without expensive filtering

### Gas Optimization

- **Pagination**: All list functions use offset/limit to prevent gas limit issues
- **Packed Data**: Efficient struct packing and storage patterns
- **Minimal External Calls**: Single-transaction publishing with all index updates

### Security Considerations

- **No Access Control**: Anyone can publish mirrors (by design)
- **No Content Validation**: Contract doesn't verify IPFS hashes or content
- **Immutable Records**: Published entries cannot be deleted or modified
- **Gas Griefing**: Pagination prevents DoS via large arrays

## Future Enhancements

Potential future additions:
- **Publisher Reputation**: On-chain scoring for mirror quality
- **Economic Incentives**: Token rewards for verified mirrors
- **Content Verification**: Integration with oracle services for content validation
- **Dispute Resolution**: Mechanism for handling malicious or incorrect mirrors

## License

MIT License - see [LICENSE](./LICENSE) for details. 