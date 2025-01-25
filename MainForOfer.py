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

    def log_data(self, date, time_str, soc, wattsInSum, wattsOutSum):
        row = [date, time_str, soc, wattsInSum, wattsOutSum]
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

    # This flag determines whether "10 -> first table" or "10 -> second table" in the current cycle
    use_first_table_for_10 = True

    while True:
        current_time = datetime.now(pytz.timezone('Asia/Jerusalem'))
        current_hour = current_time.hour
        current_second = current_time.second

        # Ensure operation only within allowed hours
        if 5 <= current_hour < 20:
            # If the second matches the first target, decide which table to log to
            if current_second == target_second_1:
                try:
                    data = ecoflow.get_data()
                    date = current_time.strftime("%Y-%m-%d")
                    time_str = current_time.strftime("%H:%M:%S")

                    if use_first_table_for_10:
                        logger_1.log_data(date, time_str, data['soc'], data['wattsInSum'], data['wattsOutSum'])
                        print(f"10 -> Sheet 1 at {time_str}")
                    else:
                        logger_2.log_data(date, time_str, data['soc'], data['wattsInSum'], data['wattsOutSum'])
                        print(f"10 -> Sheet 2 at {time_str}")

                except Exception as e:
                    print('im here -3-')
                    print(f"Error logging on target_second_1: {e}")

            # If the second matches the second target, decide which table to log to
            if current_second == target_second_2:
                try:
                    data = ecoflow.get_data()
                    date = current_time.strftime("%Y-%m-%d")
                    time_str = current_time.strftime("%H:%M:%S")

                    if use_first_table_for_10:
                        # If 10 was logged to first table, then 20 goes to second table
                        logger_2.log_data(date, time_str, data['soc'], data['wattsInSum'], data['wattsOutSum'])
                        print(f"20 -> Sheet 2 at {time_str}")
                    else:
                        # If 10 was logged to second table, then 20 goes to first table
                        logger_1.log_data(date, time_str, data['soc'], data['wattsInSum'], data['wattsOutSum'])
                        print(f"20 -> Sheet 1 at {time_str}")

                    # After logging both 10 and 20 in this cycle, flip the flag
                    # so next time the assignments reverse.
                    use_first_table_for_10 = not use_first_table_for_10

                except Exception as e:
                    print('im here -3-')
                    print(f"Error logging on target_second_2: {e}")

        else:
            print("Outside of operating hours (5 AM to 8 PM). Waiting...")

        time.sleep(1)


if __name__ == "__main__":
    main()
