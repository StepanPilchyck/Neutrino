from django.shortcuts import render
from django.http import HttpResponseNotFound
from django.template.loader import get_template
from django.template import Context
import django.utils.translation as translation
import catalogue.models as catalogue_models
import localization.models as localization_models
import catalogue.settings as catalogue_settings
import gallery.models as gallery_models
import banner.models as banner_models
import menu.models as menu_models
from django.views.decorators.cache import cache_page
from static_page.forms import ContactUs
import info_storage.models as info_storage_models
from neutrino.settings import CATALOGUE_CATEGORY_CACHE_TIME, CATALOGUE_ITEM_CACHE_TIME


class ItemContainer:
    def __init__(self, url: str, name: str, code: str, short_text: str, price: float, image: catalogue_models.ItemImagePosition):
        self.__url = url
        self.__name = name
        self.__code = code
        self.__short_text = short_text
        self.__image = image
        self.__price = price

    @property
    def url(self) -> str:
        return self.__url

    @property
    def name(self) -> str:
        return self.__name

    @property
    def code(self) -> str:
        return self.__code

    @property
    def short_text(self) -> str:
        return self.__short_text

    @property
    def image(self) -> str:
        return self.__image

    @property
    def price(self) -> float:
        return self.__price


class ItemsContainer:
    def __init__(self, items: [catalogue_models.Item], currency: localization_models.Currency):
        self.__items = []
        for item in items:
            self.append(item.url, item.name, item.code, item.short_text, item.price(currency), item.image)

    def append(self, url: str, name: str, code: str, short_text: str, price: float, image: catalogue_models.ItemImagePosition):
        self.__items.append(ItemContainer(url, name, code, short_text, price, image))

    @property
    def items(self):
        return self.__items


class TextContainer:
    def __init__(self, name: str, body: str, weight: int) -> None:
        self.__name = name
        self.__body = body
        self.__weight = weight

    @property
    def name(self) -> str:
        return self.__name

    @property
    def body(self) -> str:
        return self.__body

    @property
    def weight(self) -> str:
        return self.__weight


class TextsContainer:
    def __init__(self, items: [(str, str, int)]) -> None:
        self.__items = {}
        for name, body, weight in items:
            self.append(TextContainer(name, body, weight))

    def append(self, item: TextContainer) -> None:
        self.__items[item.name] = item

    @property
    def texts(self) -> {str: (str, str, int)}:
        return self.__items


class GalleryImageContainer:
    def __init__(self, image: gallery_models.GalleryImagePosition) -> None:
        self.__name = image.name
        self.__description = image.description
        self.__small_image = image.small_image
        self.__medium_image = image.medium_image
        self.__large_image = image.large_image
        self.__original_image = image.original_image
        self.__weight = image.weight

    @property
    def name(self) -> str:
        return self.__name

    @property
    def description(self) -> str:
        return self.__description

    @property
    def small_image(self) -> str:
        return self.__small_image

    @property
    def medium_image(self) -> str:
        return self.__medium_image

    @property
    def large_image(self) -> str:
        return self.__large_image

    @property
    def original_image(self) -> str:
        return self.__original_image

    @property
    def weight(self) -> int:
        return self.__weight


class GalleryContainer:
    def __init__(self, gallery: gallery_models.Gallery) -> None:
        self.__first_image = gallery.first_image
        self.__second_image = gallery.second_image
        images = gallery_models.GalleryImagePosition.objects. \
            filter(gallery=gallery, active=True).order_by('weight').all()
        self.__items = []
        for image in images:
            self.append(image)

    @property
    def first_image(self) -> str:
        return self.__first_image

    @property
    def second_image(self) -> str:
        return self.__second_image

    def append(self, image: gallery_models.GalleryImagePosition) -> None:
        self.__items.append(GalleryImageContainer(image))

    @property
    def images(self) -> {str: GalleryImageContainer}:
        return self.__items


class GalleriesContainer:
    def __init__(self, galleries: [gallery_models.Gallery]) -> None:
        self.__items = {}
        for item in galleries:
            self.append(item)

    def append(self, item: gallery_models.Gallery) -> None:
        self.__items[item.marker] = GalleryContainer(item)

    @property
    def galleries(self) -> {str: gallery_models.Gallery}:
        return self.__items


class BannerImageContainer:
    def __init__(self, image: banner_models.BannerImagePosition) -> None:
        self.__name = image.name
        self.__description = image.description
        self.__small_image = image.small_image
        self.__medium_image = image.medium_image
        self.__large_image = image.large_image
        self.__original_image = image.original_image
        self.__weight = image.weight

    @property
    def name(self) -> str:
        return self.__name

    @property
    def description(self) -> str:
        return self.__description

    @property
    def small_image(self) -> str:
        return self.__small_image

    @property
    def medium_image(self) -> str:
        return self.__medium_image

    @property
    def large_image(self) -> str:
        return self.__large_image

    @property
    def original_image(self) -> str:
        return self.__original_image

    @property
    def weight(self) -> int:
        return self.__weight


class BannerContainer:
    def __init__(self, banner: banner_models.Banner) -> None:
        images = banner_models.BannerImagePosition.objects. \
            filter(banner=banner, active=True).order_by('weight').all()
        self.__items = []
        for image in images:
            self.append(image)

    def append(self, image: banner_models.BannerImagePosition) -> None:
        self.__items.append(BannerImageContainer(image))

    @property
    def images(self) -> {str: BannerImageContainer}:
        return self.__items


class BannersContainer:
    def __init__(self, banners: [banner_models.Banner]) -> None:
        self.__items = {}
        for item in banners:
            self.append(item)

    def append(self, item: banner_models.Banner) -> None:
        self.__items[item.marker] = BannerContainer(item)

    @property
    def banners(self) -> {str: banner_models.Banner}:
        return self.__items


def get_currency(request):
    currency = None
    if 'currency' not in request.session:
        try:
            request.session['currency'] = localization_models.Currency.objects.get(default=True).short_name
        except Exception:
            request.session['currency'] = 'None'

    if request.session['currency'] != 'None':
        try:
            currency = localization_models.Currency.objects.get(short_name=request.session['currency'])
        except Exception:
            request.session['currency'] = 'None'
    return currency


@cache_page(CATALOGUE_CATEGORY_CACHE_TIME)
def catalogue_category(request, category: str, page: str = 1):
    try:
        category = catalogue_models.Category.objects.get(url=category)
    except Exception:
        return HttpResponseNotFound(get_template('system/404.html').render(Context({})))

    language_code = translation.get_language()
    texts = TextsContainer(catalogue_models.CategoryText.objects.order_by('weight').
                           filter(category=category, language__short_name=language_code).all().values_list('name',
                                                                                                           'body',
                                                                                                           'weight'))
    seo_info = catalogue_models.CategorySeoInformation.objects.filter(category=category,
                                                                      language__short_name=language_code).first()
    galleries = GalleriesContainer(category.galleries.all())
    banners = BannersContainer(banner_models.Banner.objects.all())

    if page is None:
        page = 1
    currency = get_currency(request)
    try:
        items = ItemsContainer(catalogue_models.Item.objects.filter(category=category, active=True)
                               [(int(page) - 1): (int(page) * catalogue_settings.PRODUCT_ON_PAGE)],
                               currency).items
        max_page = round(catalogue_models.Item.objects.filter(category=category,
                                                              active=True).count() / catalogue_settings.PRODUCT_ON_PAGE)
    except Exception:
        return HttpResponseNotFound(get_template('system/404.html').render(Context({})))

    main_menu = menu_models.MainMenu.objects.all()
    additional_menu = menu_models.AdditionalMenu.objects.all()
    extra_menu = menu_models.ExtraMenu.objects.all()

    template = category.template.path

    info_storage = info_storage_models.Storage.objects.all().values_list('key', 'value')
    info_storage_dict = {}
    for key, value in info_storage:
        info_storage_dict[key] = value

    return render(request, template, {
        'category': category,
        'languages': localization_models.Language.objects.all(),
        'language_code': language_code,
        'texts_container': texts.texts,
        'galleries_container': galleries.galleries,
        'banners_container': banners,
        'main_menu': main_menu,
        'additional_menu': additional_menu,
        'extra_menu': extra_menu,
        'seo_info': seo_info,
        'items': items,
        'max_page': max_page,
        'current_page': page,
        'currency': currency,
        'info_storage': info_storage_dict
    })


@cache_page(CATALOGUE_ITEM_CACHE_TIME)
def catalogue_item(request, category: str, item: str):
    try:
        item = catalogue_models.Item.objects.get(url=item, category__url=category)
    except Exception:
        return HttpResponseNotFound(get_template('system/404.html').render(Context({})))

    language_code = translation.get_language()
    texts = TextsContainer(catalogue_models.ItemText.objects.order_by('weight').
                           filter(item=item, language__short_name=language_code).all().values_list('name', 'body',
                                                                                                   'weight'))

    parameters = catalogue_models.ItemParameter.objects.filter(item=item).all()
    seo_info = catalogue_models.ItemSeoInformation.objects.filter(item=item,
                                                                  language__short_name=language_code).first()
    banners = BannersContainer(banner_models.Banner.objects.all())

    images = catalogue_models.ItemImagePosition.objects.filter(item=item).all()

    currency = get_currency(request)

    main_menu = menu_models.MainMenu.objects.all()
    additional_menu = menu_models.AdditionalMenu.objects.all()
    extra_menu = menu_models.ExtraMenu.objects.all()

    template = item.template.path

    price = item.price(currency)

    info_storage = info_storage_models.Storage.objects.all().values_list('key', 'value')
    info_storage_dict = {}
    for key, value in info_storage:
        info_storage_dict[key] = value

    return render(request, template, {
        'item': item,
        'language_code': language_code,
        'texts_container': texts.texts,
        'banners_container': banners,
        'main_menu': main_menu,
        'additional_menu': additional_menu,
        'extra_menu': extra_menu,
        'seo_info': seo_info,
        'parameters': parameters,
        'short_text': item.short_text,
        'images': images,
        'currency': currency,
        'price': price,
        'info_storage': info_storage_dict
    })
