#!/bin/bash

# Vérification du nombre de paramètres
if [ $# -eq 0 ]; then
    days=7  # Valeur par défaut si aucun argument n'est passé
else
    days="$1"
fi

# Chemin vers le répertoire contenant les fichiers de logs (modifier selon ton besoin)
log_dir="/tmp/fbs/backup"

# Vérification si le répertoire de logs existe
if [ ! -d "$log_dir" ]; then
    echo "Répertoire de logs non trouvé : $log_dir"
    exit 1
fi

# Chemin vers le fichier de log
log_file="/tmp/fbs/cleanup_logs.log"

# Efface le fichier de log existant ou crée-en un nouveau
> "$log_file"

# Fonction pour logger un message dans le fichier de log
log_message() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") - $1" >> "$log_file"
}

log_message "Suppression des fichiers de logs plus anciens que $days jours dans : $log_dir"

echo "Confirmez-vous la suppression ? (y/n)"
read confirm
if [ "$confirm" != "y" ]; then
    log_message "Suppression annulée."
    exit 1
fi

# Calcul de la date limite (nombre de jours passés depuis aujourd'hui)
if [ "$days" -eq 0 ]; then
    # Si days est 0, supprimer tous les fichiers de logs
    log_message "Suppression de tous les fichiers de logs dans : $log_dir"
    rm "$log_dir"/*
else
    limit_date=$(date -d "-$days days" "+%Y%m%d")

    # Parcours des fichiers de logs dans le répertoire
    for file in "$log_dir"/*
    do
        # Vérification si le fichier est un fichier régulier et s'il est plus ancien que la limite
        if [ -f "$file" ]; then
            file_date=$(date -r "$file" "+%Y%m%d")
            if [ "$file_date" -le "$limit_date" ]; then
                log_message "Suppression du fichier : $file"
                rm "$file"
            fi
        fi
    done
fi

log_message "Suppression terminée."

echo "Opérations de suppression loggées dans : $log_file"
