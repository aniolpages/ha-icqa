# ICQA Catalunya per a Home Assistant

Integració HACS per consultar a Home Assistant la qualitat de l'aire publicada per la Generalitat de Catalunya mitjançant l'Índex Català de Qualitat de l'Aire (ICQA).

[![Obre aquest repositori a HACS dins del teu Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=aniolpages&repository=ha-icqa&category=integration)

## Què permet fer

- Afegir una o més estacions de qualitat de l'aire.
- Veure la qualitat general de l'aire de cada estació.
- Consultar les mesures disponibles de contaminants com NO2, O3, PM10, PM2.5, SO2, CO, C6H6 o H2S.

## Instal·lació amb HACS

Opció ràpida:

[Obre aquest repositori a HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=aniolpages&repository=ha-icqa&category=integration)

Instal·lació manual des de HACS:

1. A HACS, afegeix aquest repositori com a repositori personalitzat de tipus `Integration`.
2. Instal·la **ICQA Catalunya**.
3. Reinicia Home Assistant.
4. Ves a **Configuració > Dispositius i serveis > Afegeix integració** i cerca `ICQA Catalunya`.
5. Selecciona l'estació que vols monitorar.

Per afegir més estacions, torna a afegir la integració i tria una altra estació.

## Entitats

Cada estació crea un dispositiu propi a Home Assistant.

Entitats principals:

- `Qualitat de l'aire`
- `Concentració de <contaminant>`

Entitats de diagnòstic:

- `Última actualització`
- `Data d'instal·lació`
- `Altitud`

## Origen de les dades

La integració consulta les dades públiques del Departament de Territori, Habitatge i Transició Ecològica de la Generalitat de Catalunya:

- Pàgina informativa de qualitat de l'aire: <https://mediambient.gencat.cat/ca/05_ambits_dactuacio/atmosfera/qualitat_de_laire/vols-saber-que-respires/>

## Llicències i reutilització

El codi d'aquesta integració es distribueix amb llicència MIT. Consulta [LICENSE](LICENSE).

Les dades i els continguts de la Generalitat de Catalunya es poden reutilitzar d'acord amb el seu [avís legal](https://tramits.gencat.cat/ca/ajuda/avis_legal/), en els termes de la Llicència oberta d'ús d'informació - Catalunya o l'instrument legal equivalent CC0 de Creative Commons.

Aquesta integració no és oficial ni està afiliada a la Generalitat de Catalunya.

## Desenvolupament

Comprovacions locals bàsiques:

```bash
python -m compileall custom_components tests
python -m unittest discover -s tests
```

El repositori inclou workflows per validar la integració amb HACS Action, Hassfest i les proves del parser.
