import ast
import re
import fitz
import os
import openai
import mysql.connector
from bs4 import BeautifulSoup
import requests


from secrets import CHAT_GPT_KEY


TEST_URLS = [
'https://acsjournals.onlinelibrary.wiley.com/doi/10.1002/(SICI)1097-0142(19970615)79:12%3C2396::AID-CNCR15%3E3.0.CO;2-M',
'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2247100/pdf/brjcancer00120-0090.pdf',
'https://onlinelibrary.wiley.com/doi/full/10.1002/ijc.20434',
'https://acsjournals.onlinelibrary.wiley.com/doi/10.1002/%28SICI%291097-0142%2819970615%2979%3A12%3C2396%3A%3AAID-CNCR15%3E3.0.CO%3B2-M',
'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4820665/',
'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9360263/',
'https://pubmed.ncbi.nlm.nih.gov/31910280/',
]


TEST_PDFS = [
    '11606_2022_Article_7414.pdf',
    'brjcancer00120-0090.pdf',
    'Cancer - 2000 - Chang - Perineal talc exposure and risk of ovarian carcinoma.pdf',
    'ede-27-334.pdf',
    'Intl Journal of Cancer - 2004 - Mills - Perineal talc exposure and epithelial ovarian cancer risk in the Central Valley of.pdf',
]


PDF_FOLDER = os.path.dirname('/Users/liamgordon/Desktop/medthread_proj/medthread_proj/process_papers/research/')


def extract_pdf_data(doc_path):
    with fitz.open(doc_path) as doc:  # open document
        doc_metadata = doc.metadata
        title = doc_metadata.get('title')
        author = doc_metadata.get('author')
        date_time_str = doc_metadata.get('creationDate')
        year = date_time_str[2:6]

        doc_metadata = {'title': title, 'author': author, 'year_pub': year}

        text_block = []
        for page in doc:
            text = page.get_text("blocks")
            for block in text:
               text_block.append(block[4])

    text_block = ' '.join(text_block)
    return text_block, doc_metadata


def match_text_chunks(pages):
    re_key_words_method = r'\n\s*((MATERIALS AND METHODS)|(MATERIALS AND METHODS)|(METHODS)|(Subjects and methods))\s*\n'
    re_key_words_results = r'\n\s*((CONCLUSIONS)|(RESULTS)|(Results)|(Conclusions and relevance))(\:)?\n\s*'
    re_section_break = r'\n\s*(([A-Z]{5,10}){1,3})|(References)|(Discussion)|(Methods)|(Results)(\:)?\s*\n'

    method_sentences = []
    result_sentences = []
    method_stop, result_stop = True, True

    sentences = pages.split('.')
    for sentence in sentences:
        re_method = re.search(re_key_words_method, sentence)
        if method_stop is False and re.search(re_section_break, sentence):
            method_stop = True
        if method_stop is True and re_method:
            method_stop = False
        if method_stop is False:
            method_sentences.append(sentence)

        re_result = re.search(re_key_words_results, sentence)

        if result_stop is False and re.search(re_section_break, sentence):
            result_stop = True
        if result_stop is True and re_result:
            result_stop = False
        if result_stop is False:
            result_sentences.append(sentence)

    result_sentences = ' '.join(result_sentences)
    method_sentences = ' '.join(method_sentences)
    print(method_sentences)
    print()
    print()
    print()
    print(result_sentences)
    return result_sentences, method_sentences


def chatGPT_extract_methods(methods_text):
    openai.api_key = CHAT_GPT_KEY

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="""Q:In this text passage which is a scientific methods description,
         return a python dictionary for the study design, Method of Talcum Powder Exposure Measurement,
         Length of Follow-Up, Dependant variable, Independant Variable and number of subjects studied
         """ + methods_text + " \nA:",
        temperature=0,
        max_tokens=250,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    return response["choices"][0]["text"]


def chatGPT_extract_results(results_text):
    openai.api_key = CHAT_GPT_KEY

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="""
        Q:In this text passage which is a scientific results, return a python dictionary with a short summary of the conclusion of
         the results, the Risk Ratio, Risk Ratio p value, odds ratio, and odds ratio p value
        """ + results_text + " \nA:",
        temperature=0,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    return response["choices"][0]["text"]


def chatGPT_test_IV_DV(ind_var, dep_var):
    openai.api_key = CHAT_GPT_KEY

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="Q: return either yes or no if this Independant variable " + ind_var + " and this " + dep_var + " roughly investigates the impact of talcum powder on cancer risk? \nA:",
        temperature=0,
        max_tokens=10,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    bool_text = response["choices"][0]["text"].strip()
    if bool_text in ('Yes', 'yes'):
        return True
    return False


def conn():
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password='liam1521',
        database="medthread"
    )

    return mydb


def insert_results(results):
    mydb = conn()
    cursor = mydb.cursor()

    relevance = meta_analysis_relavance(results)
    results['relavance'] = relevance

    sql = """
    INSERT INTO ResearchArticle (title, author, year_pub, study_design,
        method_of_talcum_powder_exposure_measurement, length_of_follow_up,
        dep_var, ind_var, number_of_subjects_studied, conclusion,
        risk_ratio_value, odds_ratio_value, risk_ratio_p,
        odds_ratio_p, relevance) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cursor.execute(sql, list(results.values()))
    mydb.commit()
    mydb.close()


def meta_analysis_relavance(results_dict):
    if not results_dict['risk_ratio_value'] and not results_dict['odds_ratio_value']:
        return False
    elif results_dict['risk_ratio_p'] > 0.05 and results_dict['odds_ratio_p'] > 0.05:
        return False
    elif not results_dict['ind_var'] or not results_dict['dep_var']:
        return False
    return chatGPT_test_IV_DV(results_dict['ind_var'], results_dict['dep_var'])


def process_pdf(doc_path):
    pages, doc_metadata = extract_pdf_data(doc_path)
    result_sentences, method_sentences = match_text_chunks(pages)

    method_related_extracts = chatGPT_extract_methods(method_sentences)
    result_related_extracts = chatGPT_extract_results(result_sentences)

    method_result = ast.literal_eval(method_related_extracts)
    result_result = ast.literal_eval(result_related_extracts)

    adjusted_methods = {
        'study_design': method_result['Study Design'],
        'method_of_talcum_powder_exposure_measurement': method_result['Method of Talcum Powder Exposure Measurement'],
        'length_of_follow_up': method_result['Length of Follow-Up'],
        'dep_var': method_result['Dependant Variable'],
        'ind_var': method_result['Independant Variable'],
        'number_of_subjects_studied': method_result['Number of Subjects Studied'],
    }

    adjusted_results = {
        'conclusion': result_result['Conclusion'],
        'risk_ratio_value': float(result_result['Risk Ratio']),
        'odds_ratio_value': float(result_result['Odds Ratio']),
        'risk_ratio_p': float(result_result['Risk Ratiop p value']),
        'odds_ratio_p': float(result_result['Odds Ratio p value']),
    }

    results = doc_metadata | adjusted_methods | adjusted_results

    return results


def extract_html_from_url(url):
    req = requests.get(url, 'html.parser', headers={
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36'})
    if req.status_code == 200:
        # Get the content of the response
        page_content = req.content

        # Create a BeautifulSoup object and specify the parser
        soup = BeautifulSoup(page_content, 'html.parser')
        # Find the section element with role='document'

        text = soup.findAll(text=True)
        text_block = ' '.join(text)

        print(text_block)
    else:
        print("Failed to retrieve the URL")


def main():
    doc_path = PDF_FOLDER + '/' + TEST_PDFS[0]
    results = process_pdf(doc_path)

    print(results)

    #insert_results(results)

    #extract_html_from_url(TEST_URLS[5])






main()
