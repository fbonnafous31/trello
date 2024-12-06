import requests
import json
import argparse
import os
import urllib.parse

# Chemin de base ou se trouvent vos fichiers JSON
base_path = '/tmp/fbs/backup'

# Configuration de l'analyseur d'arguments
parser = argparse.ArgumentParser(description="Recreer un tableau Trello a partir d'une sauvegarde JSON.")
parser.add_argument('json_file', type=str, help='Nom du fichier JSON exporte.')

args = parser.parse_args()

# Construire le chemin complet vers le fichier JSON
json_path = os.path.join(base_path, args.json_file)

# Votre cle API et votre token Trello
api_key = os.getenv('FB_TRELLO_API_KEY')
token = os.getenv('FB_TRELLO_API_TOKEN')

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
    
# Appliquer le background au nouveau tableau
background = data.get('prefs', {}).get('background', None)
if background:
    url_set_background = f"https://api.trello.com/1/boards/{new_board_id}/prefs/background?value={urllib.parse.quote(background)}&key={api_key}&token={token}"
    response_set_background = requests.put(url_set_background)
    
    if response_set_background.status_code != 200:
        print(f"Erreur lors de la configuration du background : {response_set_background.status_code} - {response_set_background.text}")
        response_set_background.raise_for_status()
    else:
        print(f"Background du tableau defini sur '{background}'.")
else:
    print("Aucun background trouve dans la sauvegarde. Utilisation du background par defaut.")

# Background image
if background and background.startswith("http"):
    url_upload_background = f"https://api.trello.com/1/boards/{new_board_id}/boardBackgrounds?key={api_key}&token={token}"
    files = {'file': ('background.jpg', requests.get(background).content)}
    response_upload_background = requests.post(url_upload_background, files=files)
    
    if response_upload_background.status_code != 200:
        print(f"Erreur lors de l'upload de l'image de background : {response_upload_background.status_code} - {response_upload_background.text}")
        response_upload_background.raise_for_status()
    else:
        print("Image de background uploadee avec succes.")             

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

# Creer les cartes dans chaque liste
card_id_map = {}
for card in data['cards']:
    if not card['closed']:
        old_list_id = card['idList']
        new_list_id = list_id_map.get(old_list_id)
        if new_list_id:
            due_date = card.get('due', None)
            url_create_card = (
                f"https://api.trello.com/1/cards?"
                f"idList={new_list_id}"
                f"&name={urllib.parse.quote(card['name'])}"
                f"&desc={urllib.parse.quote(card.get('desc', ''))}"
                f"&due={urllib.parse.quote(due_date) if due_date else ''}"
                f"&key={api_key}&token={token}"
            )            
            response_create_card = requests.post(url_create_card)

            if response_create_card.status_code == 200:
                created_card = response_create_card.json()
                card_id = created_card['id']
                print(f"Carte '{card['name']}' creee avec succes.")
            
                # Ajouter les etiquettes aux cartes
                for label in card.get('labels', []):
                    url_add_label = f"https://api.trello.com/1/cards/{card_id}/labels?color={label['color']}&name={urllib.parse.quote(label['name'])}&key={api_key}&token={token}"
                    response_add_label = requests.post(url_add_label)
                    
                    if response_add_label.status_code == 200:
                        print(f"Etiquette '{label['name']}' ajoutee avec succes a la carte '{card['name']}'.")
                    else:
                        print(f"Erreur lors de l'ajout de l'etiquette '{label['name']}' a la carte '{card['name']}': {response_add_label.text}")
                        break  # Ne pas ajouter d'autres etiquettes en cas de probleme
                                    
                # Marquer la date comme complete
                if due_date:  # Si une date existe
                    url_update_due_complete = f"https://api.trello.com/1/cards/{card_id}?key={api_key}&token={token}"
                    payload = {'dueComplete': 'true'}  # Indique que la date est cochee
                    response_update_due = requests.put(url_update_due_complete, params=payload)
            
                    if response_update_due.status_code == 200:
                        print(f"Date pour la carte '{card['name']}' marquee comme complete.")
                    else:
                        print(f"Erreur lors de la mise a jour de la date de la carte '{card['name']}': {response_update_due.text}")
            else:
                print(f"Erreur lors de la creation de la carte '{card['name']}': {response_create_card.text}")
            
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
                        url_create_checkitem = f"https://api.trello.com/1/checklists/{new_checklist_id}/checkItems?name={urllib.parse.quote(item['name'])}&checked={checked_value}&key={api_key}&token={token}"
                        response_create_checkitem = requests.post(url_create_checkitem)
                        
                        # Verifier si la reponse est correcte avant de continuer
                        if response_create_checkitem.status_code != 200:
                            print(f"Erreur lors de la creation de l'item de la checklist : {response_create_checkitem.status_code} - {response_create_checkitem.text}")
                            response_create_checkitem.raise_for_status()
                            
# Ajouter les commentaires aux cartes si presents dans les actions
for card in data['cards']:
    new_card_id = card_id_map.get(card['id'])
    if new_card_id:
        for action in card['actions']:
            if action.get('type') == 'commentCard':
                comment = action.get('data', {}).get('text', '')
                if comment:
                    url_add_comment = f"https://api.trello.com/1/cards/{new_card_id}/actions/comments?text={urllib.parse.quote(comment)}&key={api_key}&token={token}"
                    response_add_comment = requests.post(url_add_comment)
                    
                    # Verifier si la reponse est correcte avant de continuer
                    if response_add_comment.status_code != 200:
                        print(f"Erreur lors de l'ajout du commentaire : {response_add_comment.status_code} - {response_add_comment.text}")
                        response_add_comment.raise_for_status()

# Ajouter les pieces jointes aux cartes si presentes
for card in data['cards']:
    new_card_id = card_id_map.get(card['id'])
    if new_card_id:
        for attachment in card.get('attachments', []):
            url_add_attachment = f"https://api.trello.com/1/cards/{new_card_id}/attachments?url={urllib.parse.quote(attachment['url'])}&name={urllib.parse.quote(attachment['name'])}&key={api_key}&token={token}"
            response_add_attachment = requests.post(url_add_attachment)
            
            # Verifier si la reponse est correcte avant de continuer
            if response_add_attachment.status_code != 200:
                print(f"Erreur lors de l'ajout de la piece jointe : {response_add_attachment.status_code} - {response_add_attachment.text}")
                response_add_attachment.raise_for_status()                        

print(f"Le tableau '{new_board_name}' a ete cree avec succes et les donnees ont ete importe.")
