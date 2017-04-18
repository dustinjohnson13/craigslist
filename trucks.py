import html
import os
import smtplib
import sqlite3
import sys
import traceback
import urllib.request
import xml.etree.ElementTree as etree
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

url = sys.argv[1]

conn = sqlite3.connect('craigslist.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''CREATE TABLE IF NOT EXISTS searches
             (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT)''')
cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS url_idx ON searches (url)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS items
             (id INTEGER PRIMARY KEY AUTOINCREMENT, link TEXT, version INTEGER, search_id INTEGER)''')
cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS link_version_idx ON items (link, version)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS item_versions
              (id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER, title TEXT, date TEXT, description TEXT)''')
cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS item_id_idx ON item_versions (item_id)''')

for url in sys.argv[1:]:
    cursor.execute('SELECT id FROM searches WHERE url=?', (url,))
    search_id = cursor.fetchall()

    if not search_id:
        cursor.execute("""INSERT INTO searches (url) VALUES (?)""", (url,))
        search_id = cursor.lastrowid
    else:
        search_id = search_id[0][0]

    # Read from test file
    # file = open('trucks.xml', 'r')
    # xml = file.read()
    # file.close()

    # Live retrieval
    xml = urllib.request.urlopen(url).read()

    # To write to a file uncomment
    # file = open('trucks.xml', 'wb')
    # file.write(xml)
    # file.close()

    root = etree.fromstring(xml)

    # <item rdf:about="http://omaha.craigslist.org/cto/6051375941.html">
    # <title><![CDATA[2015 ram 2500 (Lavista) &#x0024;30]]></title>
    # <link>http://omaha.craigslist.org/cto/6051375941.html</link>
    # <description><![CDATA[Black 2015 ram 2500 4x4 long bed slt 6.4l hemi. 25k miles. Has muffler delete (have oem muffler). Bed liner with lifetime warranty from wood house. Tinted windows. This was a work truck. Minor dings on box. Will need tires. 30k obo thanks]]></description>
    # <dc:date>2017-03-19T19:26:15-05:00</dc:date>
    # <dc:language>en-us</dc:language>
    # <dc:rights>copyright 2017 craiglist</dc:rights>
    # <dc:source>http://omaha.craigslist.org/cto/6051375941.html</dc:source>
    # <dc:title><![CDATA[2015 ram 2500 (Lavista) &#x0024;30]]></dc:title>
    # <dc:type>text</dc:type>
    # <enc:enclosure resource="https://images.craigslist.org/00808_hjPCRbjEye2_300x300.jpg" type="image/jpeg"/>
    # <dcterms:issued>2017-03-19T19:26:15-05:00</dcterms:issued>
    # </item>
    new_results = []
    updated_results = []
    for item in root.findall('{http://purl.org/rss/1.0/}item'):
        title = html.unescape(item.find('{http://purl.org/rss/1.0/}title').text)
        dateForItem = item.find('{http://purl.org/dc/elements/1.1/}date').text
        # Remove colon in UTC offset
        dateAsString = dateForItem[:22] + dateForItem[23:]
        date = datetime.strptime(dateAsString, "%Y-%m-%dT%H:%M:%S%z")
        # Element
        description = html.unescape(item.find('{http://purl.org/rss/1.0/}description').text)
        # Attribute
        link = item.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')

        cursor.execute('SELECT MAX(id) FROM items WHERE link=?', (link,))
        mostRecentItem = cursor.fetchone()[0]

        version = -1
        if (mostRecentItem is None):
            print("Inserting ", link)
            version = 1
            new_results.append((title, link, date, description))

        else:
            cursor.execute('SELECT title, description, date FROM item_versions WHERE id=?', (mostRecentItem,))
            existingVersionRow = cursor.fetchall()
            existing_version = existingVersionRow[0]
            existingTitle = existing_version[0]
            existingDate = existing_version[2]
            existingDescription = existing_version[1]

            # Modify the date string to match the database format
            dateForComparison = dateForItem[:10] + ' ' + dateForItem[11:]

            if ((existingTitle, existingDescription, existingDate) != (title, description, dateForComparison)):
                print("Updating ", link)
                version = mostRecentItem + 1
                updated_results.append((" (OLD) " + existingTitle, link, existingDate, existingDescription))
                updated_results.append((title, link, date, description))

        if (version != -1):
            try:
                print(link, '\n', search_id, '\n', title, '\n', date, '\n', link, '\n', description)
                cursor.execute("""INSERT INTO items (link, version, search_id) VALUES (?, ?, ?)""",
                               (link, version, search_id))

                item_id = cursor.lastrowid

                cursor.execute("""INSERT INTO item_versions (item_id, title, description, date) VALUES (?, ?, ?, ?)""",
                               (item_id, title, description, date))
                conn.commit()
            except Exception:
                conn.rollback()
                print(traceback.format_exc())

    send_email = len(new_results) > 0 or len(updated_results) > 0

    htmlMessage = '\n<html>\n<h2>' + url + '</h2>\n'
    for results in (new_results, updated_results):

        if len(results) == 0:
            continue

        if results == new_results:
            plainMessage = "\n\nNew Results (" + url + "):\n\n"
            htmlMessage = htmlMessage + '<h4>New Results<h4>\n'
        else:
            plainMessage = "\n\nUpdated Results (" + url + "):\n\n"
            htmlMessage = htmlMessage + '<h4>Updated Results<h4>\n'

        htmlMessage = htmlMessage + \
                      '<table><thead>\n' \
                      '<th>Title</th>\n' \
                      '<th>Date</th>\n' \
                      '<th>Description</th>\n' \
                      '</thead>\n' \
                      '<tbody>\n'

        for result in results:
            plainMessage = plainMessage + str(result) + '\n'
            htmlMessage = htmlMessage + '<tr>\n' \
                                        '<td><a href="' + result[1] + '">' + result[0] + '</a></td>\n' \
                                        '<td>' + str(result[2]) + '</td>\n' \
                                        '<td>' + result[3] + '</td>\n' \
                                        '</tr>\n'

        htmlMessage = htmlMessage + "</tbody></table>"

    htmlMessage = htmlMessage + '</html>'

    if send_email:

        print('Sending email with:\n' + htmlMessage)

        me = "dustinjohnson13@gmail.com"
        email_password = os.environ['EMAIL_PASSWORD']

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(me, email_password)

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Craigslist Results"
        msg['From'] = me
        msg['To'] = me

        # Record the MIME types of both parts - text/plain and text/html.
        # part1 = MIMEText(message, 'plain')
        part1 = MIMEText(plainMessage, 'plain')
        part2 = MIMEText(htmlMessage, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)

        server.sendmail(me, me, msg.as_string())
        server.quit()
    else:
        print('Not sending email')

cursor.close()
conn.close()
