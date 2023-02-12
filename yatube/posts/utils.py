from django.core.paginator import Paginator

from .constants import NUMBER_POST_PER_PAGE


def get_page_of_list(request, list):
    '''
    Вычисляет возвращает фрагмент из из списка list, который должен быть
    выведен на html-странице с номером 'page' при использовании паджинатора.
    NUMBER_POST_PER_PAGE - количество элементов списка на одной странице.
    'page' передается в http запросе при обработке шаблона html.
    '''
    paginator = Paginator(list, NUMBER_POST_PER_PAGE)
    return paginator.get_page(request.GET.get('page'))
