from base64 import b64decode
from io import StringIO

import pandas
from pandas import DataFrame

from moex_stock.bonds import BondsMarket
from moex_stock.etf_parser import EtfParser
from moex_stock.shares import SharesMarket


class PositionReport:
    def __init__(self, file: str):
        self.__set_position_report(file)
        self.__set_shares_report()
        self.__set_bonds_report()

        self.__bonds_etf_df = self.__shares_df[self.__shares_df['category'] == 'bonds']
        self.__gold_etf_df = self.__shares_df[self.__shares_df['category'] == 'gold']
        self.__cash_etf_df = self.__shares_df[self.__shares_df['category'] == 'cash']
        self.__mix_assets_etf_df = self.__shares_df[self.__shares_df['category'] == 'mix_assets']

        self.__shares_df = self.__shares_df.drop(self.__shares_df[self.__shares_df['category'] == 'bonds'].index)
        self.__shares_df = self.__shares_df.drop(self.__shares_df[self.__shares_df['category'] == 'gold'].index)
        self.__shares_df = self.__shares_df.drop(self.__shares_df[self.__shares_df['category'] == 'cash'].index)

        self.__set_total_report()

    def __set_position_report(self, file: str):
        load_data = pandas.read_csv(file)

        load_data = load_data[['textBox14', 'textBox1', 'textBox2', 'textBox7', 'textBox11', 'textBox22',
                               'textBox8']]  # Отбираем определенные столбцы
        load_data = load_data.fillna(0)  # Заменяем везде NaN на 0

        cash_index = load_data[load_data['textBox1'] == 0].index.values  # Определяем строки по иностранным валютам
        sell_index = load_data[load_data['textBox7'] != 0].index.values  # Определяем строки по проданным активам

        load_data = load_data.drop(index=cash_index)  # Удаляем строки по иностранным валютам
        load_data = load_data.drop(index=sell_index)  # Удаляем строки по проданным активам
        load_data = load_data.drop(['textBox7'], axis='columns')  # Удаляем столбец с датами закрытия позиций

        load_data[['textBox22']] = load_data[['textBox22']].replace(r'\s+', '',
                                                                    regex=True)  # Убираем пробелы в столбце count
        load_data[['textBox22']] = load_data[['textBox22']].astype(int)  # Назначаем тип данных

        position_df = DataFrame()
        for ticker in load_data['textBox14'].unique():  # Выделяем строки с уникальными тикерами
            series = load_data[load_data['textBox14'].isin([ticker])].tail(1)  # По указанному тикеру берём последнюю
            # строчку из датафрейма
            position_df = position_df.append(series, ignore_index=True)  # Добавляем строку в новый датафрейм

        ''' Переименовываем колонки '''
        position_df = position_df.rename(columns={'textBox1': 'position_name',
                                                  'textBox2': 'date',
                                                  'textBox11': 'buy_price',
                                                  'textBox22': 'count',
                                                  'textBox14': 'ticker',
                                                  'textBox8': 'commission'})
        self.__position_df = position_df

    def __set_shares_report(self):
        shares_market_df = SharesMarket.update_stock_data()
        all_etf_df = EtfParser().get_df()
        shares_market_df = shares_market_df.merge(all_etf_df, how='left', on='ticker')

        '''Результат слияния датасета брокерского отчета с рынком акций биржи'''
        df = self.__position_df.merge(shares_market_df, how='inner', on='ticker')
        df = df.rename(columns={'longname': 'name'})

        df['buy_sum'] = round(df['buy_price'] * df['count'], 2)
        df['current_sum'] = round(df['current_price'] * df['count'], 2)
        df['change_sum'] = round(df['current_sum'] - df['buy_sum'], 2)

        df['income'] = round((df['current_price'] - df['buy_price']) / df['buy_price'] * 100, 2)
        sum_shares = df.current_sum.sum(axis=0)
        df['weight'] = round(df['current_sum'] / sum_shares * 100, 2)
        self.__shares_df = df

    def __set_bonds_report(self):
        bonds_market_df = BondsMarket.update_stock_data()
        '''Результат слияния датасета брокерского отчета с рынком облигаций биржи'''
        df = self.__position_df.merge(bonds_market_df, how='inner', on='ticker')
        df = df.rename(columns={'longname': 'name'})

        df['effectiveyield'] = round(df['effectiveyield'], 2)
        df['current_price'] = round((df['price'] / 100 * df['nominal']) + df['nkd'], 2)
        df['current_sum'] = round(df['current_price'] * df['count'], 2)
        self.__bonds_df = df

    def __set_total_report(self):
        total_bonds = pandas.concat([self.__bonds_df, self.__bonds_etf_df])

        shares_sum = round(self.__shares_df['current_sum'].sum(), 2)
        bonds_sum = round(total_bonds['current_sum'].sum(), 2)
        gold_sum = round(self.__gold_etf_df['current_sum'].sum(), 2)
        cash_sum = round(self.__cash_etf_df['current_sum'].sum(), 2)

        total_df = pandas.DataFrame([['Акции', shares_sum],
                                     ['Облигации', bonds_sum],
                                     ['Золото', gold_sum],
                                     ['Денежный рынок', cash_sum]],
                                    columns=['assets', 'sum'])
        self.__total_df = total_df

    def get_shares_df(self) -> DataFrame:
        return self.__shares_df

    def get_bonds_df(self) -> DataFrame:
        return self.__bonds_df

    def get_total_df(self) -> DataFrame:
        return self.__total_df

    def get_bonds_etf_df(self) -> DataFrame:
        return self.__bonds_etf_df

    def get_gold_etf_df(self) -> DataFrame:
        return self.__gold_etf_df

    def get_cash_etf_df(self) -> DataFrame:
        return self.__cash_etf_df

    def get_mix_assets_etf_df(self) -> DataFrame:
        return self.__mix_assets_etf_df
