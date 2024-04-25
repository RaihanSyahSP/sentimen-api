import subprocess
import pandas as pd

twitter_auth_token = '47508ef00f9549f9db3fe41951a797399c045b68'
filename = 'timnas.csv'
search_keyword = 'timnas indonesia lang:id'
limit = 10

command = f"npx tweet-harvest -o {filename} -s {search_keyword} -l {limit} --token {twitter_auth_token}"


# Jalankan perintah menggunakan subprocess
subprocess.run(command, shell=True)


# simpan hasil crawling ke csv
file_path = f"tweets-data/{filename}"