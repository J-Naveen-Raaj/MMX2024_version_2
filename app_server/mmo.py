import sqlite3

import pandas as pd

connection = sqlite3.connect('mmo.db')
cursor = connection.cursor()


insert_query = "UPDATE secondary_modules SET channel_tactic = 'Referral' WHERE channel_tactic = 'RAF';"

cursor.execute(insert_query)

# Commit the transaction to save the changes
connection.commit()
