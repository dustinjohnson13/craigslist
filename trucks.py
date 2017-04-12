import html
import os
import sys
import smtplib
import sqlite3
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
             (link TEXT, search_id INTEGER, title TEXT, date TEXT, description TEXT)''')
cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS link_idx ON items (link)''')

for url in sys.argv[1:]:
    cursor.execute('SELECT id FROM searches WHERE url=?', (url,))
    search_id = cursor.fetchall()

    if not search_id:
        cursor.execute("""INSERT INTO searches (url) VALUES (?)""", (url,))
        search_id = cursor.lastrowid
    else:
        search_id = search_id[0]

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
    for item in root.findall('{http://purl.org/rss/1.0/}item'):
        title = html.unescape(item.find('{http://purl.org/rss/1.0/}title').text)
        dateAsString = item.find('{http://purl.org/dc/elements/1.1/}date').text
        # Remove colon it UTC offset
        dateAsString = dateAsString[:22] + dateAsString[23:]
        date = datetime.strptime(dateAsString, "%Y-%m-%dT%H:%M:%S%z")
        # Element
        description = html.unescape(item.find('{http://purl.org/rss/1.0/}description').text)
        # Attribute
        link = item.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')

        cursor.execute('SELECT count(*)  FROM items WHERE link=?', (link,))
        existingCount = cursor.fetchone()[0]

        if (existingCount == 0):
            print("Inserting ", link)

            try:
                print(title, '\n', date, '\n', link, '\n', description)
                cursor.execute("""INSERT INTO items (link, search_id, title, description, date) VALUES (?, ?, ?, ?, ?)""",
                               (link, search_id, title, description, date))
                new_results.append((title, link, date, description))
                conn.commit()
            except Exception:
                conn.rollback()
                print(traceback.format_exc())
        else:
            print(link, " already exists")

    if (len(new_results) > 0):
        plainMessage = "New Results (" + url + "):\n\n"
        htmlMessage = '\n<html>\n<h2>' + url + '</h2>\n' \
                      '<table><thead>\n' \
                      '<th>Title</th>\n' \
                      '<th>Date</th>\n' \
                      '<th>Description</th>\n' \
                      '</thead>\n' \
                      '<tbody>\n'

        for result in new_results:
            plainMessage = plainMessage + str(result) + '\n'
            htmlMessage = htmlMessage + '<tr>\n' \
                                        '<td><a href="' + result[1] + '">' + result[0] + '</a></td>\n' \
                                                                                         '<td>' + str(result[2]) + '</td>\n' \
                                                                                                                   '<td>' + \
                          result[3] + '</td>\n' \
                                      '</tr>\n'

        htmlMessage = htmlMessage + "</tbody></table></html>"

        print('Sending email with:\n' + htmlMessage)

        me = "dustinjohnson13@gmail.com"
        email_password = os.environ['EMAIL_PASSWORD']

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(me, email_password)

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "New Craigslist Results"
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
