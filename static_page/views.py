from django.shortcuts import render
from django.http import HttpResponseNotFound
from django.template.loader import get_template
from django.template import Context
import django.utils.translation as translation
import static_page.models as static_page_models
import gallery.models as gallery_models
import banner.models as banner_models
import menu.models as menu_models
import localization.models as localization_models
from django.views.decorators.cache import cache_page
from static_page.forms import ContactUs
import info_storage.models as info_storage_models
from neutrino.settings import STATIC_PAGE_CACHE_TIME


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
        images = gallery_models.GalleryImagePosition.objects.\
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
        images = banner_models.BannerImagePosition.objects.\
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


@cache_page(STATIC_PAGE_CACHE_TIME)
def index_page(request):
    return static_page(request, 'index')


@cache_page(STATIC_PAGE_CACHE_TIME)
def static_page(request, name: str):
    try:
        page = static_page_models.StaticPage.objects.get(name=name)
    except Exception:
        return HttpResponseNotFound(get_template('system/404.html').render(Context({})))

    language_code = translation.get_language()
    texts = TextsContainer(static_page_models.Text.objects.order_by('weight').
                           filter(page=page, language__short_name=language_code).all().values_list('name', 'body',
                                                                                                   'weight'))
    seo_info = static_page_models.SeoInformation.objects.filter(page=page, language__short_name=language_code).first()
    galleries = GalleriesContainer(page.galleries.all())
    banners = BannersContainer(banner_models.Banner.objects.all())

    main_menu = menu_models.MainMenu.objects.all()
    additional_menu = menu_models.AdditionalMenu.objects.all()
    extra_menu = menu_models.ExtraMenu.objects.all()

    template = page.template.path

    info_storage = info_storage_models.Storage.objects.all().values_list('key', 'value')
    info_storage_dict = {}
    for key, value in info_storage:
        info_storage_dict[key] = value

    if request.POST:
        contact_from = ContactUs(request.POST)
        contact_from, status = contact_from.process()
    else:
        contact_from = ContactUs()

    return render(request, template, {
        'page': page,
        'languages': localization_models.Language.objects.all(),
        'language_code': language_code,
        'texts_container': texts.texts,
        'galleries_container': galleries.galleries,
        'banners_container': banners,
        'main_menu': main_menu,
        'additional_menu': additional_menu,
        'extra_menu': extra_menu,
        'contact_from': contact_from,
        'seo_info': seo_info,
        'info_storage': info_storage_dict
    })
