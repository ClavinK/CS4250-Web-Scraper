from web_scraper import WebScraper


def main():

    # Initialize web scraper class
    scraper = WebScraper()

    # web_crawler function call, 13 is target number
    scraper.web_crawler(13)
    
    # For testing, and proof that web crawler works
    for number, page in enumerate(scraper.faculty_pages, start=1):
        print(f"{number}. {page['facultyName']}")
        print(f"   URL: {page['url']}")
        print(f"   Content: {page['content']}")
        print("-" * 60)


if __name__ == "__main__":
    main()
