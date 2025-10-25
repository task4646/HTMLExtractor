import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse

def organize_text(text, soup):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    categories = {
        "headings": [],
        "paragraphs": [],
        "lists": [],
        "links": [],
        "quotes": [],
        "other": []
    }
    for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        for element in soup.find_all(tag):
            text = element.get_text(strip=True).lower()
            if text:
                categories["headings"].append({"tag": tag, "text": text})
    for element in soup.find_all('p'):
        text = element.get_text(strip=True).lower()
        if text:
            categories["paragraphs"].append(text)
    for list_type in ['ul', 'ol']:
        for lst in soup.find_all(list_type):
            for item in lst.find_all('li'):
                text = item.get_text(strip=True).lower()
                if text:
                    categories["lists"].append({"type": list_type, "item": text})
    for element in soup.find_all('a'):
        text = element.get_text(strip=True).lower()
        href = element.get('href', '')
        if text:
            categories["links"].append({"text": text, "href": href})
    for element in soup.find_all('blockquote'):
        text = element.get_text(strip=True).lower()
        if text:
            categories["quotes"].append(text)
    for element in soup.find_all(['div', 'span', 'article', 'section']):
        if not element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'a', 'blockquote']):
            text = element.get_text(strip=True).lower()
            if text:
                categories["other"].append({"tag": element.name, "text": text})
    for line in lines:
        line = line.lower()
        if not any(line in item['text'] for cat in categories.values() for item in cat if isinstance(item, dict)) and \
           not any(line == item for cat in categories.values() for item in cat if isinstance(item, str)):
            if line.isupper() or len(line) < 40 or line.endswith(':'):
                categories["headings"].append({"tag": "inferred", "text": line})
            elif re.match(r'^[-*+•]\s|^\d+\.\s|^[a-z]\)\s', line):
                categories["lists"].append({"type": "inferred", "item": line})
            elif 'http' in line.lower() or 'www.' in line.lower():
                categories["links"].append({"text": line, "href": ""})
            elif line.startswith('>') or '"' in line or "'" in line:
                categories["quotes"].append(line)
            elif len(line) > 50:
                categories["paragraphs"].append(line)
            else:
                categories["other"].append({"tag": "inferred", "text": line})
    return {k: v for k, v in categories.items() if v}

url = input("enter website url (e.g., https://example.com): ").strip()
if not url.startswith(('http://', 'https://')):
    url = 'https://' + url

try:
    headers = {'user-agent': 'mozilla/5.0 (windows nt 10.0; win64; x64) chrome/91.0.4472.124'}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()
    page_text = soup.get_text(separator='\n', strip=True)
    organized_content = organize_text(page_text, soup)
    json_data = {
        "page_url": url,
        "extracted_at": datetime.now().isoformat(),
        "total_characters": len(page_text),
        "total_lines": len(page_text.splitlines()),
        "content": organized_content
    }
    json_output = json.dumps(json_data, indent=2, ensure_ascii=False)
    domain = urlparse(url).netloc.split('.')[0]
    output_file = f"{domain}_extracted.json"
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(json_output)
    print(f"text extracted and saved to {output_file}")
    print(f"total characters: {json_data['total_characters']}")
    print(f"total lines: {json_data['total_lines']}")
    print(f"categories found: {list(organized_content.keys())}")
    print("\njson output:")
    print(json_output)

except requests.exceptions.RequestException as e:
    print(f"error fetching webpage: {e}")
except Exception as e:
    print(f"error occurred: {e}")