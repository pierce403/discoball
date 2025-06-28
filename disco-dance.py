#!/usr/bin/env python3
"""
🪩 Disco Dance - Mirror Your Own Site

This script helps domain owners mirror their own websites to IPFS and register
them in the DiscoBall smart contract registry.

Usage:
    python disco-dance.py --domain example.com --path /page --private-key YOUR_KEY

Requirements:
    - Domain must have DNS TXT record: discoball-site-verification=0xYourAddress
    - IPFS node running locally or accessible via HTTP API
    - Private key for Ethereum-compatible account
"""

import argparse
import dns.resolver
import requests
from bs4 import BeautifulSoup
import ipfshttpclient
import json
import os
from web3 import Web3
from eth_account import Account
import hashlib
import time
from urllib.parse import urljoin, urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Smart contract configuration
CONTRACT_ADDRESS = "0x..."  # Update with deployed contract address
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "domain", "type": "string"},
            {"internalType": "string", "name": "path", "type": "string"},
            {"internalType": "string", "name": "ipfsHash", "type": "string"}
        ],
        "name": "publishMirror",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

class DiscoMirror:
    def __init__(self, private_key, rpc_url="https://mainnet.base.org", ipfs_api="/ip4/127.0.0.1/tcp/5001"):
        """Initialize the disco mirror with Web3 and IPFS connections."""
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        
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
            logger.warning("Contract address not set. Please update CONTRACT_ADDRESS in the script.")
            self.contract = None
    
    def verify_dns_record(self, domain):
        """Verify that the domain has the correct DNS TXT record."""
        expected_record = f"discoball-site-verification={self.address}"
        
        try:
            result = dns.resolver.resolve(domain, 'TXT')
            for rdata in result:
                txt_record = str(rdata).strip('"')
                if txt_record == expected_record:
                    logger.info(f"✅ DNS verification successful for {domain}")
                    return True
                    
            logger.error(f"❌ DNS verification failed for {domain}")
            logger.error(f"Expected: {expected_record}")
            logger.error(f"Found records: {[str(r).strip('\"') for r in result]}")
            return False
            
        except Exception as e:
            logger.error(f"❌ DNS lookup failed for {domain}: {e}")
            return False
    
    def crawl_page(self, domain, path):
        """Crawl a single page and return its content."""
        url = f"https://{domain}{path}"
        
        try:
            logger.info(f"Crawling {url}")
            headers = {
                'User-Agent': 'DiscoBall-Mirror/1.0 (+https://github.com/pierce403/discoball)'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse and clean the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Create a snapshot object
            snapshot = {
                'url': url,
                'domain': domain,
                'path': path,
                'timestamp': int(time.time()),
                'content_type': response.headers.get('content-type', 'text/html'),
                'status_code': response.status_code,
                'html': str(soup),
                'metadata': {
                    'title': soup.title.string if soup.title else '',
                    'description': self._get_meta_content(soup, 'description'),
                    'keywords': self._get_meta_content(soup, 'keywords'),
                }
            }
            
            logger.info(f"Successfully crawled {url} ({len(snapshot['html'])} chars)")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to crawl {url}: {e}")
            return None
    
    def _get_meta_content(self, soup, name):
        """Extract meta tag content."""
        meta = soup.find('meta', attrs={'name': name})
        return meta.get('content', '') if meta else ''
    
    def upload_to_ipfs(self, snapshot):
        """Upload snapshot to IPFS and return the hash."""
        try:
            # Convert snapshot to JSON
            snapshot_json = json.dumps(snapshot, indent=2)
            
            # Upload to IPFS
            result = self.ipfs.add_json(snapshot)
            ipfs_hash = result
            
            logger.info(f"📦 Uploaded to IPFS: {ipfs_hash}")
            return ipfs_hash
            
        except Exception as e:
            logger.error(f"Failed to upload to IPFS: {e}")
            return None
    
    def publish_to_contract(self, domain, path, ipfs_hash):
        """Publish the mirror to the smart contract."""
        if not self.contract:
            logger.error("Smart contract not initialized")
            return False
            
        try:
            # Build transaction
            txn = self.contract.functions.publishMirror(
                domain, path, ipfs_hash
            ).build_transaction({
                'from': self.address,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price,
            })
            
            # Sign and send transaction
            signed_txn = self.account.sign_transaction(txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"📡 Transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.info(f"✅ Mirror published successfully! Block: {receipt.blockNumber}")
                return True
            else:
                logger.error(f"❌ Transaction failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to publish to contract: {e}")
            return False
    
    def mirror_site(self, domain, path):
        """Complete mirroring process: verify DNS, crawl, upload to IPFS, publish to contract."""
        logger.info(f"🪩 Starting mirror process for {domain}{path}")
        
        # Step 1: Verify DNS record
        if not self.verify_dns_record(domain):
            logger.error("DNS verification failed. Cannot proceed.")
            return False
        
        # Step 2: Crawl the page
        snapshot = self.crawl_page(domain, path)
        if not snapshot:
            logger.error("Failed to crawl page. Cannot proceed.")
            return False
        
        # Step 3: Upload to IPFS
        ipfs_hash = self.upload_to_ipfs(snapshot)
        if not ipfs_hash:
            logger.error("Failed to upload to IPFS. Cannot proceed.")
            return False
        
        # Step 4: Publish to smart contract
        if self.publish_to_contract(domain, path, ipfs_hash):
            logger.info(f"🎉 Successfully mirrored {domain}{path}")
            logger.info(f"   IPFS Hash: {ipfs_hash}")
            return True
        else:
            logger.error("Failed to publish to smart contract.")
            return False

def main():
    parser = argparse.ArgumentParser(description='🪩 Disco Dance - Mirror your own site')
    parser.add_argument('--domain', required=True, help='Domain to mirror (e.g., example.com)')
    parser.add_argument('--path', required=True, help='Path to mirror (e.g., /page)')
    parser.add_argument('--private-key', required=True, help='Ethereum private key')
    parser.add_argument('--rpc-url', default='https://mainnet.base.org', help='RPC URL for Base network')
    parser.add_argument('--ipfs-api', default='/ip4/127.0.0.1/tcp/5001', help='IPFS API endpoint')
    
    args = parser.parse_args()
    
    try:
        # Initialize disco mirror
        mirror = DiscoMirror(args.private_key, args.rpc_url, args.ipfs_api)
        
        # Mirror the site
        success = mirror.mirror_site(args.domain, args.path)
        
        if success:
            print(f"\n🎉 Successfully mirrored {args.domain}{args.path}")
            exit(0)
        else:
            print(f"\n❌ Failed to mirror {args.domain}{args.path}")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n👋 Disco dance interrupted!")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main() 