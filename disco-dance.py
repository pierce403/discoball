#!/usr/bin/env python3
"""
🪩 Disco Dance - Mirror Your Own Site

This script helps domain owners mirror their own websites to IPFS and register
them in the DiscoBall smart contract registry.

Usage:
    python disco-dance.py https://example.com/page

Requirements:
    - Domain must have DNS TXT record: discoball-site-verification=0xYourAddress
    - IPFS node running locally or accessible via HTTP API
    - Private key for Ethereum-compatible account (from --private-key, PRIVATE_KEY, or .secrets/deployer-base.key)
"""

import argparse
import dns.resolver
import requests
from bs4 import BeautifulSoup
import ipfshttpclient
import json
import mimetypes
import os
import re
import tempfile
from web3 import Web3
from eth_account import Account
import hashlib
import time
from urllib.parse import urljoin, urlparse
import logging
from email.utils import parsedate_to_datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Smart contract configuration
CONTRACT_ADDRESS = "0x3fB28659757a6edb6c53eFE1F84896F8Eaf6d5f7"  # DiscoBallRegistry on Base mainnet
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
        self.user_agent = 'DiscoBall-Mirror/1.0 (+https://github.com/pierce403/discoball)'
        self.request_timeout = float(os.getenv("DISCOBALL_REQUEST_TIMEOUT", "30"))
        self.max_fetch_attempts = int(os.getenv("DISCOBALL_MAX_FETCH_ATTEMPTS", "3"))
        self.default_min_interval = float(os.getenv("DISCOBALL_MIN_REQUEST_INTERVAL", "0.05"))
        self.wikimedia_min_interval = float(os.getenv("DISCOBALL_WIKIMEDIA_MIN_INTERVAL", "0.25"))
        self.default_rate_limit_cooldown = float(os.getenv("DISCOBALL_RATE_LIMIT_COOLDOWN", "120"))
        self._host_next_request_at = {}
        self._host_cooldown_until = {}
        self._host_cooldown_logged = {}
        self.http = requests.Session()
        self.http.headers.update({'User-Agent': self.user_agent})
        
        try:
            self.ipfs = ipfshttpclient.connect(ipfs_api)
            logger.info(f"Connected to IPFS at {ipfs_api}")
        except Exception as e:
            logger.error(f"Failed to connect to IPFS: {e}")
            raise
            
        # Initialize contract
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=CONTRACT_ABI
        )
    
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
                    
            logger.warning(f"⚠️ DNS verification failed for {domain}")
            logger.warning(f"Expected: {expected_record}")
            logger.warning(f"Found records: {[str(r).strip('\"') for r in result]}")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ DNS lookup failed for {domain}: {e}")
            return False
    
    def crawl_page(self, crawl_url, domain, path, output_dir):
        """Crawl a single page and build a browsable snapshot bundle."""
        try:
            logger.info(f"Crawling {crawl_url}")
            response = self._fetch(crawl_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            resolved_url = response.url
            asset_cache = {}
            capture_report = {
                "localized_downloads": 0,
                "rewritten_references": 0,
                "blocked_references": 0,
                "failed_downloads": 0,
                "missing_resources": [],
                "_missing_seen": set(),
            }
            rewritten_references = self._rewrite_html_assets(
                soup,
                resolved_url,
                output_dir,
                asset_cache,
                capture_report,
            )
            self._strip_network_hints(soup, capture_report)
            self._inject_offline_csp(soup)

            html_output = os.path.join(output_dir, "index.html")
            with open(html_output, "w", encoding="utf-8") as html_file:
                html_file.write(str(soup))

            missing_resources = capture_report["missing_resources"]
            missing_total = len(missing_resources)
            missing_limit = 100

            snapshot = {
                'url': resolved_url,
                'domain': domain,
                'path': path,
                'timestamp': int(time.time()),
                'content_type': response.headers.get('content-type', 'text/html'),
                'status_code': response.status_code,
                'metadata': {
                    'title': soup.title.string if soup.title else '',
                    'description': self._get_meta_content(soup, 'description'),
                    'keywords': self._get_meta_content(soup, 'keywords'),
                },
                'resources_localized': capture_report["localized_downloads"],
                'rewritten_references': rewritten_references,
                'blocked_references': capture_report["blocked_references"],
                'failed_downloads': capture_report["failed_downloads"],
                'missing_resources': missing_resources[:missing_limit],
                'missing_resources_truncated': max(0, missing_total - missing_limit),
            }

            snapshot_output = os.path.join(output_dir, "snapshot.json")
            with open(snapshot_output, "w", encoding="utf-8") as metadata_file:
                json.dump(snapshot, metadata_file, indent=2)

            logger.info(
                f"Successfully captured {resolved_url} "
                f"(localized={snapshot['resources_localized']}, "
                f"rewritten={rewritten_references}, blocked={snapshot['blocked_references']})"
            )
            return snapshot

        except Exception as e:
            logger.exception(f"Failed to crawl {crawl_url}: {e}")
            return None
    
    def _get_meta_content(self, soup, name):
        """Extract meta tag content."""
        meta = soup.find('meta', attrs={'name': name})
        return meta.get('content', '') if meta else ''
    
    def upload_to_ipfs(self, snapshot_dir):
        """Upload snapshot directory to IPFS and return the root hash."""
        try:
            result = self.ipfs.add(snapshot_dir, recursive=True, pin=True)
            ipfs_hash = self._extract_ipfs_hash(result, snapshot_dir)
            if not ipfs_hash:
                raise ValueError(f"Could not determine root hash from IPFS add response: {result}")

            logger.info(f"📦 Uploaded snapshot bundle to IPFS: {ipfs_hash}")
            logger.info(f"   Local preview: http://127.0.0.1:8080/ipfs/{ipfs_hash}")
            return ipfs_hash

        except Exception as e:
            logger.error(f"Failed to upload to IPFS: {e}")
            return None

    def _fetch(self, target_url, referer=None):
        """HTTP GET with polite pacing and basic rate-limit awareness."""
        parsed_target = urlparse(target_url)
        host = (parsed_target.hostname or '').lower()
        cooldown_remaining = self._respect_host_cooldown(host)
        if cooldown_remaining > 0:
            raise RuntimeError(
                f"Host {host} is in cooldown for another {int(cooldown_remaining)}s"
            )
        self._wait_for_host_slot(host)

        headers = {}
        if referer:
            headers['Referer'] = referer

        last_error = None
        for attempt in range(1, self.max_fetch_attempts + 1):
            try:
                response = self.http.get(target_url, headers=headers, timeout=self.request_timeout)

                if response.status_code in (429, 503):
                    cooldown_seconds = self._get_retry_after_seconds(response.headers.get("Retry-After"))
                    if cooldown_seconds is None:
                        cooldown_seconds = self.default_rate_limit_cooldown
                    self._set_host_cooldown(host, cooldown_seconds, response.status_code)

                return response

            except requests.RequestException as e:
                last_error = e
                if attempt >= self.max_fetch_attempts:
                    break
                backoff_seconds = min(2 ** (attempt - 1), 8)
                time.sleep(backoff_seconds)

        if last_error:
            raise last_error
        raise RuntimeError(f"Failed to fetch {target_url}")

    def _host_min_interval(self, host):
        """Return minimum seconds between requests for a host."""
        if host.endswith("wikimedia.org") or host.endswith("wikipedia.org"):
            return self.wikimedia_min_interval
        return self.default_min_interval

    def _wait_for_host_slot(self, host):
        """Enforce a minimum inter-request delay per host."""
        if not host:
            return
        now = time.monotonic()
        ready_at = self._host_next_request_at.get(host, now)
        if ready_at > now:
            time.sleep(ready_at - now)
        self._host_next_request_at[host] = time.monotonic() + self._host_min_interval(host)

    def _get_retry_after_seconds(self, retry_after_value):
        """Parse Retry-After header into seconds."""
        if not retry_after_value:
            return None

        retry_after_value = retry_after_value.strip()
        if not retry_after_value:
            return None

        if retry_after_value.isdigit():
            return max(1.0, float(retry_after_value))

        try:
            retry_datetime = parsedate_to_datetime(retry_after_value)
            delta_seconds = (retry_datetime.timestamp() - time.time())
            return max(1.0, delta_seconds)
        except Exception:
            return None

    def _set_host_cooldown(self, host, seconds, status_code):
        """Pause requests to a host after rate limiting signals."""
        if not host:
            return
        cooldown_until = time.monotonic() + max(1.0, float(seconds))
        self._host_cooldown_until[host] = cooldown_until
        self._host_cooldown_logged.pop(host, None)
        logger.warning(
            f"Rate limited by {host} (HTTP {status_code}); "
            f"cooling down requests for {int(max(1.0, float(seconds)))}s."
        )

    def _respect_host_cooldown(self, host):
        """Return cooldown seconds remaining for a host and log once if active."""
        if not host:
            return 0.0

        cooldown_until = self._host_cooldown_until.get(host)
        if cooldown_until is None:
            return 0.0

        now = time.monotonic()
        if cooldown_until <= now:
            self._host_cooldown_until.pop(host, None)
            self._host_cooldown_logged.pop(host, None)
            return 0.0

        remaining_seconds = cooldown_until - now
        if not self._host_cooldown_logged.get(host):
            logger.info(
                f"Host {host} still rate-limited; skipping new requests for {int(remaining_seconds)}s."
            )
            self._host_cooldown_logged[host] = True
        return remaining_seconds

    def _rewrite_html_assets(self, soup, base_url, output_dir, asset_cache, capture_report):
        """Download referenced assets and rewrite HTML to local snapshot paths."""
        rewrite_count = 0

        for tag_name, attr_name in (
            ('img', 'src'),
            ('script', 'src'),
            ('script', 'href'),
            ('source', 'src'),
            ('video', 'src'),
            ('video', 'poster'),
            ('audio', 'src'),
            ('iframe', 'src'),
            ('embed', 'src'),
            ('track', 'src'),
            ('object', 'data'),
            ('input', 'src'),
            ('image', 'src'),
            ('image', 'href'),
            ('image', 'xlink:href'),
            ('use', 'href'),
            ('use', 'xlink:href'),
        ):
            for tag in soup.find_all(tag_name):
                rewrite_count += self._rewrite_tag_attr(
                    tag,
                    attr_name,
                    base_url,
                    output_dir,
                    asset_cache,
                    capture_report,
                )

        for tag in soup.find_all(srcset=True):
            rewrite_count += self._rewrite_srcset_attr(
                tag,
                base_url,
                output_dir,
                asset_cache,
                capture_report,
            )

        for link in soup.find_all('link', href=True):
            if not self._is_asset_link(link):
                continue
            rewrite_count += self._rewrite_tag_attr(
                link,
                'href',
                base_url,
                output_dir,
                asset_cache,
                capture_report,
            )

        for meta in soup.find_all('meta', content=True):
            key = (meta.get('property') or meta.get('name') or '').lower()
            if key in {'og:image', 'twitter:image', 'twitter:image:src', 'msapplication-tileimage'}:
                rewrite_count += self._rewrite_tag_attr(
                    meta,
                    'content',
                    base_url,
                    output_dir,
                    asset_cache,
                    capture_report,
                )

        for style_tag in soup.find_all('style'):
            css_text = style_tag.string if style_tag.string is not None else style_tag.get_text()
            if not css_text:
                continue
            rewritten_css = self._rewrite_css_urls(
                css_text,
                base_url,
                output_dir,
                asset_cache,
                capture_report,
            )
            if rewritten_css != css_text:
                style_tag.clear()
                style_tag.append(rewritten_css)
                rewrite_count += 1

        for tag in soup.find_all(style=True):
            current_style = tag['style']
            rewritten_style = self._rewrite_css_urls(
                current_style,
                base_url,
                output_dir,
                asset_cache,
                capture_report,
            )
            if rewritten_style != current_style:
                tag['style'] = rewritten_style
                rewrite_count += 1

        return rewrite_count

    def _rewrite_tag_attr(self, tag, attr_name, base_url, output_dir, asset_cache, capture_report):
        """Rewrite a URL-like tag attribute to a local snapshot path."""
        if tag is None or getattr(tag, "attrs", None) is None:
            return 0

        current_value = (tag.attrs or {}).get(attr_name)
        if not current_value:
            return 0

        if not isinstance(current_value, str):
            return 0

        current_value = current_value.strip()
        if not current_value or self._should_skip_resource(current_value):
            return 0

        rewritten = self._localize_resource(
            current_value,
            base_url,
            output_dir,
            asset_cache,
            capture_report,
        )
        if rewritten:
            if rewritten != current_value:
                tag[attr_name] = rewritten
                self._drop_sri_attrs(tag)
                return 1
            return 0

        self._block_resource_reference(tag, attr_name, current_value, capture_report)
        return 1

    def _rewrite_srcset_attr(self, tag, base_url, output_dir, asset_cache, capture_report):
        """Rewrite srcset entries to local snapshot assets and drop unresolved entries."""
        if tag is None or getattr(tag, "attrs", None) is None:
            return 0

        srcset_value = (tag.attrs or {}).get('srcset', '')
        if not srcset_value:
            return 0

        rewritten_entries = []
        changed = False

        for entry in srcset_value.split(','):
            entry = entry.strip()
            if not entry:
                continue

            parts = entry.split()
            resource_url = parts[0]

            if self._should_skip_resource(resource_url):
                rewritten_entries.append(entry)
                continue

            rewritten = self._localize_resource(
                resource_url,
                base_url,
                output_dir,
                asset_cache,
                capture_report,
            )
            if rewritten:
                if rewritten != resource_url:
                    changed = True
                    parts[0] = rewritten
                rewritten_entries.append(' '.join(parts))
            else:
                changed = True
                capture_report["blocked_references"] += 1
                self._record_missing_resource(resource_url, "srcset_unavailable", capture_report)

        if not changed:
            return 0

        if rewritten_entries:
            tag['srcset'] = ', '.join(rewritten_entries)
        else:
            tag.attrs.pop('srcset', None)
            tag['data-discoball-srcset-blocked'] = "true"
        return 1

    def _rewrite_css_urls(self, css_text, base_url, output_dir, asset_cache, capture_report):
        """Rewrite CSS url(...) and @import links to local snapshot assets."""
        def replace_url(match):
            raw_value = match.group(1).strip().strip('"\'')
            if self._should_skip_resource(raw_value):
                return match.group(0)

            rewritten = self._localize_resource(
                raw_value,
                base_url,
                output_dir,
                asset_cache,
                capture_report,
            )
            if rewritten:
                return f'url("{rewritten}")'

            capture_report["blocked_references"] += 1
            self._record_missing_resource(raw_value, "css_url_unavailable", capture_report)
            return 'url("")'

        def replace_import(match):
            raw_value = match.group(1).strip().strip('"\'')
            if self._should_skip_resource(raw_value):
                return ""

            rewritten = self._localize_resource(
                raw_value,
                base_url,
                output_dir,
                asset_cache,
                capture_report,
            )
            if rewritten:
                return f'@import "{rewritten}";'

            capture_report["blocked_references"] += 1
            self._record_missing_resource(raw_value, "css_import_unavailable", capture_report)
            return ""

        rewritten = re.sub(r'url\(([^)]+)\)', replace_url, css_text, flags=re.IGNORECASE)
        rewritten = re.sub(
            r'@import\s+(?:url\(\s*)?[\'"]?([^\'"\)\s;]+)[\'"]?\s*\)?\s*;?',
            replace_import,
            rewritten,
            flags=re.IGNORECASE,
        )
        return rewritten

    def _is_asset_link(self, link_tag):
        """Return True if a <link> tag likely points to a render asset."""
        if link_tag is None or getattr(link_tag, "attrs", None) is None:
            return False

        rel_attr = (link_tag.attrs or {}).get('rel', [])
        if isinstance(rel_attr, str):
            rel_attr = [rel_attr]
        rel_values = [value.lower() for value in rel_attr if isinstance(value, str)]
        if not rel_values:
            href = (link_tag.attrs or {}).get('href', '')
            return '.css' in href.lower()
        asset_rel_values = {
            'stylesheet',
            'icon',
            'preload',
            'modulepreload',
            'prefetch',
            'manifest',
            'apple-touch-icon',
            'mask-icon',
        }
        return any(value in asset_rel_values for value in rel_values)

    def _localize_resource(self, raw_resource_url, base_url, output_dir, asset_cache, capture_report):
        """Download a resource and return local path relative to snapshot root."""
        resource_url = raw_resource_url.strip()
        if self._should_skip_resource(resource_url):
            return None

        absolute_url = urljoin(base_url, resource_url)
        parsed = urlparse(absolute_url)
        if parsed.scheme not in ('http', 'https'):
            return None
        host = (parsed.hostname or '').lower()
        if self._respect_host_cooldown(host) > 0:
            self._record_missing_resource(absolute_url, f"skipped_rate_limited:{host}", capture_report)
            return None

        if absolute_url in asset_cache:
            return asset_cache[absolute_url]

        local_path = self._download_asset(
            absolute_url,
            base_url,
            output_dir,
            asset_cache,
            capture_report,
        )
        if local_path:
            asset_cache[absolute_url] = local_path
        return local_path

    def _download_asset(self, asset_url, referer_url, output_dir, asset_cache, capture_report):
        """Download a single asset and optionally rewrite nested CSS references."""
        try:
            response = self._fetch(asset_url, referer=referer_url)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '').split(';')[0].strip()
            local_path = self._build_asset_path(asset_url, content_type)
            absolute_output = os.path.join(output_dir, local_path)
            os.makedirs(os.path.dirname(absolute_output), exist_ok=True)

            # Register the path before CSS rewrite to prevent recursive import loops.
            asset_cache[asset_url] = local_path

            content = response.content
            if content_type == 'text/css':
                css_text = response.text
                rewritten_css = self._rewrite_css_urls(
                    css_text,
                    response.url,
                    output_dir,
                    asset_cache,
                    capture_report,
                )
                content = rewritten_css.encode('utf-8')

            with open(absolute_output, "wb") as output_file:
                output_file.write(content)

            capture_report["localized_downloads"] += 1
            return local_path
        except Exception as e:
            # Cache failures to avoid repeated retries/noisy logs for duplicate URLs.
            asset_cache[asset_url] = None
            capture_report["failed_downloads"] += 1
            self._record_missing_resource(asset_url, f"download_failed:{e}", capture_report)
            if "is in cooldown for another" not in str(e):
                logger.warning(f"Could not localize resource {asset_url}: {e}")
            return None

    def _build_asset_path(self, resource_url, content_type):
        """Generate deterministic local filename for an asset."""
        parsed = urlparse(resource_url)
        extension = self._extension_for_content_type(content_type)
        if not extension:
            _, path_extension = os.path.splitext(parsed.path)
            if self._is_safe_path_extension(path_extension):
                extension = path_extension.lower()
            else:
                extension = mimetypes.guess_extension(content_type) or '.bin'

        digest = hashlib.sha256(resource_url.encode('utf-8')).hexdigest()[:24]
        return os.path.join('assets', f"{digest}{extension.lower()}")

    def _is_safe_path_extension(self, extension):
        """Return True for URL path extensions safe to reuse as filenames."""
        if not extension or not re.fullmatch(r'\.[A-Za-z0-9]{1,10}', extension):
            return False

        dynamic_extensions = {'.php', '.asp', '.aspx', '.jsp', '.cgi', '.pl', '.do'}
        return extension.lower() not in dynamic_extensions

    def _extension_for_content_type(self, content_type):
        """Return a preferred extension for common web content-types."""
        if not content_type:
            return None

        normalized = content_type.strip().lower()
        extension_overrides = {
            'text/css': '.css',
            'text/javascript': '.js',
            'application/javascript': '.js',
            'application/x-javascript': '.js',
            'application/ecmascript': '.js',
            'text/ecmascript': '.js',
            'application/json': '.json',
            'application/ld+json': '.json',
            'application/manifest+json': '.webmanifest',
            'image/svg+xml': '.svg',
            'text/html': '.html',
            'application/xhtml+xml': '.html',
            'application/xml': '.xml',
            'text/xml': '.xml',
            'font/woff': '.woff',
            'font/woff2': '.woff2',
            'font/ttf': '.ttf',
            'font/otf': '.otf',
            'application/vnd.ms-fontobject': '.eot',
            'image/jpeg': '.jpg',
        }
        if normalized in extension_overrides:
            return extension_overrides[normalized]

        guessed = mimetypes.guess_extension(normalized)
        if guessed in ('.jpe', '.jpeg'):
            return '.jpg'
        return guessed

    def _should_skip_resource(self, resource_url):
        """Return True for non-downloadable URL forms."""
        if not resource_url:
            return True
        lowered = resource_url.lower()
        return (
            lowered.startswith('#')
            or lowered.startswith('data:')
            or lowered.startswith('javascript:')
            or lowered.startswith('mailto:')
            or lowered.startswith('tel:')
            or lowered.startswith('blob:')
            or lowered.startswith('about:')
        )

    def _block_resource_reference(self, tag, attr_name, original_url, capture_report):
        """Remove unresolved resource references so the snapshot does not call external origins."""
        capture_report["blocked_references"] += 1
        self._record_missing_resource(original_url, f"blocked:{tag.name}[{attr_name}]", capture_report)

        if tag is None or getattr(tag, "attrs", None) is None:
            return

        self._drop_sri_attrs(tag)
        if tag.name == 'link':
            tag.decompose()
            return

        tag.attrs.pop(attr_name, None)
        safe_attr = attr_name.replace(':', '-')
        tag[f"data-discoball-{safe_attr}-blocked"] = "true"

    def _drop_sri_attrs(self, tag):
        """Remove integrity/crossorigin attributes after URL rewrites."""
        if tag is None or getattr(tag, "attrs", None) is None:
            return
        for attr in ('integrity', 'crossorigin'):
            tag.attrs.pop(attr, None)

    def _record_missing_resource(self, resource_url, reason, capture_report):
        """Track resources that could not be captured for offline rendering."""
        seen = capture_report.get("_missing_seen")
        if seen is not None:
            key = f"{reason}|{resource_url}"
            if key in seen:
                return
            seen.add(key)
        capture_report["missing_resources"].append({
            "url": resource_url,
            "reason": reason,
        })

    def _strip_network_hints(self, soup, capture_report):
        """Remove browser hints that can trigger outbound network calls."""
        for base_tag in soup.find_all('base'):
            if base_tag is None or getattr(base_tag, "attrs", None) is None:
                continue
            base_href = ((base_tag.attrs or {}).get('href') or '').strip()
            if base_href:
                capture_report["blocked_references"] += 1
                self._record_missing_resource(base_href, "base_tag_removed", capture_report)
            base_tag.decompose()

        hint_rel_values = {'dns-prefetch', 'preconnect', 'prerender', 'pingback'}
        for link in soup.find_all('link'):
            if link is None or getattr(link, "attrs", None) is None:
                continue
            rel_attr = (link.attrs or {}).get('rel', [])
            if isinstance(rel_attr, str):
                rel_attr = [rel_attr]
            rel_values = {value.lower() for value in rel_attr if isinstance(value, str)}
            if rel_values.intersection(hint_rel_values):
                link_href = ((link.attrs or {}).get('href') or '').strip()
                if link_href:
                    capture_report["blocked_references"] += 1
                    self._record_missing_resource(link_href, "network_hint_removed", capture_report)
                link.decompose()

        for meta in soup.find_all('meta'):
            if meta is None or getattr(meta, "attrs", None) is None:
                continue
            if ((meta.attrs or {}).get('http-equiv') or '').lower() == 'refresh':
                refresh_value = ((meta.attrs or {}).get('content') or '').strip()
                if refresh_value:
                    capture_report["blocked_references"] += 1
                    self._record_missing_resource(refresh_value, "meta_refresh_removed", capture_report)
                meta.decompose()

    def _inject_offline_csp(self, soup):
        """Inject CSP to prevent loading assets from external origins."""
        head = self._ensure_head(soup)
        for meta in head.find_all('meta'):
            if (meta.get('http-equiv') or '').lower() == 'content-security-policy':
                meta.decompose()

        csp_value = (
            "default-src 'self' data: blob:; "
            "img-src 'self' data: blob:; "
            "media-src 'self' data: blob:; "
            "font-src 'self' data: blob:; "
            "style-src 'self' 'unsafe-inline' data: blob:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; "
            "connect-src 'self'; "
            "frame-src 'self' data: blob:; "
            "worker-src 'self' blob:; "
            "child-src 'self' blob:; "
            "object-src 'self' data: blob:; "
            "manifest-src 'self'; "
            "form-action 'self'; "
            "base-uri 'self'"
        )
        csp_tag = soup.new_tag('meta')
        csp_tag['http-equiv'] = 'Content-Security-Policy'
        csp_tag['content'] = csp_value
        head.insert(0, csp_tag)

    def _ensure_head(self, soup):
        """Ensure HTML has a head element and return it."""
        if soup.head:
            return soup.head

        if not soup.html:
            html_tag = soup.new_tag('html')
            for child in list(soup.contents):
                html_tag.append(child.extract())
            soup.append(html_tag)

        head_tag = soup.new_tag('head')
        soup.html.insert(0, head_tag)
        return head_tag

    def _extract_ipfs_hash(self, add_result, snapshot_dir):
        """Extract the root CID from ipfs add output."""
        if isinstance(add_result, str):
            return add_result

        if isinstance(add_result, dict):
            return add_result.get('Hash')

        if isinstance(add_result, list) and add_result:
            root_name = os.path.basename(os.path.abspath(snapshot_dir))
            for entry in reversed(add_result):
                if entry.get('Name') == root_name and entry.get('Hash'):
                    return entry['Hash']
            for entry in reversed(add_result):
                if entry.get('Hash'):
                    return entry['Hash']

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
            raw_tx = getattr(signed_txn, "rawTransaction", None)
            if raw_tx is None:
                raw_tx = getattr(signed_txn, "raw_transaction", None)
            if raw_tx is None:
                raise ValueError("Signed transaction missing raw transaction bytes")

            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            
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
    
    def mirror_site(self, domain, path, crawl_url):
        """Complete mirroring process: verify DNS, crawl, upload to IPFS, publish to contract."""
        logger.info(f"🪩 Starting mirror process for {crawl_url}")
        
        # Step 1: Verify DNS record
        dns_verified = self.verify_dns_record(domain)
        if not dns_verified:
            logger.warning("⚠️ DNS verification did not pass. Proceeding anyway; this mirror will be marked UNVERIFIED.")
        
        with tempfile.TemporaryDirectory(prefix="discoball-snapshot-") as snapshot_dir:
            # Step 2: Crawl the page and build a browsable snapshot bundle
            snapshot = self.crawl_page(crawl_url, domain, path, snapshot_dir)
            if not snapshot:
                logger.error("Failed to crawl page. Cannot proceed.")
                return False, dns_verified

            # Step 3: Upload snapshot bundle directory to IPFS
            ipfs_hash = self.upload_to_ipfs(snapshot_dir)
            if not ipfs_hash:
                logger.error("Failed to upload to IPFS. Cannot proceed.")
                return False, dns_verified
        
        # Step 4: Publish to smart contract
        if self.publish_to_contract(domain, path, ipfs_hash):
            logger.info(f"🎉 Successfully mirrored {domain}{path}")
            logger.info(f"   IPFS Hash: {ipfs_hash}")
            logger.info(f"   Gateway URL: http://127.0.0.1:8080/ipfs/{ipfs_hash}")
            if dns_verified:
                logger.info("✅ DNS status: VERIFIED")
            else:
                logger.warning("⚠️ DNS status: UNVERIFIED")
            return True, dns_verified
        else:
            logger.error("Failed to publish to smart contract.")
            return False, dns_verified


def parse_target_url(raw_url):
    """Parse user-provided URL into normalized crawl URL, domain, and path."""
    candidate = raw_url.strip()
    if not candidate:
        raise ValueError("URL cannot be empty")

    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL scheme must be http or https")
    if not parsed.hostname:
        raise ValueError("URL must include a valid host")

    domain = parsed.hostname
    path = parsed.path or "/"
    if parsed.params:
        path = f"{path};{parsed.params}"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    crawl_url = f"{parsed.scheme}://{parsed.netloc}{path}"
    return domain, path, crawl_url


def resolve_private_key(private_key_arg, private_key_file):
    """Resolve private key from CLI arg, env var, or default key file."""
    if private_key_arg:
        return private_key_arg.strip()

    env_private_key = os.getenv("PRIVATE_KEY", "").strip()
    if env_private_key:
        logger.info("Using private key from PRIVATE_KEY environment variable")
        return env_private_key

    if os.path.exists(private_key_file):
        with open(private_key_file, "r", encoding="utf-8") as f:
            file_key = f.read().strip()
        if file_key:
            logger.info(f"Using private key from {private_key_file}")
            return file_key
        raise ValueError(f"Private key file is empty: {private_key_file}")

    raise ValueError(
        f"No private key found. Provide --private-key, set PRIVATE_KEY, "
        f"or create {private_key_file} via deploy-and-verify."
    )

def main():
    parser = argparse.ArgumentParser(description='🪩 Disco Dance - Mirror your own site')
    parser.add_argument('url', help='Full URL to mirror (e.g., https://example.com/page)')
    parser.add_argument('--private-key', help='Ethereum private key')
    parser.add_argument(
        '--private-key-file',
        default='.secrets/deployer-base.key',
        help='Fallback private key file (default: .secrets/deployer-base.key)'
    )
    parser.add_argument('--rpc-url', default='https://mainnet.base.org', help='RPC URL for Base network')
    parser.add_argument('--ipfs-api', default='/ip4/127.0.0.1/tcp/5001', help='IPFS API endpoint')
    
    args = parser.parse_args()
    
    try:
        domain, path, crawl_url = parse_target_url(args.url)
        private_key = resolve_private_key(args.private_key, args.private_key_file)

        # Initialize disco mirror
        mirror = DiscoMirror(private_key, args.rpc_url, args.ipfs_api)
        
        # Mirror the site
        success, dns_verified = mirror.mirror_site(domain, path, crawl_url)
        
        if success:
            print(f"\n🎉 Successfully mirrored {crawl_url}")
            if not dns_verified:
                print("⚠️ Mirror published without DNS verification (UNVERIFIED).")
            exit(0)
        else:
            print(f"\n❌ Failed to mirror {crawl_url}")
            if not dns_verified:
                print("⚠️ DNS verification did not pass (UNVERIFIED).")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n👋 Disco dance interrupted!")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main() 
