from django.db import models

# Create your models here.

class Question(models.Model):
    question = models.TextField()
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

    def __unicode__(self):
        return self.question

    def get_url(self):
        return '/question/%s' % self.id

    def get_children(self,question,children):
        graph = QuestionTree.objects.filter(parent_question=question)
        if not graph:
            return children
        for node in graph:
            if node.question and not node.question in children:
                children.append(node.question)
            #if not children.get(node.parent_question):
            #    children[node.parent_question] = {node.parent_value: node.question}
            #else:
            #    if not children[node.parent_question].get(node.parent_value):
            #        children[node.parent_question][node.parent_value] = node.question
            if node.question:
                self.get_children(node.question,children)
        return children

    def get_all_children(self):
        ques = self
        children = []
        children = self.get_children(ques,children)
        return children

    def get_parents(self, question, parents):
        graph = QuestionTree.objects.filter(question=question).exclude(parent_question=None, parent_value=None)
        if not graph:
            return parents
        
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
        parents = []
        parents = self.get_parents(ques, parents)
        return parents

    def is_leaf_question(self):
        return not(QuestionTree.objects.filter(parent_question=self).exists())

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
            par_question = QuestionTree.objects.filter(question = par_q,)
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
        return "%s - %s" % (self.question, self.field_label)


class QuestionTree(models.Model):
    parent_question = models.ForeignKey(Question, null=True, blank=True, related_name="parent_question")
    parent_value = models.CharField(max_length=200, null=True, blank=True)
    question = models.ForeignKey(Question, null=True, blank=True)
    lft = models.IntegerField(null=True, blank=True)
    rgt = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = (("question", "parent_question", "parent_value"),)

    def __unicode__(self):
        return "Q: %s, PQ: %s, PV: %s" % (self.question, self.parent_question, self.parent_value)


    # Every root question is separate tree
    # lft will start with id * 10000
    # a small hack, with an assumption that there wont be more than 5000 sub-question
    def rebuild_tree(self):
        right = self.id * 10000
        self.rebuild_node(self, right)
        

    def rebuild_node(self, parent, left):
        # the right value of this node is left + 1
        right = left + 1
        
        # get all children of this node
        #if parent.question:
        #print parent
        if parent.question:
            qt = QuestionTree.objects.filter(parent_question = parent.question)
            #print "tree :::: %s" % qt
            for q in qt:
                #if q.question:
                right = self.rebuild_node(q, right)

        # we have got the left value and since we have processed all children nodes, 
        # we also know the right value
        #print "parent :::: %s left :::: %s right ::: %s" % (parent, left, right)
        parent.rgt = right
        parent.lft = left
        parent.save()
        
        return right + 1
