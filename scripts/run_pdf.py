from datetime import datetime
import re
import fitz
import os
import requests
import openai


PDFS = [
    '11606_2022_Article_7414.pdf',
    'brjcancer00120-0090.pdf',
    'Cancer - 2000 - Chang - Perineal talc exposure and risk of ovarian carcinoma.pdf',
    'ede-27-334.pdf',
    'In re Johnson & Johnson Talcum Powder Prods. Mktg., Sales Practices & Prods. Litig.pdf',
    'Intl Journal of Cancer - 2004 - Mills - Perineal talc exposure and epithelial ovarian cancer risk in the Central Valley of.pdf',
]

PDF_FOLDER = os.path.dirname('/Users/liamgordon/Desktop/medthread_proj/research/')
doc_path = fitz.open(PDF_FOLDER + '/' + PDFS[0])

def extract_pdf_data(doc_path):
    with fitz.open(doc_path) as doc:  # open document
        doc_metadata = doc.metadata
        title = doc_metadata.get('title')
        author = doc_metadata.get('author')
        date_time_str = doc_metadata.get('creationDate')
        year = date_time_str[2:6]

        doc_metadata = {'title': title, 'author': author, 'year_published': year}
        pages = []
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)  # loads page number 'pno' of the document (0-based)
            page.get_text("text")
            pages.append(page.get_text("text"))

    pages = ' '.join(pages)
    return pages, doc_metadata


def match_text_chunks(doc_path):
    pages, _ = extract_pdf_data(doc_path)

    re_key_words_method = r'\n\s*((MATERIALS AND METHODS)|(MATERIALS AND METHODS)|(METHODS)|(Subjects and methods))\s*\n'
    re_key_words_results = r'\n\s*((CONCLUSIONS)|(RESULTS)|(Results)|(Conclusions and relevance))(\:)?\n\s*'
    re_section_break = r'\n(([A-Z]{5,10}){1,3})(\:)?\n'

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
    return result_sentences, method_sentences


def main():
    pages, doc_metadata = extract_pdf_data(doc_path)
    result_sentences, method_sentences = match_text_chunks(doc_path)

    print(result_sentences)

main()
