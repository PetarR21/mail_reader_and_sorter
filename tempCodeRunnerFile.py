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
     
      
      
        
      
      message_content = decode_base64(msg_data['payload']['parts'][0]['parts'][0]['body']['data']) 
      email["text_content"]=message_content
      
      
      print(f"The email: {email}")