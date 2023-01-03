import requests
from pprint import PrettyPrinter
printer = PrettyPrinter()

url = 'https://api.newscatcherapi.com/v2/latest_headlines?countries=US&topic=business'
BASE_URL = 'https://api.newscatcherapi.com'
JSON_FILE = '/v2/latest_headlines?countries=US&topic=news'
API_KEY = 'AN95MsEtSEOaQDMi7qPwzYY5CMa302ZOjFALQK1NKJo'
headers = {
    'x-api-key': API_KEY
}

response = requests.get(BASE_URL+JSON_FILE, headers=headers)
data = response.json()
#printer.pprint(data)

articles = data['articles']
#print(articles)
news_length = len(articles)

news_excerpts = []
news_links = []
for i in range(news_length):
    excerpt = data['articles'][i]['excerpt']
    link = data['articles'][i]['link']
    news_excerpts.append(excerpt)
    news_links.append(link)

print(news_excerpts)
print(news_links)


