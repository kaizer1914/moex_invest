import yfinance
from pandas import DataFrame


class YahooFinance:
    @staticmethod
    def get_info(tickers: list) -> DataFrame:
        df = DataFrame()
        for ticker in tickers:
            data = yfinance.Ticker(ticker.upper() + '.ME')
            info_dict = data.info
            df = df.append(DataFrame(data=[info_dict.values()], columns=info_dict.keys(), index=[ticker]))
        return df

    @staticmethod
    def get_history(ticker: str, period: str = None, interval: str = None) -> DataFrame:
        # get historical market data
        # Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        # Either Use period parameter or use start and end

        # Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        # Intraday data cannot extend last 60 days

        data = yfinance.Ticker(ticker.upper() + '.ME')
        if period or interval is not None:
            df = data.history(period, interval)
        else:
            df = data.history()
        return df

    @staticmethod
    def get_actions(ticker: str) -> DataFrame:
        # show actions (dividends, splits)
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.actions
        return df

    @staticmethod
    def get_dividends(ticker: str) -> DataFrame:
        # show dividends
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.dividends
        return df

    @staticmethod
    def get_splits(ticker: str) -> DataFrame:
        # show splits
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.splits
        return df

    @staticmethod
    def get_financials_yearly(ticker: str) -> DataFrame:
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.financials
        return df

    @staticmethod
    def get_financials_quarterly(ticker: str) -> DataFrame:
        # show financials
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.quarterly_financials
        return df

    @staticmethod
    def get_major_holders(ticker: str) -> DataFrame:
        # show major holders
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.major_holders
        return df

    @staticmethod
    def get_institutional_holders(ticker: str) -> DataFrame:
        # show institutional holders
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.institutional_holders
        return df

    @staticmethod
    def get_balance_sheet_yearly(ticker: str) -> DataFrame:
        # show balance sheet
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.balance_sheet
        return df

    @staticmethod
    def get_balance_sheet_quarterly(ticker: str) -> DataFrame:
        # show balance sheet
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.quarterly_balance_sheet
        return df

    @staticmethod
    def get_cashflow_yearly(ticker: str) -> DataFrame:
        # show cashflow
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.cashflow
        return df

    @staticmethod
    def get_cashflow_quarterly(ticker: str) -> DataFrame:
        # show cashflow
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.quarterly_cashflow
        return df

    @staticmethod
    def get_earnings_yearly(ticker: str) -> DataFrame:
        # show earnings
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.earnings
        return df

    @staticmethod
    def get_earnings_quarterly(ticker: str) -> DataFrame:
        # show earnings
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.quarterly_earnings
        return df

    @staticmethod
    def get_sustainability(ticker: str) -> DataFrame:
        # show sustainability
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.sustainability
        return df

    @staticmethod
    def get_recommendations(ticker: str) -> DataFrame:
        # show analysts recommendations
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.recommendations
        return df

    @staticmethod
    def get_calendar(ticker: str) -> DataFrame:
        # show next event (earnings, etc)
        data = yfinance.Ticker(ticker.upper() + '.ME')
        df = data.calendar
        return df

    @staticmethod
    def get_news(tickers: list) -> DataFrame:
        # show news
        df = DataFrame()
        for ticker in tickers:
            data = yfinance.Ticker(ticker.upper() + '.ME')
            news_dict = data.news[0]
            df = df.append(DataFrame(data=[news_dict.values()], columns=news_dict.keys(), index=[ticker]))
        return df
