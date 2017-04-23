import sys
import traceback
import urllib.request
import requests

import os

from Db import Db
from Mailer import Mailer
from RssParser import RssParser
from EmailFormatter import EmailFormatter

db = Db()
db.initialize()

for url in sys.argv[1:]:
    search_id = db.search_id(url)

    # Read from test file
    # file = open('trucks.xml', 'r')
    # xml = file.read()
    # file.close()

    # Live retrieval
    xml = requests.get(url).text

    # To write to a file uncomment
    # file = open('new.xml', 'w')
    # file.write(xml)
    # file.close()

    parser = RssParser()
    items = parser.parse(xml)

    new_results = []
    updated_results = []
    for item in items:
        link = item.link
        title = item.title
        description = item.description
        date = item.date

        print(link)

        mostRecentItem = db.most_recent_version(link)

        version = -1
        if mostRecentItem is None:
            print("Inserting ", link)
            version = 1
            new_results.append(item)

        else:
            existing_version = db.existing_item(mostRecentItem)

            # Modify the date string to match the database format
            dateForComparison = str(date)

            if existing_version != item:
                print("Updating ", link)
                version = mostRecentItem + 1

                existing_version.title = "(OLD) " + existing_version.title
                updated_results.append(existing_version)
                updated_results.append(item)

            else:
                print("Not Updating ", link)

        if version != -1:
            try:
                db.save(item, version, search_id)
            except Exception:
                print(traceback.format_exc())

    send_email = len(new_results) > 0 or len(updated_results) > 0

    if send_email:

        email_formatter = EmailFormatter(url)
        email_formatter.add_new_items(new_results)
        email_formatter.add_updated_items(updated_results)

        htmlMessage = email_formatter.html_message()
        plainMessage = email_formatter.plain_message()

        print('Sending email with:\n  html: ' + htmlMessage + '\n  plain: ' + plainMessage)

        me = "dustinjohnson13@gmail.com"
        email_password = os.environ['EMAIL_PASSWORD']

        mailer = Mailer()
        mailer.send_email('smtp.gmail.com', 587, me, email_password, me, me,
                          "Craigslist Results", htmlMessage, plainMessage)
    else:
        print('Not sending email')

db.close()
