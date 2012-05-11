from django.db import models

# Create your models here.

class Question(models.Model):
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

    def get_children(self,question,children):
        graph = QuestionTree.objects.filter(parent_question=question)
        if not graph:
            return children
        for node in graph:
            if not children.get(node.parent_question):
                children[node.parent_question] = {node.parent_value: node.question}
            else:
                if not children[node.parent_question].get(node.parent_value):
                    children[node.parent_question][node.parent_value] = node.question
            if node.question:
                self.get_children(node.question,children)
        return children

    def get_all_children(self):
        ques = self
        children = {}
        children = self.get_children(ques,children)
        return children

    def get_parents(self, question, parents):
        graph = QuestionTree.objects.filter(parent_question=question)
        if not graph:
            return children
        for node in graph:
            if not children.get(node.parent_question):
                children[node.parent_question] = {node.parent_value: node.question}
            else:
                if not children[node.parent_question].get(node.parent_value):
                    children[node.parent_question][node.parent_value] = node.question
            if node.question:
                self.get_children(node.question,children)
        return children

    def get_all_parents(self):
        ques = self
        parents = {}
        parents = self.get_parents(ques, parents)
        return parents
        

    def get_question_hierarchy(self):
        question_hierarchy = []
        par_question = QuestionTree.objects.filter(question = self)
        while(par_question and par_question[0].parent_question):
            par_q = par_question[0].parent_question
            par_val = par_question[0].parent_value
            question_hierarchy.append((par_q, par_val))
            par_question = QuestionTree.objects.filter(question = par_q)
        question_hierarchy.reverse()
        return question_hierarchy
                
    def get_question_status(self):
        response = {}
        response['is_leaf_question'] = not(QuestionTree.objects.filter(parent_question=self).exists())
        response['is_child_question'] = False
        response['question_tree'] = None
        question_tree = QuestionTree.objects.select_related('parent_question').filter(question=self).exclude(parent_question=None)
        if question_tree:
            response['is_child_question'] = True
            response['question_tree'] = question_tree
        return response


class Option(models.Model):
    question = models.ForeignKey(Question)
    option_value = models.CharField(max_length=100, blank=True, null=True)
    dependent_question = models.ForeignKey(Question, blank=True, null=True, related_name="dependent_question")

    def __unicode__(self):
        return "%s - %s" % (self.question, self.option_value)

    

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
    field_option = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return "%s - %s" % (self.question, self.field_label)


class QuestionTree(models.Model):
    parent_question = models.ForeignKey(Question, null=True, blank=True, related_name="parent_question")
    parent_value = models.CharField(max_length=200, null=True, blank=True)
    question = models.ForeignKey(Question, null=True, blank=True)


    class Meta:
        unique_together = (("question", "parent_question", "parent_value"),)

    def __unicode__(self):
        return "Q: %s, PQ: %s, PV: %s" % (self.question, self.parent_question, self.parent_value)
