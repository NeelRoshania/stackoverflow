from django.shortcuts import render, get_object_or_404
from django.views.generic import FormView, View, ListView
from django.views.generic.base import TemplateView, TemplateResponseMixin
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ImproperlyConfigured
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic.edit import FormMixin, ContextMixin
from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy
from django.http import JsonResponse
from .forms import UserToDoForm, UserNoteForm
from home.mixins import AjaxFormMixin_Home
from production.mixins import AjaxFormMixin_Production
from .models import UserToDo, UserNote
from urllib import parse

# Home view to redirect user
class BaseView(AjaxFormMixin_Home, AjaxFormMixin_Production, FormMixin, TemplateResponseMixin, View):
    success_url = reverse_lazy('home:index')
    template_name  = 'home/home.html'

    # get request for home page -> return context from AjaxFormMixin_Home by overiding parent class + define auto_id for generated fields
    def get(self, request, *args, **kwargs):
        self.form_class = UserToDoForm
        context = super(BaseView, self).get_context_data(**kwargs)
        context.update({
                    'userToDo_Form': UserToDoForm(auto_id='userToDoForm_%s'),
                    'userNote_Form': UserNoteForm(auto_id='userNoteForm_%s'),
                     })
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):   
        # Decide validation form class
        if (request.POST.get('ajaxStatus') == 'addUserNoteForm'):
            self.form_class = UserNoteForm
        else:
            self.form_class = UserToDoForm

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

# RefershUserToDoView -> TemplateView handles render_to_responce, which returns an HTTPResponse 
class RefershUserToDoView(AjaxFormMixin_Home, TemplateView):
    template_name = 'home/includes/objectList.html'

# DeleteUserToDoView does not need to return a template. As AJAX, it just needs to post data to the database and return a Jsonresponse
class DeleteModelView(View):

    # @method_decorator(ensure_csrf_cookie) -> Does not assist with AJAX requests
    def post(self, request, *args, **kwargs):
        self.deleteObject(request.POST.get('ajaxStatus'), self.kwargs['pk'])
        return JsonResponse('Object deleted succesfully.', safe=False)

    def deleteObject(self, ajaxStatus, pk):
        try:
            if (ajaxStatus=="deleteUserToDo"):
                _ = get_object_or_404(UserToDo, pk=pk)
                _.delete()

            elif (ajaxStatus=="deleteUserNote"):
                _ = get_object_or_404(UserNote, pk=pk)
                _.delete()

            else:
                raise ImproperlyConfigured("home:DeleteModelView -> No ajaxStatus reserved to delete object.")

        except ImproperlyConfigured as err:
            print(err.args)
            raise

# EditUserToDoView must generate a tempalte with a form to pass object information to
class EditUserToDoView(AjaxFormMixin_Home, FormMixin, TemplateResponseMixin, View):
    form_class = UserToDoForm
    success_url = reverse_lazy('home:index')
    template_name = 'home/includes/editObjectForm.html'

    # get data from database -> different from get_context_data as it does not return an HTTPResponse
    def get(self, request, *args, **kwargs):

        # Get author object and form instance and return from instance to view
        obj = get_object_or_404(UserToDo, pk=self.kwargs['pk'])
        form = UserToDoForm(instance=obj, auto_id='editUserToDo_%s')
        return self.render_to_response({'subForm': form})

    # Post data to database
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

# EditUserNoteView must generate a tempalte with a form to pass object information to
class EditUserNoteView(AjaxFormMixin_Home, FormMixin, TemplateResponseMixin, View):
    form_class = UserNoteForm
    success_url = reverse_lazy('home:index')
    template_name = 'home/includes/editUserNoteForm.html'

    # get data from database -> different from get_context_data as it does not return an HTTPResponse
    def get(self, request, *args, **kwargs):
        # Get author object and form instance and return from instance to view
        obj = get_object_or_404(UserNote, pk=self.kwargs['pk'])
        form = UserNoteForm(instance=obj, auto_id='editUserNote_%s')
        return self.render_to_response({'subForm': form})

    # Post data to database
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

# SearchObjectView must generate a tempalte to pass context objects to
class SearchUserToDoView(AjaxFormMixin_Home, TemplateView):
    template_name = 'home/includes/objectList.html'

