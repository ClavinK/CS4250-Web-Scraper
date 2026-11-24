from urllib.parse import urljoin

from pymongo import MongoClient
import string
import requests
from bs4 import BeautifulSoup

# Uncomment when ready to work with DB
# client = MongoClient("mongodb://localhost:27017/")

# db = client["CS4250WebScraper"]
# documents = db["documents"]
# inverted_index = db["inverted_index"]
class WebScraper():
    
    def __init__(self):
        # Biology Track
        self.seed = "https://www.cpp.edu/sci/biological-sciences/index.shtml"
        
        # List of faculty pages for scraping later
        self.faculty_pages = []
    
    # Main web crawler function
    def web_crawler(self, num_targets):
        
        targets_found = 0
        frontier = [self.seed]
        seen = {self.seed}
        
        while frontier and targets_found < num_targets:
            url = frontier.pop(0)
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
            except requests.RequestException:
                continue
            
            html = response.text
            
            soup = BeautifulSoup(html, "html.parser")
            
            facultyName = None
            
            if self.target_page(url, soup):
                facultyName = self.extractFacultyName(soup)
                targets_found += 1
            self.storePage(url, facultyName, html)
            if targets_found == num_targets:
                frontier.clear()
                for i in self.faculty_pages:
                    print(i["url"])
                return
            else:
                links = self.extractLinks(url, soup)
                for link in links:
                    if link in seen:
                        continue
                    else:
                        seen.add(link)
                        frontier.append(link)
            
            
    # Function to check faculty pages URL prefix
    def target_page(self, url, html):
        url_prefix = "https://www.cpp.edu/faculty/"
        
        return (
            url.startswith(url_prefix)
            and html.find("h1", class_="profheader") is not None
        )
            
    # Function for extracting faculty member's name from site
    def extractFacultyName(self, html):
        name = html.find("h1", class_="profheader")
        
        if name is not None:
            return name.get_text(strip=True)
        
        return None

    # Function for storing page
    def storePage(self, url, facultyName, html):
        if facultyName is None:
            return
        else:
            self.faculty_pages.append({
                "url": url,
                "facultyName": facultyName,
                "html": html
            })
            
    # Function for extracting links from HTML (NEEDS WORK)
    def extractLinks(self, url, html):
        links = []
        BIOLOGY_PREFIX = "https://www.cpp.edu/sci/biological-sciences/"
        FACULTY_PREFIX = "https://www.cpp.edu/faculty/"
        
        for tag in html.find_all("a", href=True):
            raw_url = tag["href"].strip()
            
            if (
                not raw_url
                or raw_url.startswith((
                    "mailto:",
                    "javascript:",
                    "tel:",
                    "#"
                ))
                or "${" in raw_url
            ):
                continue
            
            absolute_url = urljoin(url, raw_url)
            if absolute_url.startswith((BIOLOGY_PREFIX, FACULTY_PREFIX)):
                links.append(absolute_url)
        return links
        