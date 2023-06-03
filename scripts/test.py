import openai
import os
import sys
sys.path.append('Human.py')

from secrets import CHAT_GPT_KEY

DOC = """

"""

def chatGPT_extract_Methods():
    openai.api_key = CHAT_GPT_KEY 

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="Q:In this text passage which is a scientific methods description, give me bullet points for the study design, Method of Talcum Powder Exposure Measurement, Length of Follow-Up, and number of subjects studied" + DOC + " \nA:",
        temperature=0,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    response["choices"][0]["text"]


def chatGPT_extract_results():
    openai.api_key = CHAT_GPT_KEY 

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="Q:In this text passage which is a scientific results, first provide a short summary of the conclusion of the results, then provide bullet points for the Risk Ratios or odds ratio or similar important results, Statistical Significance:" + DOC + " \nA:",
        temperature=0,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    return response["choices"][0]["text"]


def chatGPT_test():
    openai.api_key = CHAT_GPT_KEY 

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="Q: what color is the sky \nA:",
        temperature=0,
        max_tokens=10,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    return response["choices"][0]["text"]

chatGPT_test()
#chatGPT_extract_results()
#chatGPT_extract_Methods()
