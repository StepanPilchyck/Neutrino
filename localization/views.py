from django.utils.translation import activate
from django.http import JsonResponse


def lang(request, lang_code: str):
    try:
        activate(lang)
        return JsonResponse({200: lang_code})
    except Exception:
        return JsonResponse({500: lang_code})


def currency(request, currency_code: str):
    request.session['currency'] = currency_code
