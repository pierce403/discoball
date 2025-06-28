// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title DiscoBallRegistry
 * @notice A decentralized registry for website mirrors on IPFS
 * @dev Stores domain/path/IPFS triples with efficient querying capabilities
 */
contract DiscoBallRegistry {
    struct MirrorEntry {
        string domain;
        string path;
        string ipfsHash;
        address publisher;
        uint256 timestamp;
        uint256 entryId;
    }

    // Global state
    uint256 public nextEntryId;
    mapping(uint256 => MirrorEntry) public entries;

    // Domain-based lookups
    mapping(string => uint256) public latestEntryByDomain;
    mapping(string => uint256[]) public entriesByDomain;

    // Publisher-based lookups
    mapping(address => uint256[]) public entriesByPublisher;

    // Path-based lookups
    mapping(string => uint256[]) public entriesByPath;

    // Combined lookups
    mapping(string => mapping(string => uint256)) public latestEntryByDomainPath;
    mapping(string => mapping(string => uint256[])) public entriesByDomainPath;
    mapping(address => mapping(string => uint256[])) public entriesByPublisherDomain;
    mapping(address => mapping(string => uint256[])) public entriesByPublisherPath;

    // Events
    event MirrorPublished(
        uint256 indexed entryId,
        string indexed domain,
        string path,
        string ipfsHash,
        address indexed publisher,
        uint256 timestamp
    );

    /**
     * @notice Publish a new mirror entry
     * @param domain The domain being mirrored
     * @param path The path being mirrored
     * @param ipfsHash The IPFS hash of the mirror
     */
    function publishMirror(
        string calldata domain,
        string calldata path,
        string calldata ipfsHash
    ) external {
        require(bytes(domain).length > 0, "Domain cannot be empty");
        require(bytes(path).length > 0, "Path cannot be empty");
        require(bytes(ipfsHash).length > 0, "IPFS hash cannot be empty");

        uint256 entryId = nextEntryId++;
        uint256 timestamp = block.timestamp;

        // Create the entry
        entries[entryId] = MirrorEntry({
            domain: domain,
            path: path,
            ipfsHash: ipfsHash,
            publisher: msg.sender,
            timestamp: timestamp,
            entryId: entryId
        });

        // Update latest domain entry
        latestEntryByDomain[domain] = entryId;

        // Update domain-path latest entry
        latestEntryByDomainPath[domain][path] = entryId;

        // Add to arrays for listing
        entriesByDomain[domain].push(entryId);
        entriesByPublisher[msg.sender].push(entryId);
        entriesByPath[path].push(entryId);
        entriesByDomainPath[domain][path].push(entryId);
        entriesByPublisherDomain[msg.sender][domain].push(entryId);
        entriesByPublisherPath[msg.sender][path].push(entryId);

        emit MirrorPublished(entryId, domain, path, ipfsHash, msg.sender, timestamp);
    }

    // VIEW FUNCTIONS

    /**
     * @notice Get an entry by ID
     * @param entryId The entry ID to query
     * @return The MirrorEntry for the given ID
     */
    function getEntry(uint256 entryId) external view returns (MirrorEntry memory) {
        return entries[entryId];
    }

    /**
     * @notice Get the latest mirror for a domain
     * @param domain The domain to query
     * @return The latest MirrorEntry for the domain
     */
    function getLatestByDomain(string calldata domain) external view returns (MirrorEntry memory) {
        uint256 entryId = latestEntryByDomain[domain];
        require(entryId != 0 || entries[entryId].timestamp != 0, "No entries for domain");
        return entries[entryId];
    }

    /**
     * @notice Get the latest mirror for a specific domain/path combination
     * @param domain The domain to query
     * @param path The path to query
     * @return The latest MirrorEntry for the domain/path
     */
    function getLatestByDomainPath(string calldata domain, string calldata path) 
        external view returns (MirrorEntry memory) {
        uint256 entryId = latestEntryByDomainPath[domain][path];
        require(entryId != 0 || entries[entryId].timestamp != 0, "No entries for domain/path");
        return entries[entryId];
    }

    /**
     * @notice Get all entries for a domain (paginated)
     * @param domain The domain to query
     * @param offset Starting index
     * @param limit Maximum number of entries to return
     * @return Array of MirrorEntry structs
     */
    function getEntriesByDomain(string calldata domain, uint256 offset, uint256 limit) 
        external view returns (MirrorEntry[] memory) {
        uint256[] memory entryIds = entriesByDomain[domain];
        return _getEntriesFromIds(entryIds, offset, limit);
    }

    /**
     * @notice Get all entries by a publisher (paginated)
     * @param publisher The publisher address to query
     * @param offset Starting index
     * @param limit Maximum number of entries to return
     * @return Array of MirrorEntry structs
     */
    function getEntriesByPublisher(address publisher, uint256 offset, uint256 limit) 
        external view returns (MirrorEntry[] memory) {
        uint256[] memory entryIds = entriesByPublisher[publisher];
        return _getEntriesFromIds(entryIds, offset, limit);
    }

    /**
     * @notice Get all entries for a path (paginated)
     * @param path The path to query
     * @param offset Starting index
     * @param limit Maximum number of entries to return
     * @return Array of MirrorEntry structs
     */
    function getEntriesByPath(string calldata path, uint256 offset, uint256 limit) 
        external view returns (MirrorEntry[] memory) {
        uint256[] memory entryIds = entriesByPath[path];
        return _getEntriesFromIds(entryIds, offset, limit);
    }

    /**
     * @notice Get entries by publisher and domain (paginated)
     * @param publisher The publisher address to query
     * @param domain The domain to query
     * @param offset Starting index
     * @param limit Maximum number of entries to return
     * @return Array of MirrorEntry structs
     */
    function getEntriesByPublisherDomain(address publisher, string calldata domain, uint256 offset, uint256 limit) 
        external view returns (MirrorEntry[] memory) {
        uint256[] memory entryIds = entriesByPublisherDomain[publisher][domain];
        return _getEntriesFromIds(entryIds, offset, limit);
    }

    /**
     * @notice Get entries by publisher and path (paginated)
     * @param publisher The publisher address to query
     * @param path The path to query
     * @param offset Starting index
     * @param limit Maximum number of entries to return
     * @return Array of MirrorEntry structs
     */
    function getEntriesByPublisherPath(address publisher, string calldata path, uint256 offset, uint256 limit) 
        external view returns (MirrorEntry[] memory) {
        uint256[] memory entryIds = entriesByPublisherPath[publisher][path];
        return _getEntriesFromIds(entryIds, offset, limit);
    }

    /**
     * @notice Get entries by domain and path (paginated)
     * @param domain The domain to query
     * @param path The path to query
     * @param offset Starting index
     * @param limit Maximum number of entries to return
     * @return Array of MirrorEntry structs
     */
    function getEntriesByDomainPath(string calldata domain, string calldata path, uint256 offset, uint256 limit) 
        external view returns (MirrorEntry[] memory) {
        uint256[] memory entryIds = entriesByDomainPath[domain][path];
        return _getEntriesFromIds(entryIds, offset, limit);
    }

    /**
     * @notice Get count of entries for a domain
     * @param domain The domain to query
     * @return Number of entries for the domain
     */
    function getEntryCountByDomain(string calldata domain) external view returns (uint256) {
        return entriesByDomain[domain].length;
    }

    /**
     * @notice Get count of entries by a publisher
     * @param publisher The publisher address to query
     * @return Number of entries by the publisher
     */
    function getEntryCountByPublisher(address publisher) external view returns (uint256) {
        return entriesByPublisher[publisher].length;
    }

    /**
     * @notice Get count of entries for a path
     * @param path The path to query
     * @return Number of entries for the path
     */
    function getEntryCountByPath(string calldata path) external view returns (uint256) {
        return entriesByPath[path].length;
    }

    // INTERNAL FUNCTIONS

    /**
     * @dev Helper function to convert entry IDs to MirrorEntry structs with pagination
     * @param entryIds Array of entry IDs
     * @param offset Starting index
     * @param limit Maximum number of entries to return
     * @return Array of MirrorEntry structs
     */
    function _getEntriesFromIds(uint256[] memory entryIds, uint256 offset, uint256 limit) 
        internal view returns (MirrorEntry[] memory) {
        if (offset >= entryIds.length) {
            return new MirrorEntry[](0);
        }

        uint256 end = offset + limit;
        if (end > entryIds.length) {
            end = entryIds.length;
        }

        uint256 length = end - offset;
        MirrorEntry[] memory result = new MirrorEntry[](length);

        for (uint256 i = 0; i < length; i++) {
            result[i] = entries[entryIds[offset + i]];
        }

        return result;
    }
} 