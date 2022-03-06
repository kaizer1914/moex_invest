import yfinance
from pandas import DataFrame

from moex_stock.moscow_exchange import MoscowExchange


class YahooFinance:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.__data = yfinance.Ticker(ticker.upper())

    def get_info(self) -> DataFrame:
        info_dict = self.__data.info
        df = DataFrame(data=[info_dict.values()], columns=info_dict.keys(), index=[self.ticker])
        df = df.fillna(0)

        df['netDebt'] = df['totalDebt'] - df['totalCash']  # Попутно вычисляем чистый долг
        '''Переводим показатели эффективности в процентный вид'''
        df['grossMargins'] = df['grossMargins'] * 100
        df['operatingMargins'] = df['operatingMargins'] * 100
        df['profitMargins'] = df['profitMargins'] * 100
        df['ebitdaMargins'] = df['ebitdaMargins'] * 100
        df['returnOnAssets'] = df['returnOnAssets'] * 100
        df['returnOnEquity'] = df['returnOnEquity'] * 100

        df = df[[
            'marketCap',
            'financialCurrency',
            #   Коэффициенты эффективности
            'grossMargins',
            'operatingMargins',
            'profitMargins',
            'ebitdaMargins',
            'returnOnAssets',
            'returnOnEquity',
            #   Денежные потоки
            'ebitda',
            'operatingCashflow',
            'freeCashflow',
            #   Прибыль
            'totalRevenue',
            'grossProfits',
            'netIncomeToCommon',
            #   Долг
            # 'totalCash',
            # 'totalDebt',
            'netDebt',
            #   Коэффициенты ликвидности, долга к капиталу
            'currentRatio',
            'quickRatio',
            'debtToEquity',
        ]]

        '''Добавление курса рубля по валюте отчетности (USD)'''
        get_currency_course = lambda financial_currency: MoscowExchange.get_currency_course(financial_currency) \
            if financial_currency != 'RUB' else 1
        df['currencyCourse'] = df['financialCurrency'].apply(get_currency_course)
        df['marketCap'] = df['marketCap'] / df['currencyCourse']
        return df

    def get_history(self, period: str = None) -> DataFrame:
        # get historical market data
        # Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        if period is not None:
            df = self.__data.history(period)
        else:
            df = self.__data.history()
        return df

    def get_actions(self) -> DataFrame:
        # show actions (dividends, splits)
        return self.__data.actions

    def get_dividends(self) -> DataFrame:
        # show dividends
        return self.__data.dividends

    def get_splits(self) -> DataFrame:
        # show splits
        return self.__data.splits

    def get_financials(self, quarterly: bool = False) -> DataFrame:
        if quarterly:
            df = self.__data.quarterly_financials
        else:
            df = self.__data.financials
        df = df.T.dropna(axis='columns', how='all', inplace=False)
        return df

    def get_major_holders(self) -> DataFrame:
        # show major holders
        return self.__data.major_holders

    def get_institutional_holders(self) -> DataFrame:
        # show institutional holders
        return self.__data.institutional_holders

    def get_balance_sheet(self, quarterly: bool = False) -> DataFrame:
        # show balance sheet
        if quarterly:
            df = self.__data.quarterly_balance_sheet
        else:
            df = self.__data.balance_sheet
        return df.T

    def get_cashflow(self, quarterly: bool = False) -> DataFrame:
        # show cashflow
        if quarterly:
            df = self.__data.quarterly_cashflow
        else:
            df = self.__data.cashflow
        return df.T

    def get_earnings(self, quarterly: bool = False) -> DataFrame:
        # show earnings
        if quarterly:
            df = self.__data.quarterly_earnings
        else:
            df = self.__data.earnings
        return df

    def get_sustainability(self) -> DataFrame:
        # show sustainability
        return self.__data.sustainability

    def get_recommendations(self) -> DataFrame:
        # show analysts recommendations
        return self.__data.recommendations

    def get_calendar(self) -> DataFrame:
        # show next event (earnings, etc)
        return self.__data.calendar

    def get_news(self) -> DataFrame:
        # show news
        news_dict = self.__data.news[0]
        df = DataFrame(data=[news_dict.values()], columns=news_dict.keys(), index=[self.ticker])
        return df
