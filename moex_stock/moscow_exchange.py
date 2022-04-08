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
        # market = response_data['marketdata']

        '''Задаем содержимое и заголовки колонок'''
        securities_df = DataFrame(data=securities.data, columns=securities.columns)
        # market_data = DataFrame(data=market.data, columns=market.columns)

        # securities_data = securities_data.merge(market_data, how='left')  # Объединяем таблицы
        securities_df = securities_df.fillna(0)  # Замена NaN на 0

        '''Ищем и удаляем строки'''
        small_index = securities_df[securities_df['BOARDID'] == 'SMAL'].index.values  # Неполные лоты (акции)
        securities_df = securities_df.drop(index=small_index)

        speq_index = securities_df[securities_df['BOARDID'] == 'SPEQ'].index.values  # Поставка по СК (акции)
        securities_df = securities_df.drop(index=speq_index)

        tqdp_index = securities_df[securities_df['BOARDID'] == 'TQDP'].index.values  # Крупные пакеты - Акции
        securities_df = securities_df.drop(index=tqdp_index)

        currency_usd_index = securities_df[securities_df['CURRENCYID'] == 'USD'].index.values  # В долларах
        securities_df = securities_df.drop(index=currency_usd_index)

        currency_eur_index = securities_df[securities_df['CURRENCYID'] == 'EUR'].index.values  # В евро
        securities_df = securities_df.drop(index=currency_eur_index)

        null_price_index = securities_df[securities_df['PREVPRICE'] == 0].index.values
        securities_df = securities_df.drop(index=null_price_index)

        '''Отбираем нужные колонки'''
        securities_df = securities_df[[
            'SECID', 'SHORTNAME', 'SECNAME', 'ISIN', 'PREVPRICE', 'DECIMALS', 'LOTSIZE', 'CURRENCYID', 'SECTYPE',
            'LISTLEVEL', 'ISSUESIZE']]

        '''Переименовываем колонки'''
        securities_df = securities_df.rename(columns={'SHORTNAME': 'shortname',
                                                      'SECID': 'ticker',
                                                      'SECNAME': 'longname',
                                                      'ISIN': 'isin',
                                                      'PREVPRICE': 'current_price',
                                                      'DECIMALS': 'decimals',
                                                      'LOTSIZE': 'lotsize',
                                                      'CURRENCYID': 'currency',
                                                      # 'ISSUECAPITALIZATION': 'market_cap',
                                                      'SECTYPE': 'sectype',
                                                      'LISTLEVEL': 'listlevel',
                                                      'ISSUESIZE': 'issuesize',
                                                      })
        '''Округление по данным биржи'''
        round_by_decimals = lambda x: round(x['current_price'], x['decimals'])
        securities_df['current_price'] = securities_df.apply(round_by_decimals, axis=1)

        '''Вычисление рыночной капитализации'''
        securities_df['market_cap'] = securities_df['issuesize'] * securities_df['current_price']

        '''Замена значений типа бумаги на более понятные'''
        securities_df['sectype'] = securities_df['sectype'].replace('1', 'usual')
        securities_df['sectype'] = securities_df['sectype'].replace('2', 'pref')
        securities_df['sectype'] = securities_df['sectype'].replace('9', 'open_pif')
        securities_df['sectype'] = securities_df['sectype'].replace('A', 'interval_pif')
        securities_df['sectype'] = securities_df['sectype'].replace('B', 'close_pif')
        securities_df['sectype'] = securities_df['sectype'].replace('D', 'dr')
        securities_df['sectype'] = securities_df['sectype'].replace('E', 'ETF')
        securities_df['sectype'] = securities_df['sectype'].replace('J', 'stock_pif')

        return securities_df

    @staticmethod
    def get_foreign_shares_df() -> DataFrame:
        url = 'https://iss.moex.com/iss/engines/stock/markets/foreignshares/securities.json?iss.meta=off'
        response_df = pandas.read_json(url)
        securities = response_df['securities']
        market = response_df['marketdata']

        '''Задаем содержимое и заголовки колонок'''
        securities_df = DataFrame(data=securities.data, columns=securities.columns)
        market_df = DataFrame(data=market.data, columns=market.columns)

        response_df = securities_df.merge(market_df, how='left')  # Объединяем таблицы
        response_df = response_df.fillna(0)  # Замена NaN на 0

        '''Отбираем нужные колонки'''
        response_df = response_df[
            ['SECID', 'BOARDID', 'SHORTNAME', 'LOTSIZE', 'DECIMALS', 'SECNAME', 'ISSUESIZE', 'ISIN', 'CURRENCYID',
             'SECTYPE', 'LISTLEVEL', 'PREVPRICE']]

        '''Переименовываем колонки'''
        response_df = response_df.rename(columns={'SHORTNAME': 'shortname',
                                                  'SECID': 'ticker',
                                                  'SECNAME': 'longname',
                                                  'ISIN': 'isin',
                                                  'DECIMALS': 'decimals',
                                                  'LOTSIZE': 'lotsize',
                                                  'CURRENCYID': 'currency',
                                                  'SECTYPE': 'sectype',
                                                  'LISTLEVEL': 'listlevel',
                                                  'ISSUESIZE': 'issuesize',
                                                  'BOARDID': 'boardid',
                                                  'PREVPRICE': 'price'
                                                  })

        '''Лямбда-функция, убирающая суффикс-RM из тикера'''
        catch_suffix = lambda suffix: suffix.rsplit('-RM', 1)[0]
        response_df['ticker'] = response_df['ticker'].apply(catch_suffix)

        '''Определение цены в рублях и в долларах'''
        usd_df = response_df[response_df['boardid'].isin(['TQBD'])]
        rub_df = response_df[response_df['boardid'].isin(['FQBR'])]

        usd_df = usd_df.rename(columns={'price': 'price_usd'})
        rub_df = rub_df.rename(columns={'price': 'price_rub'})

        '''Округление по значению DECIMALS'''
        rounded_usd = lambda x: round(x['price_usd'], x['decimals'])
        rounded_rub = lambda x: round(x['price_rub'], x['decimals'])

        usd_df['price_usd'] = usd_df.apply(rounded_usd, axis=1)
        rub_df['price_rub'] = rub_df.apply(rounded_rub, axis=1)

        usd_df = usd_df.drop(['boardid', 'currency', 'decimals'], axis='columns')
        rub_df = rub_df.drop(['boardid', 'currency', 'decimals'], axis='columns')

        response_df = pandas.merge(usd_df, rub_df, how='inner',
                                   on=['ticker', 'shortname', 'lotsize', 'longname', 'isin', 'sectype', 'listlevel',
                                       'longname', 'issuesize'])
        return response_df

    @staticmethod
    def get_tickers_for_yahoo() -> DataFrame:
        # add_suffix_me = lambda x: str(x) + '.ME'
        # up_letters = lambda x: str(x).upper()

        native_shares_df = MoscowExchange.get_shares_and_etf_df()
        native_shares_df = native_shares_df[native_shares_df['sectype'].isin(['usual', 'pref', 'dr'])]
        # native_shares_df['ticker'] = native_shares_df['ticker'].apply(up_letters)
        # native_shares_df['ticker'] = native_shares_df['ticker'].apply(add_suffix_me)

        # foreign_shares_df = MoscowExchange.get_foreign_shares_df()
        # foreign_shares_df['ticker'] = foreign_shares_df['ticker'].apply(up_letters)
        # yahoo_df = pandas.merge(native_shares_df['ticker'], foreign_shares_df['ticker'], how='outer')
        return native_shares_df

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

    @staticmethod
    def get_market_cap(ticker: str):
        ticker = ticker.upper()
        url = f'https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker}/securities.json?iss.meta=off'
        response_df = pandas.read_json(url)
        securities = response_df['securities']
        securities_df = DataFrame(data=securities.data, columns=securities.columns)
        founded_df = securities_df[securities_df['BOARDID'].isin(['TQBR'])]
        market_cap = founded_df['PREVPRICE'].values[0] * founded_df['ISSUESIZE'].values[0]
        market_cap_pref = 0
        if len(ticker) == 5 and ticker[4] == 'P':  # Если префы
            url = f'https://iss.moex.com/iss/engines/stock/markets/shares/securities/{ticker[:4]}' \
                  f'/securities.json?iss.meta=off'
            response_df = pandas.read_json(url)
            securities = response_df['securities']
            securities_df = DataFrame(data=securities.data, columns=securities.columns)
            founded_df = securities_df[securities_df['BOARDID'].isin(['TQBR'])]
            market_cap_pref = founded_df['PREVPRICE'].values[0] * founded_df['ISSUESIZE'].values[0]
        market_cap = market_cap + market_cap_pref
        return market_cap

    # Данные для графика цены акции
    @staticmethod
    def get_security_history(ticker: str, begin_date: str) -> DataFrame:
        ticker = ticker.upper()
        index = 0
        page_size = 0
        total = 1
        result_df = None

        while index + page_size <= total:
            url = f'https://iss.moex.com/iss/history/engines/stock/markets/shares/securities/{ticker}.json?' \
                  f'iss.meta=off&start={index + page_size}&from={begin_date}'
            response_df = pandas.read_json(url)
            history_cursor = response_df['history.cursor']
            history_cursor_df = DataFrame(data=history_cursor.data, columns=history_cursor.columns)

            index = history_cursor_df['INDEX'].values[0]
            page_size = history_cursor_df['PAGESIZE'].values[0]
            total = history_cursor_df['TOTAL'].values[0]
            # print(index, page_size, total)

            history = response_df['history']
            history_df = DataFrame(data=history.data, columns=history.columns)
            history_df = history_df[history_df['BOARDID'].isin(['TQBR'])]
            if result_df is None:
                result_df = history_df
            else:
                result_df = pandas.concat([result_df, history_df])

        result_df = result_df[['SECID', 'SHORTNAME', 'TRADEDATE', 'NUMTRADES', 'VALUE', 'OPEN', 'LOW', 'HIGH',
                               'WAPRICE', 'CLOSE', 'VOLUME']]
        result_df = result_df.rename(columns={'SECID': 'ticker',
                                              'SHORTNAME': 'short_name',
                                              'TRADEDATE': 'date',
                                              'NUMTRADES': 'num_trades',
                                              'VALUE': 'trading_volume',
                                              'VOLUME': 'trading_sec',
                                              'OPEN': 'open_price',
                                              'LOW': 'low_price',
                                              'HIGH': 'high_price',
                                              'WAPRICE': 'medium_price',
                                              'CLOSE': 'close_price'
                                              })
        result_df = result_df.fillna(0)
        null_price_index = result_df[result_df['trading_sec'] == 0].index.values
        result_df = result_df.drop(index=null_price_index)
        result_df = result_df.reset_index(drop=True)

        result_df['average'] = round(result_df['medium_price'] / result_df['medium_price'].mean() * 100, 2)
        return result_df

    @staticmethod
    def get_securities_history(tickers: list, begin_date: str) -> DataFrame:
        companies_df = None
        for ticker in tickers:
            company_df = MoscowExchange.get_security_history(ticker, begin_date)
            if companies_df is None:
                companies_df = company_df
            else:
                companies_df = pandas.concat([companies_df, company_df])
        return companies_df
