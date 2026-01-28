from googleapiclient.errors import HttpError
from email_api_setup import get_gmail_service
import json
import base64

def decode_base64(encoded_string):
  encoded_bytes = encoded_string.encode('utf-8')
  
  decoded_bytes = base64.b64decode(encoded_bytes)
  
  text = decoded_bytes.decode('utf-8')
  
  return text.rstrip()

def main():
  try:
    service = get_gmail_service()

    results = service.users().messages().list(userId="me", labelIds=["INBOX"],maxResults=1).execute()
   
    messages = results.get("messages", [])
    
    if not messages:
      print("No messages found.")
      return
    
    print("Messages:")
    for message in messages:
      print(f'Message ID: {message["id"]}')
      msg_data = service.users().messages().get(userId="me", id=message["id"]).execute()
     
      try:
        with open("data.json", 'w', encoding='utf-8') as json_file:
          json.dump(msg_data, json_file, indent=4) 
        
      except IOError as e:
        print(f"Error writing to file: {e}")
      break
      
      
      email = {}
      headers = msg_data['payload']['headers']
      
      for header in headers:
        if header['name'] == 'Subject':
          email["subject"] = header['value']
        if header['name'] == 'From':
          email['from'] = header['value']
        if header['name'] == 'Date':
          email['date'] = header['value'] 
          
        if 'subject' in email and 'from' in email and 'date' in email:
          break
      print(f"The email: {email}")
  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")

if __name__ == "__main__":
  main()