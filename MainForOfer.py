import time
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz


class EcoFlowAPI:
    def __init__(self):
        self.api_key = "2e3a969006b1436fad5e36877b6da053"
        self.secret_key = "ffb0dd5edf3f49d2bd5481b34cd5068f"
        self.serial_number = 'R611ZEB5XF2E0465'
        self.base_url = 'https://api.ecoflow.com/iot-service/open/api/device/queryDeviceQuota'

    def get_data(self):
        url = f"{self.base_url}?sn={self.serial_number}"
        headers = {
            'appKey': self.api_key,
            'secretKey': self.secret_key
        }
        response = requests.get(url, headers=headers)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")  # Debugging log
        data = response.json()
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
    # Get inputs from the user
    try:
        target_second_1 = int(input("Enter the first target second (0-59): "))
        target_second_2 = int(input("Enter the second target second (0-59): "))
        if not (0 <= target_second_1 <= 59) or not (0 <= target_second_2 <= 59):
            raise ValueError("Invalid second value. Must be between 0 and 59.")
    except ValueError as e:
        print('im here -2-')
        print(f"Error: {e}")
        return

    ecoflow = EcoFlowAPI()
    logger_1 = GoogleSheetLogger(
        credentials_file="solbazz3-afbe6ca17ca8.json",
        sheet_name='SolBazz_test_3'
    )
    logger_2 = GoogleSheetLogger(
        credentials_file="solbazz3-afbe6ca17ca8.json",
        sheet_name='SolBazz_test_2'
    )

    while True:
        current_time = datetime.now(pytz.timezone('Asia/Jerusalem'))
        current_hour = current_time.hour
        current_minute = current_time.minute
        current_second = current_time.second

        # Ensure operation only within allowed hours
        if 5 <= current_hour < 20:
            # If current_second matches the first target second, log to the first sheet
            if current_second == target_second_1:
                try:
                    data = ecoflow.get_data()
                    date = current_time.strftime("%Y-%m-%d")
                    time_str = current_time.strftime("%H:%M:%S")
                    logger_1.log_data(date, time_str, data['soc'], data['wattsInSum'], data['wattsOutSum'])
                    print(f"Data logged successfully in sheet 1 at {time_str}")
                except Exception as e:
                    print('im here -3-')
                    print(f"Error logging to sheet 1: {e}")

            # If current_second matches the second target second, log to the second sheet
            if current_second == target_second_2:
                try:
                    data = ecoflow.get_data()
                    date = current_time.strftime("%Y-%m-%d")
                    time_str = current_time.strftime("%H:%M:%S")
                    logger_2.log_data(date, time_str, data['soc'], data['wattsInSum'], data['wattsOutSum'])
                    print(f"Data logged successfully in sheet 2 at {time_str}")
                except Exception as e:
                    print('im here -3-')
                    print(f"Error logging to sheet 2: {e}")

            if current_second not in (target_second_1, target_second_2):
                print(f"Waiting... Current time: {current_time.strftime('%H:%M:%S')}")
        else:
            print("Outside of operating hours (5 AM to 8 PM). Waiting...")

        time.sleep(1)


if __name__ == "__main__":
    main()
