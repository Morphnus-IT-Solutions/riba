# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from categories.models import Category, CategoryGraph
from categories.forms import *


def view_all_categories(request):
    cat = Category.objects.all()
    q = request.GET.get('q')
    if q:
        cat =  cat.filter(name__icontains=q)
    cat_dict = {    
        'categories': cat,
        'q':q,
        }    
    return render_to_response('categories/view_all_categories.html', cat_dict, context_instance=RequestContext(request))


def add_category(request, id=None):
    form = CategoryForm()
    errors = []
    if request.method == "POST":
        if 'save' in request.POST:
            form = CategoryForm(request.POST, request.FILES)
            if form.is_valid():
                q = form.save()
                return HttpResponseRedirect('/categories/%s' %q.id)
            else:
                for er in form.errors:
                    errors.append(form.errors[er])
    ctxt = {
        'form': form,
        'errors': errors,
    }
    return render_to_response('categories/add_category.html', ctxt, context_instance=RequestContext(request))


def view_category(request, id):
    q = Category.objects.get(pk=id)
    ctxt = {
        'category': q,
    }
    return render_to_response('categories/category.html', ctxt, context_instance=RequestContext(request))


def edit_category(request, id):
    errors = []
    cat = Category.objects.get(pk=id)
    form = CategoryForm(instance=cat)
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=cat)
        if form.is_valid():
            cat = form.save()
            return HttpResponseRedirect('/categories/%s' %cat.id)
        else:
            for er in form.errors:
                errors.append(form.errors[er])
    ctxt = {
        'category': cat,
        'form': form,
        'errors': errors
    }
    return render_to_response('categories/edit_category.html', ctxt, context_instance=RequestContext(request))

def delete_category(request, id):
    try:
        category = Category.objects.get(id = id)
    except Category.DoesNotExist:
        raise Http404
    if request.method == "POST":
        del_confirm = request.POST.get('del_confirm', 'No')
        if del_confirm == "Yes":
            category.delete()
        return HttpResponseRedirect('/categories/view/')
        
    ctxt = {
        'category':category,
    }    
    return render_to_response('categories/category_delete_confirm.html', ctxt, context_instance=RequestContext(request))
