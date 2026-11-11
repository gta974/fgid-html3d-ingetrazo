# FGId HTML3D pour IngeTrazo — 0.13.0

Installation : fermer IngeTrazo, remplacer le dossier FGId_HTML3D dans le répertoire ouvert par Extensions → Open plugins folder, puis relancer. Désactiver les anciennes copies séparées fgid_html3d.py pour éviter les doublons. Commande Extensions → Export HTML3D… .

Le HTML embarque le modèle GLB, ses images, Three.js et OrbitControls. Le lien NEXDATA est facultatif et ne sert pas au chargement. Télécharger le HTML depuis Drive puis l’ouvrir dans un navigateur moderne ; l’aperçu Drive n’est pas un viewer WebGL.

Paramètres : thème, arêtes calculées, arêtes libres désactivées par défaut ou monochromes/couleurs des Tags disponibles, annotations, nuage FGId affiché et ouverture du navigateur. Les calques sans couleur source suivent le thème. Les trois états sont normal, transparent et masqué. Les Tags imbriqués restent contrôlables ; le masquage d’un parent masque ses descendants. oneface conserve les faces avant sans modifier le modèle.

Le nuage optionnel embarque tous les points actuellement chargés, y compris les points masqués par le crop, avec leurs couleurs source. Il transfère la taille en pixels et l’opacité. L’EDL et les modes de couleur du rendu natif restent propres à IngeTrazo. Le viewer propose ses propres réglages de taille et placement. L’export de millions de points peut produire un HTML très volumineux.

Validation : quatre petits SKP (51 à 61 Ko), export dans le portable réel, rendu Chrome, changement de thème et projection. Modèle de contrôle : UV répétés, texture intégrée, Tags imbriqués, oneface, texte, cote, arête libre et nuage transformé/découpé. Le navigateur piloté ne permet pas file:// : le rendu est vérifié via HTTP local, et l’absence de ressources externes par inspection. L’ouverture directe hors ligne reste à confirmer manuellement.

Limites : bêta, performances sur gros modèles non validées ; fidélité limitée aux données conservées par l’import IngeTrazo. Les figures face-me sont exportées dans leur orientation géométrique, sans animation automatique vers la caméra. Les couleurs de Tags absentes ne sont pas inventées. Les cotes transférées sont linéaires. Aucun fichier source SKP n’est modifié.

Le writer GLB adapté conserve la licence GPL-3.0-or-later d’IngeTrazo (Marco Sumari Tellez et contributeurs). Le viewer provient du RBZ HTML3D Exporter fourni par Gilles Tarnus, avec adaptations de portage. Three.js/OrbitControls : licence MIT jointe et intégrée au HTML. Aucun runtime Ruby nécessaire.

Export des scènes : cochez l’option puis sélectionnez les scènes à inclure. Le panneau Scènes du HTML rappelle la caméra enregistrée, les Tags, les objets masqués et les coupes actives. Les coupes imbriquées nécessitent les métadonnées conservées par FGId SKP. Les sections sont affichées avec un contour rouge, sans remplissage. Le fond et les arêtes sont les réglages de style rappelés. Les données de points sont communes aux scènes, avec un état visuel distinct par scène.




Le modèle GLB est compressé en gzip dans le HTML. Le visualiseur affiche la progression de la décompression puis prépare le premier affichage.

Current view enregistre le cadrage courant dans la liste des scènes. L’option du nuage apparaît lorsque le nuage FGId est affiché.

Dans la liste des scènes, sélectionnez une ligne puis utilisez Monter ou Descendre pour définir l’ordre du menu HTML.

Si Current view est décochée, la première scène exportée s’affiche à l’ouverture et devient la vue par défaut.


## États du nuage par scène — 0.9.0

Cocher « Inclure le nuage FGId chargé (états des scènes) ». Les scènes rappellent
la visibilité, la découpe locale XYZ, la taille des points en pixels, l’opacité,
le déplacement/la rotation et les sous-nuages masqués. Current view retrouve
l’état courant. Une scène ancienne sans état de nuage utilise l’état courant.

Un seul échantillon de points est inclus, sans duplication par scène.
Tous les points actuellement chargés sont inclus, même hors du crop courant.
Le HTML peut donc être plus volumineux qu’un export limité au crop.
Il contient uniquement le fichier de nuage actuellement chargé. Une scène
associée à un autre fichier de nuage masque ce nuage dans le HTML.
Les paramètres doivent être enregistrés dans les scènes IngeTrazo avant export.


## Navigation IngeTrazo — 0.10.0
La rotation choisit le point du modèle sous la souris au début du geste.
Si le curseur vise le vide, elle utilise le milieu du modèle traversé par le
rayon central. Le pivot reste fixe pendant le glissement. La caméra et sa
cible tournent ensemble : le point visé reste à sa place dans l’image.
La sensibilité suit celle d’IngeTrazo, sans inertie ajoutée à la rotation.
La projection parallèle et le tactile sont pris en charge.
Les scènes exportent la caméra native enregistrée dans IngeTrazo.

Navigation adaptée de core/camera.py et views/viewport.py d’IngeTrazo
0.5.10.1, Marco Sumari Tellez et contributeurs, GPL-3.0-or-later.
Les états du nuage par scène restent disponibles comme dans la version 0.9.


## Zoom et déplacement — 0.11.0
Le déplacement utilise la profondeur du point visé au début du glissement.
Le modèle suit la souris, indépendamment de la distance de la cible de scène.
Le zoom rapproche ou éloigne le cadre complet autour du point visé.
Les grands deltas de molette sont plafonnés pour éviter les sauts.
Souris, zoom par bouton central et projection parallèle sont pris en charge.


## Modes de rendu — 0.12.0
Le menu « Rendu » du HTML propose Textures, Couleurs seules, Monochrome,
Lignes cachées, Filaire, Rayons X, Argile et Normales.
Le mode choisi reste actif quand on rappelle une autre scène.
Les textures et matériaux d’origine sont conservés pour revenir à Textures.
Les coupes, Tags et états du nuage par scène restent utilisables.
Les lignes cachées imposent les contours visibles. Le filaire affiche la
triangulation complète du maillage, à travers les volumes. Les faces aux
Rayons X ont une opacité réduite et conservent la transparence des Tags.
Couleurs seules utilise la couleur moyenne de l’image pour les matériaux
texturés. Argile utilise l’éclairage du viewer sur un matériau uniforme.


## Mode initial et barre d’outils — 0.13.0
La fenêtre d’export propose le mode de rendu initial. Il est présélectionné
d’après le style courant d’IngeTrazo : textures, shaded/couleurs seules,
hidden_line/lignes cachées, monochrome, wireframe/filaire ou xray/rayons X.
Argile et Normales restent disponibles comme choix explicites.
Le HTML applique le mode choisi dès le premier affichage. Son sélecteur
s’intègre aux commandes de la barre d’outils, avec le nom du mode visible
et sans libellé « Rendu » supplémentaire. Le mode reste modifiable dans le HTML.
