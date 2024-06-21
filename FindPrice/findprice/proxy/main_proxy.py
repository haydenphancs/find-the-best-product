import requests

#Or go to this website to check: https://checkerproxy.net/report/988ebaad-7910-4c2e-b60c-11573238664b


with open('valid_proxies.txt', 'r') as f:
    proxies = f.read().split('\n')


sites_to_check = ['www.amazon.com/s?k=shoe',
                  'www.amazon.com/s?k=clock',
                  'www.amazon.com/s?k=laptop']
counter = 0
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
    "Accept-Encoding": "gzip, deflate", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "DNT": "1", "Connection": "close", "Upgrade-Insecure-Requests": "1"}

for site in sites_to_check:
    try:
        print(f'Using the proxy: {proxies[counter]}')
        res = requests.get(site, headers=headers, proxies={'http': proxies[counter], 'https': proxies[counter]})
        print(res.status_code)
    except:
        print("Failed")
    finally:
        counter +=1
        counter % len(proxies)