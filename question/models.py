from django.db import models

# Create your models here.

class Question(models.Model):
    parent = models.ForeignKey("self", null=True, blank=True, db_index=True, related_name="parent_question")
    parent_value = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    question = models.TextField()
    answer_type = models.CharField(max_length=15, db_index=True,
            		default='char', choices=(
                		('text', 'Text'),
                		('textarea', 'TextArea'),
                		('check', 'Check'),
						('radio', 'Radio'),
					    ('datetime', 'DateTime'),
					    ('dropdown', 'Dropdown'),
					    ('imagefield', 'ImageField'),
					    ))
    type = models.CharField(max_length=10,default='normal', db_index=True, choices=(
     ('normal','Normal'),
     ('dependent','Dependent'),
     ('recurring', 'Recurring'),
     ('dependent recurring', 'Dependent Recurring'),
     ))
    max_times = models.IntegerField(null=True, blank=True, default=1)

    def __unicode__(self):
        return self.question


class Option(models.Model):
    question = models.ForeignKey(Question)
    value = models.CharField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        return "%s - %s" % (question.question, value)

    #dependent_question = models.ForeignKey(Question, blank=True, null=True, related_name="dependent_question")

class Field(models.Model):
    question = models.ForeignKey(Question)
    field_label = models.CharField(max_length=100, blank=True, null=True)
    field_type = models.CharField(max_length=15, db_index=True,
            		default='char', choices=(
                		('text', 'Text'),
                		('textarea', 'TextArea'),
                		('check', 'Check'),
						('radio', 'Radio'),
					    ('datetime', 'DateTime'),
					    ('dropdown', 'Dropdown'),
					    ('imagefield', 'ImageField'),
					    ))

    def __unicode__(self):
        return "%s - %s" % (question.question, fieldname)


#class QuestionTree(models.Model):
#    question = models.ForeignKey(Question)
#    parent_question = models.ForeignKey(Question, null=True, blank=True, related_name="parent_question")
#    parent_value = models.CharField(max_length=200)

#    class Meta:
#        unique_together = (("question", "parent_question", "parent_value"),)

#    def __unicode__(self):
#        return "Q: %s, PQ: %s, PV: %s" % (question, parent_question, parent_value)
