import pandas as pd

df = pd.read_csv('movies_metadata.csv')

df_unique = df.drop_duplicates(subset=['title'])

df_unique.to_csv('movies_metadata.csv', index=False)