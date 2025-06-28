#!/usr/bin/env python3
"""
🪩 Disco Party - Pin Your Friends' Mirrors

This script reads a list of trusted publisher addresses from friends.txt and
pins all their IPFS mirrors locally to help maintain the decentralized web.

Usage:
    python disco-party.py [--friends-file friends.txt] [--rpc-url URL]

The friends.txt file should contain one Ethereum address per line:
    0x1234567890123456789012345678901234567890
    0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef
"""

import argparse
import ipfshttpclient
import json
import os
from web3 import Web3
import logging
import time
from typing import List, Dict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Smart contract configuration
CONTRACT_ADDRESS = "0x..."  # Update with deployed contract address
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "publisher", "type": "address"},
            {"internalType": "uint256", "name": "offset", "type": "uint256"},
            {"internalType": "uint256", "name": "limit", "type": "uint256"}
        ],
        "name": "getEntriesByPublisher",
        "outputs": [
            {
                "components": [
                    {"internalType": "string", "name": "domain", "type": "string"},
                    {"internalType": "string", "name": "path", "type": "string"},
                    {"internalType": "string", "name": "ipfsHash", "type": "string"},
                    {"internalType": "address", "name": "publisher", "type": "address"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                    {"internalType": "uint256", "name": "entryId", "type": "uint256"}
                ],
                "internalType": "struct DiscoBallRegistry.MirrorEntry[]",
                "name": "",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "publisher", "type": "address"}
        ],
        "name": "getEntryCountByPublisher",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

class DiscoParty:
    def __init__(self, rpc_url="https://mainnet.base.org", ipfs_api="/ip4/127.0.0.1/tcp/5001"):
        """Initialize the disco party with Web3 and IPFS connections."""
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        try:
            self.ipfs = ipfshttpclient.connect(ipfs_api)
            logger.info(f"Connected to IPFS at {ipfs_api}")
        except Exception as e:
            logger.error(f"Failed to connect to IPFS: {e}")
            raise
            
        # Initialize contract
        if CONTRACT_ADDRESS != "0x...":
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(CONTRACT_ADDRESS),
                abi=CONTRACT_ABI
            )
        else:
            logger.error("Contract address not set. Please update CONTRACT_ADDRESS in the script.")
            self.contract = None
    
    def load_friends(self, friends_file="friends.txt"):
        """Load friend addresses from file."""
        if not os.path.exists(friends_file):
            logger.error(f"Friends file not found: {friends_file}")
            logger.info("Create friends.txt with one Ethereum address per line")
            return []
        
        friends = []
        try:
            with open(friends_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Basic address validation
                        if line.startswith('0x') and len(line) == 42:
                            try:
                                checksum_addr = Web3.to_checksum_address(line)
                                friends.append(checksum_addr)
                                logger.debug(f"Added friend: {checksum_addr}")
                            except Exception as e:
                                logger.warning(f"Invalid address on line {line_num}: {line}")
                        else:
                            logger.warning(f"Invalid address format on line {line_num}: {line}")
            
            logger.info(f"Loaded {len(friends)} friend addresses from {friends_file}")
            return friends
            
        except Exception as e:
            logger.error(f"Failed to read {friends_file}: {e}")
            return []
    
    def get_publisher_entries(self, publisher_address, batch_size=50):
        """Get all entries for a specific publisher."""
        if not self.contract:
            logger.error("Smart contract not initialized")
            return []
        
        try:
            # Get total count for this publisher
            total_count = self.contract.functions.getEntryCountByPublisher(publisher_address).call()
            logger.info(f"Publisher {publisher_address} has {total_count} entries")
            
            if total_count == 0:
                return []
            
            all_entries = []
            offset = 0
            
            # Fetch entries in batches
            while offset < total_count:
                limit = min(batch_size, total_count - offset)
                logger.debug(f"Fetching entries {offset}-{offset+limit-1} for {publisher_address}")
                
                entries = self.contract.functions.getEntriesByPublisher(
                    publisher_address, offset, limit
                ).call()
                
                all_entries.extend(entries)
                offset += limit
            
            logger.info(f"Retrieved {len(all_entries)} entries for {publisher_address}")
            return all_entries
            
        except Exception as e:
            logger.error(f"Failed to get entries for {publisher_address}: {e}")
            return []
    
    def pin_ipfs_hash(self, ipfs_hash, metadata=None):
        """Pin an IPFS hash locally."""
        try:
            # Check if already pinned
            pinned_hashes = self.ipfs.pin.ls(type='recursive')['Keys']
            if ipfs_hash in pinned_hashes:
                logger.debug(f"Already pinned: {ipfs_hash}")
                return True
            
            # Pin the hash
            logger.info(f"📌 Pinning {ipfs_hash}")
            if metadata:
                logger.info(f"   {metadata['domain']}{metadata['path']} from {metadata['timestamp']}")
            
            self.ipfs.pin.add(ipfs_hash)
            logger.info(f"✅ Successfully pinned {ipfs_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pin {ipfs_hash}: {e}")
            return False
    
    def pin_friend_content(self, friend_address):
        """Pin all content from a specific friend."""
        logger.info(f"🪩 Processing friend: {friend_address}")
        
        entries = self.get_publisher_entries(friend_address)
        if not entries:
            logger.info(f"No entries found for {friend_address}")
            return 0
        
        pinned_count = 0
        for entry in entries:
            domain, path, ipfs_hash, publisher, timestamp, entry_id = entry
            
            metadata = {
                'domain': domain,
                'path': path,
                'publisher': publisher,
                'timestamp': timestamp,
                'entry_id': entry_id
            }
            
            if self.pin_ipfs_hash(ipfs_hash, metadata):
                pinned_count += 1
            
            # Small delay to be nice to IPFS
            time.sleep(0.1)
        
        logger.info(f"✨ Pinned {pinned_count}/{len(entries)} entries for {friend_address}")
        return pinned_count
    
    def start_party(self, friends_file="friends.txt"):
        """Start the disco party - pin all friends' content."""
        logger.info("🎉 Starting the disco party!")
        
        # Load friend addresses
        friends = self.load_friends(friends_file)
        if not friends:
            logger.error("No friends found. Party cancelled! 😢")
            return False
        
        total_pinned = 0
        successful_friends = 0
        
        for friend in friends:
            try:
                pinned_count = self.pin_friend_content(friend)
                if pinned_count > 0:
                    successful_friends += 1
                    total_pinned += pinned_count
            except Exception as e:
                logger.error(f"Failed to process friend {friend}: {e}")
        
        logger.info(f"🎊 Party complete!")
        logger.info(f"   Friends processed: {successful_friends}/{len(friends)}")
        logger.info(f"   Total content pinned: {total_pinned}")
        
        return successful_friends > 0
    
    def show_stats(self):
        """Show statistics about pinned content."""
        try:
            pins = self.ipfs.pin.ls(type='recursive')
            pin_count = len(pins['Keys'])
            logger.info(f"📊 Currently pinning {pin_count} IPFS objects")
            
            # Show repo stats
            stats = self.ipfs.repo.stat()
            size_gb = stats['RepoSize'] / (1024**3)
            logger.info(f"📊 Repo size: {size_gb:.2f} GB")
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")

def create_sample_friends_file():
    """Create a sample friends.txt file."""
    sample_content = """# DiscoBall Friends List
# Add one Ethereum address per line
# Lines starting with # are comments

# Example addresses (replace with real friends):
# 0x1234567890123456789012345678901234567890
# 0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef

# Add your trusted publishers here:
"""
    
    with open("friends.txt", "w") as f:
        f.write(sample_content)
    
    logger.info("Created sample friends.txt file")

def main():
    parser = argparse.ArgumentParser(description='🪩 Disco Party - Pin your friends\' mirrors')
    parser.add_argument('--friends-file', default='friends.txt', help='File containing friend addresses')
    parser.add_argument('--rpc-url', default='https://mainnet.base.org', help='RPC URL for Base network')
    parser.add_argument('--ipfs-api', default='/ip4/127.0.0.1/tcp/5001', help='IPFS API endpoint')
    parser.add_argument('--create-sample', action='store_true', help='Create a sample friends.txt file')
    parser.add_argument('--stats', action='store_true', help='Show IPFS statistics')
    
    args = parser.parse_args()
    
    try:
        if args.create_sample:
            create_sample_friends_file()
            return
        
        # Initialize disco party
        party = DiscoParty(args.rpc_url, args.ipfs_api)
        
        if args.stats:
            party.show_stats()
            return
        
        # Start the party!
        success = party.start_party(args.friends_file)
        
        if success:
            print("\n🎉 Disco party successful! Your friends' content is now pinned locally.")
            party.show_stats()
        else:
            print("\n😢 Disco party had some issues. Check the logs above.")
            
    except KeyboardInterrupt:
        print("\n👋 Disco party interrupted!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main() 