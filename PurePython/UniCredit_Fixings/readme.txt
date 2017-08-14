# Bank Austria Fixing Prices

This project will allow Unicredit to provide an automated fixing service to Bank Austria via Bloomberg and Barracuda.

Bank Austria will submit orders to Barracuda on a daily basis. This script will download the orders, which will be exported from Barracuda as a CSV, then request prices from Bloomberg using their SFTP service.

Once prices have been retrieved from Bloomberg, a margin is applied to any currency pair where an order exists. The fixing prices are then written to XML so they can be imported by Barracuda. The prices will also be emailed to Bank Austria as a CSV.

Additionally, prices must be persisted to a KDB database.

Once Barracuda has the fixing prices, the orders are filled and booked via Apama the same way all other Barracuda orders are booked.

