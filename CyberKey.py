from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning
import requests
from datetime import datetime
from dateutil import tz


class Device:
    users = []

    def __init__(self, imei, phone_number, name):
        self.imei = imei
        self.phone_number = phone_number
        self.name = name

    def __str__(self):
        return '{}: {} <{} users>'.format(self.phone_number, self.name, len(self.users))


class User:
    logs = []

    def __init__(self, name, phone_number):
        self.name = name
        self.phone_number = phone_number

    def __str__(self):
        return '{}: {} <{} calls>'.format(self.phone_number, self.name, len(self.logs))


class CyberKey:
    cyberkey = 'http://www.sendit.no/Cyberkey2/'
    oslo_tz = tz.gettz('Europe/Oslo')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Accept-Language': 'en-gb'
    }

    def __init__(self, username, password):
        payload = {'CustID': username,
                   'passwd': password,
                   'Submit input': 'Logg på'}

        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

        self.session = requests.Session()
        self.session.headers = self.headers
        self.session.get(self.cyberkey + 'Logon.asp')
        self.session.post(self.cyberkey + 'validateuser.asp', data=payload)

    def devices(self):
        devices_r = self.session.get(self.cyberkey + 'Enheter2.asp')
        device_soup = BeautifulSoup(devices_r.text, 'html.parser')
        device_list = device_soup.find('ul').find_all('li')

        devices = []
        for device_element in device_list:
            imei = device_element.find('span', {"class": "comment"}).text.strip()
            phone_number = device_element.find('span', {"class": "starcomment"}).text.split()[0].strip()
            name = device_element.find('span', {"class": "name"}).text.strip()
            device = Device(imei, phone_number, name)
            devices.append(device)

        return devices

    def device_users(self, device):
        self.session.get(self.cyberkey + 'Index.asp', params={'IMEIcode': device.imei})

        device_users = []

        ### Get the users in batches
        index = 0
        has_more_pages = True
        while has_more_pages:
            users_r = self.session.get(self.cyberkey + 'Brukere.asp', params={'RecordStart': index})
            user_soup = BeautifulSoup(users_r.text, 'html.parser')
            next_fifty = user_soup.find('input', attrs={'value': 'Neste 50 brukere'})
            if not next_fifty:
                has_more_pages = False
            user_list = user_soup.find('ul').find_all('li')
            for user_element in user_list:
                detail_link = user_element.find('a', href=True)
                if detail_link is None:
                    continue
                href_link = detail_link['href']
                user_details_r = self.session.get(self.cyberkey + href_link)
                detail_soup = BeautifulSoup(user_details_r.text, 'html.parser')
                name = detail_soup.find('input', attrs={'name': 'UserName3'})['value'].strip()
                phone_number = detail_soup.find('input', attrs={'name': 'PhoneNumber3'})['value'].strip()
                date_from = detail_soup.find('input', attrs={'name': 'DateFrom3'})['value'].strip()
                date_to = detail_soup.find('input', attrs={'name': 'DateTo3'})['value'].strip()
                time = detail_soup.find('input', attrs={'name': 'Timedata3'})['value'].strip()
                status = detail_soup.find('input', attrs={'name': 'Status3'})['value'].strip()
                saldo = detail_soup.find('input', attrs={'name': 'Saldo3'})['value'].strip()

                user = User(name, phone_number)
                user.date_from = date_from
                user.date_to = date_to
                user.time = time
                user.status = status
                user.balance = saldo
                device_users.append(user)
            index += 50
        return device_users

    def user_logs(self, user):
        user_logs = []

        log_r = self.session.post(self.cyberkey + 'Logg.asp', data={'SName': user.phone_number})
        log_soup = BeautifulSoup(log_r.text, 'html.parser')
        uls = log_soup.find_all('ul', {'class': 'pageitem'})
        for log_entry in uls[2:]:
            date_time = log_entry.find('span', {'class': 'graytitle'}).text.strip()
            dt = datetime.strptime(date_time, '%d/%m/%y,%H:%M')
            dt = dt.replace(tzinfo=self.oslo_tz)
            phone, name = log_entry.find('li', {'class': 'textbox'}).text.split(',', 1)
            if user.phone_number == phone.strip():
                user_logs.insert(0, dt)
            else:
                print('Non-matching: {}'.format(phone.strip()))
        return user_logs