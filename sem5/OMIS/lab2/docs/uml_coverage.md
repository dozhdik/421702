# Инвентаризация базовой UML-модели (этап 0)

Исходные русские подписи ниже оставлены для сверки с PDF. Реальные программные классы, поля и методы переименованы на английский; полная карта с файлами — в [uml_name_mapping.md](uml_name_mapping.md). Состав базовых диаграмм A/E и связи не сокращались. Регистрация использует `User`, `UserAccount`, `ContentAuthor`, `Reader`; пять новых статей проходят `PublicationController`, `PublicationRecord`, `SearchIndex`.

Дополнение 2026-11-11: `Article.deleted_at` и `Article.deleted_by` реализуют мягкое удаление. Это дополнительные поля существующего класса `Article`; обязательные UML-атрибуты, методы и связи сохранены. `deleted_by` ссылается на `User.user_id`, а общий репозиторий статей выполняет мягкое удаление.

Источник: [исходный отчёт](reference/ОМИС%20Лаба%201%20Отчёт.pdf), страницы 4–6 (A.1–A.7), 11–13 (E.1–E.5). Имена и типы ниже взяты с диаграмм; `String` отображается в `str`, `Long`/`Integer` в `int`, `Double` в `float`, `Boolean` в `bool`, `List` в типизированный список. Сущности, повторённые на разных диаграммах, реализуются одним классом. Диаграммы F исключены.

Обозначение `[x]` означает реализацию в указанных файлах. Машинная проверка публичных полей и методов находится в `tests/test_uml_coverage.py`; поведение и сохранение проверяются сценарными тестами. Дополнительные поля и методы обслуживают связи, не заменяя UML-элементы.

## E.1: модель и репозитории, стр. 11

| Статус | Класс | Все UML-поля (тип) | Все UML-методы | Реализация / проверка |
| --- | --- | --- | --- | --- |
| [x] | `Пользователь` | `идПользователя:String`, `фио:String`, `пароль:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `УчетнаяЗапись` | `идАккаунта:String`, `логин:String`, `пароль:String`, `статусАктивности:Boolean` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `Роль` | `идРоли:String`, `названиеРоли:String`, `описание:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `ПравоДоступа` | `идПрава:String`, `кодОперации:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `АвторКонтента` | `идАвтора:String`, `фио:String`, `отдел:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `Редактор` | `идРедактора:String`, `фио:String`, `секция:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `Читатель` | `идЧитателя:String`, `фио:String`, `должность:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `АдминистраторПлатформы` | `идАдминистратора:String`, `фио:String`, `уровеньДоступа:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `Статья` | `идСтатьи:String`, `заголовок:String`, `содержание:String`, `статусПубликации:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `Рубрика` | `идРубрики:String`, `название:String`, `описание:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `Тег` | `идТега:String`, `ключевоеСлово:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `Медиавложение` | `идМедиафайла:String`, `urlФайла:String`, `типКонтента:String`, `размер:Long` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `ПараметрыОформления` | `идПараметров:String`, `шрифт:String`, `наличиеПревью:Boolean` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `ОчередьМодерации` | `идЗаявки:String`, `приоритет:Integer` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `ЗамечаниеРедактора` | `идЗамечания:String`, `текстЗамечания:String`, `критичность:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `ПротоколПубликации` | `идПротокола:String`, `результат:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `Комментарий` | `идКомментария:String`, `текст:String`, `статус:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `Жалоба` | `идЖалобы:String`, `причина:String`, `статус:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `Реакция` | `идРеакции:String`, `типРеакции:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `ПоисковыйИндекс` | `идИндекса:String`, `лексемы:String` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `ОтчетАктивности` | `идОтчета:String`, `период:String`, `метрикаОхвата:Double` | — | `omis_blog/domain.py`, `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `IРепозиторий` | — | `получитьПоИд(ид:String):Object`, `сохранить(объект:Object):void`, `удалить(ид:String):void` | `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `РепозиторийСтатей` | — | `получитьСвежиеПубликации():List`, `сохранитьСтатью(статья:Статья):void`, `обновитьСтатус(ид:String,статус:String):void`; также контракт `IРепозиторий` | `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `РепозиторийКомментариев` | — | `получитьПоСтатье(идСтатьи:String):List`, `сохранитьКомментарий(комментарий:Комментарий):void`, `обновитьСтатус(ид:String,статус:String):void`; также контракт `IРепозиторий` | `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `РепозиторийЖалоб` | — | `получитьОчередьЖалоб():List`, `сохранитьЖалобу(жалоба:Жалоба):void`, `получитьКоличествоЖалоб(идКомментария:String):Integer`; также контракт `IРепозиторий` | `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |
| [x] | `РепозиторийОтчетов` | — | `получитьОтчеты(период:String):List`, `сохранитьОтчет(отчет:ОтчетАктивности):void`; также контракт `IРепозиторий` | `omis_blog/storage.py`; `tests/test_uml_coverage.py`, `tests/test_storage.py` |

## A.7: состояние UI, стр. 6

| Статус | Сущность | Все поля (тип) | Реализация / проверка |
| --- | --- | --- | --- |
| [x] | `ИнтерфейснаяПодсистема` | `статусПодключения:String`, `текущаяТемаОформления:String` | `omis_blog/domain.py`, `omis_blog/web.py`; `tests/test_uml_coverage.py`, `tests/test_web.py` |
| [x] | `СессияПользователя` | `идСессии:String`, `токенАвторизации:String` | `omis_blog/domain.py`, `omis_blog/web.py`; `tests/test_uml_coverage.py`, `tests/test_web.py` |
| [x] | `ЛентаПубликаций` | `идЛенты:String`, `текущаяСтраница:Integer`, `выбранныйФильтр:String` | `omis_blog/domain.py`, `omis_blog/web.py`; `tests/test_uml_coverage.py`, `tests/test_web.py` |
| [x] | `ФормаРедактора` | `идФормы:String`, `черновикТекста:String`, `статусАвтосохранения:String` | `omis_blog/domain.py`, `omis_blog/web.py`; `tests/test_uml_coverage.py`, `tests/test_web.py` |
| [x] | `КабинетМодератора` | `идКабинета:String`, `фильтрОчереди:String` | `omis_blog/domain.py`, `omis_blog/web.py`; `tests/test_uml_coverage.py`, `tests/test_web.py` |
| [x] | `ОкноЧтенияСтатьи` | `идПросмотра:String`, `идПросматриваемойСтатьи:String` | `omis_blog/domain.py`, `omis_blog/web.py`; `tests/test_uml_coverage.py`, `tests/test_web.py` |

## E.2: контроллеры, Strategy и Command, стр. 11

| Статус | Класс | Все UML-методы | Реализация / проверка |
| --- | --- | --- | --- |
| [x] | `КонтроллерПубликаций` | `обработатьЗаявку(статья:Статья):void`, `валидироватьПоля(статья:Статья):Boolean`, `опубликоватьМатериал(идСтатьи:String):void`, `обновитьИндекс(индекс:ПоисковыйИндекс):void` | `omis_blog/controllers.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |
| [x] | `КонтроллерМодерации` | `зарегистрироватьЖалобу(жалоба:Жалоба):void`, `применитьРешение(вердикт:String):void`, `проверитьПорогСкрытия(идКомментария:String):Boolean` | `omis_blog/controllers.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |
| [x] | `КонтроллерУведомлений` | `уведомитьРедактора(идСтатьи:String):void`, `отправитьПредупреждение(идЧитателя:String):void`, `уведомитьЗаявителя(результат:String):void` | `omis_blog/controllers.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |
| [x] | `КонтроллерЛенты` | `получитьОбновленияЛенты():List`, `фильтроватьПоРубрике(идРубрики:String):List` | `omis_blog/controllers.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |
| [x] | `КонтроллерОтчетов` | `сформироватьОтчет(период:String):ОтчетАктивности`, `получитьОтчеты():List` | `omis_blog/controllers.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |
| [x] | `IСтратегияМодерации` | `проверить(содержание:String):Boolean` | `omis_blog/patterns.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |
| [x] | `СтратегияРучнойМодерации` | `проверить(содержание:String):Boolean` | `omis_blog/patterns.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |
| [x] | `СтратегияАвтоФильтрации` | `проверить(содержание:String):Boolean` | `omis_blog/patterns.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |
| [x] | `IКоманда` | `выполнить():void`, `отменить():void` | `omis_blog/patterns.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |
| [x] | `КомандаПубликации` | `выполнить():void`, `отменить():void` | `omis_blog/patterns.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |
| [x] | `КомандаОтклоненияСтатьи` | `выполнить():void`, `отменить():void` | `omis_blog/patterns.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |
| [x] | `КомандаСкрытияКомментария` | `выполнить():void`, `отменить():void` | `omis_blog/patterns.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |
| [x] | `КомандаУдаленияКомментария` | `выполнить():void`, `отменить():void` | `omis_blog/patterns.py`; `tests/test_uml_coverage.py`, `tests/test_controllers.py` |

## E.3: представления, стр. 12

| Статус | Класс | Поле и все UML-методы | Реализация / проверка |
| --- | --- | --- | --- |
| [x] | `IПредставление` | `отобразить(данные:Object):void`, `обновить(данные:Object):void` | `omis_blog/presentation.py`, `omis_blog/infrastructure.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |
| [x] | `БазовоеПредставление` | `идПредставления:String`; `отобразить(данные:Object):void`, `обновить(данные:Object):void` | `omis_blog/presentation.py`, `omis_blog/infrastructure.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |
| [x] | `IПредставлениеЛенты` | `отобразитьЛенту(статьи:List):void`, `применитьФильтр(выбранныйФильтр:String):void` | `omis_blog/presentation.py`, `omis_blog/infrastructure.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |
| [x] | `IПредставлениеФормыРедактора` | `отобразитьЧерновик(черновикТекста:String):void`, `показатьСтатусАвтосохранения(статус:String):void` | `omis_blog/presentation.py`, `omis_blog/infrastructure.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |
| [x] | `IПредставлениеКабинетаМодератора` | `отобразитьОчередь(фильтрОчереди:String):void`, `показатьТикеты(жалобы:List):void` | `omis_blog/presentation.py`, `omis_blog/infrastructure.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |
| [x] | `IПредставлениеЧтенияСтатьи` | `открытьСтатью(идСтатьи:String):void`, `отобразитьКомментарии(комментарии:List):void` | `omis_blog/presentation.py`, `omis_blog/infrastructure.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |
| [x] | четыре конкретных представления | реализуют соответствующий интерфейс и наследуют базовое поведение | `omis_blog/presentation.py`, `omis_blog/infrastructure.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |

## E.4–E.5: инфраструктура и точка входа, стр. 12–13

| Статус | Класс | Поля и все UML-методы | Реализация / проверка |
| --- | --- | --- | --- |
| [x] | `КонтейнерЗависимостей` | `зарегистрировать(интерфейс:Class,реализация:Class):void`, `разрешить(интерфейс:Class):Object`, `создатьКонтроллер(тип:Class):Object`, `создатьПредставление(тип:Class):Object` | `omis_blog/infrastructure.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |
| [x] | `ФабрикаКонтроллеров` | `создатьКонтроллерПубликаций(репозиторий:РепозиторийСтатей):КонтроллерПубликаций`, `создатьКонтроллерМодерации(репКомм:РепозиторийКомментариев,репЖалоб:РепозиторийЖалоб):КонтроллерМодерации`, `создатьКонтроллерУведомлений():КонтроллерУведомлений`, `создатьКонтроллерЛенты(репозиторий:РепозиторийСтатей):КонтроллерЛенты`, `создатьКонтроллерОтчетов(репозиторий:РепозиторийОтчетов):КонтроллерОтчетов` | `omis_blog/infrastructure.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |
| [x] | `ФабрикаПредставлений` | `создатьПредставлениеЛенты(контроллер:КонтроллерЛенты):IПредставлениеЛенты`, `создатьПредставлениеФормы(контроллер:КонтроллерПубликаций):IПредставлениеФормыРедактора`, `создатьПредставлениеКабинета(контроллер:КонтроллерМодерации):IПредставлениеКабинетаМодератора`, `создатьПредставлениеЧтения(контроллер:КонтроллерМодерации):IПредставлениеЧтенияСтатьи` | `omis_blog/infrastructure.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |
| [x] | `КонфигураторСистемы` | `настроитьЗависимости(контейнер:КонтейнерЗависимостей):void`, `создатьРепозитории():List`, `создатьКонтроллеры(репозитории:List):List`, `создатьПредставления(контроллеры:List):List`, `связатьКомпоненты():void` | `omis_blog/infrastructure.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |
| [x] | `ПриложениеБлогПлатформы` | `контейнер:КонтейнерЗависимостей`, `контроллеры:List`, `представления:List`; `main(args:String[]):void`, `инициализироватьСистему():void`, `запуститьПриложение():void`, `остановитьПриложение():void` | `omis_blog/main.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |

## Связи E.1/A.1–A.7 и атрибуты связей

| Статус | Связь и кардинальность | Атрибут связи | Реализация / проверка |
| --- | --- | --- | --- |
| [x] | Пользователь 1—1 УчетнаяЗапись; УчетнаяЗапись N—1 Роль; Роль 1—N ПравоДоступа (A.2) | — | `omis_blog/domain.py`, `omis_blog/storage.py`, `omis_blog/auth.py`; `tests/test_auth.py`, `tests/test_storage.py` |
| [x] | АвторКонтента 1—N Статья (A.1/A.3) | `датаСоздания:datetime` | `omis_blog/domain.py:Article.author_id/created_at`, `omis_blog/storage.py`; `tests/test_controllers.py::test_publication_rejection_resubmission_and_index` |
| [x] | Редактор 1—N Статья (A.1) | `датаПроверки:datetime` | `omis_blog/domain.py:Article.editor_id/reviewed_at`, `omis_blog/storage.py`; `tests/test_controllers.py::test_publication_rejection_resubmission_and_index` |
| [x] | АдминистраторПлатформы 1—N Рубрика; 1—N ОтчетАктивности (A.1) | `датаИзменения:datetime`, `датаФормирования:datetime` | `omis_blog/domain.py:Category/ActivityReport`, `omis_blog/web.py`; `tests/test_web.py::test_role_scenarios_in_browser` |
| [x] | Рубрика 1—N Статья (A.6) | `датаКлассификации:datetime` | `omis_blog/domain.py:Article.category_id/classified_at`, `omis_blog/storage.py`; `tests/test_web.py::test_editor_media_autosave_search_archive_and_moderation` |
| [x] | Статья N—M Тег (A.6) | `датаРазметки:datetime` | `omis_blog/storage.py:Database.set_article_tags/get_article_tags`; `tests/test_storage.py::test_article_tags_are_persistent` |
| [x] | Статья 1—N Медиавложение; 1—1 ПараметрыОформления (A.3) | — | `omis_blog/domain.py:MediaAttachment/FormattingOptions`, `omis_blog/web.py`; `tests/test_web.py::test_editor_media_autosave_search_archive_and_moderation` |
| [x] | Статья 1—1 ПоисковыйИндекс (A.6) | `датаОбновленияИндекса:datetime` | `omis_blog/domain.py:SearchIndex`, `omis_blog/controllers.py:PublicationController.update_index`; `tests/test_controllers.py::test_publication_rejection_resubmission_and_index` |
| [x] | Статья 1—N ОчередьМодерации; Редактор 1—N ОчередьМодерации (A.4/E.1) | `датаПоступления:datetime`, `датаОбработки:datetime` | `omis_blog/domain.py:ModerationQueueEntry`, `omis_blog/controllers.py:PublicationController`; `tests/test_controllers.py::test_publication_rejection_resubmission_and_index` |
| [x] | Статья 1—N ЗамечаниеРедактора; Редактор 1—N ЗамечаниеРедактора (A.4) | `датаПолучения:datetime`, `датаФормирования:datetime` | `omis_blog/domain.py:EditorRemark`, `omis_blog/controllers.py:PublicationController`; `tests/test_controllers.py::test_publication_rejection_resubmission_and_index` |
| [x] | Редактор 1—N ПротоколПубликации; протокол относится к статье (A.4) | `датаУтверждения:datetime` | `omis_blog/domain.py:PublicationRecord`, `omis_blog/controllers.py:PublicationController`; `tests/test_controllers.py::test_publication_rejection_resubmission_and_index` |
| [x] | Статья 1—N Комментарий; Читатель 1—N Комментарий; Комментарий 1—N ответы (A.5) | `датаДобавления:datetime`, `датаОтправки:datetime`, `датаОтвета:datetime` | `omis_blog/domain.py:Comment`, `omis_blog/web.py`; `tests/test_web.py::test_role_scenarios_in_browser` |
| [x] | Статья 1—N Реакция; Читатель 1—N Реакция (A.5) | `датаОтметки:datetime` | `omis_blog/domain.py:Reaction`, `omis_blog/web.py`; `tests/test_web.py::test_role_scenarios_in_browser` |
| [x] | Комментарий 1—N Жалоба; Читатель 1—N Жалоба (A.5) | `датаПодачи:datetime` | `omis_blog/domain.py:Complaint`, `omis_blog/controllers.py:ModerationController`; `tests/test_controllers.py::test_complaint_threshold_unique_and_both_decisions` |
| [x] | Репозитории агрегируют соответствующие сущности; все четыре реализуют `IРепозиторий` (E.1) | — | `omis_blog/storage.py:IRepository/ArticleRepository/CommentRepository/ComplaintRepository/ReportRepository`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |
| [x] | КонтроллерПубликаций → РепозиторийСтатей, IКоманда, IПредставление; КонтроллерМодерации → IСтратегияМодерации, РепозиторийЖалоб, РепозиторийКомментариев, IКоманда (E.2) | — | `omis_blog/controllers.py`, `omis_blog/patterns.py`, `omis_blog/infrastructure.py`; `tests/test_controllers.py`, `tests/test_infrastructure.py` |
| [x] | КонтроллерЛенты → РепозиторийСтатей, IПредставление; КонтроллерОтчетов → РепозиторийОтчетов, IПредставление (E.2) | — | `omis_blog/controllers.py`, `omis_blog/presentation.py`, `omis_blog/infrastructure.py`; `tests/test_controllers.py`, `tests/test_infrastructure.py` |
| [x] | БазовоеПредставление и четыре специальных интерфейса → IПредставление; специализированные представления → соответствующие контроллеры (E.3) | — | `omis_blog/presentation.py`, `omis_blog/infrastructure.py`; `tests/test_uml_coverage.py`, `tests/test_infrastructure.py` |
| [x] | КонтейнерЗависимостей 1—1 ФабрикаКонтроллеров, 1—1 ФабрикаПредставлений; фабрики создают контроллеры/представления (E.4) | — | `omis_blog/infrastructure.py:DependencyContainer/ControllerFactory/ViewFactory`; `tests/test_infrastructure.py` |
| [x] | ПриложениеБлогПлатформы 1—1 КонтейнерЗависимостей, 1—1 КонфигураторСистемы; использует пять контроллеров и IРепозиторий (E.5) | — | `omis_blog/main.py:BlogPlatformApp`, `omis_blog/infrastructure.py`; `tests/test_infrastructure.py` |
| [x] | ИнтерфейснаяПодсистема 1—N СессияПользователя; 1—1 ЛентаПубликаций, ФормаРедактора, КабинетМодератора, ОкноЧтенияСтатьи (A.7) | `датаВходаВСистему`, `датаОбновленияЛенты`, `датаАвтосохранения`, `датаПримененияФильтра`, `датаПереходаКСтатье` (все `datetime`) | `omis_blog/domain.py:InterfaceSubsystem`, `omis_blog/presentation.py`, `omis_blog/web.py`; `tests/test_web.py` |

Бизнес-переходы и тесты перечислены в [матрице](test_matrix.md). Страница 10 задаёт порог трёх уникальных жалоб и две ветви решения редактора.
