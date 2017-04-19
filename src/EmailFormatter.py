class EmailFormatter:
    def __init__(self, url):
        self.html = '\n<html>\n<h2>' + url + '</h2>\n'
        self.plain = '\n' + url + '\n\n'

    def add_new_items(self, items):
        self.__add_items__('New Results', items)

    def add_updated_items(self, items):
        self.__add_items__('Updated Results', items)

    def __add_items__(self, title, items):
        if len(items) == 0:
            return

        self.plain = self.plain + "\n" + title + ":\n"
        self.html = self.html + '<h4>' + title + '<h4>\n'

        self.html = self.html + \
                    '<table><thead>\n' \
                    '<th>Title</th>\n' \
                    '<th>Date</th>\n' \
                    '<th>Description</th>\n' \
                    '</thead>\n' \
                    '<tbody>\n'

        for item in items:
            self.plain = self.plain + str(item) + '\n\n'

            anchor = '<a href="' + item.link + '">' + item.title + '</a>'
            title_column = '<td>' + anchor + '</td>\n'
            date_column = '<td>' + str(item.date) + '</td>\n'
            description_column = '<td>' + item.description + '</td>\n'

            self.html = self.html + '<tr>\n' + title_column + date_column + description_column + '</tr>\n'

        self.html = self.html + "</tbody></table>"

    def html_message(self):
        return self.html + '</html>'


    def plain_message(self):
        return self.plain
