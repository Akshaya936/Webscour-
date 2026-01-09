import requests  # to send https request
from bs4 import BeautifulSoup  # for parsing html pages
import time  # to add delays and measure execution time
import os   # to create directories and execute files
from urllib.parse import urlparse  # to extract domain information from URLs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# TASK 6: Retry logic for failed URLs
# FUNCTION: Fetch page with retry mechanism
# Attempts to download a webpage up to 3 times before failing.
def fetch_page(url, retries=3):
    header = {"User-Agent": "WebScourCrawler/1.0"}   # Identifies crawler to the server
    # Loop for retry attempts
    for attempt in range(1, retries + 1):
        try:
            # Send HTTP GET request
            response = requests.get(url, timeout=5, headers=header)

            # Check if the response is valid and has content
            if response.ok and response.text.strip():
                return response.text     

            print(f"[Attempt {attempt}] Failed response for {url}")

        # catch any network or request-related error
        except Exception as e:
            print(f"[Attempt {attempt}] Error fetching {url}: {e}")

        time.sleep(1)   # Wait before retrying to avoid overwhelming the server

    # If all retries fail, return None
    return None


# FUNCTION: Extract all links from the HTML page 
# BeautifulSoup helps parse HTML easily
def extract_links(html):
    soup = BeautifulSoup(html, "html.parser")
    # return all href values found in anchor tags
    return [a.get("href") for a in soup.find_all("a", href=True)]


# FUNCTION: Filter useless, invalid, or external links 
# # Keeps only clean, valid HTTP/HTTPS URLs from the same domain.
def filter_link(link, seed_domain):
    
    # TASK 3: Filter useless links
    # Ignore useless links (not real webpages)
    if (
        link.startswith("mailto:") or
        link.startswith("javascript:") or
        link.startswith("tel:") or
        link.startswith("#") or
        not link.strip()                     # Skip empty href
    ):
        return None

    # Only accept full URLs (relative URLs are skipped for now)
    if not link.startswith(("http://", "https://")):
        return None
    
    # TASK 4: Same-domain crawling only
    # Restrict crawling only to same domain as seed
    if urlparse(link).netloc != seed_domain:
        return None

    return link    


# MAIN FUNCTION: Crawl pages starting from seed URL
def crawl(seed_url, MAX_PAGES):

    # Extract domain name from the seed URL
    seed_domain = urlparse(seed_url).netloc

    queue = [seed_url]           # Queue to store URLs waiting to be crawled
    visited = set()              # To prevent re-visiting URLs
    unique_urls = set()          # Track all unique discovered URLs
    duplicate_count = 0          # Count duplicates found

    page_id = 1                  # Increment for saved pages

    # TASK 2: Create folder to store downloaded pages
    PAGES_DIR = os.path.join(BASE_DIR, "pages")
    os.makedirs(PAGES_DIR, exist_ok=True)

    

    print(f"Seed URL: {seed_url}\nStarting crawler...\n")
    start_time = time.time()     # Track total crawl time
    
    # TASK 1: Crawl only up to MAX_PAGES
    # Crawl until we either reach MAX_PAGES or queue becomes empty
    while queue and page_id <= MAX_PAGES:
        url = queue.pop(0)

        # Skip URLs already visited
        if url in visited:
            duplicate_count += 1
            continue

        print(f"\n=== Crawling page {page_id}: {url} ===")

        # Start timing for this page
        page_start_time = time.time()

        # Download HTML page
        html = fetch_page(url)
        
        # If page download fails, skip URL
        if html is None:
            print("Failed to fetch:", url)
            continue     # Skip to next URL
        
        
        # TASK 1: Save the HTML page inside pages/ folder
        filename = os.path.join(PAGES_DIR, f"page_{page_id}.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved: {filename}")

        # Extract all links from the HTML page
        links = extract_links(html)
        before = len(queue)   # Queue size before adding new links

        added_links = []      # To count how many new links added

        # Process each extracted link
        for link in links:

            cleaned = filter_link(link, seed_domain)

            # Skip invalid links  
            if not cleaned:
                continue

            # Count unique & duplicate URLs
            if cleaned not in unique_urls:
                unique_urls.add(cleaned)
            else:
                duplicate_count += 1

            # Add to queue if not already seen
            if cleaned not in visited and cleaned not in queue:
                queue.append(cleaned)
                added_links.append(cleaned)

        # Store queue size after adding links
        after = len(queue)

        # Show crawling progress
        print(f"Links added: {len(added_links)}")
        print(f"Queue size: {before} -> {after}")

        # Mark current URL as visited
        visited.add(url)
        page_id += 1           # Move to next page number
        
        # End timing for this page
        page_time = round(time.time() - page_start_time, 2)
        print(f"Time taken for this page: {page_time} seconds")

        # Sleep between requests
        time.sleep(0.5)

    total_time = round(time.time() - start_time, 2)

    # TASK 5:Save visited URLs to a file
    with open("visited.txt", "w") as f:
        for u in visited:
            f.write(u + "\n")

    # Print summary
    print("\n========== SUMMARY ==========")
    print("Pages crawled:", len(visited))
    print("Total time:", total_time, "seconds")
    print("Unique URLs:", len(unique_urls))
    print("Duplicates:", duplicate_count)
    print("Final queue size:", len(queue))

if __name__ == "__main__":
    seed = "https://www.geeksforgeeks.org/"   # Starting URL
    MAX_PAGES = 10                    # crawl first 10 pages
    crawl(seed, MAX_PAGES)
