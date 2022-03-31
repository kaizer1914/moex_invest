from lxml import objectify
from pandas import DataFrame

from moex_stock.moscow_exchange import MoscowExchange


class BrokerReportAlpha:
    def __init__(self, file):
        active_list = list()
        cash_list = list()

        # get(имя_атрибута) - извлечение атрибута, text - значение, tag - имя
        xml_data = objectify.parse(file)
        root = xml_data.getroot()
        financial_results = root.Financial_results.Report.Tablix1.code_curr_Collection
        for code_curr in financial_results.getchildren():
            for Details_Collection in code_curr.getchildren():
                for Details in Details_Collection.getchildren():
                    currency = Details.get('code_curr')
                    active_type = Details.get('active_type')
                    name = Details.get('p_name')
                    buy_sum = Details.get('CostOpenPosEnd8')
                    count = Details.get('forword_rest3')
                    if count == '':
                        count = 0
                    isin = Details.get('ISIN4')
                    if active_type == 'Деньги':
                        cash_list.append([active_type, buy_sum, currency])
                    else:
                        active_list.append([isin, name, active_type, count, currency])
        active_df = DataFrame(data=active_list, columns=['isin', 'name', 'active_type', 'count', 'currency'])
        active_df = active_df.astype({'count': 'float'})

        self.__cash_df = DataFrame(data=cash_list, columns=['active_type', 'currency', 'buy_sum'])

        shares_and_etf_df = MoscowExchange.get_shares_and_etf_df()
        bonds_market_df = MoscowExchange.get_bonds_df()

        shares_and_etf_df = shares_and_etf_df.drop(labels='currency', axis='columns')
        bonds_market_df = bonds_market_df.drop(labels='currency', axis='columns')

        shares_market_df = shares_and_etf_df[shares_and_etf_df['sectype'].isin(['usual', 'pref', 'dr'])]
        etf_market_df = shares_and_etf_df[shares_and_etf_df['sectype'].isin(['open_pif', 'interval_pif', 'close_pif',
                                                                             'ETF', 'stock_pif'])]

        shares_df = active_df[active_df['active_type'].isin(['Акции'])]
        etf_df = active_df[active_df['active_type'].isin(['Прочее'])]
        bonds_df = active_df[active_df['active_type'].isin(['Облигации'])]

        shares_df = shares_market_df.merge(shares_df, on='isin', how='inner')
        etf_df = etf_market_df.merge(etf_df, on='isin', how='inner')
        bonds_df = bonds_market_df.merge(bonds_df, on='isin', how='inner')

        shares_df['current_sum'] = round(shares_df['current_price'] * shares_df['count'], 2)
        sum_shares = shares_df.current_sum.sum(axis=0)
        # shares_df['weight'] = round(shares_df['current_sum'] / sum_shares * 100, 2)

        etf_df['current_sum'] = round(etf_df['current_price'] * etf_df['count'], 2)
        sum_etf = etf_df.current_sum.sum(axis=0)
        # etf_df['weight'] = round(etf_df['current_sum'] / sum_etf * 100, 2)

        bonds_df['effectiveyield'] = round(bonds_df['effectiveyield'], 2)
        bonds_df['current_price'] = round((bonds_df['price'] / 100 * bonds_df['nominal']) + bonds_df['nkd'], 2)
        bonds_df['current_sum'] = round(bonds_df['current_price'] * bonds_df['count'], 2)
        sum_bonds = round(bonds_df['current_sum'].sum(), 2)

        total_df = DataFrame([['Акции', sum_shares],
                              ['Облигации', sum_bonds],
                              ['Фонды', sum_etf]],
                             columns=['assets', 'sum'])

        self.__total_df = total_df
        self.__shares_df = shares_df
        self.__etf_df = etf_df
        self.__bonds_df = bonds_df

    def get_cash_df(self) -> DataFrame:
        return self.__cash_df

    def get_shares_df(self) -> DataFrame:
        return self.__shares_df

    def get_etf_df(self) -> DataFrame:
        return self.__etf_df

    def get_bonds_df(self) -> DataFrame:
        return self.__bonds_df

    def get_total_df(self) -> DataFrame:
        return self.__total_df
