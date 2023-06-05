from django.http import HttpResponse
from django.shortcuts import redirect, render
import ast
import re
import fitz
import openai
import mysql.connector
from pathlib import Path

from .local_secrets import LOCAL_PW, CHAT_GPT_KEY

RESEARCH_DIR = str(Path(__file__).resolve().parent) + '/research/'


def say_hello(request):
    """
    This function returns a simple "Hello World" message.
    """
    return HttpResponse('Hello World')


def home_page(request):
    """
    This function renders the home page.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: A response object containing the rendered home page.
    """
    if request.method == 'POST' and request.FILES.get('myfile'):
        """
        This code block checks if the request method is POST and if the request contains a file named `myfile`.
        If both of these conditions are met, the file is processed using the `process_pdf()` function.
        """
        pdf = request.FILES['myfile']
        results = process_pdf(RESEARCH_DIR + str(pdf))
        insert_id = insert_results(results)
        return redirect('paper-summary/' + str(insert_id) + '/')

    return render(request, 'home.html')


def dashboard(request):
    """
    This function renders the dashboard.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: A response object containing the rendered dashboard.
    """
    mydb = conn()
    cursor = mydb.cursor()
    cursor.execute('SELECT title, year_pub, ind_var, dep_var, conclusion, relevance, id FROM ResearchArticle;')
    dashboard = []
    for row in cursor:
        row = list(row)
        # turns boolean integer into High vs Low
        if row[5] == 1:
            row[5] = 'High'
        else:
            row[5] = 'Low'
        dashboard.append(row)
    mydb.commit()
    mydb.close()

    return render(request, 'dashboard.html',
        {'dashboard': dashboard}
    )


def paper_summary(request, id):
    """
    This function renders the paper summary page.

    Args:
        request (HttpRequest): The request object.
        id (int): The ID of the paper to be summarized.

    Returns:
        HttpResponse: A response object containing the rendered paper summary page.
    """
    mydb = conn()
    cursor = mydb.cursor()
    cursor.execute('SELECT * FROM ResearchArticle WHERE id = {};'.format(id))
    result = cursor.fetchone()
    html_objects = {
        'title': result[1],
        'author': result[2],
        'year_pub': result[3],
        'study_design': result[4],
        'method_of_talcum_powder_exposure_measurement': result[5],
        'length_of_follow_up': result[6],
        'dep_var': result[7],
        'ind_var': result[8],
        'number_of_subjects_studied': result[9],
        'conclusion': result[10],
        'risk_ratio_value': result[11],
        'odds_ratio_value': result[12],
        'risk_ratio_p': result[13],
        'odds_ratio_p': result[14],
        'relevance': result[15],
    }

    mydb.commit()
    mydb.close()

    return render(request, 'view_paper.html', html_objects)


####################
# HELPER FUNCTIONS #
####################


def extract_pdf_data(doc_path):
    """
    This function extracts metadata and text from a PDF file.

    Args:
        doc_path (str): The path to the PDF file.

    Returns:
        metadata (dict): A dictionary containing the metadata of the PDF file.
        text (str): The text of the PDF file.
    """
    with fitz.open(doc_path) as doc:  # open document
        doc_metadata = doc.metadata
        title = doc_metadata.get('title')
        author = doc_metadata.get('author')
        date_time_str = doc_metadata.get('creationDate')
        year = date_time_str[2:6]
        # metadata has been grabbed, is not always reliable

        doc_metadata = {'title': title, 'author': author, 'year_pub': year}

        text_block = []
        for page in doc:
            text = page.get_text("blocks")
            for block in text:
               text_block.append(block[4])

    text_block = ' '.join(text_block)
    return text_block, doc_metadata


def match_text_chunks(pages):
    """
    This function matches text chunks in a string.

    Args:
        text (str): The string to search.

    Returns:
        method_sentences (list): A list of sentences that contain the keyword "Methods".
        result_sentences (list): A list of sentences that contain the keyword "Results".
    """
    # these regexs tell us when to start and stop different sentences
    re_key_words_method = r'\n\s*((MATERIALS AND METHODS)|(MATERIALS AND METHODS)|(METHODS)|(Subjects and methods))\s*\n'
    re_key_words_results = r'\n\s*((CONCLUSIONS)|(RESULTS)|(Results)|(Conclusions and relevance))(\:)?\n\s*'
    re_section_break = r'\n\s*(([A-Z]{5,10}){1,3})|(References)|(Discussion)|(Methods)|(Results)(\:)?\s*\n'

    method_sentences = []
    result_sentences = []
    method_stop, result_stop = True, True

    # we have sentences we want to loop through so we can group paragraphs on a sentence level
    sentences = pages.split('.')
    for sentence in sentences:
        re_method = re.search(re_key_words_method, sentence)
        # these three if statements stop the adding to our method sentences once we see the results or
        # heaven forbid the discussion sections. We add sentences otherwise.
        if method_stop is False and re.search(re_section_break, sentence):
            method_stop = True
        # this just makes sure we dont skip a methods section if there is a mini one in the abstract
        if method_stop is True and re_method:
            method_stop = False
        if method_stop is False:
            method_sentences.append(sentence)

        re_result = re.search(re_key_words_results, sentence)

        # this code does the same thing except for the results section
        if result_stop is False and re.search(re_section_break, sentence):
            result_stop = True
        if result_stop is True and re_result:
            result_stop = False
        if result_stop is False:
            result_sentences.append(sentence)

    # because of tables, the results sections can be too big so basically if we
    # have a sentence which is more than 4 lines then we assume its a table and we remove the sentence
    new_result_sentences = []
    for sentence in result_sentences:
        num_lines = len(sentence.split('\n'))
        if num_lines < 4:
            new_result_sentences.append(sentence)

    result_sentences = ' '.join(new_result_sentences)
    method_sentences = ' '.join(method_sentences)


    return result_sentences, method_sentences


def chatGPT_extract_methods(methods_text):
    """
    This function extracts methods from a text string using OpenAI's ChatGPT API.

    Args:
        methods_text (str): The text to extract methods from.

    Returns:
        methods (dict): A dictionary containing the methods extracted from the text.
    """
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
    """
    This function extracts results from a text string using OpenAI's ChatGPT API.

    Args:
        results_text (str): The text to extract results from.

    Returns:
        results (dict): A dictionary containing the results extracted from the text.
    """
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
    """
    This function tests if a given independent variable (IV) and dependent variable (DV) are relevant for a meta-analysis.

    Args:
        ind_var (str): The independent variable.
        dep_var (str): The dependent variable.

    Returns:
        bool: True if the IV and DV are relevant, False otherwise.
    """
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
    """
    This function establishes a connection to the MySQL database `medthread`.

    Returns:
        mydb (mysql.connector.connection): A connection to the MySQL database `medthread`.
    """
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password=LOCAL_PW,
        database="medthread"
    )
    return mydb


def insert_results(results):
    """
    This function inserts a set of results into the MySQL database `medthread`.

    Args:
        results (dict): A dictionary containing the results to be inserted.

    Returns:
        insert_id (int): The ID of the row that was inserted.
    """
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
    """
    This function determines if a given set of results is relevant for a meta-analysis.

    Args:
        results_dict (dict): A dictionary containing the results of a study.

    Returns:
        bool: True if the results are relevant, False otherwise.
    """
    # if we cannot find any statistical conclusions, this paper is not relevant
    if not results_dict['risk_ratio_value'] and not results_dict['odds_ratio_value']:
        return False
    # also if the p values show insignificance
    elif (results_dict['risk_ratio_p'] and not results_dict['odds_ratio_p'] and results_dict['risk_ratio_p'] > 0.05):
        return False
    elif (not results_dict['risk_ratio_p'] and results_dict['odds_ratio_p'] and results_dict['odds_ratio_p'] > 0.05):
        return False
    # if we cannot find the ind. var and dep. var
    elif not results_dict['ind_var'] or not results_dict['dep_var']:
        return False
    # test if these are the IVs and DVs we are looking for
    return chatGPT_test_IV_DV(results_dict['ind_var'], results_dict['dep_var'])


def process_pdf(doc_path):
    """
    This function processes a PDF file and returns a dictionary containing the extracted metadata, methods, and results.

    Args:
        doc_path (str): The path to the PDF file.

    Returns:
        results (dict): A dictionary containing the extracted metadata, methods, and results.
    """
    # Extract the metadata from the PDF file.
    pages, doc_metadata = extract_pdf_data(doc_path)
    result_sentences, method_sentences = match_text_chunks(pages)

    # Extract the methods and results from the PDF file
    method_related_extracts = chatGPT_extract_methods(method_sentences)
    result_related_extracts = chatGPT_extract_results(result_sentences)

    # Convert the extracted methods and results to dictionaries.
    method_result = ast.literal_eval(method_related_extracts)
    result_result = ast.literal_eval(result_related_extracts)

    # Adjust the extracted methods dictionary.
    adjusted_methods = {
        'study_design': method_result['Study Design'],
        'method_of_talcum_powder_exposure_measurement': method_result['Method of Talcum Powder Exposure Measurement'],
        'length_of_follow_up': method_result['Length of Follow-Up'],
        'dep_var': method_result['Dependant Variable'],
        'ind_var': method_result['Independant Variable'],
        'number_of_subjects_studied': method_result['Number of Subjects Studied'],
    }

    # Adjust the extracted results dictionary.
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

    # Combine the metadata, methods, and results into a single dictionary.
    results = doc_metadata | adjusted_methods | adjusted_results
    # Determine the relevance of the results.
    relevance = meta_analysis_relevance(results)
    results['relevance'] = relevance

    return results