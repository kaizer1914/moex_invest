import pandas
from pandas import DataFrame

'''
https://iss.moex.com/iss/engines/stock/markets/shares/securities.xml?iss.meta=off - список всех российских акций
https://iss.moex.com/iss/engines/stock/markets/foreignshares/securities.xml?iss.meta=off - список всех иностранных акций

https://iss.moex.com/iss/engines/stock/markets/shares.xml?iss.meta=off  - справка по рынкам российских акций
https://iss.moex.com/iss/engines/stock/markets/foreignshares.xml?iss.meta=off  - справка по рынкам иностранных акций

https://iss.moex.com/iss/engines/stock/markets/bonds/securities.xml?iss.meta=off - список всех облигаций
https://iss.moex.com/iss/engines/stock/markets/bonds.xml?iss.meta=off  - справка по рынкам облигаций
'''


class MoscowExchange:
    @staticmethod
    def get_shares_and_etf_df() -> DataFrame:
        url = 'https://iss.moex.com/iss/engines/stock/markets/shares/securities.json?iss.meta=off'
        response_data = pandas.read_json(url)
        securities = response_data['securities']
        market = response_data['marketdata']

        '''Задаем содержимое и заголовки колонок'''
        securities_data = DataFrame(data=securities.data, columns=securities.columns)
        market_data = DataFrame(data=market.data, columns=market.columns)

        securities_data = securities_data.merge(market_data, how='left')  # Объединяем таблицы
        securities_data = securities_data.fillna(0)  # Замена NaN на 0

        '''Ищем и удаляем строки'''
        small_index = securities_data[securities_data['BOARDID'] == 'SMAL'].index.values  # Неполные лоты (акции)
        speq_index = securities_data[securities_data['BOARDID'] == 'SPEQ'].index.values  # Поставка по СК (акции)
        tqdp_index = securities_data[securities_data['BOARDID'] == 'TQDP'].index.values  # Крупные пакеты - Акции
        currency_usd_index = securities_data[securities_data['CURRENCYID'] == 'USD'].index.values  # В долларах
        currency_eur_index = securities_data[securities_data['CURRENCYID'] == 'EUR'].index.values  # В евро

        securities_data = securities_data.drop(index=small_index)
        securities_data = securities_data.drop(index=speq_index)
        securities_data = securities_data.drop(index=tqdp_index)
        securities_data = securities_data.drop(index=currency_usd_index)
        securities_data = securities_data.drop(index=currency_eur_index)

        null_price_index = securities_data[securities_data['LAST'] == 0].index.values
        securities_data = securities_data.drop(index=null_price_index)

        '''Отбираем нужные колонки'''
        securities_data = securities_data[
            ['SECID', 'SHORTNAME', 'SECNAME', 'ISIN', 'LAST', 'DECIMALS', 'LOTSIZE', 'CURRENCYID',
             'ISSUECAPITALIZATION', 'SECTYPE', 'LISTLEVEL', 'ISSUESIZE']]

        '''Переименовываем колонки'''
        securities_data = securities_data.rename(columns={'SHORTNAME': 'shortname',
                                                          'SECID': 'ticker',
                                                          'SECNAME': 'longname',
                                                          'ISIN': 'isin',
                                                          'LAST': 'current_price',
                                                          'DECIMALS': 'decimals',
                                                          'LOTSIZE': 'lotsize',
                                                          'CURRENCYID': 'currency',
                                                          'ISSUECAPITALIZATION': 'market_cap',
                                                          'SECTYPE': 'sectype',
                                                          'LISTLEVEL': 'listlevel',
                                                          'ISSUESIZE': 'issuesize',
                                                          })
        '''Округление по данным биржи'''
        rounded = lambda x: round(x['current_price'], x['decimals'])
        securities_data['current_price'] = securities_data.apply(rounded, axis=1)

        '''Замена значений типа бумаги на более понятные'''
        securities_data['sectype'] = securities_data['sectype'].replace('1', 'usual')
        securities_data['sectype'] = securities_data['sectype'].replace('2', 'pref')
        securities_data['sectype'] = securities_data['sectype'].replace('9', 'open_pif')
        securities_data['sectype'] = securities_data['sectype'].replace('A', 'interval_pif')
        securities_data['sectype'] = securities_data['sectype'].replace('B', 'close_pif')
        securities_data['sectype'] = securities_data['sectype'].replace('D', 'dr')
        securities_data['sectype'] = securities_data['sectype'].replace('E', 'ETF')
        securities_data['sectype'] = securities_data['sectype'].replace('J', 'stock_pif')

        return securities_data

    @staticmethod
    def get_foreign_shares_df() -> DataFrame:
        url = 'https://iss.moex.com/iss/engines/stock/markets/foreignshares/securities.json?iss.meta=off'
        response_df = pandas.read_json(url)
        return response_df

    @staticmethod
    def get_bonds_df() -> DataFrame:
        url = 'https://iss.moex.com/iss/engines/stock/markets/bonds/securities.json?iss.meta=off'
        response_data = pandas.read_json(url)
        securities = response_data['securities']
        market_yields = response_data['marketdata_yields']

        '''Задаем содержимое и заголовки колонок'''
        securities_data = DataFrame(data=securities.data, columns=securities.columns)
        market_yields_data = DataFrame(data=market_yields.data, columns=market_yields.columns)

        securities_data = securities_data.merge(market_yields_data, how='left')  # Объединяем таблицы
        securities_data = securities_data.fillna(0)  # Замена NaN на 0

        empty_index = securities_data[securities_data['PRICE'] == 0].index.values  # Ищем строки с нулевой ценой

        '''Удаляем такие строки'''
        securities_data = securities_data.drop(index=empty_index)

        '''Отбираем нужные колонки'''
        securities_data = securities_data[
            ['SECID', 'SHORTNAME', 'SECNAME', 'ISIN', 'PRICE', 'DECIMALS', 'ACCRUEDINT', 'LOTVALUE',
             'LOTSIZE', 'CURRENCYID', 'COUPONVALUE', 'COUPONPERCENT', 'COUPONPERIOD', 'NEXTCOUPON', 'EFFECTIVEYIELD',
             'DURATION', 'YIELDDATE', 'YIELDDATETYPE', 'OFFERDATE', 'MATDATE', 'ISSUESIZEPLACED', 'SECTYPE',
             'LISTLEVEL']]

        '''Назначаем тикер в качестве индекса'''
        securities_data.index = securities_data['SECID']
        securities_data.index.name = 'ticker'
        securities_data = securities_data.drop(['SECID'], axis=1)

        '''Переименовываем колонки'''
        securities_data = securities_data.rename(columns={'SHORTNAME': 'shortname',
                                                          'SECNAME': 'longname',
                                                          'ISIN': 'isin',
                                                          'PRICE': 'price',
                                                          'DECIMALS': 'decimals',
                                                          'ACCRUEDINT': 'nkd',
                                                          'LOTVALUE': 'nominal',
                                                          'LOTSIZE': 'lotsize',
                                                          'CURRENCYID': 'currency',
                                                          'COUPONVALUE': 'couponvalue',
                                                          'COUPONPERCENT': 'couponpercent',
                                                          'COUPONPERIOD': 'couponperiod',
                                                          'NEXTCOUPON': 'nextcoupon',
                                                          'EFFECTIVEYIELD': 'effectiveyield',
                                                          'DURATION': 'duration',
                                                          'YIELDDATE': 'yielddate',
                                                          'YIELDDATETYPE': 'endtype',
                                                          'OFFERDATE': 'offerdate',
                                                          'MATDATE': 'enddate',
                                                          'ISSUESIZEPLACED': 'issuesize',
                                                          'SECTYPE': 'sectype',
                                                          'LISTLEVEL': 'listlevel'
                                                          })
        '''Округление по данным биржи'''
        rounded = lambda x: round(x['price'], x['decimals'])
        securities_data['price'] = securities_data.apply(rounded, axis=1)

        '''Замена значений типа бумаги на более понятные'''
        securities_data['sectype'] = securities_data['sectype'].replace('3', 'ОФЗ')
        securities_data['sectype'] = securities_data['sectype'].replace('4', 'Муниципальные')
        securities_data['sectype'] = securities_data['sectype'].replace('5', 'ЦБ')
        securities_data['sectype'] = securities_data['sectype'].replace('6', 'Корпоративные')
        securities_data['sectype'] = securities_data['sectype'].replace('7', 'МФО')
        securities_data['sectype'] = securities_data['sectype'].replace('8', 'Корпоративные')
        securities_data['sectype'] = securities_data['sectype'].replace('C', 'Муниципальные')

        return securities_data

    @staticmethod
    def get_currencies_df() -> DataFrame:
        url = 'https://iss.moex.com/iss/statistics/engines/futures/markets/indicativerates/securities.json?iss.meta=off'
        response_df = pandas.read_json(url)
        response_df = response_df['securities']
        response_list = response_df.tolist()
        response_df = DataFrame(data=response_list[1], columns=response_list[0])
        return response_df

    @staticmethod
    def get_currency_course(first_currency: str, second_currency: str = 'RUB') -> float:
        first_currency = first_currency.upper()
        second_currency = second_currency.upper()
        currencies_par = first_currency + '/' + second_currency  # Валютная пара, которая интересует
        cur_df = MoscowExchange.get_currencies_df()  # Получаем датафрейм с валютами с Мосбиржи
        cur_df = cur_df[cur_df['secid'].isin([currencies_par])]  # Находим строку в датафрейме с валютной парой
        course = cur_df['rate'].values[0]  # Извлекаем значение курса из строки
        return course


if __name__ == '__main__':
    df = MoscowExchange.get_foreign_shares_df()
    print(df)
