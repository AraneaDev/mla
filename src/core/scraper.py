"""
Meme Scraping Module
Handles fetching memes from various online sources
"""

import requests
from bs4 import BeautifulSoup
import random
import hashlib
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import re

from config import config

class ScrapingError(Exception):
    """Custom exception for scraping errors"""
    pass

class MemeScraper:
    """Advanced meme scraper with multiple source support"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.scraping.user_agent
        })

        # Configure session for better reliability
        self.session.timeout = config.scraping.request_timeout

        # Track failed sources to avoid repeated attempts
        self.failed_sources = set()

        print("🔍 MemeScraper initialized")

    def scrape_memedroid(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Enhanced Memedroid scraping with multiple page support"""
        if 'memedroid' in self.failed_sources:
            return []

        try:
            # Get configuration
            memedroid_config = config.scraping.sources.get('memedroid', {})
            if not memedroid_config.get('enabled', True):
                return []

            pages = memedroid_config.get('pages', ['feed'])
            selectors = memedroid_config.get('selectors', ['article.gallery-item'])

            # Choose random page for variety
            page = random.choice(pages)
            url = (f"https://www.memedroid.com/memes/tag/{page}"
                   if page != 'feed' else "https://www.memedroid.com/memes/tag/feed")

            response = self.session.get(url, timeout=config.scraping.request_timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            memes = []
            seen_urls = set()

            # Try different selectors until we find memes
            meme_items = []
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    meme_items = items[:limit * 2]  # Get extra for filtering
                    break

            if not meme_items:
                raise ScrapingError("No meme items found with any selector")

            for item in meme_items:
                if len(memes) >= limit:
                    break

                try:
                    img_tag = item.find('img')
                    if not img_tag or not img_tag.get('src'):
                        continue

                    # Process image URL
                    meme_url = img_tag['src']
                    if meme_url.startswith('//'):
                        meme_url = 'https:' + meme_url
                    elif meme_url.startswith('/'):
                        meme_url = 'https://www.memedroid.com' + meme_url

                    # Skip duplicates
                    if meme_url in seen_urls:
                        continue
                    seen_urls.add(meme_url)

                    # Validate URL
                    if not self._is_valid_image_url(meme_url):
                        continue

                    # Get title
                    title_tag = (item.find('h2') or item.find('h3') or
                               item.find(class_='meme-title'))
                    title = (title_tag.get_text(strip=True)
                           if title_tag else f"Memedroid Meme #{len(memes)+1}")

                    # Generate unique ID
                    meme_id = hashlib.md5(
                        (meme_url + str(time.time()) + title).encode()
                    ).hexdigest()

                    memes.append({
                        'id': meme_id,
                        'url': meme_url,
                        'title': self._clean_title(title),
                        'source': 'memedroid',
                        'tags': ['general', page, 'memedroid']
                    })

                except Exception as e:
                    continue  # Skip problematic items

            print(f"✅ Memedroid: Found {len(memes)} memes from page '{page}'")
            return memes

        except Exception as e:
            print(f"❌ Memedroid scraping failed: {e}")
            self.failed_sources.add('memedroid')
            return []

    def scrape_reddit(self, subreddit: str = 'memes', limit: int = 15) -> List[Dict[str, Any]]:
        """Enhanced Reddit scraping with multiple sort types"""
        source_key = f'reddit_{subreddit}'
        if source_key in self.failed_sources:
            return []

        try:
            # Get configuration
            reddit_config = config.scraping.sources.get('reddit', {})
            if not reddit_config.get('enabled', True):
                return []

            sort_types = reddit_config.get('sort_types', ['hot'])

            # Choose random sort type for variety
            sort_type = random.choice(sort_types)
            time_filter = '?t=day' if sort_type == 'top' else ''

            # Build URL
            url = (f"https://www.reddit.com/r/{subreddit}/{sort_type}.json"
                   f"?limit={limit * 3}{time_filter}")

            response = self.session.get(url, timeout=config.scraping.request_timeout)
            response.raise_for_status()

            data = response.json()

            if 'data' not in data or 'children' not in data['data']:
                raise ScrapingError("Invalid Reddit API response structure")

            memes = []
            seen_urls = set()

            for post in data['data']['children']:
                if len(memes) >= limit:
                    break

                try:
                    post_data = post.get('data', {})
                    post_url = post_data.get('url', '')

                    # Filter for image posts
                    if not self._is_valid_image_url(post_url):
                        continue

                    # Skip duplicates
                    if post_url in seen_urls:
                        continue
                    seen_urls.add(post_url)

                    # Skip NSFW content
                    if post_data.get('over_18', False):
                        continue

                    # Generate unique ID
                    post_id = post_data.get('id', '')
                    meme_id = f"{post_id}_{int(time.time())}"

                    title = self._clean_title(post_data.get('title', 'Reddit Meme'))

                    memes.append({
                        'id': meme_id,
                        'url': post_url,
                        'title': title[:100],  # Limit title length
                        'source': f'reddit_{subreddit}',
                        'tags': [subreddit, 'reddit', sort_type]
                    })

                except Exception as e:
                    continue  # Skip problematic posts

            print(f"✅ Reddit r/{subreddit}: Found {len(memes)} memes ({sort_type})")
            return memes

        except Exception as e:
            print(f"❌ Reddit r/{subreddit} scraping failed: {e}")
            self.failed_sources.add(source_key)
            return []

    def get_random_memes(self, count: int = None) -> List[Dict[str, Any]]:
        """Get diverse memes from multiple sources"""
        if count is None:
            count = config.scraping.default_meme_count

        # Clear failed sources occasionally to retry
        if len(self.failed_sources) > 3:
            self.failed_sources.clear()

        all_memes = []

        # Define source functions with weights
        reddit_config = config.scraping.sources.get('reddit', {})
        subreddits = reddit_config.get('subreddits', ['memes', 'funny'])

        sources = [
            ('memedroid', lambda: self.scrape_memedroid(count // 3)),
        ]

        # Add Reddit sources
        for subreddit in subreddits:
            sources.append((
                f'reddit_{subreddit}',
                lambda sr=subreddit: self.scrape_reddit(sr, count // len(subreddits))
            ))

        # Randomize source order for variety
        random.shuffle(sources)

        # Collect memes from all sources
        for source_name, scraper_func in sources:
            try:
                memes = scraper_func()
                if memes:
                    all_memes.extend(memes)
                    print(f"✅ {source_name}: Added {len(memes)} memes")
                else:
                    print(f"⚠️ {source_name}: No memes found")

            except Exception as e:
                print(f"❌ {source_name}: Scraping failed - {e}")
                continue

        # Remove duplicates by URL
        unique_memes = self._remove_duplicates(all_memes)

        # Shuffle for randomness
        random.shuffle(unique_memes)

        # Return requested count
        final_memes = unique_memes[:count]

        print(f"🎯 Final collection: {len(final_memes)} unique memes from {len(set(m['source'] for m in final_memes))} sources")
        return final_memes

    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL points to a valid image"""
        if not url or not isinstance(url, str):
            return False

        # Check for image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        url_lower = url.lower()

        # Direct image URL
        if any(url_lower.endswith(ext) for ext in image_extensions):
            return True

        # Common image hosting patterns
        image_hosts = [
            'i.redd.it', 'i.imgur.com', 'imgur.com',
            'memedroid.com', 'imgflip.com'
        ]

        try:
            parsed = urlparse(url)
            if any(host in parsed.netloc for host in image_hosts):
                return True
        except Exception:
            pass

        return False

    def _clean_title(self, title: str) -> str:
        """Clean and normalize meme title"""
        if not title or not isinstance(title, str):
            return "Untitled Meme"

        # Remove excessive whitespace
        title = re.sub(r'\s+', ' ', title.strip())

        # Remove common Reddit prefixes
        prefixes_to_remove = [
            r'^\[OC\]\s*',
            r'^\[MEME\]\s*',
            r'^\w+\s*\|\s*',  # Subreddit prefixes
        ]

        for prefix in prefixes_to_remove:
            title = re.sub(prefix, '', title, flags=re.IGNORECASE)

        # Limit length
        if len(title) > 200:
            title = title[:197] + "..."

        return title.strip() or "Untitled Meme"

    def _remove_duplicates(self, memes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate memes by URL"""
        seen_urls = set()
        unique_memes = []

        for meme in memes:
            url = meme.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_memes.append(meme)

        return unique_memes

    def get_source_status(self) -> Dict[str, Any]:
        """Get status of all scraping sources"""
        status = {
            'available_sources': list(config.scraping.sources.keys()),
            'failed_sources': list(self.failed_sources),
            'active_sources': [],
            'last_check': time.time()
        }

        # Determine active sources
        for source in config.scraping.sources:
            if (config.scraping.sources[source].get('enabled', True) and
                source not in self.failed_sources):
                status['active_sources'].append(source)

        return status

    def reset_failed_sources(self):
        """Reset failed sources list to retry them"""
        self.failed_sources.clear()
        print("🔄 Reset failed sources - will retry all sources")

    def test_source(self, source_name: str) -> bool:
        """Test if a specific source is working"""
        try:
            if source_name == 'memedroid':
                memes = self.scrape_memedroid(1)
                return len(memes) > 0
            elif source_name.startswith('reddit_'):
                subreddit = source_name.replace('reddit_', '')
                memes = self.scrape_reddit(subreddit, 1)
                return len(memes) > 0
            else:
                return False

        except Exception as e:
            print(f"❌ Source test failed for {source_name}: {e}")
            return False

    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get scraping statistics and performance metrics"""
        return {
            'session_info': {
                'timeout': self.session.timeout,
                'user_agent': self.session.headers.get('User-Agent', 'Unknown')
            },
            'source_config': config.scraping.sources,
            'failed_sources_count': len(self.failed_sources),
            'total_configured_sources': len(config.scraping.sources)
        }