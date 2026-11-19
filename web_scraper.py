from pymongo import MongoClient
import string
import requests
from bs4 import BeautifulSoup

# Uncomment when ready to work with DB
# client = MongoClient("mongodb://localhost:27017/")

# db = client["CS4250WebScraper"]
# documents = db["documents"]
# inverted_index = db["inverted_index"]

# Biology track
seed = "https://www.cpp.edu/sci/biological-sciences/index.shtml"

# List of faculty pages for scraping later
faculty_pages = []

# Main web crawler function
def web_crawler(seed, num_targets):
    
    targets_found = 0
    frontier = [seed]
    seen = {seed}
    
    while frontier:
        url = frontier.pop(0)
        
        html = requests.get(url)
        html.raise_for_status()
        
        soup = BeautifulSoup(html.text, "html.parser")
        
        facultyName = None
        
        if target_page(url, soup):
            facultyName = extractFacultyName(soup)
            targets_found += 1
        storePage(url, facultyName, soup)
        if targets_found == num_targets:
            frontier.clear()
            return
        else:
            links = extractLinks(soup)
            for link in links:
                if link in seen:
                    continue
                else:
                    seen.append(link)
                    frontier.append(link)
        
        
# Function to check faculty pages URL prefix
def target_page(url, html):
    url_prefix = "https://www.cpp.edu/faculty/"
    
    return (
        url.startswith(url_prefix)
        and html.find("h1", class_="profheader") is not None
    )
        
# Function for extracting faculty member's name from site
def extractFacultyName(html):
    name = html.find("h1", class_="profheader")
    
    if name is not None:
        return name.get_text(strip=True)
    
    return None

# Function for storing page
def storePage(url, facultyName, html):
    if facultyName is None:
        return
    else:
        faculty_pages.append({
            "url": url,
            "facultyName": facultyName,
            "html": html
        })
        
# Function for extracting links from HTML (NEEDS WORK)
def extractLinks(html):
    return
        
        