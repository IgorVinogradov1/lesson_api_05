import os
import requests
from itertools import count
from dotenv import load_dotenv
from terminaltables import SingleTable


def get_vacancies_hh(prog_lang, region_hh):
    vacancies_catalog = []
    headers = {'User-Agent': 'HH-User-Agent'}
    payload = {'text': f'программист {prog_lang}', 'area': region_hh}
    url_hh = 'https://api.hh.ru/vacancies'
    response = requests.get(url_hh, params=payload, headers=headers)
    response.raise_for_status()
    vacancies_found = response.json()['found']
    for page in count(0):
        payload = {'text': f'программист {prog_lang}', 'area': region_hh, 'page': page}
        response = requests.get(url_hh, params=payload, headers=headers)
        response.raise_for_status()
        page_payload = response.json()
        vacancies_catalog.extend(page_payload['items'])
        if page >= page_payload['pages']:
            break   
    return vacancies_found, vacancies_catalog

def get_vacancies_sj(prog_lang, region_sj, sj_token):
    vacancies_catalog = []
    headers = {'X-Api-App-Id': sj_token}
    payload = {'catalogues': 48, 'keywords': prog_lang, 'town': region_sj}
    url_sj = 'https://api.superjob.ru/2.0/vacancies'
    response = requests.get(url_sj, params=payload, headers=headers)
    response.raise_for_status()
    vacancies_found = response.json()['total']
    for page in count(0):
        payload = {'catalogues': 48, 'keywords': prog_lang, 'town': region_sj, 'page': page, 'count': 100}
        response = requests.get(url_sj, params=payload, headers=headers)
        response.raise_for_status()
        page_payload = response.json()
        vacancies_catalog.extend(page_payload['objects'])
        if not page_payload['more']:
            break   
    return vacancies_found, vacancies_catalog

def predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    if not salary:
        return None
    if salary.get('currency') != 'RUR':
        return None

    frm = salary.get('from')
    to = salary.get('to')

    if not frm:
        return int(to * 0.8)
    elif not to:
        return int(frm * 1.2)
    else:
        return int((frm + to) / 2)

def predict_rub_salary_sj(vacancy):
    frm = vacancy.get('payment_from')
    to = vacancy.get('payment_to')
    currency = vacancy.get('currency')

    if (not frm and not to) or currency != 'rub':
        return None
    elif frm and not to:
        return int(frm * 1.2)
    elif to and not frm:
        return int(to * 0.8)
    else:
        return int((frm + to) / 2)  

def get_hh_vacancy_stats(prog_languages, region_hh):
    lang_stats = {}
    for prog_lang in prog_languages:
        vacancies_found, vacancies_for_processing = get_vacancies_hh(prog_lang, region_hh)
        vacancies_processed = 0
        total_salary = 0
        average_salary = 0
        if vacancies_for_processing:
            for vacancy in vacancies_for_processing:
                medium_salary = predict_rub_salary_hh(vacancy)
                if medium_salary:
                    vacancies_processed += 1
                    total_salary += medium_salary
            if vacancies_processed > 0:
                average_salary = int(total_salary / vacancies_processed)
        lang_stats[prog_lang] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
    return lang_stats

def get_sj_vacancy_stats(prog_languages, region_sj, sj_token):
    lang_stats = {}
    for prog_lang in prog_languages:
        vacancies_found, vacancies_for_processing = get_vacancies_sj(prog_lang, region_sj, sj_token)
        vacancies_processed = 0
        total_salary = 0
        average_salary = 0
        if vacancies_for_processing:
            for vacancy in vacancies_for_processing:
                medium_salary = predict_rub_salary_sj(vacancy)
                if medium_salary:
                    vacancies_processed += 1
                    total_salary += medium_salary
            if vacancies_processed > 0:
                average_salary = int(total_salary / vacancies_processed)
        lang_stats[prog_lang] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
    return lang_stats   

def print_stats_table(lang_stats, title):
    table_data = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'],
        *[
            [prog_lang,
            stats['vacancies_found'],
            stats['vacancies_processed'],
            stats['average_salary']]
            for prog_lang, stats in lang_stats.items()
        ]
    ]

    table_instance = SingleTable(table_data, title)
    table_instance.justify_columns[2] = 'left'
    print(table_instance.table)
    print()

def main():
    load_dotenv()
    sj_token = os.environ['SJ_TOKEN']
    
    prog_languages = ['C#', 'Objective-C', 'Ruby', 'Java', 'Typescript', 'Scala', 'Go', 'Swift', 'C++', 'PHP', 'JavaScript', 'Python']
    
    region_hh = 1
    region_sj = 4
    title_hh = 'HeadHunter Moscow'
    title_sj = 'SuperJob Moscow'

    lang_stats = get_hh_vacancy_stats(prog_languages, region_hh)
    print_stats_table(lang_stats, title_hh)
    lang_stats = get_sj_vacancy_stats(prog_languages, region_sj, sj_token)
    print_stats_table(lang_stats, title_sj)

if __name__ == '__main__':
    main()