import os
import requests
import json
import datetime

# Définir les variables
api_key =       # Clé d'API Trello (https://trello.com/power-ups/admin)
token =         # Token Trello
board_ids =     # Liste des IDs de tes tableaux
backup_dir =    # Chemin vers le repertoire de sauvegarde

# Verifier si le repertoire de sauvegarde existe, sinon le creer
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

for board_id in board_ids:
    # Construire l'URL pour acceder aux donnees du tableau
    url = f'https://api.trello.com/1/boards/{board_id}?key={api_key}&token={token}&lists=all&cards=all&card_checklists=all&labels=all'
    
    # Faire la requete GET a l'API Trello
    response = requests.get(url)
    
    # Verifier si la requete a reussi
    if response.status_code == 200:
        board_data = response.json()
        
        # Pour chaque carte, recuperer les actions (commentaires)
        for card in board_data.get('cards', []):
            card_id = card['id']
            actions_url = f'https://api.trello.com/1/cards/{card_id}/actions?key={api_key}&token={token}&filter=commentCard'
            actions_response = requests.get(actions_url)
            
            if actions_response.status_code == 200:
                actions = actions_response.json()
                card['actions'] = actions  # Ajouter les actions a la carte
            
            # Recuperer les checklists de la carte
            checklists_url = f'https://api.trello.com/1/cards/{card_id}/checklists?key={api_key}&token={token}'
            checklists_response = requests.get(checklists_url)
            
            if checklists_response.status_code == 200:
                checklists = checklists_response.json()
                card['checklists'] = checklists  # Ajouter les checklists a la carte

        # Generer un nom de fichier avec la date et l'heure
        file_name = f'{backup_dir}/trello_board_{board_id}_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # Enregistrer les donnees dans un fichier JSON
        with open(file_name, 'w') as json_file:
            json.dump(board_data, json_file, indent=4)
        
        print(f"Exportation reussie du tableau {board_id} ! Les donnees sont enregistrees dans {file_name}")
    else:
        print(f"Erreur lors de la requete pour le tableau {board_id} : {response.status_code}")
        print(response.text)  # Affiche la reponse complete pour deboguer
