from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, UpdateView, CreateView, DetailView, DeleteView, FormView
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from .models import Post, Response
from .forms import PostForm, RespondForm, ResponsesFilterForm


from django.core.mail import send_mail


class Index(ListView):
    model = Post
    template_name = 'index.html'
    context_object_name = 'posts'


class PostItem(DetailView):
    model = Post
    template_name = 'post_item.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if Response.objects.filter(author_id=self.request.user.id).filter(post_id=self.kwargs.get('pk')):
            context['respond'] = "Откликнулся"
        elif self.request.user == Post.objects.get(pk=self.kwargs.get('pk')).author:
            context['respond'] = "Мое_объявление"
        context['responsesPost'] = Response.objects.filter(post_id=self.kwargs.get('pk'))
        return context


class CreatePost(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'create_post.html'
    form_class = PostForm

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.has_perm('board.add_post'):
            return HttpResponseRedirect(reverse('account_profile'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = User.objects.get(id=self.request.user.id)
        post.save()
        return redirect(f'/post/{post.id}')


class EditPost(PermissionRequiredMixin, UpdateView):
    permission_required = 'board.change_post'
    template_name = 'create_post.html'
    form_class = PostForm
    success_url = '/create/'

    def dispatch(self, request, *args, **kwargs):
        author = Post.objects.get(pk=self.kwargs.get('pk')).author.username
        if self.request.user.username == 'admin' or self.request.user.username == author:
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Редактировать объявление может только его автор")

    def get_object(self, **kwargs):
        id = self.kwargs.get('pk')
        return Post.objects.get(pk=id)

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect('/post/' + str(self.kwargs.get('pk')))


class DeletePost(PermissionRequiredMixin, DeleteView):
    permission_required = 'board.delete_post'
    template_name = 'delete_post.html'
    queryset = Post.objects.all()
    success_url = '/index'

    def dispatch(self, request, *args, **kwargs):
        author = Post.objects.get(pk=self.kwargs.get('pk')).author.username
        if self.request.user.username == 'admin' or self.request.user.username == author:
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponse("Удалить объявление может только его автор")


title = str("")


class Responses(LoginRequiredMixin, ListView):
    model = Response
    template_name = 'responses.html'
    context_object_name = 'responses'

    def get_context_data(self, **kwargs):
        context = super(Responses, self).get_context_data(**kwargs)
        global title

        if self.kwargs.get('pk') and Post.objects.filter(id=self.kwargs.get('pk')).exists():
            title = str(Post.objects.get(id=self.kwargs.get('pk')).title)
            print(title)
        context['form'] = ResponsesFilterForm(self.request.user, initial={'title': title})
        context['title'] = title
        if title:
            post_id = Post.objects.get(title=title)
            context['filter_responses'] = list(Response.objects.filter(post_id=post_id).order_by('-dateCreation'))
            context['response_post_id'] = post_id.id
        else:
            context['filter_responses'] = list(Response.objects.filter(post_id__author_id=self.request.user).order_by('-dateCreation'))
        context['myresponses'] = list(Response.objects.filter(author_id=self.request.user).order_by('-dateCreation'))
        return context

    def post(self, request, *args, **kwargs):
        global title
        title = self.request.POST.get('title')

        if self.kwargs.get('pk'):
            return HttpResponseRedirect('/responses')
        return self.get(request, *args, **kwargs)


@login_required
def response_accept(request, **kwargs):
    if request.user.is_authenticated:
        response = Response.objects.get(id=kwargs.get('pk'))
        response.status = True
        response.save()

        respond = Response.objects.get(id=response.id)
        print(respond.post.author.email)
        send_mail(
            subject=f'Forum MMORPG: Ваш отклик принят!',
            message=f'Привет, {respond.author}, Автор объявления {respond.post.title} принял Ваш отклик!\n'
                    f'Посмотреть принятые отклики:\nhttp://127.0.0.1:8000/responses',
            from_email='petrovskill23@yandex.ru',
            recipient_list=[respond.author.email, ],
        )
        return HttpResponseRedirect('/responses')
    else:
        return HttpResponseRedirect('/accounts/login')


@login_required
def response_delete(request, **kwargs):
    if request.user.is_authenticated:
        response = Response.objects.get(id=kwargs.get('pk'))
        response.delete()
        return HttpResponseRedirect('/responses')
    else:
        return HttpResponseRedirect('/accounts/login')


class Respond(LoginRequiredMixin, CreateView):
    model = Response
    template_name = 'respond.html'
    form_class = RespondForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        respond = form.save(commit=False)
        respond.author = User.objects.get(id=self.request.user.id)
        respond.post = Post.objects.get(id=self.kwargs.get('pk'))
        respond.save()

        respond = Response.objects.get(id=respond.id)
        send_mail(
            subject=f'MMORPG: новый отклик на объявление!',
            message=f'Доброго дня, {respond.post.author}, ! На ваше объявление есть новый отклик!\n' 
                    f'Прочитать отклик:\n http://127.0.0.1:8000/responses/{respond.post.id}',
            from_email='petrovskill23@yandex.ru',
            recipient_list=[respond.post.author.email, ],
        )
        return HttpResponseRedirect('/responses')
