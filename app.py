import pandas
import plotly.express as px
import streamlit
from pandas import DataFrame

from moex_stock.bonds import BondsMarket
from moex_stock.shares import SharesMarket
from vtb.position_report import PositionReport
from yahoo.yahoo_finance import YahooFinance


@streamlit.cache
def get_position_report(file: str) -> PositionReport:
    return PositionReport(file)


@streamlit.cache
def get_shares_and_etf_df() -> DataFrame:
    shares_and_etf_df = SharesMarket.update_stock_data()
    return shares_and_etf_df


@streamlit.cache
def get_bonds_stock_df() -> DataFrame:
    bonds_stock_df = BondsMarket.update_stock_data()
    return bonds_stock_df


def get_shares_df() -> DataFrame:
    shares_df = get_shares_and_etf_df()
    shares_df = shares_df[shares_df['sectype'].isin(['usual', 'pref', 'dr'])]
    return shares_df


upload_file = streamlit.sidebar.file_uploader('Отчет по позициям (ВТБ)', 'csv')
if upload_file is not None:
    position_report = get_position_report(upload_file)

    with streamlit.expander('По классу активов'):
        total_df = position_report.get_total_df()
        total_pie = px.pie(total_df, values='sum', names='assets', title='Активы',
                           labels={'assets': 'Активы', 'sum': 'Сумма'})
        streamlit.plotly_chart(total_pie)

    with streamlit.expander('Акции'):
        shares_df = position_report.get_shares_df()
        labels = {'ticker': 'Тикер', 'name': 'Наименование', 'current_sum': 'Текущая сумма', 'change_sum': 'Прибыль'}

        shares_sum_pie = px.pie(shares_df, values='current_sum', names='name', hover_data=['ticker'], title='По долям',
                                labels=labels)
        shares_sum_bar = px.bar(shares_df, x='ticker', y='current_sum', color='change_sum', hover_data=['name'],
                                labels=labels, title='По сумме')
        shares_income_bar = px.bar(shares_df, x='ticker', y='change_sum', hover_data=['name', 'current_sum'],
                                   labels=labels, title='По доходности')

        streamlit.plotly_chart(shares_sum_pie)
        streamlit.plotly_chart(shares_sum_bar)
        streamlit.plotly_chart(shares_income_bar)
        # streamlit.table(shares_df)

    with streamlit.expander('Облигации'):
        labels = {'current_sum': 'Текущая сумма', 'company': 'Компания', 'region': 'Регион', 'type': 'Тип',
                  'sectype': 'Тип'}
        bonds_df = position_report.get_bonds_df()

        catch_last_word = lambda longname: longname.rsplit(' ', 1)[0]
        catch_first_word = lambda longname: longname.split(' ', 1)[0]

        bonds_corp_df = bonds_df[bonds_df['sectype'].isin(['Корпоративные'])]
        bonds_region_df = bonds_df[bonds_df['sectype'].isin(['Муниципальные'])]
        bonds_ofz_df = bonds_df[bonds_df['sectype'].isin(['ОФЗ'])]

        bonds_corp_df['company'] = bonds_corp_df['name'].apply(catch_last_word)
        bonds_region_df['region'] = bonds_region_df['name'].apply(catch_last_word)
        bonds_ofz_df['type'] = bonds_ofz_df['name'].apply(catch_first_word)

        bonds_corp_df.groupby('name').sum()
        bonds_region_df.groupby('name').sum()
        bonds_ofz_df.groupby('name').sum()

        bonds_sectype_df = pandas.concat([bonds_df, position_report.get_bonds_etf_df()])

        all_type_pie = px.pie(bonds_sectype_df, values='current_sum', names='sectype', labels=labels, title='По типу')
        corporate_pie = px.pie(bonds_corp_df, values='current_sum', names='company', labels=labels,
                               title='Корпоративные')
        region_pie = px.pie(bonds_region_df, values='current_sum', names='region', labels=labels, title='Муниципальные')
        ofz_pie = px.pie(bonds_ofz_df, values='current_sum', names='type', labels=labels, title='Государственные')

        streamlit.plotly_chart(all_type_pie)
        streamlit.plotly_chart(ofz_pie)
        streamlit.plotly_chart(region_pie)
        streamlit.plotly_chart(corporate_pie)

select_company = streamlit.multiselect('Тикеры', get_shares_df()['ticker'])
if select_company:
    # labels = {'Close': 'Цена акции', 'Date': 'Дата', 'Dividends': 'Дивиденд'}

    for ticker in select_company:
        name = get_shares_df().isin([ticker]).values[0]
        streamlit.write(name)
        info = YahooFinance(ticker).get_info()
        streamlit.write(info)
        streamlit.write(f"[{ticker}] ({info.get('website')})")

    # history_df = yahoo_data.get_history('max')
    # history_area = px.area(history_df, x=history_df.index, y='Close', labels=labels)
    # streamlit.plotly_chart(history_area)
    #
    # select_period = streamlit.radio('Отчеты', ['Годовые', 'Квартальные'])
    # quarterly_period = False
    # if select_period == 'Годовые':
    #     quarterly_period = False
    # elif select_period == 'Квартальные':
    #     quarterly_period = True
    #
    # select_report = streamlit.radio('Тип отчета', ['Прибыль', 'Баланс', 'Денежные потоки'])
    # financials_df = DataFrame()
    # if select_report == 'Прибыль':
    #     financials_df = yahoo_data.get_financials(quarterly_period)
    # elif select_report == 'Баланс':
    #     financials_df = yahoo_data.get_balance_sheet(quarterly_period)
    # elif select_report == 'Денежные потоки':
    #     financials_df = yahoo_data.get_cashflow(quarterly_period)
    #
    # select_financials = streamlit.selectbox('Показатель', financials_df.columns)
    # financials_bar = px.bar(financials_df, x=financials_df.index, y=select_financials, labels=labels)
    # streamlit.plotly_chart(financials_bar)
    # streamlit.write(financials_df.T)
