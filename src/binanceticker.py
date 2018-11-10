#!/usr/bin/env python3


import json
import gi.repository
from os.path import expanduser
from gi.repository import Budgie, GObject, Gtk, Gdk, Pango
from binance.websockets import BinanceSocketManager
from binance.client import Client
gi.require_version('Pango', '1.0')
gi.require_version('Budgie', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version("Gdk", "3.0")

home = expanduser("~")


class BinanceTicker(GObject.GObject, Budgie.Plugin):

    __gtype_name__ = "BinanceTicker"

    def __int__(self):
        GObject.Object.__init__(self)

    def do_get_panel_widget(self, uuid):
        return BinanceTickerApplet(uuid)


class BinanceTickerApplet(Budgie.Applet):

    def __init__(self, uuid):
        Budgie.Applet.__init__(self)

        # Create inital variables
        self.instantiate()

        # Grab ticker data
        self.grab_data()

        # Build the widegts
        self.create_desktop_window()
        self.create_labels()
        self.create_event_box()

        # Start loop
        self.updateScrollingText()
        self.start_socket()

        # Show the widgets
        self.win.show_all()
        self.show_all()

        self.home = expanduser("~")

    def instantiate(self):

        # Builder
        self.builder = Gtk.Builder()
        self.builder.add_from_file(f"{home}/.local/share/budgie-desktop/plugins/binanceticker/dropdown.glade")

        # Ticker variables/arrays
        self.index = 0
        with open(f'{home}/.local/share/budgie-desktop/plugins/binanceticker/usertickers.json') as data_file:
            tickerArray = json.load(data_file)
        self.tickerArray = tickerArray
        self.priceArray = []
        self.tickerWidgetArray = []
        self.text = ""

        # Binance login info
        with open(f'{home}/.local/share/budgie-desktop/plugins/binanceticker/keys.json') as data_file:
            keys = json.load(data_file)
        self.client = Client(keys['api_key'], keys['api_secret'])

    def create_desktop_window(self):

        self.win = Gtk.Window()
        self.win.set_decorated(False)
        self.win.set_keep_below(True)
        self.win.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.win.move(110, 960)

        visual = self.win.get_screen().get_rgba_visual()
        if all([visual, self.win.get_screen().is_composited()]):
            self.win.set_visual(visual)
        self.win.set_app_paintable(True)

        self.win.connect("destroy", Gtk.main_quit)

    def create_labels(self):

        self.desktopTicker = Gtk.Label("")
        self.win.add(self.desktopTicker)

        self.taskbarTicker = Gtk.Label("")
        self.taskbarTicker.valign = Gtk.Align.CENTER

    # clickable button
    def create_event_box(self):
        # turns eventbox into a button
        self.event = Gtk.EventBox()
        self.event.connect("button_press_event", self.popup)
        self.event.add(self.taskbarTicker)
        self.add(self.event)

        # builds the popover(shows on event)
        self.popover = Budgie.Popover.new(self.event)
        self.popover.set_default_size(310, 400)

        # adds scrollable textwindow and shows
        self.popover.add(self.builder.get_object("scrolled"))
        self.popover.get_child().show_all()
        self.show_all()

        # this holds all the tickers, we refrence this when we add tickers
        self.holder = self.builder.get_object("holder")

        # adds tickers to the holder. Adds references to the an array for later
        for symbol in self.tickerArray:
            x = self.new_ticker(symbol)
            self.holder.pack_start(x[0], False, True, 0)
            self.tickerWidgetArray.append(x[1])

    # live data in the dropdown widget
    def start_socket(self):
        self.socket = BinanceSocketManager(self.client)
        self.socket.start_ticker_socket(self.process_message)
        self.socket.start()

    # for the scrolling text
    def grab_data(self):
        self.tickerData = self.client.get_symbol_ticker()
        self.index = 0
        self.text = ""

        self.priceArray.clear()
        for i, ticker in enumerate(self.tickerArray):
            for data in self.tickerData:
                if data[u'symbol'] == ticker:
                    self.text += (self.tickerArray[i])[:3] + \
                        " " + data[u'price'][:6] + "    |    "

    # everyone half second
    def updateScrollingText(self):
        GObject.timeout_add(500, self.updateScrollingText)

        # [1:] is everything but the first char
        # [:1] is the last char
        self.text = self.text[1:] + self.text[:1]
        self.taskbarTicker.set_markup(self.text[:50])
        self.desktopTicker.set_markup(self.text[:200])

        # after the text rotates back around we update the values
        self.index += 1
        if self.index >= len(self.text):
            self.index = 0
            self.grab_data()

    # hide or show the widget
    def popup(self, widget, event):
        if event.button != 1:
            return Gdk.EVENT_PROPAGATE
        if self.popover.get_visible():
            self.popover.hide()
        else:

            self.popover.show_all()
        return Gdk.EVENT_STOP

    # construct a ticker box
    def new_ticker(self, symbol):
        # create a box named after symbol
        ticker = Gtk.Box()

        def tickerObject(): return None
        tickerObject.name = symbol
        tickerObject.lastprice = ""

        # Create ticker widegts
        tickerObject.symbolHolder = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL)
        tickerObject.symbolLabel = Gtk.Label(symbol)
        tickerObject.symbolLabelFull = Gtk.Label("loading...")
        tickerObject.price = Gtk.Label("")
        tickerObject.changeHolder = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL)
        tickerObject.changeLabel = Gtk.Label("loading...")
        tickerObject.percentLabel = Gtk.Label("loading...")

        # organize and name widegts
        tickerObject.changeHolder.set_property("margin_left", 25)
        tickerObject.changeHolder.set_property("width_request", 60)
        tickerObject.changeLabel.set_property("margin_top", 6)
        tickerObject.changeLabel.set_property("halign", Gtk.Align.END)
        tickerObject.changeLabel.set_name("changeLabel")
        tickerObject.percentLabel.set_property("margin_bottom", 8)
        tickerObject.percentLabel.set_property("halign", Gtk.Align.END)
        tickerObject.percentLabel.set_name("percentLabel")
        tickerObject.price.set_property("halign", Gtk.Align.END)
        tickerObject.price.set_property("ellipsize", Pango.EllipsizeMode.NONE)
        tickerObject.price.set_name("price")
        tickerObject.symbolLabelFull.set_property("halign", Gtk.Align.START)
        tickerObject.symbolLabelFull.set_name("symbolLabelFull")
        tickerObject.symbolLabel.set_property("margin_top", 4)
        tickerObject.symbolLabel.set_property("halign", Gtk.Align.START)
        tickerObject.symbolLabel.set_name("symbolLabel")

        desc = tickerObject.symbolLabel.get_pango_context().get_font_description()
        desc.set_size(12000)

        pricedesc = tickerObject.price.get_pango_context().get_font_description()
        pricedesc.set_size(12000)

        fulldesc = tickerObject.symbolLabelFull.get_pango_context().get_font_description()
        fulldesc.set_weight(Pango.Weight.LIGHT)
        fulldesc.set_size(9500)

        tickerObject.symbolLabel.modify_font(desc)
        tickerObject.price.modify_font(pricedesc)
        tickerObject.symbolLabelFull.modify_font(fulldesc)

        # place widegts in ticker widget
        tickerObject.symbolHolder.pack_start(
            tickerObject.symbolLabel, False, False, 4)
        tickerObject.symbolHolder.pack_start(
            tickerObject.symbolLabelFull, False, False, 0)
        tickerObject.changeHolder.pack_start(
            tickerObject.changeLabel, True, True, 3)
        tickerObject.changeHolder.pack_start(
            tickerObject.percentLabel, False, False, 0)
        ticker.pack_start(tickerObject.symbolHolder, True, True, 0)
        ticker.pack_start(tickerObject.price, True, True, 0)
        ticker.pack_start(tickerObject.changeHolder, False, False, 0)

        return [ticker, tickerObject]

    # update all the tickers according to the data from binance api
    def process_message(self, data):
        for ticker in self.tickerWidgetArray:
            for symbol in self.tickerArray:
                if ticker.name == symbol:
                    for dataset in data:
                        if dataset['s'] == symbol:
                            change = dataset['p'][:6]
                            percent = dataset['P'][:4]
                            price = dataset['a'][:6]
                            label = self.get_full(symbol)
                            arrow = ""
                            color24h = ""
                            colorlive = None

                            if ticker.price.get_text() != "":
                                ticker.lastprice = ticker.price.get_text()

                                if float(price) > float(ticker.lastprice):
                                    colorlive = Gdk.color_parse('#3CBC98')
                                elif float(price) < float(ticker.lastprice):
                                    colorlive = Gdk.color_parse('#FF4A68')
                                else:
                                    colorlive = None

                            if change[:1] == '-':
                                arrow = "▾ "
                                color24h = Gdk.color_parse('#FF4A68')
                            else:
                                arrow = "▴ "
                                color24h = Gdk.color_parse('#3CBC98')

                            ticker.symbolLabelFull.set_markup(label)
                            ticker.price.set_markup(price)
                            ticker.percentLabel.set_text("(" + percent + "%)")
                            ticker.changeLabel.set_text(arrow + change)

                            fdesc = ticker.percentLabel.get_pango_context().get_font_description()
                            fdesc.set_weight(Pango.Weight.SEMILIGHT)
                            # fdesc.set_size("")

                            ticker.price.modify_fg(
                                Gtk.StateFlags.NORMAL, colorlive)
                            ticker.percentLabel.modify_fg(
                                Gtk.StateFlags.NORMAL, color24h)
                            ticker.percentLabel.modify_font(fdesc)
                            ticker.changeLabel.modify_fg(
                                Gtk.StateFlags.NORMAL, color24h)
                            ticker.changeLabel.modify_font(fdesc)

    # return expanded tickersymbol eg:  BTCUSDT turns into Bitcoin / Tether
    def get_full(self, symbol):
        with open(f'{home}/.local/share/budgie-desktop/plugins/binanceticker/cryptocurrencies.json') as data_file:
            data = json.load(data_file)

        # symbols are 3 or 4 long: BTCUSDT or BTCETH
        # if the symbol is not 3 is must for 4
        try:
            crypto = data[symbol[:3]]
        except:
            crypto = data[symbol[:4]]
        try:
            currency = data[symbol[3:]]
        except:
            currency = data[symbol[4:]]

        # BTCUSDT turns into Bitcoin / Tether
        return f"{crypto} / {currency}"
