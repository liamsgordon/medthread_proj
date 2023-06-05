import ast
import re
import fitz
import os
import openai
import mysql.connector
from bs4 import BeautifulSoup
import requests

from secrets import CHAT_GPT_KEY


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
    abstract_sentences = []
    method_stop, result_stop, count_sentences = True, True, 0

    sentences = pages.split('.')
    for sentence in sentences:
        if count_sentences < 25:
            abstract_sentences.append(sentence)
        count_sentences += 1
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

    new_result_sentences = []
    for sentence in result_sentences:
        num_lines = len(sentence.split('\n'))
        if num_lines < 4:
            new_result_sentences.append(sentence)

    result_sentences = ' '.join(new_result_sentences)
    method_sentences = ' '.join(method_sentences)
    abstract_sentences = ' '.join(abstract_sentences)


    return result_sentences, method_sentences, abstract_sentences


def chatGPT_extract_abstract(abstract_text):
    openai.api_key = CHAT_GPT_KEY

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="""Q:In this text passage which is a scientific methods description,
         return a python dictionary for the author, title, year published,
         Dependant variable, Independant Variable
         """ + abstract_text + " \nA:",
        temperature=0,
        max_tokens=750,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    return response["choices"][0]["text"]


def conn():
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password='liam1521',
        database="medthread"
    )

    return mydb


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
         the results, the Risk Ratio (as a float), Risk Ratio p value, Odds Ratio (as a float), and odds Ratio p value
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
        password=LOCAL_PW,
        database="medthread"
    )
    return mydb


def insert_results(results):
    mydb = conn()
    cursor = mydb.cursor()

    sql = """
    INSERT INTO ResearchArticle (title, author, year_pub, study_design,
        method_of_talcum_powder_exposure_measurement, length_of_follow_up,
        dep_var, ind_var, number_of_subjects_studied, conclusion,
        risk_ratio_value, odds_ratio_value, risk_ratio_p,
        odds_ratio_p, relevance) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cursor.execute(sql, list(results.values()))
    insert_id = cursor.lastrowid
    mydb.commit()
    cursor.close()
    mydb.close()

    return insert_id


def meta_analysis_relevance(results_dict):
    if not results_dict['risk_ratio_value'] and not results_dict['odds_ratio_value']:
        return False
    elif not results_dict['risk_ratio_p'] and not results_dict['odds_ratio_p']:
        return False
    elif (results_dict['risk_ratio_p'] and not results_dict['odds_ratio_p'] and results_dict['risk_ratio_p'] > 0.05):
        return False
    elif (not results_dict['risk_ratio_p'] and results_dict['odds_ratio_p'] and results_dict['odds_ratio_p'] > 0.05):
        return False
    elif not results_dict['ind_var'] or not results_dict['dep_var']:
        return False
    return chatGPT_test_IV_DV(results_dict['ind_var'], results_dict['dep_var'])


def process_pdf(doc_path):
    pages, _ = extract_pdf_data(doc_path)
    result_sentences, method_sentences, abstract_sentences = match_text_chunks(pages)


    abstract_related_extracts = chatGPT_extract_abstract(abstract_sentences)
    method_related_extracts = chatGPT_extract_methods(method_sentences)
    result_related_extracts = chatGPT_extract_results(result_sentences)

    method_result = ast.literal_eval(method_related_extracts)
    result_result = ast.literal_eval(result_related_extracts)
    abstract_result = ast.literal_eval(abstract_related_extracts)

    adjusted_abstract = {
        'author': abstract_result['Author'],
        'title': abstract_result['Title'],
        'year_pub': abstract_result['Year Published'],
        'dep_var': abstract_result['Dependant Variable'],
        'ind_var': abstract_result['Independant Variable'],
    }

    adjusted_methods = {
        'study_design': method_result['Study Design'],
        'method_of_talcum_powder_exposure_measurement': method_result['Method of Talcum Powder Exposure Measurement'],
        'length_of_follow_up': method_result['Length of Follow-Up'],
        'dep_var': method_result['Dependant Variable'],
        'ind_var': method_result['Independant Variable'],
        'number_of_subjects_studied': method_result['Number of Subjects Studied'],
    }

    if isinstance(result_result['Risk Ratio p value'], str):
        rr_pvalue = float(re.sub("[^\d\.]", "", result_result['Risk Ratio p value']))
    elif isinstance(result_result['Risk Ratio p value'], float):
        rr_pvalue = result_result['Risk Ratio p value']
    else:
        rr_pvalue = None

    if isinstance(result_result['Odds Ratio p value'], str):
        or_pvalue = float(re.sub("[^\d\.]", "", result_result['Odds Ratio p value']))
    elif isinstance(result_result['Odds Ratio p value'], float):
        or_pvalue = result_result['Odds Ratio p value']
    else:
        or_pvalue = None

    adjusted_results = {
        'conclusion': result_result['Conclusion'],
        'risk_ratio_value': float(result_result['Risk Ratio']),
        'odds_ratio_value': float(result_result['Odds Ratio']),
        'risk_ratio_p': rr_pvalue,
        'odds_ratio_p': or_pvalue,
    }

    results = adjusted_abstract | adjusted_methods | adjusted_results
    relevance = meta_analysis_relevance(results)
    results['relevance'] = relevance

    return results


def main():
    doc_path = PDF_FOLDER + '/' + TEST_PDFS[2]
    results = process_pdf(doc_path)

    print(results)

    #insert_results(results)

    #extract_html_from_url(TEST_URLS[5])

main()
