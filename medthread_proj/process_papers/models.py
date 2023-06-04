from django.db import models

# Create your models here.
class ResearchArticle(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    year_published = models.IntegerField()
    study_design = models.CharField(max_length=200)
    method_of_talcum_powder_exposure_measurement = models.CharField(max_length=200)
    length_of_follow_up = models.CharField(max_length=200)
    dependent_variable = models.CharField(max_length=200)
    independent_variable = models.CharField(max_length=200)
    number_of_subjects_studied = models.IntegerField()
    conclusion = models.TextField()
    risk_ratio_value = models.FloatField()
    odds_ratio_value = models.FloatField()
    risk_ratio_p = models.FloatField()
    odds_ratio_p = models.FloatField()
    relevance = models.BooleanField()

    def __str__(self):
        return self.title