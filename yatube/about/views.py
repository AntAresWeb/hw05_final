from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    '''Отображает страницу информации об авторе'''
    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    '''Отображает страницу информации об используемых технологиях'''
    template_name = 'about/tech.html'
