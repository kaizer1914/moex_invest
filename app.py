import pandas
import plotly.express as px
import streamlit
from pandas import DataFrame

from moex_stock.moscow_exchange import MoscowExchange
from vtb.position_report import PositionReport
from yahoo.yahoo_finance import YahooFinance


@streamlit.cache
def get_position_report(file: str) -> PositionReport:
    return PositionReport(file)


@streamlit.cache
def get_shares_and_etf_stock_df() -> DataFrame:
    shares_and_etf_stock_df = MoscowExchange.get_shares_and_etf_df()
    return shares_and_etf_stock_df


@streamlit.cache
def get_bonds_stock_df() -> DataFrame:
    bonds_stock_df = MoscowExchange.get_bonds_df()
    return bonds_stock_df


@streamlit.cache
def get_tickers_df() -> DataFrame:
    tickers_df = MoscowExchange.get_tickers_for_yahoo()
    return tickers_df


@streamlit.cache
def get_info(ticker: str) -> DataFrame:
    df = YahooFinance(ticker).get_info()
    return df


@streamlit.cache
def get_earnings(ticker: str, is_quarterly: bool) -> DataFrame:
    return YahooFinance(ticker).get_financials(is_quarterly)


@streamlit.cache
def get_balance_sheet(ticker: str, is_quarterly: bool) -> DataFrame:
    return YahooFinance(ticker).get_balance_sheet(is_quarterly)


@streamlit.cache
def get_cashflow(ticker: str, is_quarterly: bool) -> DataFrame:
    return YahooFinance(ticker).get_cashflow(is_quarterly)


@streamlit.cache
def get_history_sec(ticker: str):
    return MoscowExchange.get_security_history(ticker)


# Анализ отчета по позициям
upload_file = streamlit.sidebar.file_uploader('Отчет по позициям (ВТБ)', 'csv')
if upload_file is not None:
    streamlit.title('Анализ отчета по позициям')
    position_report = get_position_report(upload_file)

    with streamlit.expander('По классу активов'):
        total_df = position_report.get_total_df()
        total_pie = px.pie(total_df, values='sum', names='assets', title='Активы',
                           labels={'assets': 'Активы', 'sum': 'Сумма'})
        streamlit.plotly_chart(total_pie)

    with streamlit.expander('Акции'):
        shares_df = position_report.get_shares_df()
        labels = {'ticker': 'Тикер', 'name': 'Компания', 'current_sum': 'Текущая сумма', 'change_sum': 'Прибыль'}

        shares_sum_pie = px.pie(shares_df, values='current_sum', names='name', hover_data=['ticker'], title='По долям',
                                labels=labels)
        shares_sum_bar = px.bar(shares_df, x='ticker', y='current_sum', color='change_sum', hover_data=['name'],
                                labels=labels, title='По сумме')
        shares_income_bar = px.bar(shares_df, x='ticker', y='change_sum', hover_data=['name', 'current_sum'],
                                   labels=labels, title='По доходности')

        streamlit.plotly_chart(shares_sum_pie)
        streamlit.plotly_chart(shares_sum_bar)
        streamlit.plotly_chart(shares_income_bar)
        streamlit.write(shares_df)

    with streamlit.expander('Фонды'):
        labels = {'ticker': 'Тикер', 'name': 'Наименование', 'current_sum': 'Текущая сумма', 'change_sum': 'Прибыль'}
        etf_df = position_report.get_etf_df()

        etf_sum_pie = px.pie(etf_df, values='current_sum', names='name', hover_data=['ticker'], title='По долям',
                             labels=labels)
        etf_sum_bar = px.bar(etf_df, x='ticker', y='current_sum', color='change_sum', hover_data=['name'],
                             labels=labels, title='По сумме')
        etf_income_bar = px.bar(etf_df, x='ticker', y='change_sum', hover_data=['name', 'current_sum'],
                                labels=labels, title='По доходности')

        streamlit.plotly_chart(etf_sum_pie)
        streamlit.plotly_chart(etf_sum_bar)
        streamlit.plotly_chart(etf_income_bar)
        streamlit.write(etf_df)

    with streamlit.expander('Облигации'):
        labels = {'current_sum': 'Текущая сумма', 'company': 'Компания', 'region': 'Регион', 'type': 'Тип',
                  'sec-type': 'Тип'}
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

        all_type_pie = px.pie(bonds_df, values='current_sum', names='sectype', labels=labels, title='По типу')
        corporate_pie = px.pie(bonds_corp_df, values='current_sum', names='company', labels=labels,
                               title='Корпоративные')
        region_pie = px.pie(bonds_region_df, values='current_sum', names='region', labels=labels, title='Муниципальные')
        ofz_pie = px.pie(bonds_ofz_df, values='current_sum', names='type', labels=labels, title='Государственные')

        streamlit.plotly_chart(all_type_pie)
        streamlit.plotly_chart(ofz_pie)
        streamlit.plotly_chart(region_pie)
        streamlit.plotly_chart(corporate_pie)
        streamlit.write(bonds_df)

# Yahoo Finance
streamlit.sidebar.header('Yahoo! finance', 'https://finance.yahoo.com/')
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
    info_parameters = streamlit.multiselect('Выбор текущих финансовых показателей', info_df.columns)
    if info_parameters:
        info_bar = px.bar(info_df, x=info_df.index, y=info_parameters, hover_data=['financialCurrency'],
                          labels={'value': 'Значение', 'index': 'Компания', 'variable': 'Финансовые показатели'},
                          title='Сравнение текущих финансовых показателей', barmode='group')
        streamlit.plotly_chart(info_bar)
    streamlit.subheader('Текущие показатели')
    streamlit.write(info_df)

    # Диаграммы и таблицы отчетов
    streamlit.header('Обзор компании')
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

        show_history = streamlit.checkbox('Показать исторический график')
        if show_history:
            history_df = get_history_sec(select_ticker)
            history_line = px.line(history_df, history_df['date'], history_df['medium_price'])
            streamlit.plotly_chart(history_line)
