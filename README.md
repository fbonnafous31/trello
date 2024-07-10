# Automatisation de la sauvegarde de tableaux Trello

Cr�er une cl� API pour Trello
**Ressources**
https://developer.atlassian.com/cloud/trello/guides/rest-api/api-introduction/
https://trello.com/power-ups/admin

## Cr�er un script Python pour automatiser la savegarde des tableaux Trello
Sauvegarde des informations relatives aux tableaux, fond d'�cran, listes, cartes, labels, commentaires et checklist
export_TrelloBoards.py 

**D�finir les variables**
![D�finition des variables](assets/images/init_export_TrelloBoard.png)

Liste des tableaux � sauvegarder
board_ids = ['taz0b9Dw', '...', '...']  # Liste des IDs de tes tableaux
o� la cl� du tableau est accessible via l'URL du tableau https://trello.com/b/taz0b9Dw/side-projects-2024
 
**Donner les droits d'ex�cution** 
chmod +x export_TrelloBoards.py

**Ex�cution du script** 
python3 export_TrelloBoards.py

![R�sultat de l'ex�cution de la sauvegarde](assets/images/execute_export_TrelloBoards.png)

## S�curiser de la cl� et le token
export TRELLO_API_KEY='...'
export TRELLO_API_TOKEN='...'
source ~/.bashrc

## Cr�er un cron pour automatiser la sauvegarde
crontab -e
crontab -l

![Exemple de cron](assets/images/cron.png)

## Cr�ation d'un shell Linux pour supprimer les sauvegardes anciennes
cleanup_logs.sh

**Donner les droits d'ex�cution** 
chmod +x cleanup_logs.sh

**Lancement** 
./cleanup_logs.sh

## Cr�er d'un script Python pour cr�er un tableau Trello � partir d'une sauvegarde JSON
Chargement des informations du tableau d'origine, fond d'�cran, listes, cartes, labels, commentaires et checklist
load_TrelloBoard.py 

**D�finir les variables**
![D�finition des variables](assets/images/init_load_TrelloBoard.png)

**Donner les droits d'ex�cution** 
chmod +x load_TrelloBoard.py

**Ex�cution du script** 
python load_TrelloBoard.py trelloBoardName

![R�sultat de l'ex�cution du chargement](assets/images/execute_load_TrelloBoard.png)

**Exemple de r�sultat** 
![R�sultat de l'import](assets/images/TrelloBoards.png)
![Contenu du tableau import�](assets/images/ImportedTrello.png)
