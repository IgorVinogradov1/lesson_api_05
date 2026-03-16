import os
import requests
from itertools import count
from dotenv import load_dotenv
from terminaltables import SingleTable


def get_vacancies_hh(prog_lang, region_hh):
    for page in count(0):
        headers = {'User-Agent': 'HH-User-Agent'}
        payload = {'text': f'программист {prog_lang}', 'area': region_hh, 'page': page}
        url_hh = 'https://api.hh.ru/vacancies'
        response = requests.get(url_hh, params=payload, headers=headers)
        response.raise_for_status()
        page_payload = response.json()
        if page == 0:
            yield {'found': page_payload['found']}
        yield from page_payload['items']
        if page >= page_payload['pages']:
            break

def get_vacancies_sj(prog_lang, region_sj, sj_token):
    for page in count(0):
        headers = {'X-Api-App-Id': sj_token}
        payload = {'catalogues': 48, 'keywords': prog_lang, 'town': region_sj, 'page': page, 'count': 100}
        url_sj = 'https://api.superjob.ru/2.0/vacancies'
        response = requests.get(url_sj, params=payload, headers=headers)
        response.raise_for_status()
        page_payload = response.json()
        if page == 0:
            yield {'found': page_payload['total']}
        yield from page_payload['objects']    
        if not page_payload['more']:
            break

def predict_rub_salary_hh(vacancy):
    try:
        if 'salary' not in vacancy or vacancy['salary'].get('currency') != 'RUR':
            return None
        elif vacancy['salary'].get('from') is None:
            return int(vacancy['salary'].get('to') * 0.8) 
        elif vacancy['salary'].get('to') is None:
            return int(vacancy['salary'].get('from') * 1.2)
        else:
            return int((vacancy['salary'].get('from') + vacancy['salary'].get('to')) / 2)
    except:
        return None

def predict_rub_salary_sj(vacancy):
    try:
        if (vacancy['payment_from'] == 0 and vacancy['payment_to'] == 0) or vacancy['currency'] != 'rub':
            return None
        elif vacancy['payment_from'] != 0 and vacancy['payment_to'] == 0:
            return int(vacancy['payment_from'] * 1.2)
        elif vacancy['payment_from'] == 0 and vacancy['payment_to'] != 0:
            return int(vacancy['payment_to'] * 0.8)
        else:
            return int((vacancy['payment_from'] + vacancy['payment_to']) / 2)  
    except:
        return None

def get_hh_vacancy_stats(prog_languages, region_hh):
    lang_stats = {}
    for prog_lang in prog_languages:
        vacancies = list(get_vacancies_hh(prog_lang, region_hh))
        vacancies_found = vacancies[0]['found']
        vacancies_for_processing = vacancies[1:]
        vacancies_processed = 0
        total_salary = 0
        average_salary = 0
        if vacancies_for_processing:
            for vacancy in vacancies_for_processing:
                medium_salary = predict_rub_salary_hh(vacancy)
                if medium_salary:
                    vacancies_processed += 1
                    total_salary += medium_salary
            average_salary = int(total_salary / vacancies_processed)
        lang_stats.update({
            prog_lang: {
                'vacancies_found': vacancies_found,
                'vacancies_processed': vacancies_processed,
                'average_salary': average_salary
                }
            })
    return lang_stats

def get_sj_vacancy_stats(prog_languages, region_sj, sj_token):
    lang_stats = {}
    for prog_lang in prog_languages:
        vacancies = list(get_vacancies_sj(prog_lang, region_sj, sj_token))
        vacancies_found = vacancies[0]['found']
        vacancies_for_processing = vacancies[1:]
        vacancies_processed = 0
        total_salary = 0
        average_salary = 0
        if vacancies_for_processing:
            for vacancy in vacancies_for_processing:
                medium_salary = predict_rub_salary_sj(vacancy)
                if medium_salary:
                    vacancies_processed += 1
                    total_salary += medium_salary
            average_salary = int(total_salary / vacancies_processed)
        lang_stats.update({
            prog_lang: {
                'vacancies_found': vacancies_found,
                'vacancies_processed': vacancies_processed,
                'average_salary': average_salary
                }
            })
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

