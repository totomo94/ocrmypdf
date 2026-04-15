#!/bin/bash

# Ordner, in dem die PDF-Dateien komprimiert werden sollen
FOLDER=$1

# Ordner, in dem die komprimierten PDF-Dateien gespeichert werden sollen
OUTPUT_FOLDER="Compressed"

# Qualitätsstufe der Komprimierung (e.g., Screen, Ebook, Printer, Prepress)
QUALITY="ebook"

# Prüfen, ob ein Ordner übergeben wurde
if [ -z "$FOLDER" ]; then
    echo "Please specify a folder!"
    exit 1
fi

# Prüfen, ob der Ordner existiert
if [ ! -d "$FOLDER" ]; then
    echo "This folder does not exist!"
    exit 1
fi

#

# Prüfen ob Ordner existiert und ggfs. erstellen
if [ ! -d "$OUTPUT_FOLDER" ]; then    
    mkdir -p $OUTPUT_FOLDER
fi

# Schleife über alle PDF-Dateien im Ordner
for file in "$FOLDER"/*.pdf; do
    if [ -f "$file" ]; then
        echo "Processing file: $file"

        # Ausgangsdatei und Zielpfad definieren
        filename=$(basename "$file" .pdf)
        output="$OUTPUT_FOLDER/${filename}.pdf"

        # Ghostscript-Befehl zur Komprimierung
        gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/$QUALITY -dNOPAUSE -dQUIET -dBATCH -sOutputFile="$output" "$file"

        # Option: Komprimierte Datei verschieben
        #mv "$output" ../"$OUTPUT_FOLDER"+"$file"
    fi
done

echo "Compressing complete."
