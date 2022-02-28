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


def get_shares_df() -> DataFrame:
    only_shares_df = get_shares_and_etf_stock_df()
    only_shares_df = only_shares_df[only_shares_df['sectype'].isin(['usual', 'pref', 'dr'])]
    return only_shares_df


# Анализ отчета по позициям
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
select_companies = streamlit.sidebar.multiselect('Выбрать компании', get_shares_df()['ticker'])
if select_companies:
    compare_df = None
    for ticker in select_companies:
        yf_data = YahooFinance(ticker)
        info_df = yf_data.get_info()

        # finance_df = yf_data.get_financials()
        # balance_df = yf_data.get_balance_sheet()
        # cashflow_df = yf_data.get_cashflow()
        #
        # streamlit.write(finance_df)
        # streamlit.write(balance_df)
        # streamlit.write(cashflow_df)

        if compare_df is None:
            compare_df = info_df
        else:
            compare_df = pandas.concat([compare_df, info_df])
    streamlit.write(compare_df)

    select_parameters = streamlit.multiselect('Сравнение финансовых показателей', compare_df.columns)
    if select_parameters:
        parameters_bar = px.bar(compare_df, x=compare_df.index, y=select_parameters, hover_data=['financialCurrency'],
                                labels={'value': 'Значение', 'index': 'Компания', 'variable': 'Финансовые показатели'},
                                title='Сравнение финансовых показателей', barmode='group')
        streamlit.plotly_chart(parameters_bar)
