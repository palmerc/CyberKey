import csv
import configparser
import CyberKey

csv_columns = ['device_imei', 'device_name', 'device_number',
               'name', 'number', 'date']


def main():
    config = configparser.ConfigParser()
    config.read('login.ini')
    login_ini = config['DEFAULT']
    cyber_key = CyberKey.CyberKey(login_ini['username'], login_ini['password'])

    try:
        with open('log.csv', 'w') as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=csv_columns)
            csv_writer.writeheader()

            for device in cyber_key.devices():
                device.users = cyber_key.device_users(device)
                print(device)
                count = 1
                for user in device.users:
                    print('\t{})'.format(count), end=' ')
                    user.logs = cyber_key.user_logs(user)
                    print(user)
                    count += 1

                    try:
                        row = {'device_imei': device.imei,
                               'device_name': device.name,
                               'device_number': device.phone_number,
                               'name': user.name,
                               'number': user.phone_number,
                               'date': ''}
                        for log_entry in user.logs:
                            row['date'] = log_entry.isoformat()
                            csv_writer.writerow(row)
                    except KeyError:
                        print('Error: ' + str(user))
    except IOError:
        print("I/O error")


if __name__ == '__main__':
    main()
