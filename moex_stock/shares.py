import pandas
from pandas import DataFrame


# https://iss.moex.com/iss/engines/stock/markets/shares/securities.xml?iss.meta=off - список всех акций
# https://iss.moex.com/iss/engines/stock/markets/shares.xml?iss.meta=off  - справка по рынкам акций

class SharesMarket:
    @staticmethod
    def update_stock_data() -> DataFrame:
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
