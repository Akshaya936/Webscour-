# Webscour-
Infosys springboard project 

#  WebScour – Mini Search Engine

A simple search engine built in 4 phases.

---

##  **Milestone 1 – Basic Crawler**

* Fetches web pages starting from a seed URL
* Extracts hyperlinks
* Avoids duplicates
* Saves HTML files into `pages/`

---

##  **Milestone 2 – Parallel Crawler**

* Uses RabbitMQ + worker threads
* Multiple workers crawl URLs at the same time
* Extract new links and push back to queue
* Stops after crawling set number of pages
* Saves all pages inside `pages/`

---

##  **Milestone 3 – Indexing (TF-IDF)**

* Read every HTML file from `pages/`
* Extract text using BeautifulSoup
* Tokenize text (lowercase + remove punctuation)
* Compute:

  * **TF (term frequency per document)**
  * **IDF (importance across documents)**
* Build inverted index:

  ```
  word → [(document_id, frequency), ...]
  ```
* Save:

  * `inverted_index.json`
  * `idf.json`

---

##  **Milestone 4 – Search App**

* Flask web UI
* User enters search words
* Search engine uses TF × IDF scores
* Returns most relevant documents
* Shows results ranked by score

---

## Final Outcome

✔ Crawl websites
✔ Build searchable index
✔ Rank pages using TF-IDF
✔ Search through crawled pages using a browser


