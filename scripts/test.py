from bs4 import BeautifulSoup
import requests
import mysql.connector

URLS = [
'https://acsjournals.onlinelibrary.wiley.com/doi/epdf/10.1002/%28SICI%291097-0142%2819970615%2979%3A12%3C2396%3A%3AAID-CNCR15%3E3.0.CO%3B2-M',
'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2247100/pdf/brjcancer00120-0090.pdf',
'https://onlinelibrary.wiley.com/doi/full/10.1002/ijc.20434',
'https://acsjournals.onlinelibrary.wiley.com/doi/10.1002/%28SICI%291097-0142%2819970615%2979%3A12%3C2396%3A%3AAID-CNCR15%3E3.0.CO%3B2-M',
'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4820665/',
'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9360263/',
'https://pubmed.ncbi.nlm.nih.gov/31910280/',
]

def extract_html_from_url(url):
    req = requests.get(url, 'html.parser', headers={
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36'})
    if req.status_code == 200:
        # Get the content of the response
        page_content = req.content

        # Create a BeautifulSoup object and specify the parser
        soup = BeautifulSoup(page_content, 'html.parser')
        # Find the section element with role='document'

        section = soup.find('section', attrs={'role':'document'})

        # Print the text within this section
        if section:
            print(section)
        else:
            print("No section with role='document' found.")
    else:
        print("Failed to retrieve the URL")



def main():
    #extract_html_from_url(URLS[6])
    print()
    print(dashboard())

main()
