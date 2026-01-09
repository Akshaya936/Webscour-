import pika                      # to communicate with RabbitMQ 
import requests                  # HTTP requests to fetch web pages 
from bs4 import BeautifulSoup    # HTML parsing to extract links 
import time                      # Used for timestamps & performance tracking 
import os                        # File and process operations 
import threading                 # Run multiple workers in parallel 


MAX_PAGES = 30      # Maximum pages to crawl 
NUM_WORKERS = 3      # Number of parallel workers 

visited_urls = set() # Shared visited URL set 
pages_crawled = 0    # Counter for crawled pages 

lock = threading.Lock()  # Thread lock to protect shared data 
START_TIME = time.time() # Start time for performance analysis 


# FETCH PAGE FUNCTION 

def fetch_page(url, retries=3):
    # Header to identify our crawler
    header = {"User-Agent": "WebScourCrawler/1.0"}

    # Retry logic: try fetching page up to 3 times
    for attempt in range(1, retries + 1):
        try:
            # Send HTTP GET request
            response = requests.get(url, timeout=5, headers=header)

            # If response is valid and has content, return HTML
            if response.ok and response.text.strip():
                return response.text
            
        # catch any network or request-related error
        except Exception as e:
            # Print error if request fails
            print(f"[Attempt {attempt}] Error fetching {url}: {e}")

        # Wait before retrying
        time.sleep(1)

    # Return None if all retries fail
    return None

# EXTRACT LINKS FUNCTION 

def extract_links(html):
    # Parse HTML content
    soup = BeautifulSoup(html, "html.parser")

    # Extract all href links
    return [a.get("href") for a in soup.find_all("a", href=True)]


# FILTER LINKS FUNCTION 

def filter_link(link):
    # Ignore empty links
    if not link:
        return None

    # Ignore unwanted schemes
    if link.startswith(("mailto:", "javascript:", "#", "tel:")):
        return None

    # Accept only valid HTTP/HTTPS URLs
    if not link.startswith(("http://", "https://")):
        return None

    return link


# CORE CRAWL LOGIC 

def crawl(url, worker_id, ch, method):
    global pages_crawled

    # Duplicate & limit check 
    with lock:
        if url in visited_urls or pages_crawled >= MAX_PAGES:
            ch.basic_ack(method.delivery_tag)  # Acknowledge and skip
            return
        visited_urls.add(url)

    # Log which worker is crawling which URL 
    print(f"[WORKER-{worker_id}] Crawling -> {url}")

    # Fetch web page 
    html = fetch_page(url)
    if not html:
        ch.basic_ack(method.delivery_tag)  # Acknowledge failed crawl
        return

    # Create directory to save pages
    os.makedirs("pages", exist_ok=True)

    # Generate unique filename
    filename = f"pages/{int(time.time()*1000)}.html"

    # Save HTML content 
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[SAVED] {filename}")

    # Update page counter safely 
    with lock:
        pages_crawled += 1

    # Extract links from HTML 
    links = extract_links(html)

    # Publish new links back to RabbitMQ queue 
    for link in links:
        clean = filter_link(link)
        if clean:
            with lock:
                #send newly discovered URLs back to RabbitMQ
                if clean not in visited_urls and pages_crawled < MAX_PAGES:
                    ch.basic_publish(
                        exchange='',
                        routing_key='url_queue',
                        body=clean
                    )

    # Acknowledge message AFTER successful processing 
    ch.basic_ack(method.delivery_tag)

    # Stop condition when max pages reached 
    with lock:
        if pages_crawled >= MAX_PAGES:
            stop_all()


# WORKER THREAD FUNCTION 

def start_worker(worker_id):
    # Create a connection to the RabbitMQ server running on localhost
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    # Declare shared queue 
    channel.queue_declare(queue='url_queue', durable=True)

    # Fair dispatch: one message per worker at a time 
    channel.basic_qos(prefetch_count=1)

    # Callback when URL is received from queue 
    def callback(ch, method, properties, body):
        url = body.decode()
        crawl(url, worker_id, ch, method)

    print(f"[WORKER-{worker_id}] Waiting for URLs...")

    # Start consuming URLs from queue
    channel.basic_consume(queue='url_queue', on_message_callback=callback)
    channel.start_consuming()


# STOP & SUMMARY FUNCTION 

def stop_all():
    total_time = round(time.time() - START_TIME, 2)

    print("\n========== SUMMARY ==========")
    print("Workers used        :", NUM_WORKERS)
    print("Total pages crawled :", pages_crawled)
    print("Time taken (sec)    :", total_time)
    print("=============================")

    # Force exit all threads
    os._exit(0)


# MAIN 

if __name__ == "__main__":
    threads = []

    # Start multiple workers in parallel 
    for i in range(1, NUM_WORKERS + 1):
        t = threading.Thread(target=start_worker, args=(i,))
        t.start()
        threads.append(t)

    # Wait for all worker threads
    for t in threads:
        t.join()
