from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']



def get_sheet_data(URL):

    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    assert URL.startswith('https://docs.google.com/spreadsheets/d/'), "does not appear to be a valid google sheets url, it should begin with 'https://docs.google.com/spreadsheets/d/'"
    # The ID and range of a sample spreadsheet.
    #SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
    SAMPLE_SPREADSHEET_ID = URL.replace('https://docs.google.com/spreadsheets/d/', '').split('/')[0]
    SAMPLE_RANGE_NAME = 'A:H'

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        print('Found data.')
    return values

if __name__ == '__main__':
    get_sheet_data('https://docs.google.com/spreadsheets/d/1sm_spcmOLZifyvjM8ERmrYTss8bxT8kw6hAAwp7eRxM/edit#gid=0')