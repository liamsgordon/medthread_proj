from django.http import HttpResponse
from django.shortcuts import render
import mysql.connector

from .local_secrets import LOCAL_PW


# Create your views here.


def say_hello(request):
    return HttpResponse('Hello World')


def home_page(request):
    return render(request, 'home.html')


def dashboard(request):
    mydb = conn()
    cursor = mydb.cursor()
    cursor.execute('SELECT title, year_pub, ind_var, dep_var, conclusion, relevance, id FROM ResearchArticle;')
    dashboard = []
    for row in cursor:
        row = list(row)
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


def conn():
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password=LOCAL_PW,
        database="medthread"
    )

    return mydb