"""
https://www.moex.com/msn/etf
Спарсить страничку с целью выяснения etf и бпиф Московской биржи по классу активов
и последующего сохранения в БД
"""

import pandas
import requests
from bs4 import BeautifulSoup


class EtfParser:
    columns = {
        1: 'fund',
        2: 'provider',
        3: 'base_asset',
        4: 'currency',
        5: 'type',
        6: 'ticker',
    }

    def __init__(self):
        url = 'https://www.moex.com/msn/etf'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        table = soup.findAll('table')[1].tbody
        rows = table.find_all('tr')
        # print(rows)

        data = list()
        for row in rows:
            cols = row.find_all('td')
            headers = row.find_all('strong')
            cols = [element.text.strip() for element in cols]
            headers = [element.string for element in headers]
            if cols:
                data.append([element for element in cols if element])
            elif headers:
                data.append(headers)
        print(data)

        bonds_index = 0
        cash_index = 0
        shares_index = 0
        products_index = 0
        gold_index = 0
        mix_assets_index = 0

        for row in data:
            if row[0] == 'Облигации/Еврооблигации':
                bonds_index = data.index(row)
            elif row[0] == 'Денежный рынок':
                cash_index = data.index(row)
            elif row[0] == 'Акции':
                shares_index = data.index(row)
            elif row[0] == 'Товары':
                products_index = data.index(row)
            elif row[0] == 'Золото':
                gold_index = data.index(row)
            elif row[0] == 'Смешанные активы':
                mix_assets_index = data.index(row)
            else:
                row[1] = row[1].replace('\n', '').replace('\r', '').replace('\t', '')
                row[2] = row[2].replace('\n', '').replace('\r', '').replace('\t', '')
                row[3] = row[3].replace('\n', '').replace('\r', '').replace('\t', '')

        bonds_df = pandas.DataFrame(data[bonds_index + 1:cash_index])
        cash_df = pandas.DataFrame(data[cash_index + 1:shares_index])
        shares_df = pandas.DataFrame(data[shares_index + 1:products_index])
        gold_df = pandas.DataFrame(data[gold_index + 1:mix_assets_index])
        mix_assets_df = pandas.DataFrame(data[mix_assets_index + 1:])

        bonds_df['category'] = 'bonds'
        cash_df['category'] = 'cash'
        shares_df['category'] = 'shares'
        gold_df['category'] = 'gold'
        mix_assets_df['category'] = 'mix_assets'

        df = pandas.concat([bonds_df, cash_df, shares_df, gold_df, mix_assets_df], ignore_index=True, axis='rows')
        df = df.rename(self.columns, axis='columns')
        df = df.drop(0, axis='columns')  # Удаляем номера строк
        df = df.drop(7, axis='columns')  # Удаляем бесполезную колонку
        self.__etf_df = df

    def get_df(self):
        return self.__etf_df
