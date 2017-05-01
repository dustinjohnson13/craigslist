class Item:
    def __init__(self, link, title, description, date):
        self.link = link
        self.title = title
        self.description = description
        self.date = date

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Email:
    def __init__(self, id, html, plain, sent):
        self.id = id
        self.html = html
        self.plain = plain
        self.sent = sent

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
