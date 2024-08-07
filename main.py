import time
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz


class EcoFlowAPI:
    def __init__(self):
        self.api_key = '9d7b928dd63547a6b4eb9485344bf72f'
        self.secret_key = '232ba90501204986b7bdc8a314bdf5bc'
        self.serial_number = 'R331ZEB4KF1C2139'
        self.base_url = 'https://api.ecoflow.com/iot-service/open/api/device/queryDeviceQuota'

    def get_data(self):
        url = f"{self.base_url}?sn={self.serial_number}"
        headers = {
            'appKey': self.api_key,
            'secretKey': self.secret_key
        }
        print(f"Request URL: {url}")
        print(f"Request Headers: {headers}")
        response = requests.get(url, headers=headers)
        data = response.json()
        print(f"Response Data: {data}")
        if data.get('code') == '0' and 'data' in data:
            return {
                'soc': data['data'].get('soc', 'N/A'),
                'wattsInSum': data['data'].get('wattsInSum', 'N/A'),
                'wattsOutSum': data['data'].get('wattsOutSum', 'N/A')
            }
        else:
            raise Exception(f"Failed to retrieve data: {data.get('message', 'Unknown error')}")


class GoogleSheetLogger:
    def __init__(self, credentials_file, sheet_name):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open(sheet_name)
        self.current_worksheet = self.sheet.sheet1  # Use the first worksheet only

    def log_data(self, date, time, soc, wattsInSum, wattsOutSum):
        row = [date, time, soc, wattsInSum, wattsOutSum]
        self.current_worksheet.append_row(row)


def main():
    ecoflow = EcoFlowAPI()
    logger = GoogleSheetLogger(
        credentials_file="solbazz2-eefe7285c1bb.json",
        sheet_name='SolBazz_test_1'
    )

    while True:
        current_time = datetime.now(pytz.timezone('Asia/Jerusalem'))
        current_hour = current_time.hour

        if 6 <= current_hour < 20:
            try:
                # Log data
                data = ecoflow.get_data()
                date = current_time.strftime("%Y-%m-%d")
                time_str = current_time.strftime("%H:%M:%S")
                logger.log_data(date, time_str, data['soc'], data['wattsInSum'], data['wattsOutSum'])
                print("Data logged successfully")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("Outside of operating hours. Waiting until the next check.")

        # Pause for 59 seconds
        time.sleep(59)


if __name__ == "__main__":
    main()
