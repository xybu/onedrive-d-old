#!/usr/bin/python

import pygtk
import gtk
import appindicator

class AppIndicatorExample:
    def __init__(self):
        self.ind = appindicator.Indicator ("example-simple-client", "indicator-messages", appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status (appindicator.STATUS_ACTIVE)
        self.ind.set_attention_icon ("indicator-messages-new")
        self.ind.set_icon("distributor-logo")

        # create a menu
        self.menu = gtk.Menu()

        # create items for the menu - labels, checkboxes, radio buttons and images are supported:
        
        item = gtk.MenuItem("Regular Menu Item")
        item.show()
        self.menu.append(item)

        check = gtk.CheckMenuItem("Check Menu Item")
        check.show()
        self.menu.append(check)

        radio = gtk.RadioMenuItem(None, "Radio Menu Item")
        radio.show()
        self.menu.append(radio)

        image = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        image.connect("activate", self.quit)
        image.show()
        self.menu.append(image)
                    
        self.menu.show()

        self.ind.set_menu(self.menu)

    def quit(self, widget, data=None):
        gtk.main_quit()


def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    indicator = AppIndicatorExample()
    main()
