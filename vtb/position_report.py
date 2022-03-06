import pandas
from pandas import DataFrame

from moex_stock.moscow_exchange import MoscowExchange


class PositionReport:
    def __init__(self, file: str):
        self.__read_csv_to_dataframe(file)

        self.__join_with_shares_market()
        self.__join_with_bonds_market()
        self.__set_total_report()

    def __read_csv_to_dataframe(self, file: str):
        load_data = pandas.read_csv(file)

        load_data = load_data[['textBox14', 'textBox1', 'textBox2', 'textBox7', 'textBox11', 'textBox22',
                               'textBox8']]  # Отбираем определенные столбцы
        load_data = load_data.fillna(0)  # Заменяем везде NaN на 0

        cash_index = load_data[load_data['textBox1'] == 0].index.values  # Определяем строки по иностранным валютам
        sell_index = load_data[load_data['textBox7'] != 0].index.values  # Определяем строки по проданным активам

        load_data = load_data.drop(index=cash_index)  # Удаляем строки по иностранным валютам
        load_data = load_data.drop(index=sell_index)  # Удаляем строки по проданным активам
        load_data = load_data.drop(['textBox7'], axis='columns')  # Удаляем столбец с датами закрытия позиций

        load_data[['textBox22']] = load_data[['textBox22']].replace(r'\s+', '', regex=True)  # Убираем пробелы в
        # столбце count
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

    def __join_with_shares_market(self):
        shares_market_df = MoscowExchange.get_shares_and_etf_df()

        '''Результат слияния датасета брокерского отчета с рынком акций биржи'''
        shares_and_etf_df = self.__position_df.merge(shares_market_df, how='inner', on='ticker')
        shares_and_etf_df = shares_and_etf_df.rename(columns={'longname': 'name'})

        shares_and_etf_df['buy_sum'] = round(shares_and_etf_df['buy_price'] * shares_and_etf_df['count'], 2)
        shares_and_etf_df['current_sum'] = round(shares_and_etf_df['current_price'] * shares_and_etf_df['count'], 2)
        shares_and_etf_df['change_sum'] = round(shares_and_etf_df['current_sum'] - shares_and_etf_df['buy_sum'], 2)
        shares_and_etf_df['income'] = round((shares_and_etf_df['current_price'] - shares_and_etf_df['buy_price']) /
                                            shares_and_etf_df['buy_price'] * 100, 2)

        shares_df = shares_and_etf_df[shares_and_etf_df['sectype'].isin(['usual', 'pref', 'dr'])]
        etf_df = shares_and_etf_df[shares_and_etf_df['sectype'].isin(['open_pif', 'interval_pif', 'close_pif', 'ETF',
                                                                      'stock_pif'])]
        sum_shares = shares_df.current_sum.sum(axis=0)
        sum_etf = etf_df.current_sum.sum(axis=0)

        shares_df['weight'] = round(shares_df['current_sum'] / sum_shares * 100, 2)
        etf_df['weight'] = round(etf_df['current_sum'] / sum_etf * 100, 2)

        self.__shares_df = shares_df
        self.__etf_df = etf_df

    def __join_with_bonds_market(self):
        bonds_market_df = MoscowExchange.get_bonds_df()
        '''Результат слияния датасета брокерского отчета с рынком облигаций биржи'''
        df = self.__position_df.merge(bonds_market_df, how='inner', on='ticker')
        df = df.rename(columns={'longname': 'name'})

        df['effectiveyield'] = round(df['effectiveyield'], 2)
        df['current_price'] = round((df['price'] / 100 * df['nominal']) + df['nkd'], 2)
        df['current_sum'] = round(df['current_price'] * df['count'], 2)
        self.__bonds_df = df

    def __set_total_report(self):
        shares_sum = round(self.__shares_df['current_sum'].sum(), 2)
        bonds_sum = round(self.__bonds_df['current_sum'].sum(), 2)
        etf_sum = round(self.__etf_df['current_sum'].sum(), 2)

        total_df = pandas.DataFrame([['Акции', shares_sum],
                                     ['Облигации', bonds_sum],
                                     ['Фонды', etf_sum]],
                                    columns=['assets', 'sum'])
        self.__total_df = total_df

    def get_shares_df(self) -> DataFrame:
        return self.__shares_df

    def get_bonds_df(self) -> DataFrame:
        return self.__bonds_df

    def get_etf_df(self) -> DataFrame:
        return self.__etf_df

    def get_total_df(self) -> DataFrame:
        return self.__total_df
