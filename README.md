# iiif-downloader
Code adapted from https://github.com/monniert/docExtractor/blob/master/src/iiif_downloader.py

```
python3 -m venv venv
source venv/bin/activate
python src/iiif_downloader.py -f test-manifests.txt -o <output_dir> --width <width-in-px> --height <height-in-px> --sleep <duration-in-sec>
```

## Institutions specificities

### Download limit

Leiden University: https://digitalcollections.universiteitleiden.nl/iiif_manifest/item%3A3411841/manifest
Qatar Digital Library: https://www.qdl.qa/en/iiif/81055/vdc_100030968238.0x000001/manifest

### Gallica 
5 downloads above 1000px allowed by minute
```
https://gallica.bnf.fr/iiif/ark:/12148/bpt6k6281569x/manifest.json
```

### Bibliothèque Inter-Universitaire de la Sorbonne
Providing a size (either width or height) is mandatory
```
https://nubis.univ-paris1.fr/iiif/3/47206/manifest
```

### List of tested manifest providers

Find manifests using [Biblissima IIIF Collections](https://iiif.biblissima.fr/collections/search?q=)

``` bash
https://gallica.bnf.fr/iiif/ark:/12148/btv1b11002469m/manifest.json                        # Bibliothèque nationale de France
https://digi.vatlib.it/iiif/MSS_Vat.gr.1087/manifest.json                                  # Biblioteca Apostolica Vaticana
https://content.staatsbibliothek-berlin.de/dc/744029791/manifest                           # Staatsbibliothek zu Berlin
https://bibnum.institutdefrance.fr/iiif/22490/manifest                                     # Institut de France
https://nubis.univ-paris1.fr/iiif/2/ark:/15733/1556/manifest                               # Bibliothèque Inter-Universitaire de la Sorbonne
https://api.digitale-sammlungen.de/iiif/presentation/v2/bsb00045298/manifest               # Münchener DigitalisierungsZentrum
https://www.qdl.qa/en/iiif/81055/vdc_100030968238.0x000001/manifest                        # Qatar Digital Library
https://digitalcollections.universiteitleiden.nl/iiif_manifest/item%3A1572906/manifest     # Universiteit Leiden
https://collections.library.yale.edu/manifests/16960303                                    # Yale Library
https://iiif.slub-dresden.de/iiif/2/323548814/manifest.json                                # SLUB Dresden
https://iiif.nli.org.il/IIIFv21/DOCID/PNX_MANUSCRIPTS990001221250205171-1/manifest         # National Library of Israel
https://iiif.bodleian.ox.ac.uk/iiif/manifest/f7abf7d2-d365-4aa9-9f44-ab7d626a4d47.json     # Oxford Bodleian Libraries
https://api.bl.uk/metadata/iiif/ark:/81055/vdc_100162804369.0x000001/manifest.json         # British Library
https://iiif.archivelab.org/iiif/b30413163_0003/manifest.json                              # Internet Archive
https://mazarinum.bibliotheque-mazarine.fr/iiif/2134/manifest                              # Bibliothèque Mazarine
https://view.nls.uk/manifest/1929/8425/192984258/manifest.json                             # National Library of Scotland
https://bijzonderecollecties.ubn.ru.nl/iiif/2/Handschriften:12689/manifest.json            # Universiteit Utrecht
https://cudl.lib.cam.ac.uk//iiif/MS-KK-00005-00031                                         # Cambridge University Library
https://www.e-codices.unifr.ch/metadata/iiif/fmb-cb-0115/manifest.json                     # Bibliothèque virtuelle des manuscrits en Suisse
https://bvmm.irht.cnrs.fr/iiif/24971/manifest                                              # Institut de recherche et d'histoire des textes
https://eida.obspm.fr/eida/iiif/auto/manuscript/ms-3/manifest.json                         # EIDA platform
https://digital.blb-karlsruhe.de/i3f/v20/1942311/manifest                                  # Badische Landesbibliothek
https://iiif.lib.harvard.edu/manifests/drs:13086510                                        # Harvard Library
https://www.e-rara.ch/i3f/v20/14465351/manifest                                            # E-rara
https://permalinkbnd.bnportugal.gov.pt/iiif/3750/manifest                                  # Biblioteca Nacional de Portugal
https://cecilia.mediatheques.grand-albigeois.fr/iiif/15/manifest                           # Médiathèques d'Albi
https://digi.ub.uni-heidelberg.de/diglit/iiif/cpg765/manifest.json                         # Universität Heidelberg
https://www.digitalcollections.manchester.ac.uk/iiif/MS-ENGLISH-00078                      # University of Manchester
https://adore.ugent.be/IIIF/manifests/archive.ugent.be%253A010C9ED6-94DB-11E3-AFBA-2845D43445F2 # Ghent University Library
https://iiif.library.utoronto.ca/presentation/v2/fisher2:F6521/manifest                    # University of Toronto Libraries
https://sharedcanvas.be/IIIF/manifests/B_OB_MS618                                          # Mmmonk
https://cdm16003.contentdm.oclc.org/iiif/2/p15150coll7:10585/manifest.json                 # The Huntington Library
```
