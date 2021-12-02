import pandas
import plotly.express as px
import streamlit
from pandas import DataFrame

from moex_stock.shares import SharesMarket
from vtb.position_report import PositionReport

upload_file = streamlit.sidebar.file_uploader('Выберите csv-файл отчет по позициям от брокера ВТБ', 'csv')


@streamlit.cache
def get_position_report(file: str) -> PositionReport:
    return PositionReport(file)


@streamlit.cache
def get_tickers() -> list:
    df = SharesMarket.update_stock_data()
    df = df[df['sectype'].isin(['usual', 'pref', 'dr'])]
    tickers = df['longname'].values
    return tickers


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

select_company = streamlit.sidebar.selectbox('Тикер', get_tickers())
