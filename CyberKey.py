from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning
import requests
import csv

cyberkey = 'http://www.sendit.no/Cyberkey2/'
username = ''
password = ''

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Accept-Language': 'en-gb'
}

payload = {'CustID': username, 'passwd': password, 'Submit input': 'Logg på'}

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

session = requests.Session()
session.headers = headers
session.get(cyberkey + 'Logon.asp')
devices_r = session.post(cyberkey + 'validateuser.asp', data=payload)

dataset = {}
device_soup = BeautifulSoup(devices_r.text, 'html.parser')
devices = device_soup.find('ul').find_all('li')
### Get the 'enheter'
for device in devices:
    ### Get the users in batches
    device_imei = device.find('span', {"class": "comment"}).text.strip()
    device_number = device.find('span', {"class": "starcomment"}).text.split()[0].strip()
    device_name = device.find('span', {"class": "name"}).text.strip()
    device_data = {'device_name': device_name, 'device_number': device_number, 'users': []}
    session.get(cyberkey + 'Index.asp', params={'IMEIcode': device_imei})

    index = 0
    has_more_pages = True
    while has_more_pages:
        users_r = session.get(cyberkey + 'Brukere.asp', params={'RecordStart': index})
        user_soup = BeautifulSoup(users_r.text, 'html.parser')
        next_fifty = user_soup.find('input', attrs={'value': 'Neste 50 brukere'})
        if not next_fifty:
            has_more_pages = False
        users = user_soup.find('ul').find_all('li')
        for user in users:
            detail_link = user.find('a', href=True)
            if detail_link is None:
                continue
            href_link = detail_link['href']
            user_details_r = session.get(cyberkey + href_link)
            detail_soup = BeautifulSoup(user_details_r.text, 'html.parser')
            number = detail_soup.find('input', attrs={'name': 'PhoneNumber3'})['value'].strip()
            name = detail_soup.find('input', attrs={'name': 'UserName3'})['value'].strip()
            date_from = detail_soup.find('input', attrs={'name': 'DateFrom3'})['value'].strip()
            date_to = detail_soup.find('input', attrs={'name': 'DateTo3'})['value'].strip()
            time = detail_soup.find('input', attrs={'name': 'Timedata3'})['value'].strip()
            status = detail_soup.find('input', attrs={'name': 'Status3'})['value'].strip()
            saldo = detail_soup.find('input', attrs={'name': 'Saldo3'})['value'].strip()
            user_data = {'name': name,
                         'number': number,
                         'date_from': date_from,
                         'date_to': date_to,
                         'time': time,
                         'status': status,
                         'saldo': saldo}
            device_data['users'].append(user_data)
        index += 50
        dataset[device_imei] = device_data

csv_columns = ['device_imei', 'device_name', 'device_number',
               'name', 'number', 'date_from', 'date_to', 'time',
               'status', 'saldo']
try:
    with open('report.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for imei, device in dataset.items():
            for user in device['users']:
                user['device_imei'] = imei
                user['device_name'] = device['device_name']
                user['device_number'] = device['device_number']
                writer.writerow(user)
except IOError:
    print("I/O error")
