// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {Test, console} from "forge-std/Test.sol";
import {DiscoBallRegistry} from "../src/DiscoBallRegistry.sol";

contract DiscoBallRegistryTest is Test {
    DiscoBallRegistry public registry;
    
    address public publisher1 = address(0x1);
    address public publisher2 = address(0x2);
    address public publisher3 = address(0x3);

    event MirrorPublished(
        uint256 indexed entryId,
        string indexed domain,
        string path,
        string ipfsHash,
        address indexed publisher,
        uint256 timestamp
    );

    function setUp() public {
        registry = new DiscoBallRegistry();
    }

    function test_PublishMirror() public {
        vm.prank(publisher1);
        
        vm.expectEmit(true, true, true, true);
        emit MirrorPublished(
            0,
            "example.com",
            "/path1",
            "QmHash1",
            publisher1,
            block.timestamp
        );
        
        registry.publishMirror("example.com", "/path1", "QmHash1");
        
        // Verify the entry was created
        DiscoBallRegistry.MirrorEntry memory entry = registry.getEntry(0);
        assertEq(entry.domain, "example.com");
        assertEq(entry.path, "/path1");
        assertEq(entry.ipfsHash, "QmHash1");
        assertEq(entry.publisher, publisher1);
        assertEq(entry.timestamp, block.timestamp);
        assertEq(entry.entryId, 0);
    }

    function test_PublishMirrorValidation() public {
        vm.prank(publisher1);
        
        // Test empty domain
        vm.expectRevert("Domain cannot be empty");
        registry.publishMirror("", "/path1", "QmHash1");
        
        // Test empty path
        vm.expectRevert("Path cannot be empty");
        registry.publishMirror("example.com", "", "QmHash1");
        
        // Test empty IPFS hash
        vm.expectRevert("IPFS hash cannot be empty");
        registry.publishMirror("example.com", "/path1", "");
    }

    function test_GetLatestByDomain() public {
        // Publish first mirror
        vm.prank(publisher1);
        registry.publishMirror("example.com", "/path1", "QmHash1");
        
        // Wait some time and publish second mirror
        vm.warp(block.timestamp + 100);
        vm.prank(publisher2);
        registry.publishMirror("example.com", "/path2", "QmHash2");
        
        // Get latest should return the second entry
        DiscoBallRegistry.MirrorEntry memory latest = registry.getLatestByDomain("example.com");
        assertEq(latest.entryId, 1);
        assertEq(latest.domain, "example.com");
        assertEq(latest.path, "/path2");
        assertEq(latest.ipfsHash, "QmHash2");
        assertEq(latest.publisher, publisher2);
    }

    function test_GetLatestByDomainPath() public {
        // Publish multiple mirrors for same domain but different paths
        vm.prank(publisher1);
        registry.publishMirror("example.com", "/path1", "QmHash1");
        
        vm.warp(block.timestamp + 100);
        vm.prank(publisher2);
        registry.publishMirror("example.com", "/path1", "QmHash2");
        
        vm.prank(publisher3);
        registry.publishMirror("example.com", "/path2", "QmHash3");
        
        // Get latest for specific domain/path
        DiscoBallRegistry.MirrorEntry memory latest = registry.getLatestByDomainPath("example.com", "/path1");
        assertEq(latest.entryId, 1);
        assertEq(latest.ipfsHash, "QmHash2");
        assertEq(latest.publisher, publisher2);
        
        latest = registry.getLatestByDomainPath("example.com", "/path2");
        assertEq(latest.entryId, 2);
        assertEq(latest.ipfsHash, "QmHash3");
        assertEq(latest.publisher, publisher3);
    }

    function test_GetEntriesByDomain() public {
        // Publish multiple entries for same domain
        vm.prank(publisher1);
        registry.publishMirror("example.com", "/path1", "QmHash1");
        
        vm.prank(publisher2);
        registry.publishMirror("example.com", "/path2", "QmHash2");
        
        vm.prank(publisher3);
        registry.publishMirror("other.com", "/path1", "QmHash3");
        
        // Get entries by domain
        DiscoBallRegistry.MirrorEntry[] memory entries = registry.getEntriesByDomain("example.com", 0, 10);
        assertEq(entries.length, 2);
        assertEq(entries[0].entryId, 0);
        assertEq(entries[1].entryId, 1);
        
        // Test pagination
        entries = registry.getEntriesByDomain("example.com", 1, 1);
        assertEq(entries.length, 1);
        assertEq(entries[0].entryId, 1);
    }

    function test_GetEntriesByPublisher() public {
        // Publisher1 publishes multiple entries
        vm.startPrank(publisher1);
        registry.publishMirror("example.com", "/path1", "QmHash1");
        registry.publishMirror("other.com", "/path2", "QmHash2");
        vm.stopPrank();
        
        vm.prank(publisher2);
        registry.publishMirror("example.com", "/path3", "QmHash3");
        
        // Get entries by publisher
        DiscoBallRegistry.MirrorEntry[] memory entries = registry.getEntriesByPublisher(publisher1, 0, 10);
        assertEq(entries.length, 2);
        assertEq(entries[0].publisher, publisher1);
        assertEq(entries[1].publisher, publisher1);
        
        entries = registry.getEntriesByPublisher(publisher2, 0, 10);
        assertEq(entries.length, 1);
        assertEq(entries[0].publisher, publisher2);
    }

    function test_GetEntriesByPath() public {
        vm.prank(publisher1);
        registry.publishMirror("example.com", "/common", "QmHash1");
        
        vm.prank(publisher2);
        registry.publishMirror("other.com", "/common", "QmHash2");
        
        vm.prank(publisher3);
        registry.publishMirror("example.com", "/different", "QmHash3");
        
        // Get entries by path
        DiscoBallRegistry.MirrorEntry[] memory entries = registry.getEntriesByPath("/common", 0, 10);
        assertEq(entries.length, 2);
        
        entries = registry.getEntriesByPath("/different", 0, 10);
        assertEq(entries.length, 1);
    }

    function test_GetEntriesByPublisherDomain() public {
        vm.startPrank(publisher1);
        registry.publishMirror("example.com", "/path1", "QmHash1");
        registry.publishMirror("example.com", "/path2", "QmHash2");
        registry.publishMirror("other.com", "/path1", "QmHash3");
        vm.stopPrank();
        
        // Get entries by publisher and domain
        DiscoBallRegistry.MirrorEntry[] memory entries = registry.getEntriesByPublisherDomain(publisher1, "example.com", 0, 10);
        assertEq(entries.length, 2);
        assertEq(entries[0].domain, "example.com");
        assertEq(entries[1].domain, "example.com");
        
        entries = registry.getEntriesByPublisherDomain(publisher1, "other.com", 0, 10);
        assertEq(entries.length, 1);
        assertEq(entries[0].domain, "other.com");
    }

    function test_GetEntriesByPublisherPath() public {
        vm.startPrank(publisher1);
        registry.publishMirror("example.com", "/common", "QmHash1");
        registry.publishMirror("other.com", "/common", "QmHash2");
        registry.publishMirror("example.com", "/different", "QmHash3");
        vm.stopPrank();
        
        // Get entries by publisher and path
        DiscoBallRegistry.MirrorEntry[] memory entries = registry.getEntriesByPublisherPath(publisher1, "/common", 0, 10);
        assertEq(entries.length, 2);
        assertEq(entries[0].path, "/common");
        assertEq(entries[1].path, "/common");
        
        entries = registry.getEntriesByPublisherPath(publisher1, "/different", 0, 10);
        assertEq(entries.length, 1);
        assertEq(entries[0].path, "/different");
    }

    function test_GetEntriesByDomainPath() public {
        vm.prank(publisher1);
        registry.publishMirror("example.com", "/path1", "QmHash1");
        
        vm.prank(publisher2);
        registry.publishMirror("example.com", "/path1", "QmHash2");
        
        vm.prank(publisher3);
        registry.publishMirror("example.com", "/path2", "QmHash3");
        
        // Get entries by domain and path
        DiscoBallRegistry.MirrorEntry[] memory entries = registry.getEntriesByDomainPath("example.com", "/path1", 0, 10);
        assertEq(entries.length, 2);
        
        entries = registry.getEntriesByDomainPath("example.com", "/path2", 0, 10);
        assertEq(entries.length, 1);
    }

    function test_GetEntryCounts() public {
        vm.prank(publisher1);
        registry.publishMirror("example.com", "/path1", "QmHash1");
        
        vm.prank(publisher2);
        registry.publishMirror("example.com", "/path2", "QmHash2");
        
        vm.prank(publisher1);
        registry.publishMirror("other.com", "/path1", "QmHash3");
        
        // Test counts
        assertEq(registry.getEntryCountByDomain("example.com"), 2);
        assertEq(registry.getEntryCountByDomain("other.com"), 1);
        assertEq(registry.getEntryCountByPublisher(publisher1), 2);
        assertEq(registry.getEntryCountByPublisher(publisher2), 1);
        assertEq(registry.getEntryCountByPath("/path1"), 2);
        assertEq(registry.getEntryCountByPath("/path2"), 1);
    }

    function test_NextEntryIdIncrement() public {
        assertEq(registry.nextEntryId(), 0);
        
        vm.prank(publisher1);
        registry.publishMirror("example.com", "/path1", "QmHash1");
        assertEq(registry.nextEntryId(), 1);
        
        vm.prank(publisher2);
        registry.publishMirror("example.com", "/path2", "QmHash2");
        assertEq(registry.nextEntryId(), 2);
    }

    function test_PaginationEdgeCases() public {
        vm.prank(publisher1);
        registry.publishMirror("example.com", "/path1", "QmHash1");
        
        // Test offset beyond array length
        DiscoBallRegistry.MirrorEntry[] memory entries = registry.getEntriesByDomain("example.com", 10, 5);
        assertEq(entries.length, 0);
        
        // Test limit larger than remaining entries
        entries = registry.getEntriesByDomain("example.com", 0, 10);
        assertEq(entries.length, 1);
    }

    function test_EmptyQueries() public {
        // Test queries on empty registry
        vm.expectRevert("No entries for domain");
        registry.getLatestByDomain("nonexistent.com");
        
        vm.expectRevert("No entries for domain/path");
        registry.getLatestByDomainPath("nonexistent.com", "/path");
        
        DiscoBallRegistry.MirrorEntry[] memory entries = registry.getEntriesByDomain("nonexistent.com", 0, 10);
        assertEq(entries.length, 0);
    }

    function test_MultiplePublishersOverTime() public {
        // Simulate realistic usage over time
        vm.warp(1000);
        vm.prank(publisher1);
        registry.publishMirror("news.com", "/article1", "QmHash1");
        
        vm.warp(2000);
        vm.prank(publisher2);
        registry.publishMirror("news.com", "/article1", "QmHash2");
        
        vm.warp(3000);
        vm.prank(publisher1);
        registry.publishMirror("news.com", "/article2", "QmHash3");
        
        // Verify latest entries
        DiscoBallRegistry.MirrorEntry memory latest = registry.getLatestByDomain("news.com");
        assertEq(latest.entryId, 2);
        assertEq(latest.timestamp, 3000);
        
        latest = registry.getLatestByDomainPath("news.com", "/article1");
        assertEq(latest.entryId, 1);
        assertEq(latest.timestamp, 2000);
        assertEq(latest.publisher, publisher2);
    }
} 