This Project is for the MedThread Interview Process

# Talcum-Cancer Analysis Web App

This web application is designed to process and analyze research papers related to the effects of talcum on cancer. The primary purpose of the app is to assess the relevance and usefulness of each paper in understanding the given hypothesis, based on a range of factors.

The application performs the following key functions:

1. Processes PDFs of research papers
2. Analyzes the content of the papers
3. Determines the relevance of the paper to the hypothesis
4. Summarizes the paper from methods and results section


## Built With

- [Django](https://www.djangoproject.com/) - The web framework used
- [MySQL](https://www.mysql.com/) - Database
- [Bootstrap](https://getbootstrap.com/) - Front-end component library
- [ChatGPT](https://openai.com/research/chatgpt) - AI model by OpenAI
- Various Python Libraries for scraping and understanding scientific articles

Our hope is that this application will help facilitate a deeper understanding of the connection between talcum usage and cancer.



## Pages


#### Main Page

![Alt text](https://raw.githubusercontent.com/liamsgordon/medthread_proj/main/imgs/Screenshot%202023-06-05%20at%203.40.58%20AM.png)

#### Dashboard

![Alt text](https://raw.githubusercontent.com/liamsgordon/medthread_proj/main/imgs/Screenshot%202023-06-05%20at%203.42.32%20AM.png)

#### Article Summary

![Alt text](https://raw.githubusercontent.com/liamsgordon/medthread_proj/main/imgs/Screenshot%202023-06-05%20at%203.42.04%20AM.png)

## Documentation

The submit button on the main page triggers a process where the pdf is processed by the function `process_pdf()`, which is the main function in this project. It takes a path to a PDF file as input and returns a dictionary containing the extracted metadata, methods, and results.

The first step in the `process_pdf()` function is to extract the metadata from the PDF file. This is done using the `extract_pdf_data()` function. The `extract_pdf_data()` function returns a tuple containing a list of pages and a dictionary of metadata.

The next step is to extract the methods and results from the PDF file. This is done using the `match_text_chunks()` function. The `match_text_chunks()` function splits the text of the PDF file into chunks and then matches each chunk against a list of keywords. The keywords are used to identify the methods and results sections of the PDF file.

The `chatGPT_extract_methods()` and `chatGPT_extract_results()` functions are used to extract the methods and results from the text chunks. These functions use the OpenAI ChatGPT API to generate text that summarizes the methods and results sections of the PDF file.

The `ast.literal_eval()` function is used to convert the text generated by the ChatGPT API into dictionaries.

The `adjusted_methods` and `adjusted_results` dictionaries are created by adjusting the extracted methods and results dictionaries. The `adjusted_methods` dictionary is adjusted by removing any keys that are not relevant to the meta-analysis. The `adjusted_results` dictionary is adjusted by converting the Risk Ratio p value and Odds Ratio p value keys to floats.

The `results dictionary` is created by combining the `doc_metadata`, `adjusted_methods`, and `adjusted_results` dictionaries.

The `meta_analysis_relevance()` function is used to determine the relevance of the results. This function returns True if the results are relevant for a meta-analysis and False otherwise.

The relevance key is added to the results dictionary. Then the resultsobject is converted into a row of text inserted into this SQL table


~~~~
CREATE TABLE ResearchArticle (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year_pub INT NOT NULL,
    study_design TEXT NOT NULL,
    method_of_talcum_powder_exposure_measurement TEXT NOT NULL,
    length_of_follow_up TEXT NOT NULL,
    dep_var TEXT NOT NULL,
    ind_var TEXT NOT NULL,
    number_of_subjects_studied TEXT NOT NULL,
    conclusion TEXT NOT NULL,
    risk_ratio_value FLOAT NOT NULL,
    odds_ratio_value FLOAT NOT NULL,
    risk_ratio_p FLOAT NOT NULL,
    odds_ratio_p FLOAT NOT NULL,
    relevance BOOLEAN NOT NULL
);
~~~~

This SQL data is grabbed by the `dashboard/` and `paper-summary/<int:id>/`



