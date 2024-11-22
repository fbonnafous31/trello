import os
import requests
import json
import datetime
import re
import unicodedata

# Charger les variables depuis le fichier de configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Extraire les variables depuis le fichier de configuration
board_ids = config['board_ids']
backup_dir = config['backup_dir']

# Remplace ces valeurs par ta propre cle API et token
api_key = os.getenv('FB_TRELLO_API_KEY')
api_token = os.getenv('FB_TRELLO_API_TOKEN')

def to_camel_case(text):
    # Supprimer les accents
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn'
    )
    # Supprimer les caracteres non-alphanumeriques
    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    # Convertir en camel case
    words = text.split()
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

# Verifier si le repertoire de sauvegarde existe, sinon le creer
if not os.path.exists(backup_dir):  
    os.makedirs(backup_dir)

for board_id in board_ids:
    # Construire l'URL pour acceder aux donnees du tableau
    url = f'https://api.trello.com/1/boards/{board_id}?key={api_key}&token={api_token}&lists=all&cards=all&card_checklists=all&labels=all'
    
    # Faire la requete GET a l'API Trello
    response = requests.get(url)
    
    # Verifier si la requete a reussi
    if response.status_code == 200:
        board_data = response.json()
        board_name = board_data.get('name', board_id)  # Recuperer le nom du tableau ou utiliser l'ID comme fallback
        
        # Pour chaque carte, recuperer les actions (commentaires) et pieces jointes
        for card in board_data.get('cards', []):
            card_id = card['id']
            
            # Recuperer les actions (commentaires)
            actions_url = f'https://api.trello.com/1/cards/{card_id}/actions?key={api_key}&token={api_token}&filter=commentCard'
            actions_response = requests.get(actions_url)
            if actions_response.status_code == 200:
                actions = actions_response.json()
                card['actions'] = actions  # Ajouter les actions a la carte
            
            # Recuperer les checklists de la carte
            checklists_url = f'https://api.trello.com/1/cards/{card_id}/checklists?key={api_key}&token={api_token}'
            checklists_response = requests.get(checklists_url)
            if checklists_response.status_code == 200:
                checklists = checklists_response.json()
                card['checklists'] = checklists  # Ajouter les checklists a la carte
            
            # Recuperer les pieces jointes de la carte
            attachments_url = f'https://api.trello.com/1/cards/{card_id}/attachments?key={api_key}&token={api_token}'
            attachments_response = requests.get(attachments_url)
            if attachments_response.status_code == 200:
                attachments = attachments_response.json()
                card['attachments'] = attachments  # Ajouter les pieces jointes a la carte

        # Generer un nom de fichier avec le nom du tableau en camel case, la date et l'heure
        camel_case_board_name = to_camel_case(board_name)
        file_name = f'{backup_dir}/trello_board_{camel_case_board_name}_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # Enregistrer les donnees dans un fichier JSON
        with open(file_name, 'w') as json_file:
            json.dump(board_data, json_file, indent=4)
        
        print(f"Exportation reussie du tableau {board_name} ! Les donnees sont enregistrees dans {file_name}")
    else:
        print(f"Erreur lors de la requete pour le tableau {board_id} : {response.status_code}")
        print(response.text)  # Affiche la reponse complete pour deboguer
