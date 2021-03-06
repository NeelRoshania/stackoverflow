from django.http import JsonResponse
from home.models import UserToDo, UserNote
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ImproperlyConfigured
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic.base import TemplateResponseMixin, ContextMixin
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from .forms import UserToDoForm, UserNoteForm

class AjaxFormMixin_Home(ContextMixin, object):

    # Update the object if form is in-valid
    def form_invalid(self, form):
        response = super(AjaxFormMixin_Home, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response

    # Update the object if form is valid
    def form_valid(self, form):
        response = super(AjaxFormMixin_Home, self).form_valid(form)=
        return self.handleAjax(
            self.request,
            form,
            response,
            )

    # This method was writted to override that of UserToDoFormView method -> context data is not being passed to form
    def get_context_data(self, **kwargs):
        context = super(AjaxFormMixin_Home, self).get_context_data(**kwargs)
        userToDoPage = self.request.GET.get('userToDoPage') # Get page from ajax request
        obj = UserToDo

        # If an ajax, general search request has been executed
        if self.request.is_ajax() and self.request.GET.get('searchObjectSubmit'):
            # Define the appropriate Model for the querySet
            obj = UserNote if (self.request.GET.get('ajaxStatus') == 'searchUserNote') else UserToDo
            querySet = self.handleAjax(self.request, model=obj)

            # Define multiple form instances to be returned to the view
            formInstances = {
                'userToDo_Form': UserToDoForm(auto_id='userToDoForm_%s'),
                'userNote_Form': UserNoteForm(auto_id='userNoteForm_%s'),
            }
            return self.processPaginatorContext(Paginator(querySet, 5), formInstances, userToDoPage, context)
        else:
            formInstances = {
            'userToDo_Form': UserToDoForm(auto_id='userToDoForm_%s'),
            'userNote_Form': UserNoteForm(auto_id='userNoteForm_%s'),
            }
            return self.processPaginatorContext(Paginator(self.getQuerySet(obj), 5), formInstances, userToDoPage, context)

    def getQuerySet(self, model, pk=None):
        # If the QuerySet requires a pk
        if pk:
            return get_object_or_404(model, pk=self.kwargs['pk'])
        else:
            return model.objects.order_by('-id')

    def processPaginatorContext(self, paginatorObject, formInstances, page, context):
        try:
            paginatedObjects = paginatorObject.page(page)
            contextData = {**formInstances, 'paginatedObjects':paginatedObjects}
            context.update(contextData)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            paginatedObjects = paginatorObject.page(1)
            contextData = {**formInstances, 'paginatedObjects':paginatedObjects}
            context.update(contextData)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            paginatedObjects = paginatorObject.page(paginatorObject.num_pages)
            contextData = {**formInstances, 'paginatedObjects':paginatedObjects}
            context.update(contextData)
        return context

    # Method to detect status of form validation for custom Models
    def handleAjax(self, requestObj, form=None, response=None, model=None):
        try:

            if requestObj.is_ajax():
                if requestObj.method == 'POST':
                    if (requestObj.POST.get('ajaxStatus') == "addUserToDoForm"):
                        obj = UserToDo(
                            subject=form.cleaned_data['subject'], 
                            toDoProgress=form.cleaned_data['toDoProgress'],
                            )
                        obj.save()
                        return JsonResponse({'message': "Object modified successfully.",})

                    if (requestObj.POST.get('ajaxStatus') == "addUserNoteForm"):
                        obj = UserNote(
                            taskNote=form.cleaned_data['taskNote'], 
                            noteProgress=form.cleaned_data['noteProgress'],
                        )                   
                        obj.save()
                        obj.UserToDo.add(UserToDo.objects.get(id=requestObj.POST.get('userToDo')))
                        return response

                    if (requestObj.POST.get('ajaxStatus') == "editObjectForm"):
                        # Get object and modify
                        obj = self.getQuerySet(UserToDo, pk=self.kwargs['pk'])
                        obj.subject = form.cleaned_data['subject']
                        obj.toDoProgress = form.cleaned_data['toDoProgress']
                        obj.save()
                        return response

                    if (requestObj.POST.get('ajaxStatus') == "editUserNoteForm"):
                        obj = self.getQuerySet(UserNote, pk=self.kwargs['pk'])
                        obj.noteProgress = form.cleaned_data['noteProgress']
                        obj.taskNote = form.cleaned_data['taskNote']
                        obj.save()
                        return response
                else:

                    if (requestObj.GET.get('ajaxStatus') == "searchUserToDo"):
                        print("AjaxFormMixin_Home:handleAjax called -> request to search User To Do")
                        searchText = self.request.GET.get('searchObjectFieldText')
                        if self.request.GET.get('radio') == "subject":
                            return model.objects.filter(subject__contains=searchText)
                        elif self.request.GET.get('radio') == "todoprogress":
                            return model.objects.filter(toDoProgress__contains=searchText)
                        else:
                            return model.objects.filter(name__contains=searchText)

                    # Since UserNote can be in many UserToDo's, perform query to return relevant UserToDo objects
                    if (requestObj.GET.get('ajaxStatus') == "searchUserNote"):
                        print("AjaxFormMixin_Home:handleAjax called -> request to search User Note")
                        searchText = self.request.GET.get('searchObjectFieldText')
                        if self.request.GET.get('radio') == "tasknote":
                            return UserToDo.objects.filter(usernote__in=UserNote.objects.filter(taskNote__contains=searchText)).distinct()
                        elif self.request.GET.get('radio') == "noteprogress":
                            return UserToDo.objects.filter(usernote__in=UserNote.objects.filter(noteProgress__contains=searchText)).distinct()
                        else:
                            return model.objects.filter(name__contains=searchText)
            else:
                print("AjaxFormMixin_Home:handleAjax called -> Neither ajax nor form submit...")
                return response

        except ImproperlyConfigured:
            print("ajaxStatus not properly configured.")


