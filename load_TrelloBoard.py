import requests
import json
import argparse
import os
import urllib.parse

# Chemin de base ou se trouvent vos fichiers JSON
base_path = # Chemin vers le repertoire de sauvegarde

# Configuration de l'analyseur d'arguments
parser = argparse.ArgumentParser(description="Recreer un tableau Trello a partir d'une sauvegarde JSON.")
parser.add_argument('json_file', type=str, help='Nom du fichier JSON exporte.')

args = parser.parse_args()

# Construire le chemin complet vers le fichier JSON
json_path = os.path.join(base_path, args.json_file)

# Votre cle API et votre token Trello
api_key =   # Clé d'API Trello (https://trello.com/power-ups/admin)
token =     # Token Trello

if not api_key or not token:
    raise ValueError("Les cles API ou le token sont manquants.")

# Charger le fichier JSON
with open(json_path, 'r') as file:
    data = json.load(file)

# Nom du nouveau tableau base sur le nom dans le fichier JSON
new_board_name = data['name'] + ' (imported)'

# Creer un nouveau tableau
url_create_board = f"https://api.trello.com/1/boards/?name={urllib.parse.quote(new_board_name)}&key={api_key}&token={token}"
response_create_board = requests.post(url_create_board)

# Verifier si la reponse est correcte avant de continuer
if response_create_board.status_code != 200:
    print(f"Erreur lors de la creation du tableau : {response_create_board.status_code} - {response_create_board.text}")
    response_create_board.raise_for_status()

# Recuperer l'ID du nouveau tableau cree
try:
    new_board_data = response_create_board.json()
    new_board_id = new_board_data['id']
except json.JSONDecodeError:
    print(f"Erreur de decodage JSON lors de la creation du tableau : {response_create_board.text}")
    raise

# Recuperer le fond d'ecran du tableau d'origine
if 'prefs' in data and 'background' in data['prefs']:
    background_url = data['prefs']['background']
    if background_url:
        url_set_background = f"https://api.trello.com/1/boards/{new_board_id}/prefs/background?key={api_key}&token={token}&value={background_url}"
        response_set_background = requests.put(url_set_background)

        # Verifier si la reponse est correcte avant de continuer
        if response_set_background.status_code != 200:
            print(f"Erreur lors du reglage du fond d'ecran : {response_set_background.status_code} - {response_set_background.text}")
            response_set_background.raise_for_status()

# Recuperer les listes par defaut du nouveau tableau
url_get_lists = f"https://api.trello.com/1/boards/{new_board_id}/lists?key={api_key}&token={token}"
response_get_lists = requests.get(url_get_lists)
if response_get_lists.status_code != 200:
    print(f"Erreur lors de la recuperation des listes par defaut : {response_get_lists.status_code} - {response_get_lists.text}")
    response_get_lists.raise_for_status()

# Verifier si la reponse contient du JSON valide
try:
    default_lists = response_get_lists.json()
except json.JSONDecodeError:
    print(f"Erreur de decodage JSON lors de la recuperation des listes par defaut : {response_get_lists.text}")
    raise

# Supprimer les listes par defaut
for default_list in default_lists:
    url_delete_list = f"https://api.trello.com/1/lists/{default_list['id']}/closed?value=true&key={api_key}&token={token}"
    response_delete_list = requests.put(url_delete_list)
    if response_delete_list.status_code != 200:
        print(f"Erreur lors de la suppression de la liste par defaut : {response_delete_list.status_code} - {response_delete_list.text}")
        response_delete_list.raise_for_status()

# Dictionnaire pour mapper les anciennes listes aux nouvelles
list_id_map = {}

# Trier les listes par 'pos'
sorted_lists = sorted(data['lists'], key=lambda x: x['pos'])

# Creer les listes dans le nouveau tableau dans l'ordre original
for lst in sorted_lists:
    if not lst['closed']:
        url_create_list = f"https://api.trello.com/1/lists?name={urllib.parse.quote(lst['name'])}&idBoard={new_board_id}&pos={lst['pos']}&key={api_key}&token={token}"
        response_create_list = requests.post(url_create_list)
        
        # Verifier si la reponse est correcte avant de continuer
        if response_create_list.status_code != 200:
            print(f"Erreur lors de la creation de la liste : {response_create_list.status_code} - {response_create_list.text}")
            response_create_list.raise_for_status()

        # Verifier si la reponse contient du JSON valide
        try:
            response_data = response_create_list.json()
        except json.JSONDecodeError:
            print(f"Erreur de decodage JSON lors de la creation de la liste : {response_create_list.text}")
            raise

        new_list_id = response_data['id']
        list_id_map[lst['id']] = new_list_id

# Creer les etiquettes dans le nouveau tableau
label_id_map = {}
for label in data['labels']:
    url_create_label = f"https://api.trello.com/1/labels?name={urllib.parse.quote(label['name'])}&color={label['color']}&idBoard={new_board_id}&key={api_key}&token={token}"
    response_create_label = requests.post(url_create_label)
    
    # Verifier si la reponse est correcte avant de continuer
    if response_create_label.status_code != 200:
        print(f"Erreur lors de la creation de l'etiquette : {response_create_label.status_code} - {response_create_label.text}")
        response_create_label.raise_for_status()
    
    # Verifier si la reponse contient du JSON valide
    try:
        response_data = response_create_label.json()
    except json.JSONDecodeError:
        print(f"Erreur de decodage JSON lors de la creation de l'etiquette : {response_create_label.text}")
        raise

    new_label_id = response_data['id']
    label_id_map[label['id']] = new_label_id

# Creer les cartes dans chaque liste
card_id_map = {}
for card in data['cards']:
    if not card['closed']:
        old_list_id = card['idList']
        new_list_id = list_id_map.get(old_list_id)
        if new_list_id:
            url_create_card = f"https://api.trello.com/1/cards?idList={new_list_id}&name={urllib.parse.quote(card['name'])}&desc={urllib.parse.quote(card.get('desc', ''))}&key={api_key}&token={token}"
            response_create_card = requests.post(url_create_card)
            
            # Verifier si la reponse est correcte avant de continuer
            if response_create_card.status_code != 200:
                print(f"Erreur lors de la creation de la carte : {response_create_card.status_code} - {response_create_card.text}")
                response_create_card.raise_for_status()
            
            # Verifier si la reponse contient du JSON valide
            try:
                response_data = response_create_card.json()
            except json.JSONDecodeError:
                print(f"Erreur de decodage JSON lors de la creation de la carte : {response_create_card.text}")
                raise

            new_card_id = response_data['id']
            card_id_map[card['id']] = new_card_id

            # Ajouter les checklists a la carte si elles existent
            if 'checklists' in card:
                for checklist in card['checklists']:
                    url_create_checklist = f"https://api.trello.com/1/checklists?idCard={new_card_id}&name={urllib.parse.quote(checklist['name'])}&key={api_key}&token={token}"
                    response_create_checklist = requests.post(url_create_checklist)
                    
                    # Verifier si la reponse est correcte avant de continuer
                    if response_create_checklist.status_code != 200:
                        print(f"Erreur lors de la creation de la checklist : {response_create_checklist.status_code} - {response_create_checklist.text}")
                        response_create_checklist.raise_for_status()
                    
                    # Verifier si la reponse contient du JSON valide
                    try:
                        checklist_data = response_create_checklist.json()
                    except json.JSONDecodeError:
                        print(f"Erreur de decodage JSON lors de la creation de la checklist : {response_create_checklist.text}")
                        raise

                    new_checklist_id = checklist_data['id']

                    # Ajouter les items de la checklist
                    for item in checklist['checkItems']:
                        checked_value = "true" if item['state'] == 'complete' else "false"
                        url_create_checkitem = f"https://api.trello.com/1/checklists/{new_checklist_id}/checkItems?name={urllib.parse.quote(item['name'])}&pos={item['pos']}&checked={checked_value}&key={api_key}&token={token}"
                        response_create_checkitem = requests.post(url_create_checkitem)
                        
                        # Verifier si la reponse est correcte avant de continuer
                        if response_create_checkitem.status_code != 200:
                            print(f"Erreur lors de la creation de l'item de checklist : {response_create_checkitem.status_code} - {response_create_checkitem.text}")
                            response_create_checkitem.raise_for_status()

            # Ajouter les commentaires a la carte si des actions existent
            if 'actions' in card:
                for action in card['actions']:
                    if action['type'] == 'commentCard' and 'data' in action and 'text' in action['data']:
                        url_create_comment = f"https://api.trello.com/1/cards/{new_card_id}/actions/comments?text={urllib.parse.quote(action['data']['text'])}&key={api_key}&token={token}"
                        response_create_comment = requests.post(url_create_comment)
                        if response_create_comment.status_code != 200:
                            print(f"Erreur lors de la creation du commentaire : {response_create_comment.status_code} - {response_create_comment.text}")
                            response_create_comment.raise_for_status()

            # Ajouter les etiquettes a la carte
            if 'idLabels' in card:
                for old_label_id in card['idLabels']:
                    new_label_id = label_id_map.get(old_label_id)
                    if new_label_id:
                        url_add_label = f"https://api.trello.com/1/cards/{new_card_id}/idLabels?value={new_label_id}&key={api_key}&token={token}"
                        response_add_label = requests.post(url_add_label)
                        if response_add_label.status_code != 200:
                            print(f"Erreur lors de l'ajout de l'etiquette a la carte : {response_add_label.status_code} - {response_add_label.text}")
                            response_add_label.raise_for_status()

print(f"Le tableau '{new_board_name}' a ete recree avec succes.")
print(f"Le tableau recree est accessible a l'URL : https://trello.com/b/{new_board_id}")
