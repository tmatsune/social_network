import requests
from pprint import PrettyPrinter
printer = PrettyPrinter()


BASE_URL = 'https://finnhub.io/api/v1'
JSON_FILE = '/news?category=general'
API_KEY = 'cenvkb2ad3i2t1u1dce0cenvkb2ad3i2t1u1dceg'
headers = {
    'X-Finnhub-Token': API_KEY
}
response = requests.get(BASE_URL+JSON_FILE, headers=headers)
data = response.json()
print(response)
printer.pprint(data)

#articles = data['articles']
#print(articles)
news_headlines = []
news_url = []
for i in range(10):
    news = data[i]['headline']
    url = data[i]['url']
    news_headlines.append(news)
    news_url.append(url)




