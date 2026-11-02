# Integracja Home Assistant: Meteo.pl Meteogram

Niestandardowa integracja tworzy encję `sensor.<miejscowość>_meteogram`. Jej stan to temperatura z najnowszego przebiegu modelu UM4 60 h, a `entity_picture` wskazuje generowany obraz meteogramu (temperatura min./maks., opad, prawdopodobieństwo opadu, zachmurzenie i wiatr).

## Instalacja

Dodaj repozytorium `pawelczykkacper/newmeteo` do HACS jako integrację niestandardową, zainstaluj Meteo.pl Meteogram, a następnie wybierz **Ustawienia → Urządzenia i usługi → Dodaj integrację** i wpisz miejscowość.

Możesz też skopiować katalog `custom_components/meteo_pl` do katalogu `custom_components` w Home Assistant. Po instalacji wybierz **Ustawienia → Urządzenia i usługi → Dodaj integrację → Meteo.pl Meteogram**.

Obraz jest dostępny w `/local/meteo_pl_<id wpisu>.png` i aktualizuje się wraz z odświeżeniem danych co godzinę. Można go użyć w encji lub w karcie obrazu:

```yaml
type: picture-entity
entity: sensor.warszawa_meteogram
show_name: true
show_state: true
```

Integracja korzysta z geokodera oraz API używanego przez aplikację [app.meteo.pl](https://app.meteo.pl), dla modelu UM4. Wartości pobiera dla najbliższego węzła siatki modelu; dokładność lokalizacji prognozy jest więc ograniczona rozdzielczością siatki.

Meteogram zawiera wyraźne oznaczenie źródła: „meteo.pl / ICM UW”. Warunki wykorzystania prognoz i wymagania dotyczące informacji o źródle opisuje [FAQ meteo.pl](https://faq.meteo.pl/).

Ikona integracji pochodzi z favicony [meteo.pl](https://www.meteo.pl/).
