from django.db import models
from categories.models import Category

# Create your models here.

class Question(models.Model):
    question = models.TextField()
    category = models.ForeignKey(Category)
    description = models.TextField(blank=True, null=True)
    answer_type = models.CharField(max_length=15, db_index=True,
            		default='char', choices=(
                		('text', 'Text'),
                		('textarea', 'TextArea'),
                		('checkbox', 'Checkbox'),
						('radio', 'Radio Button'),
					    ('date', 'Date'),
					    ('dropdown', 'Dropdown'),
					    ('attachment', 'Attachment'),
					    ))
    type = models.CharField(max_length=10,default='normal', db_index=True, choices=(
     ('recurring', 'Recurring'),
     ), null=True, blank=True)
    #max_times = models.IntegerField(null=True, blank=True, default=1)
    rows = models.IntegerField(null=True, blank=True, default=5)
    columns = models.IntegerField(null=True, blank=True, default=40)
    level = models.IntegerField(default=1)

    def __unicode__(self):
        return self.question

    def get_url(self):
        return '/question/%s' % self.id

    def get_all_children(self):
        ques = self
        par_q = QuestionTree.objects.filter(parent_question=ques)
        children = []
        for q in par_q:
            qt = QuestionTree.objects.filter(lft__gte=q.lft, rgt__lte=q.rgt).order_by('lft')
            for chq in qt:
                children.append(chq)
        return children


    def get_all_parents(self):
        parents = []
        par_question = QuestionTree.objects.get(question=self)
        while(par_question and par_question.parent_question):
            par_q = par_question.parent_question
            par_val = par_question.parent_value
            parents.append(par_question)
            par_question = QuestionTree.objects.get(question = par_q)
        parents.reverse()
        return parents

    def is_root_question(self):
        return QuestionTree.objects.filter(question=self, parent_question=None, parent_value=None).exists()
    
    def is_leaf_question(self):
        return not(QuestionTree.objects.filter(parent_question=self).exists())

    def get_root_question(self):
        try:
            qt = QuestionTree.objects.get(question=self)
        except QuestionTree.DoesNotExist:
            raise Http404
        except QuestionTree.MultipleObjectsReturned:
            qt = QuestionTree.objects.filter(question=self)
            qt = qt[0]
        root_lft = qt.lft - (qt.lft % 1000)
        qt = QuestionTree.objects.get(lft=root_lft)
        return qt

    def get_question_hierarchy(self):
        question_hierarchy = []
        # check if question has parent questions
        # avoid question with parent_question and parent_value as None
        # such questions are root question
        par_question = QuestionTree.objects.filter(parent_question = self)
        #if not self.is_leaf_question():
        #    question_hierarchy.append((parent_question))
        
        while(par_question and par_question[0].parent_question):
            par_q = par_question[0].parent_question
            par_val = par_question[0].parent_value
            question_hierarchy.append(par_question[0])
            par_question = QuestionTree.objects.filter(question = par_q)
        question_hierarchy.reverse()
        return question_hierarchy
                
    def get_question_status(self):
        response = {}
        response['is_leaf_question'] = not(QuestionTree.objects.filter(parent_question=self).exists())
        respons['is_child_question'] = False
        response['question_tree'] = None
        question_tree = QuestionTree.objects.select_related('parent_question').filter(question=self).exclude(parent_question=None)
        if question_tree:
            response['is_child_question'] = True
            response['question_tree'] = question_tree
        return response


    def rebuild_nsm(self):
        try:
            qt = QuestionTree.objects.get(question = self)
        except:
            raise Http404
        qt.rebuild_tree()


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
        return self.field_label


class QuestionTree(models.Model):
    parent_question = models.ForeignKey(Question, null=True, blank=True, related_name="parent_question")
    parent_value = models.CharField(max_length=200, null=True, blank=True)
    question = models.ForeignKey(Question, null=True, blank=True)
    lft = models.IntegerField(null=True, blank=True)
    rgt = models.IntegerField(null=True, blank=True)
    level = models.IntegerField(default=1)

    class Meta:
        unique_together = (("question", "parent_question", "parent_value"),)

    def __unicode__(self):
        return "Q: %s, PQ: %s, PV: %s" % (self.question, self.parent_question, self.parent_value)


    # Every root question is separate tree
    # lft will start with id * 10000
    # a small hack, with an assumption that there wont be more than 5000 sub-question
    def rebuild_tree(self):
        right = self.id * 10000
        self.rebuild_node(self, right, 0)
        

    def rebuild_node(self, parent, left, level):
        # the right value of this node is left + 1
        right = left + 1
        level += 1 
        # get all children of this node
        #if parent.question:
        if parent.question:
            qt = QuestionTree.objects.filter(parent_question = parent.question)
            for q in qt:
                right = self.rebuild_node(q, right, level)

        # we have got the left value and since we have processed all children nodes, 
        # we also know the right value
        #print "parent :::: %s left :::: %s right ::: %s" % (parent, left, right)
        parent.rgt = right
        parent.lft = left
        parent.level = level
        if parent.question:
            parent.question.level = level
            parent.question.save()
        parent.save()
        
        return right + 1
