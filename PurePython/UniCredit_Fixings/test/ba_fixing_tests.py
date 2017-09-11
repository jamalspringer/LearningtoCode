import unittest
from ba_fixing import *
from datetime import datetime
from os.path import isfile, isdir
from os import makedirs, listdir, remove

class TestBAFixing(unittest.TestCase):
    def test_read_orders(self):
        """
        Parse all orders from the orders file
        """
        ticker_map = BloombergTickerLookup.parse('./test_data/symbol_ticker_map.csv')
        orders = Orders.parse('./test_data/ActiveOrders-09032017-1516.csv', ticker_map)

        self.assertTrue(orders.contains('EURNOK'))
        self.assertTrue(orders.contains('EURUSD'))

        nok = orders.get('EURNOK')
        usd = orders.get('EURUSD')

        self.assertEqual(nok.order_id, '5BF2C7DBAC6BAB922C5EB36998DC15A7_0')
        self.assertEqual(nok.direction, 'BUY')
        self.assertEqual(nok.quantity, 400.0)

        self.assertEqual(usd.order_id, '886C01A7BA31A62651C8B368AD946B8A_0')
        self.assertEqual(usd.direction, 'BUY')
        self.assertEqual(usd.quantity, 123.0)

    def test_read_margins(self):
        """
        Parse the margins from the margins file
        """
        margins = Margins.parse_margins('test_data/margins.csv')

        margin = margins.get('EURUSD')

        self.assertEqual(margin.symbol, 'EURUSD')
        self.assertEqual(margin.bid_offset, 0.02191)
        self.assertEqual(margin.good_until, datetime(2017,11,1,22))

        margin = margins.get('EURNOK')
        self.assertEqual(margin.bid_offset, 0.1)
        self.assertEqual(margin.good_until, datetime(2017,11,1,22))
        self.assertEqual(margin.ask_pull_offset, 0.4)

    def test_read_bloomberg_prices(self):
        """
        Parse the prices returned from Bloomberg SFTP service
        """
        prices = BloombergPrices.parse('./test_data/response/2017-03-24.csv', True)

        self.assertEquals(prices.get("EURUSD"), 1.0802)
        self.assertEquals(prices.get("EURRON"), 4.5558)
        self.assertEquals(prices.get("EURISK"), 119.24)

    def test_apply_margins(self):
        """
        Margins should only be applied to currency pairs that have orders
        """
        ticker_map = BloombergTickerLookup.parse('./test_data/symbol_ticker_map.csv')
        orders = Orders.parse('./test_data/ActiveOrders-09032017-1516.csv', ticker_map)

        margins = Margins.parse_margins('test_data/margins.csv')

        prices = BloombergPrices.parse('./test_data/response/2017-03-24.csv', True)

        fixing_prices = prices.calculate_fixing_prices(orders, margins)

        eur_usd_fixing = fixing_prices["EURUSD"]

        self.assertEquals(eur_usd_fixing.currency, "EURUSD")
        self.assertEquals(eur_usd_fixing.quantity, 123)
        self.assertEquals(eur_usd_fixing.side, "BUY")
        self.assertEquals(eur_usd_fixing.tenor, "SP")
        self.assertEquals(eur_usd_fixing.price, 1.0802 + 0.02191)

    def test_create_fixing_prices(self):
        """
        We should create a file with the fixing prices to upload to Barracuda
        """
        fixing_output_path = check_path('./test_data/barracuda_prices')

        if not isdir(fixing_output_path):
            makedirs(fixing_output_path)

        # now we want to delete any files that already exists
        files = listdir(fixing_output_path)

        for f in files:
            remove(fixing_output_path + f)

        ticker_map = BloombergTickerLookup.parse('./test_data/symbol_ticker_map.csv')
        orders = Orders.parse('./test_data/ActiveOrders-09032017-1516.csv', ticker_map)

        margins = Margins.parse_margins('test_data/margins.csv')

        prices = BloombergPrices.parse('./test_data/response/2017-03-24.csv', True)

        fixing_prices = prices.calculate_fixing_prices(orders, margins)

        barracuda_files = BloombergPrices.create_xml_files(fixing_prices, fixing_output_path)

        self.assertEquals(len(barracuda_files), len(ticker_map))


    def test_insert_into_kdb(self):
        """
        Once the prices have been generated, they should be inserted to KDB
        """
        self.fail('Not implemented')

    def test_configuration_validation(self):
        """
        We should have all configuration settings supplied for the given environment
        """
        test_properties = ['./test_data/test_environment.properties', './test_data/test_config.properties']

        config = read_config(test_properties, False)

        self.assertEqual(False, validate_config('invalid_properties', config))
        self.assertEqual(True, validate_config('valid_properties', config))

    def test_symbol_ticker_mapping(self):
        """
        We should be able to read a symbol ticker map into memory and use it to lookup Bloomberg ticker
        from currency pair symbols
        """

        ticker_lookup = BloombergTickerLookup.parse('./test_data/symbol_ticker_map.csv')
        self.assertEqual('EURUSD Curncy', ticker_lookup.get('EURUSD'))
        self.assertEqual('EURGBP Curncy', ticker_lookup.get('EURGBP'))
        self.assertEqual('', ticker_lookup.get('GBPUSD'))

    def test_create_bloomberg_request_file(self):
        """
        We should be able to create a file to request prices from Bloomberg
        """

        ticker_lookup = BloombergTickerLookup.parse('./test_data/symbol_ticker_map.csv')
        request_file = BloombergPrices.generate_request_file(ticker_lookup, './test_data/requests/')

        # check that the file exists
        self.assertTrue(isfile(request_file))

        # now open the file and count the number of lines
        line_count = 0
        with codecs.open(request_file, 'r', encoding='utf8') as input_file:
            input_reader = csv.reader(input_file, delimiter=',')
            for line in input_reader:
                if len(line) > 0:
                    line_count += 1

        # count should be the number of tickers + 1 line for the header
        self.assertEquals(line_count, len(ticker_lookup) + 1)


if __name__ == '__main__':
    unittest.main()

