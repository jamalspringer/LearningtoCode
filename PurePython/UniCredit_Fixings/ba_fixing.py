# Bank of Austria Fixing Script
# This script use the BFIX rates file from Bloomberg and all the active Orders which it got from Barracuda 

import ConfigParser
import csv
import codecs
import cx_Oracle
import os
from xml.etree.ElementTree import Element, SubElement, tostring  # need these to create the barracuda order file
from datetime import datetime
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import Encoders
from os.path import basename, isfile, exists
from os import makedirs
import subprocess
import xml.dom.minidom
import collections
import xlsxwriter
#from qpytexihon import qconnection


class ApplicationError(Exception):
    """
    Generic Application error in case something goes wrong
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ConfigurationProperties:
    """
    Class to define settings in the configuration file and helper methods to ensure we have the appropriate
    settings defined
    """
    def __init__(self):
        pass

    @property
    def section_global(self):
        return 'global'

    @property
    def environment(self):
        return 'env'

    """
    Path to the margin file
    """
    @property
    def margin_file(self):
        return 'margin.file'

    """
    Path to upload the Bloomberg request file to
    """
    @property
    def bloomberg_upload_path(self):
        return 'bloomberg.upload.path'

    """
    Path to download the Bloomberg pricing file to
    """
    @property
    def bloomberg_download_path(self):
        return 'bloomberg.download.path'

    """
    Local path to write Bloomberg request file to
    """
    @property
    def bloomberg_request_file_path(self):
        return 'bloomberg.request.path'

    """
    Remote path where BFIX results will be published
    """
    @property
    def bloomberg_publish_path(self):
        return 'bloomberg.publish.path'

    """
    Bloomberg SFTP user name
    """
    @property
    def bloomberg_user(self):
        return 'bloomberg.user.name'

    """
    Bloomberg SFTP host server address
    """
    @property
    def bloomberg_sftp_host(self):
        return 'bloomberg.sftp.host'

    """
    Bloomberg SFTP host server port
    """
    @property
    def bloomberg_sftp_port(self):
        return 'bloomberg.sftp.port'

    """
    Bloomberg Ticker Mapping File
    """
    @property
    def bloomberg_ticker_mapping_file(self):
        return 'bloomberg.ticker.mapping.file'

    """
    Barracuda SSH Private Key
    """
    @property
    def barracuda_identity_file(self):
        return 'barracuda.identity.file'

    """
    Barracuda Input File
    """
    @property
    def barracuda_orders_inputFile(self):
        return 'barracuda.orders.inputFile'

    """
    Bloomberg Input file
    """
    @property
    def bloomberg_request_file(self):
        return 'bloomberg.request.file'

    @property
    def tmp_file_location(self):
        return 'tmp.file.location'

    """
    Bloomberg SSH Private Key
    """
    @property
    def bloomberg_identity_file(self):
        return 'bloomberg.identity.file'

    """
    SSH user name for Barracuda server
    """
    @property
    def barracuda_user(self):
        return 'barracuda.user.name'

    @property
    def apama_user(self):
        return 'apama.user.name'

    """
    Barracuda host to connect to and retrieve order file and publish prices
    """
    @property
    def barracuda_scp_host(self):
        return 'barracuda.scp.host'

    """
    Barracuda host port to connect to and retrieve order file and publish prices
    """
    @property
    def barracuda_scp_port(self):
        return 'barracuda.scp.port'

    """
    Path on Barracuda server to load prices file to
    """
    @property
    def barracuda_upload_path(self):
        return 'barracuda.upload.path'

    """
    Path on Barracuda server to download order file from
    """
    @property
    def barracuda_download_path(self):
        return 'barracuda.download.path'

    """
    Local path to download the order file to
    """
    @property
    def barracuda_orders_path(self):
        return 'barracuda.orders.path'

    """
    Local Path to write the Barracuda Fixing prices to
    """
    @property
    def barracuda_fixing_path(self):
        return 'barracuda.fixing.path'

    """
    Where to read the margin data from, file or database
    """
    @property
    def margin_source(self):
        return 'margin.source'

    @property
    def database_host(self):
        return 'margin.database.host'

    @property
    def database_port(self):
        return 'margin.database.port'

    @property
    def database_name(self):
        return 'margin.database.name'

    @property
    def database_user(self):
        return 'margin.database.user'

    @property
    def database_password(self):
        return 'margin.database.password'

    @property
    def from_database(self):
        return "DATABASE"

    @property
    def from_file(self):
        return "FILE"

    @property
    def email_server(self):
        return 'email.server'

    @property
    def email_sender(self):
        return 'email.sender'

    @property
    def email_recipients(self):
        return 'email.recipients'

    @property
    def email_recipients_for_input_file(self):
        return 'email.recipients.for.input.file'

    @property
    def kdb_server(self):
        return 'kdb.server'

    @property
    def kdb_port(self):
        return 'kdb.port'


class BloombergTickerLookup:
    def __init__(self):
        self.lookup = {}

    def add(self, symbol, ticker):
        self.lookup[symbol] = ticker

    def get(self, symbol):
        """
        Retrieve the Bloomberg ticker that corresponds with the given symbol
        :type symbol: str
        :param symbol: Currency pair to lookup the Bloomberg Ticker for
        :return: The Bloomberg Ticker if found, otherwise an empty string
        """
        ticker = 0.0
        try:
            ticker = self.lookup[symbol]
            return ticker
        except KeyError:
            return ticker

    def symbols(self):
        return self.lookup.keys()

    def __len__(self):
        return self.lookup.__len__()

    def __iter__(self):
        return self.lookup

    @classmethod
    def parse(cls, ticker_mapping_file, headers=False):
        """
        Parse the ticker mapping file into the provided lookup object
        :type ticker_mapping_file: str
        :param ticker_mapping_file: path to the ticker mapping file
        :type headers: bool
        :param headers: default=False - indicates whether file has headers
        :return: BloombergTickerLookup object with the symbol to ticker mappings
        """
        lookup = BloombergTickerLookup()
        ticker = 0.0

        with open(ticker_mapping_file, 'r') as mapping_file:
	    eurUsd = 0.0
            map_reader = csv.reader(mapping_file, delimiter='|')
            
            for row in map_reader:
                if len(row) < 5:
                    continue
                elif row[3] == 'EURUSD':
                    eurUsd = float(row[4])
	    mapping_file.seek(0)
            for row in map_reader:	
                # Skip the header if one exists
                if len(row) < 5:
                    continue

                try:
                    symbol = row[3]
                    ticker = float(row[4])		    
                    if(symbol == 'USDAZN' or symbol == 'USDDZD' or symbol == 'USDPKR'):
                        lookup.add('EUR' + symbol[-3:], ticker * eurUsd)			
                    else:
                        lookup.add(symbol, ticker)			
                except IndexError:		    
                    continue

	    lookup.add('EURBAM', 1.9558)
        return lookup


class FixingPrice(object):
    def __init__(self, currency):
        self.currency = currency
        self._quantity = 0.0
        self._side = ''
        self._price = 0.0
        self._tenor = 'SP'
        self._timestamp = datetime.utcnow()

    # We give the bid, mid and ask the same value after calculating what the
    # price with the given spread will be
    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        self._price = value

    @property
    def major_currency(self):
        return self.currency[:3]

    @property
    def minor_currency(self):
        return self.currency[-3:]

    @property
    def curve(self):
        return "WM_BACA"

    @property
    def benchmark_date(self):
        return self._timestamp.strftime('%Y-%m-%d')

    @property
    def benchmark_time(self):
        return self._timestamp.strftime('%H:%M')

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        self._quantity = value

    @property
    def side(self):
        return self._side

    @side.setter
    def side(self, value):
        self._side = value

    @property
    def tenor(self):
        return self._tenor


class BarracudaOrder:
    def __init__(self, order_id, currency_pair, fixed_symbol, direction, quantity):
        self.order_id = order_id
        self.currency_pair = currency_pair
        self.fixed_symbol = fixed_symbol
        self.direction = direction
        self.quantity = quantity

    @staticmethod
    def validate(columns, ticker_map):
        """
        Validate the data that has been read from the order file
        :type columns: list
        :param columns: A list of the values read from a row in the order file
        :type ticker_map: BloombergTickerLookup
        :param ticker_map: A Bloomberg Ticker map as the orders should only be for currencies available in this map
        :return: True if the data can be validated, otherwise False
        """
        if len(columns) != 21:
            print "Line does not have the correct number of columns, expected 21 columns, parsed " + str(len(columns))
            return False

        if not columns[2] in ticker_map.symbols():
            print "Currency pair " + columns[2] + " is not in the permitted list of currency pairs"
            return False

        if columns[4].upper() != 'BUY' and columns[4].upper() != 'SELL':
            print "Direction is not BUY or SELL"
            return False

        if not columns[3] in columns[2]:
            print "Fixed currency " + columns[3] + " is not one of the currency pair " + columns[2]
            return False

        return True


class Orders:
    def __init__(self):
        self.orders = {}

    def add(self, symbol, order):
        self.orders[symbol] = order

    def contains(self, symbol):
        return symbol in self.orders

    def get(self, symbol):
        if symbol in self.orders:
            return self.orders[symbol]
        else:
            return None

    def __iter__(self):
        return self.orders.keys()

    @classmethod
    def parse(cls, file_name, ticker_map, header=False):
        """
        Reads the order file that has been created from Barracuda
        :type file_name: str
        :param file_name: path to the order file that was created by Barracuda
        :type ticker_map: BloombergTickerLookup
        :param ticker_map: list of valid tickers supported for Bank Austria
        :type header: bool
        :param header: file contains a header row; True or False (default=False)
        :return: An array of BarracudaOrder objects that have been parsed from the file
        """
        orders = Orders()

        with open(file_name, 'r') as barracuda_orders:
            order_reader = csv.reader(barracuda_orders, delimiter=',')
            for row in order_reader:
                if header:
                    header = False
                    continue

                if not BarracudaOrder.validate(row, ticker_map):
                    continue

                try:
                    order_id = row[16]
                    currency_pair = row[2]
                    fixed_symbol = row[3]
                    direction = row[4]

                    try:
                        quantity = float(row[5])
                    except ValueError:
                        print "Quantity provided: " + row[5] + " is not valid!"
                        continue

                    orders.add(currency_pair, BarracudaOrder(order_id, currency_pair, fixed_symbol, direction, quantity))
                except IndexError:
                    continue

        return orders


class BloombergPrices:
    def __init__(self):
        self.prices = {}

    def add(self, symbol, price):
        """
        Add a price for the given symbol to the price map
        :type symbol: str
        :param symbol: Currency Pair the price is for
        :type price: float
        :param price: The price returned by Bloomberg
        """
        self.prices[symbol] = price

    def get(self, symbol):
        """
        Retrieve the Bloomberg price for the given symbol
        :type symbol: str
        :param symbol: Currency Pair the price is requested for
        :return: The Bloomberg price for the corresponding currency pair
        """
        if symbol in self.prices:
            return self.prices[symbol]
        else:
            return 0.0

    def calculate_fixing_prices(self, orders, margins):
        """
        Calculate the fixing price to publish to Bank Austria
        :type orders: Orders
        :param orders: The orders that were submitted by Bank Austria
        :type margins: Margins
        :param margins: The margins configuration
        :return: A map of prices for the currency pairs that are supported for Bank Austria.
                 Only currency pairs with orders have margins applied to the price.
        """
        fixing_prices = {}

        for symbol in self.prices.keys():
            fixing_price = FixingPrice(symbol)

            final_price = self.prices.get(symbol)
            if orders.contains(symbol):
                # apply margin
                margin = margins.get(symbol)
                order = orders.get(symbol)

                if order is None:
                    continue

                fixing_price.side = order.direction
                fixing_price.quantity = order.quantity

                if fixing_price.side == 'BUY':
                    # increase the price
                    final_price += margin.bid
                else:
                    final_price -= margin.ask

            fixing_price.price = final_price

            fixing_prices[symbol] = fixing_price

        return fixing_prices

    # XML must comply with the schema defined in https://www.bcdfx.com/confluence/display/OMS34/Benchmark+Rates+File+Repository
    @staticmethod
    def create_xml_files(fixing_prices, output_file_path,time):
        """
        Create the Barracuda fixing price XML files
        :type fixing_prices: dict
        :param fixing_prices: The calculated fixing prices
        :param output_file_path: The location to write the price files
        """

        xml_files = []

        # we traverse the prices
        # if there is an order for the currency pair then we apply the margin to the price
        # otherwise we output the raw price from Bloomberg

        # we have to create one file per
        directory = '{}'.format(datetime.utcnow().strftime('%Y-%m-%d'))
        if not os.path.exists(output_file_path + directory):
            os.makedirs(output_file_path + directory)

	for symbol in fixing_prices.keys():
            file_name = symbol + time
	    if time == '-WM_BACA@1030.xml':
                benchmarkTime = '10:30'
            else:
                benchmarkTime = '11:30'

            benchmark = Element('StandardBenchmark')
            benchmark.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            benchmark.set('noNamespaceSchemaLocation', 'curve.xsd')
            benchmark.set('benchmarkDate', fixing_prices[symbol].benchmark_date)
            benchmark.set('benchmarkTime', benchmarkTime)
            benchmark.set('curve', fixing_prices[symbol].curve)
            benchmark.set('majorCcy', fixing_prices[symbol].major_currency)
            benchmark.set('minorCcy', fixing_prices[symbol].minor_currency)

            rate = SubElement(benchmark, 'Rate')
            rate.set('bid', str(fixing_prices[symbol].price))
            rate.set('mid', str(fixing_prices[symbol].price))
            rate.set('ask', str(fixing_prices[symbol].price))
            rate.set('tenor', fixing_prices[symbol].tenor)

            fixing_file = output_file_path + directory + '/' + file_name
            xml_files.append(fixing_file)

            with codecs.open(fixing_file, 'wb', encoding='utf8') as order_file:
                order_file.write(tostring(benchmark))

	    xmlFile = xml.dom.minidom.parse(fixing_file) # or xml.dom.minidom.parseString(xml_string)
            pretty_xml_as_string = xmlFile.toprettyxml(encoding = 'utf-8')

            with codecs.open(fixing_file, 'w', encoding='utf8') as order_file:
                order_file.write(pretty_xml_as_string)

        return xml_files

    @staticmethod
    def parse(price_file, headers=False):
        """
        Parse the price file returned from Bloomberg
        :type price_file: str
        :param price_file: Path of the price file retrieved from Bloomberg
        :type headers: bool
        :param headers: Flag to indicate if the file has headers (default=False)
        :return: A bloomberg prices object that contains the list of prices
        """

        prices = BloombergPrices()
	
        with open(price_file, 'r') as bloomberg_prices:
            eurUsd = 0.0
            price_reader = csv.reader(bloomberg_prices, delimiter='|')
            for row in price_reader:
                if len(row) < 5:
		    
                    continue
                elif row[3] == 'EURUSD':
                    eurUsd = float(row[4])
            bloomberg_prices.seek(0) 
            for row in price_reader:
                # Skip the header row if there is one
                if len(row) < 5:
                    continue

                symbol = None
                price = 0.0

                try:
                    symbol = row[3]
                    price = float(row[4])

                    if(symbol == 'USDAZN' or symbol == 'USDDZD' or symbol == 'USDPKR'):
                        prices.add('EUR' + symbol[-3:], price * eurUsd)		
                    else:
                        prices.add(symbol, price)
                except IndexError:
                    continue
                except ValueError:
                    if symbol is not None:
                        prices.add(symbol, price)
                    continue

            prices.add('EURBAM', 1.9558)
        return prices


    @staticmethod
    def generate_request_file(lookup, output_path):
        """
        Create a file to upload to Bloomberg in order to retrieve prices
        :type lookup: BloombergTickerLookup
        :param lookup: a BloombergTickerLookup object of currency pair's and the corresponding Bloomberg ticker
        :type output_path: String
        :param output_path: location to write the request file
        """

        if not exists(output_path):
            makedirs(output_path)

        request_file = output_path + datetime.utcnow().strftime('%Y-%m-%d.csv')

        with codecs.open(request_file, 'w', encoding='utf8') as upload_file:
            upload_file.write("TICKER,MID_PRICE\n")
            for key in lookup.symbols():
                upload_file.write(lookup.get(key) + ",\n")

        return request_file


class Margin:
    def __init__(self, symbol, bid, ask):
        #assert isinstance(good_until, datetime)
        assert isinstance(bid, float)
        assert isinstance(ask, float)
        #assert isinstance(bid_pull_offset, float)
        #assert isinstance(ask_pull_offset, float)

        self.symbol = symbol
        self.bid = bid
        self.ask = ask
        #self.good_until = good_until
        #self.bid_pull_offset = bid_pull_offset
        #self.ask_pull_offset = ask_pull_offset


class Margins:
    def __init__(self):
        self.margins = {}

    def add(self, symbol, bid, ask):
        """
        Add margin to map
        :type symbol: str
        :param symbol: Currency Pair the margin applies to
        :type bid_offset: float
        :param bid_offset: The amount of margin to apply on the bid side
        :type ask_offset: float
        :param ask_offset: The amount of margin to apply on the ask side
        :type good_until: datetime
        :param good_until: Date until which the margin is good for
        :type bid_pull_offset: float
        :param bid_pull_offset: The amount of margin to apply on the bid side
        :type ask_pull_offset: float
        :param ask_pull_offset: The amount of margin to apply on the ask side
        """
        self.margins[symbol] = Margin(symbol, bid, ask)

    def get(self, symbol):
        """
        Retrieve the margin for the given symbol
        :type symbol: str
        :param symbol: The currency pair to retrieve the margin for
        :return: The margin to apply for the given symbol (0.0 if the symbol is not found)
        """
        if symbol in self.margins:
            return self.margins[symbol]
        else:
            return 0.0

    @staticmethod
    def parse_margins(margin_file, headers=False):
        """
        Parse a margin configuration file
        :type margin_file: str
        :param margin_file: The file containing the margin details
        :type headers: bool
        :param headers: Flag to indicate whether the file has a header
        :return: A Margins object containing the margins parsed from the file
        """
        parsed_margins = Margins()

        with codecs.open(margin_file, 'r', encoding='utf8') as margin_config:
            margin_reader = csv.reader(margin_config, delimiter=',')
            for row in margin_reader:
                if headers:
                    headers = False
                    continue

                if len(row) != 6:
                    continue

                current_symbol = None

                try:
                    current_symbol = row[0]
                    bid = float(row[1])
                    ask = float(row[2])
                    #good_until = datetime.strptime(row[3], '%Y.%m.%d %H:%M:%S')
                    #bid_pull_offset = float(row[4])
                    #ask_pull_offset = float(row[5])

                    parsed_margins.add(current_symbol, bid, ask)
                except IndexError:
                    continue
                except ValueError:
                    if current_symbol is not None:
                        parsed_margins.add(current_symbol, 0.0, 0.0)
                    continue

        return parsed_margins

    @staticmethod
    def load_margins(db_host, db_port, db_name, db_user, db_pass):
        """
        Load the margins configuration from an Oracle database - alternative method requested by the business
        :type db_host: str
        :param db_host: hostname of the Oracle database
        :type db_port: str
        :param db_port: port to connect to
        :type db_name: str
        :param db_name: name of the database to connect to
        :type db_user: str
        :param db_user: user to connect as
        :type db_pass: str
        :param db_pass: password to connect with
        :return: A Margins object containing the margins read from the database
        """
        imported_margins = Margins()

        connect_string = '{0}/{1}@{2}:{3}/{4}'.format(db_user, db_pass, db_host, db_port, db_name)

        print "Connecting to oracle database: {0}".format(connect_string)

        conn = cx_Oracle.connect(connect_string)
        cur = conn.cursor()

        #cur.execute('''select sym.SYMBOL, sp.BID_OFFSET, sp.ASK_OFFSET,
        #              sp.GOOD_UNTIL, sp.BID_PULL_OFFSET, sp.ASK_PULL_OFFSET
        #             from APAMA_PAYFX_SPREADS sp join APAMA_SYMBOLS sym on sp.symbolid = sym.id''')
        
	cur.execute('''select ba.SYMBOL, ba.BID, ba.ASK
                       from BA_MARGINS ba''')

        for result in cur:
	    imported_margins.add(result[0],result[1],result[2])
            print result[0]

        cur.close()
        conn.close()

        return imported_margins


def __execute_scp(source, destination, identity_file, port):
    """
    Execute the SSH copy from one secure server to another
    :type source: str
    :param source: Path of the file to be copied
    :type destination: str
    :param destination: Path where the file should be written
    :param identity_file: Path of the SSH private key to use as identity file
    :return:
    """

    subprocess.call(["scp", "-i", identity_file, "-p", port, source, destination])
    
    
def __execute_scp_folder(source, destination, identity_file, port):
    """
    Execute the SSH copy from one secure server to another
    :type source: str
    :param source: Path of the file to be copied
    :type destination: str
    :param destination: Path where the file should be written
    :param identity_file: Path of the SSH private key to use as identity file
    :return:
    """
    
    subprocess.call(["scp", "-i", identity_file, "-rp", port, source, destination])


def download_barracuda_file(config, env, props):
    """
    Download the Barracuda order file from the Barracuda server
    :type config: ConfigParser.RawConfigParser
    :param config configuration settings
    :type env: str
    :param env: current environment (Test, UAT, Production etc.)
    :type props: ConfigurationProperties
    :param props: Configuration properties
    """
    print 'dowload barracuda file ' 
    barracuda_order_file_name = __get_barracuda_order_file_name()
    print 'barracudaa file name :'+ barracuda_order_file_name


    source = '{}@{}:{}{}'.format(
        configuration.get(environment, configuration_properties.apama_user),
        configuration.get(environment, configuration_properties.barracuda_scp_host),
        check_path(configuration.get(environment, configuration_properties.barracuda_download_path)),
        barracuda_order_file_name
    )
    print 'barracudaa source :' + source

    destination = '{}'.format(
        check_path(configuration.get(environment, configuration_properties.barracuda_orders_path))
        #barracuda_order_file_name
    )
    print 'barracudaa destination :'+ destination

    __execute_scp(
        source,
        destination,
        configuration.get(environment, configuration_properties.barracuda_identity_file),
        configuration.get(environment, configuration_properties.barracuda_scp_port)
    )

    return destination + barracuda_order_file_name


def upload_barracuda_file(config, env, props, fixing_prices):
    """
    Upload the Barracuda Fixing prices file to the Barracuda server
    :type config: ConfigParser.RawConfigParser
    :param config configuration settings
    :type env: str
    :param env: current environment (Test, UAT, Production etc.)
    :type props: ConfigurationProperties
    :param props: Configuration properties
    :type fixing_prices: dict
    :param fixing_prices: Calculated Fixing prices to send to Barracuda
    :return Number of files uploaded
    """

    #fixing_files = BloombergPrices.create_xml_files(
    #    fixing_prices,
    #    check_path(config.get(env, props.barracuda_fixing_path))
    #)

    identity_file = config.get(env, props.barracuda_identity_file)
    barracuda_port = configuration.get(environment, configuration_properties.barracuda_scp_port)

    #for fixing_file in fixing_files:
    source = configuration.get(environment, configuration_properties.barracuda_fixing_path) + datetime.today().strftime('%Y-%m-%d')
    print 'source_upload :' + source
    destination = '{}@{}:{}'.format(
        config.get(env, props.barracuda_user),
        config.get(env, props.barracuda_scp_host),
        check_path(config.get(env, props.barracuda_upload_path)),
        # basename(fixing_file)
    )
    print 'destination_upload :' + destination
    __execute_scp_folder(source, destination, identity_file, barracuda_port)

    return source

def __get_bloomberg_price_filename():
    return ""


def download_bloomberg_price_file(config, env, props):
    """
    Download the Prices returned from Bloomberg SFTP service
    :type config: ConfigParser.RawConfigParser
    :param config configuration settings
    :type env: str
    :param env: current environment (Test, UAT, Production etc.)
    :type props: ConfigurationProperties
    :param props: Configuration properties
    """
    price_file_name = __get_bloomberg_price_filename()

    source = '{}@{}:{}{}'.format(
        configuration.get(environment, configuration_properties.bloomberg_user),
        configuration.get(environment, configuration_properties.bloomberg_sftp_host),
        check_path(configuration.get(environment, configuration_properties.bloomberg_publish_path)),
        price_file_name
    )

    destination = '{}{}'.format(
        check_path(config.get(env, props.bloomberg_download_path)),
        price_file_name
    )

    __execute_scp(
        source,
        destination,
        config.get(env, props.bloomberg_identity_file),
        configuration.get(environment, configuration_properties.bloomberg_sftp_port)
    )

    return destination


def upload_bloomberg_request_file(config, env, props):
    """
    Upload the price request file to Bloomberg SFTP service
    :type config: ConfigParser.RawConfigParser
    :param config configuration settings
    :type env: str
    :param env: current environment (Test, UAT, Production etc.)
    :type props: ConfigurationProperties
    :param props: Configuration properties
    """

    # now we need to create a Bloomberg request file to get the prices from Bloomberg
    source = BloombergPrices.generate_request_file(
        ticker_lookup, config.get(environment, check_path(configuration_properties.bloomberg_request_file_path))
    )

    request_file_name = basename(bloomberg_request_file)

    destination = '{}@{}:{}{}'.format(
        config.get(env, props.bloomberg_user),
        config.get(env, props.bloomberg_sftp_host),
        check_path(config.get(env, props.bloomberg_upload_path)),
        request_file_name
    )

    __execute_scp(
        source,
        destination,
        config.get(env, props.bloomberg_identity_file),
        config.get(env, props.bloomberg_sftp_port)
    )

    return bloomberg_request_file


def write_prices_to_kdb(fixing_prices, kdb_host, kdb_port):
    """
    Write the fixing prices generated to KDB
    :type fixing_prices: dict
    :param fixing_prices: the fixing prices to insert into KDB
    :type kdb_host: str
    :param kdb_host: KDB host to connect to
    :type kdb_port: str
    :param kdb_port: KDB port to connect to
    :return:
    """
    # print ('In write_prices_to_kdb')
    # print (kdb_host)
    # print(kdb_port)
    # #conn=kdb.q(kdb_host,kdb_port,'admin')
    # q = qconnection.QConnection(host=kdb_host, port=kdb_port, numpy_temporals = False)
    # q.open()
    # print(q) 
    # print('IPC version: %s. Is connected: %s' % (q.protocol_version, q.is_connected())) 
    # #c = q.conn(host=kdb_host, port=kdb_port, user=admin)
    pass


def email_prices(server, fixing_path, fixing_prices, sender, recipients):
    """
    Email the calculated fixing prices to the list of recipients
    :type server: str
    :param server: SMTP server to use to send the email
    :type fixing_path: str
    :param fixing_path: Location to write fixing
    :type fixing_prices: dict
    :param fixing_prices: Calculated fixing prices
    :type sender: str
    :param sender: Email address of the sender
    :type recipients: list
    :param recipients: List of email addresses to send the mail to
    """

    # ensure that the recipients is a list
    assert isinstance(recipients, list)

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = COMMASPACE.join(recipients)
    msg['Date'] = formatdate(localtime=True)

    fixing_date = datetime.utcnow().strftime('%Y-%m-%d')

    msg['Subject'] = 'Bank Austria Fixing Prices - {0}'.format(fixing_date)
    msg.attach(MIMEText('Please find attached fixing prices for the date: {0}'.format(fixing_date)))
    
    __create_attachment(fixing_path, fixing_prices)
    attachment = __create_xls_attachment(fixing_path, fixing_prices)

    part = MIMEBase('application', 'base64')
    part.set_payload(open(attachment, 'rb').read())
    Encoders.encode_base64(part)

    part.add_header('Content-Disposition', 'attachment; filename="{}"'.format(basename(attachment)))

    msg.attach(part)

    smtp = smtplib.SMTP(server)
    smtp.sendmail(sender, recipients, msg.as_string())
    smtp.close()


def __create_attachment(fixing_path, fixing_prices):
    """
    Create a CSV file with the fixing prices to attach to the email
    :type fixing_path: str
    :param fixing_path: Location to write the fixing attachment file
    :type fixing_prices: dict
    :param fixing_prices: Fixing prices that have been generated from the Bloomberg data
    :return: Path to the file that should be attached to the email
    """

    attachment_path = check_path(fixing_path) + datetime.utcnow().strftime("%Y.%m.%dD%H.%M.%S.%f") + '.upd.viennaAutoFix' + '.csv'
    date = datetime.utcnow().strftime('%Y%m%d')
    with open(attachment_path, mode='w') as attachment:
        attachment.write('{},{},{},{},{}{}'.format('sym','fixDate','quantity','side','price','\n'))
        sortedSymbols = collections.OrderedDict(sorted(fixing_prices.items()))

        for symbol in sortedSymbols:
            fixing_price = fixing_prices[symbol]
            attachment.write('{},{},{},{},{}{}'.format(symbol,date,fixing_price.quantity,fixing_price.side,fixing_price.price,'\n'))
            #attachment.write('{},{},{},{},{}{}'.format(date, symbol, fixing_price.quantity, fixing_price.side, fixing_price.price,'\n'))

    return attachment_path


def __create_xls_attachment(fixing_path, fixing_prices):
    """
    Create a xls file with the fixing prices to attach to the email
    :type fixing_path: str
    :param fixing_path: Location to write the fixing attachment file
    :type fixing_prices: dict
    :param fixing_prices: Fixing prices that have been generated from the Bloomberg data
    :return: Path to the file that should be attached to the email
    """
    attachment_path = check_path(fixing_path) + datetime.utcnow().strftime('%Y-%m-%d') + '.xlsx'
    date = datetime.utcnow().strftime('%Y-%m-%d')
    workbook = xlsxwriter.Workbook(attachment_path)
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': 1})

    worksheet.write('A1', 'BFIX for Bank Austria', bold)
    worksheet.write('A2', 'Date', bold)
    worksheet.write('B2', date)
    worksheet.write('A3', 'Currency pair', bold)
    worksheet.write('B3', 'rates ag.EUR', bold)
    worksheet.write('C3', 'Side', bold)
    worksheet.write('D3', 'Quantity in ccy 2', bold)

    row = 3
    col = 0
    sortedSymbols = collections.OrderedDict(sorted(fixing_prices.items()))
    # Iterate over the data and write it out row by row.
    for symbol in sortedSymbols:
        fixing_price = fixing_prices[symbol]
        worksheet.write(row, col,     symbol)
        worksheet.write(row, col + 1, fixing_price.price)
        worksheet.write(row, col + 2, fixing_price.side)
        worksheet.write(row, col + 3, fixing_price.quantity)
        row += 1

    workbook.close()

    return attachment_path

def check_path(path):
    checked_path = path
    if path[-1:] != '/':
        checked_path += '/'

    return checked_path


def read_config(config_files=[], remove_unused=True):
    """
    Read the application configuration files
    :type config_files: list of strings
    :param config_files: files to read configuration settings from
    :type remove_unused: bool
    :param remove_unused: Remove sections that are not going to be used, default=True
    :return: Configurations
    """
    config = ConfigParser.RawConfigParser()

    if isfile('./environment.properties'):
        config.read('./environment.properties')
    else:
        print('default environment.properties file could not be found.')

    if isfile('./config.properties'):
        config.read('./config.properties')
    else:
        print('default config.properties file could not be found')

    if len(config_files) != 0:
        for file in config_files:
            print 'Reading properties file from ' + file
            config.read(file)

    props = ConfigurationProperties()

    env = config.get(props.section_global, props.environment)

    if not validate_config(env, config):
        raise ApplicationError("Configuration files could not be read properly, perhaps you are missing some configuration settings?")

    sections = config.sections()

    # only keep the section we need for the current environment
    if remove_unused:
        for section in sections:
            if section != env and section != props.section_global:
                config.remove_section(section)

    return config


def validate_config(section, config):
    """
    Validate the configuration file to make sure we have all the necessary properties
    :param section: The section of the configuration for the given environment i.e. DEV, TEST, PRODUCTION etc.
    :param config: The config object that contains the configuration data read
    :return: True if all required properties are present and not empty
    """

    props = ConfigurationProperties()

    try:
        if not is_valid_property(config.get(section, props.margin_file)) or \
                not is_valid_property(config.get(section, props.barracuda_orders_path)) or \
                not is_valid_property(config.get(section, props.barracuda_download_path)) or \
                not is_valid_property(config.get(section, props.barracuda_upload_path)) or \
                not is_valid_property(config.get(section, props.barracuda_scp_host)) or \
                not is_valid_property(config.get(section, props.barracuda_scp_port)) or \
                not is_valid_property(config.get(section, props.bloomberg_upload_path)) or \
                not is_valid_property(config.get(section, props.bloomberg_download_path)) or \
                not is_valid_property(config.get(section, props.bloomberg_sftp_host)) or \
                not is_valid_property(config.get(section, props.bloomberg_sftp_port)) or \
                not is_valid_property(config.get(section, props.bloomberg_request_file_path)) or \
                not is_valid_property(config.get(section, props.barracuda_fixing_path)):
            return False

        # make sure we have all the database properties if the margin source is DATABASE
        if config.get(section, props.margin_source) == props.from_database:
            if not is_valid_property(config.get(section, props.database_host)) or \
                    not is_valid_property(config.get(section, props.database_port)) or \
                    not is_valid_property(config.get(section, props.database_name)) or \
                    not is_valid_property(config.get(section, props.database_user)) or \
                    not is_valid_property(config.get(section, props.database_password)):
                return False

    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
        print "You have undefined properties for the current environment: " + section
        return False

    return True


def is_valid_property(prop):
    """
    Checks if the provided value is valid (i.e., not empty)
    :type prop: str
    :param prop: property to validate
    :return: True if not empty string, otherwise False
    """
    assert isinstance(prop, str)

    return not len(prop.strip()) == 0


def get_margins(config, env, props):
    """
    Load margins either from file or database depending on how the configuration is set up
    :type config: ConfigParser.RawConfigParser
    :param config configuration settings
    :type env: str
    :param env: current environment (Test, UAT, Production etc.)
    :type props: ConfigurationProperties
    :param props: Configuration properties
    :return: Margins to be applied per currency pair

    """
    if config.get(env, props.margin_source) == props.from_database:
        return Margins.load_margins(
            config.get(env, props.database_host),
            config.get(env, props.database_port),
            config.get(env, props.database_name),
            config.get(env, props.database_user),
            config.get(env, props.database_password)
        )
    else:
        return Margins.parse_margins(config.get(env, props.margin_file))


def __get_barracuda_order_file_name():
    return 'ActiveOrders_' + datetime.utcnow().strftime('%Y-%m-%d.csv')

def process_further_actions(time):
    # read the orders
    ba_orders = Orders.parse(barracuda_order_file, ticker_lookup, True)

    # upload the request file to Bloomberg's SFTP server
    bloomberg_request_file = configuration.get(environment, configuration_properties.bloomberg_request_file)

    # download the bloomberg prices file from Bloomberg's SFTP server
    bloomberg_price_file = bloomberg_request_file
    #download_bloomberg_price_file(configuration, environment, configuration_properties)

    # parse the pricing file
    bloomberg_prices = BloombergPrices.parse(bloomberg_price_file, True)

    ba_prices = bloomberg_prices.calculate_fixing_prices(ba_orders, ba_margins)

    fixing_path = configuration.get(environment, configuration_properties.barracuda_fixing_path)

    BloombergPrices.create_xml_files(
        ba_prices,
        fixing_path,
        time
    )

    upload_barracuda_file(configuration, environment, configuration_properties, ba_prices)

    email_prices(
        configuration.get(environment, configuration_properties.email_server),
        fixing_path,
        ba_prices,
        configuration.get(environment, configuration_properties.email_sender),
        configuration.get(environment, configuration_properties.email_recipients).split(',')
    )

    write_prices_to_kdb(
        ba_prices,
        configuration.get(environment, configuration_properties.kdb_server),
        configuration.get(environment, configuration_properties.kdb_port)
    )

def send_email_for_input_file():
    recipients = configuration.get(environment, configuration_properties.email_recipients_for_input_file).split(',')
    assert isinstance(recipients, list)
    msg = MIMEMultipart()
    msg['From'] = configuration.get(environment, configuration_properties.email_sender)
    msg['To'] = COMMASPACE.join(recipients)
    msg['Date'] = formatdate(localtime=True)

    msg['Subject'] = 'No Open Orders Found'
    msg.attach(MIMEText('Dear Users\n' + 'There are currently no open orders for the 12.30pm Fixing. '
                                         'If you have missed the cutoff window then please upload your open '
                                         'orders before the next cut off at 12.25pm or the next fixing at 13.00pm\n'
                                         'Regards\n' + 'eFX Support.'))

    server = configuration.get(environment, configuration_properties.email_server)
    smtp = smtplib.SMTP(server)
    smtp.sendmail(configuration.get(environment, configuration_properties.email_sender), recipients, msg.as_string())
    smtp.close()

if __name__ == "__main__":
    # read_config already checks to make sure the configuration is valid and will raise an error
    # if not so we just have to read it in here
    configuration = read_config()
    configuration_properties = ConfigurationProperties()

    environment = configuration.get(configuration_properties.section_global, configuration_properties.environment)

    ba_margins = get_margins(configuration, environment, configuration_properties)

    ticker_lookup = BloombergTickerLookup.parse(
        configuration.get(environment, configuration_properties.bloomberg_ticker_mapping_file)
    )

    # now we have the configuration settings and the margins, we need to fetch the order file from Barracuda
    inputFileName = 'ActiveOrders_' + datetime.utcnow().strftime('%Y-%m-%d.csv')
    barracuda_order_file =  download_barracuda_file(configuration, environment, configuration_properties)

    tmpStatusFile = configuration.get(environment, configuration_properties.tmp_file_location) + 'tmpFile.txt'

    if not isfile(tmpStatusFile):
        if isfile(barracuda_order_file):
            process_further_actions('-WM_BACA@1030.xml')
        else:
            f = open(tmpStatusFile,"w")
            send_email_for_input_file()
            f.close()
    else:
        os.remove(tmpStatusFile)       
        process_further_actions('-WM_BACA@1100.xml')
        
