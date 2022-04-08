import datetime

import pandas
import plotly.express as px
import streamlit
from pandas import DataFrame
from streamlit.uploaded_file_manager import UploadedFile

from broker_report.alpha import BrokerReportAlpha
from broker_report.position_report_vtb import PositionReportVTB
from moex_stock.moscow_exchange import MoscowExchange
from yahoo.yahoo_finance import YahooFinance


@streamlit.cache(suppress_st_warning=True)
def get_position_report(file: UploadedFile):
    if file.type == 'text/xml':
        return BrokerReportAlpha(file)
    elif file.type == 'text/csv':
        return PositionReportVTB(file)


@streamlit.cache(suppress_st_warning=True)
def get_shares_and_etf_stock_df() -> DataFrame:
    shares_and_etf_stock_df = MoscowExchange.get_shares_and_etf_df()
    return shares_and_etf_stock_df


@streamlit.cache(suppress_st_warning=True)
def get_bonds_stock_df() -> DataFrame:
    bonds_stock_df = MoscowExchange.get_bonds_df()
    return bonds_stock_df


@streamlit.cache(suppress_st_warning=True)
def get_tickers_df() -> DataFrame:
    tickers_df = MoscowExchange.get_tickers_for_yahoo()
    return tickers_df


@streamlit.cache(suppress_st_warning=True)
def get_info(ticker: str) -> DataFrame:
    df = YahooFinance(ticker).get_info()
    return df


@streamlit.cache(suppress_st_warning=True)
def get_earnings(ticker: str, is_quarterly: bool) -> DataFrame:
    return YahooFinance(ticker).get_financials(is_quarterly)


@streamlit.cache(suppress_st_warning=True)
def get_balance_sheet(ticker: str, is_quarterly: bool) -> DataFrame:
    return YahooFinance(ticker).get_balance_sheet(is_quarterly)


@streamlit.cache(suppress_st_warning=True)
def get_cashflow(ticker: str, is_quarterly: bool) -> DataFrame:
    return YahooFinance(ticker).get_cashflow(is_quarterly)


@streamlit.cache(suppress_st_warning=True)
def get_history_sec(tickers: list, date: str):
    return MoscowExchange.get_securities_history(tickers, date)


# Отчет по позициям
streamlit.sidebar.header('Брокерский отчет')
broker_file = streamlit.sidebar.file_uploader('Загрузить отчет по позициям ВТБ (csv), '
                                              'брокерский отчет Альфа Банк (xml)',
                                              ['xml', 'csv'])
if broker_file is not None:
    streamlit.title('Анализ отчета по позициям')
    position_report = get_position_report(broker_file)

    streamlit.header('По классу активов')
    total_df = position_report.get_total_df()
    total_pie = px.pie(total_df, values='sum', names='assets', title='Активы',
                       labels={'assets': 'Активы', 'sum': 'Сумма'})
    streamlit.plotly_chart(total_pie)

    streamlit.header('Акции')
    shares_df = position_report.get_shares_df()
    labels = {'ticker': 'Тикер', 'longname': 'Компания', 'current_sum': 'Текущая сумма'}
    shares_sum_pie = px.pie(shares_df, values='current_sum', names='longname', hover_data=['ticker'], title='По долям',
                            labels=labels)
    streamlit.plotly_chart(shares_sum_pie)
    streamlit.write(shares_df)

    streamlit.header('Фонды')
    labels = {'ticker': 'Тикер', 'longname': 'Наименование', 'current_sum': 'Текущая сумма'}
    etf_df = position_report.get_etf_df()
    etf_sum_pie = px.pie(etf_df, values='current_sum', names='longname', hover_data=['ticker'], title='По долям',
                         labels=labels)
    streamlit.plotly_chart(etf_sum_pie)
    streamlit.write(etf_df)

    streamlit.header('Облигации')
    labels = {'current_sum': 'Текущая сумма', 'company': 'Компания', 'region': 'Регион', 'type': 'Тип',
              'sec-type': 'Тип'}
    bonds_df = position_report.get_bonds_df()

    catch_last_word = lambda longname: longname.rsplit(' ', 1)[0]
    catch_first_word = lambda longname: longname.split(' ', 1)[0]

    bonds_corp_df = bonds_df[bonds_df['sectype'].isin(['Корпоративные'])]
    bonds_region_df = bonds_df[bonds_df['sectype'].isin(['Муниципальные'])]
    bonds_ofz_df = bonds_df[bonds_df['sectype'].isin(['ОФЗ'])]

    bonds_corp_df['company'] = bonds_corp_df['longname'].apply(catch_last_word)
    bonds_region_df['region'] = bonds_region_df['longname'].apply(catch_last_word)
    bonds_ofz_df['type'] = bonds_ofz_df['longname'].apply(catch_first_word)

    bonds_corp_df.groupby('longname').sum()
    bonds_region_df.groupby('longname').sum()
    bonds_ofz_df.groupby('longname').sum()

    all_type_pie = px.pie(bonds_df, values='current_sum', names='sectype', labels=labels, title='По типу')
    corporate_pie = px.pie(bonds_corp_df, values='current_sum', names='company', labels=labels, title='Корпоративные')
    region_pie = px.pie(bonds_region_df, values='current_sum', names='region', labels=labels, title='Муниципальные')
    ofz_pie = px.pie(bonds_ofz_df, values='current_sum', names='type', labels=labels, title='Государственные')

    streamlit.plotly_chart(all_type_pie)
    streamlit.plotly_chart(ofz_pie)
    streamlit.plotly_chart(region_pie)
    streamlit.plotly_chart(corporate_pie)
    streamlit.write(bonds_df)

# Yahoo Finance
streamlit.sidebar.header('Данные компаний')
select_companies = streamlit.sidebar.multiselect('Выбрать компании', get_tickers_df())  # Выбираем тикер из списка
# компаний Мосбиржи
if select_companies:
    streamlit.title('Обзор и сравнение компаний')

    streamlit.header('Сравнение текущих финансовых показателей')
    # Формирование датафрейма сравнения
    info_df = None
    for ticker in select_companies:
        begin_info_df = get_info(ticker)
        if info_df is None:
            info_df = begin_info_df
        else:
            info_df = pandas.concat([info_df, begin_info_df])

    # Диаграмма и таблица текущих показателей
    info_parameters = streamlit.multiselect('Выбор параметров', info_df.columns)
    if info_parameters:
        info_bar = px.bar(info_df, x=info_df.index, y=info_parameters, hover_data=['financialCurrency'],
                          labels={'value': 'Значение', 'index': 'Компания', 'variable': 'Финансовые показатели'},
                          title='Диаграмма показателей', barmode='group')
        streamlit.plotly_chart(info_bar)
    streamlit.subheader('Текущие финансовые показатели')
    streamlit.write(info_df)

    # График сравнения цены
    streamlit.header('Сравнение цены')
    date = streamlit.date_input('Выбор даты', datetime.date(2022, 1, 1))
    history_df = get_history_sec(select_companies, date)
    history_line = px.line(history_df, x=history_df['date'], y=history_df['average'], color=history_df['ticker'],
                           labels={'date': 'Дата', 'average': 'Средняя цена, %', 'ticker': 'Тикер',
                                   'medium_price': 'Средняя цена'},
                           hover_data=['medium_price'], title='Ценовая диаграмма')
    streamlit.plotly_chart(history_line)

    # Диаграммы и таблицы отчетов
    streamlit.header('Исторические данные компаний')
    select_ticker = streamlit.selectbox('Выбор компании', select_companies)  # Выбор отдельной компании
    if select_ticker:
        income = 'Прибыль'
        balance = 'Баланс'
        cashflow = 'Денежный поток'
        yearly = 'Годовой'
        quarterly = 'Квартальный'

        select_date_range = streamlit.radio('Временной период', (yearly, quarterly))  # Квартальные или годовые отчеты
        is_quarterly = False
        if select_date_range == yearly:
            is_quarterly = False
        elif select_date_range == quarterly:
            is_quarterly = True

        select_report = streamlit.radio('Вид отчета',
                                        (income, balance, cashflow))  # Отчеты: Балансовый, Прибыль, Денежный поток
        report_df = None
        if select_report == income:
            report_df = get_earnings(select_ticker, is_quarterly)
        elif select_report == balance:
            report_df = get_balance_sheet(select_ticker, is_quarterly)
        elif select_report == cashflow:
            report_df = get_cashflow(select_ticker, is_quarterly)

        report_parameters = streamlit.multiselect('Выбор показателей отчета', report_df.columns)
        if report_parameters:
            report_bar = px.bar(report_df, x=report_df.index, y=report_parameters,
                                labels={'value': 'Значение', 'index': 'Компания', 'variable': 'Финансовые показатели'},
                                title='Сравнение показателей отчета о прибыли', barmode='group')
            streamlit.plotly_chart(report_bar)

        if is_quarterly:  # Просто для красивой надписи
            streamlit.subheader(select_report + ' по кварталам')
        else:
            streamlit.subheader(select_report + ' по годам')
        streamlit.write(report_df)
