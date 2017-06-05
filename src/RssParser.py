import html
import xml.etree.ElementTree as etree
from datetime import datetime

from Domain import Item


class RssParser:
    def parse(self, xml):
        root = etree.fromstring(xml)

        items = []

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
        for item in root.findall('{http://purl.org/rss/1.0/}item'):
            title = html.unescape(item.find('{http://purl.org/rss/1.0/}title').text)
            dateForItem = item.find('{http://purl.org/dc/elements/1.1/}date').text
            # Remove colon in UTC offset
            dateAsString = dateForItem[:22] + dateForItem[23:]
            date = datetime.strptime(dateAsString, "%Y-%m-%dT%H:%M:%S%z")

            # Element
            descriptionElement = item.find('{http://purl.org/rss/1.0/}description')
            if descriptionElement is None:
                description = ''
            else:
                description = html.unescape(descriptionElement.text)

            # Attribute
            link = item.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')

            i = Item(link, title, description, date)
            items.append(i)

        return items
