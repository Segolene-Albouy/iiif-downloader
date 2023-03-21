# iiif-downloader
Code adapted from https://github.com/monniert/docExtractor/blob/master/src/iiif_downloader.py

```
python3 -m venv venv
source venv/bin/activate
python src/iiif_downloader.py -f test-manifests.txt -o <output_dir> --width <width-in-px> --height <height-in-px> --sleep <duration-in-sec>
```

## Institutions specificities

### Gallica 

Too frequent downloads in full size result in error, either reduce the size by providing a width or a height, or extend the time between two downloads
```
https://gallica.bnf.fr/iiif/ark:/12148/bpt6k6281569x/manifest.json
```

### Bibliothèque Inter-Universitaire de la Sorbonne
Providing a size (either width or height) is mandatory
```
https://nubis.univ-paris1.fr/iiif/3/47206/manifest
```

### Others
No special issue

``` bash
https://www.e-rara.ch/i3f/v20/14465351/manifest                                 # E-rara
https://iiif.archivelab.org/iiif/b30413163_0003/manifest.json                   # Archive lab
https://mazarinum.bibliotheque-mazarine.fr/iiif/2134/test-manifests             # Bibliothèque Mazarine
https://view.nls.uk/manifest/1929/8425/192984258/manifest.json                  # Library of Scotland
https://bijzonderecollecties.ubn.ru.nl/iiif/2/Handschriften:12689/manifest.json # Radboud Universiteitsbibliotheek
https://cudl.lib.cam.ac.uk//iiif/MS-KK-00005-00031                              # University of Cambridge
https://www.e-codices.unifr.ch/metadata/iiif/fmb-cb-0115/manifest.json          # e-Codices
https://digi.vatlib.it/iiif/MSS_Vat.lat.3379/manifest.json                      # DigiVatLib
https://bibnum.institutdefrance.fr/iiif/22490/test-manifests                    # Institut de France
https://content.staatsbibliothek-berlin.de/dc/744029791/test-manifests          # Berlin Staatsbibliothek
```
