import pandas as pd
import os
from collections import Counter

def aus_allen_zu_reduzierter_liste():
    # Load the list of values from the reference CSV file (stored in column 1)
    reference_csv = r"C:\Users\K3000\Documents\Goerkem\alle schaden uber 900.csv"  # Replace with the path to your reference CSV file
    reference_df = pd.read_csv(reference_csv, usecols=[0], header=None, delimiter=';')
    reference_list = reference_df[0].tolist()

    input_directory = r"C:\Users\K3000\Documents\Goerkem\Dorr_Damages_2"  # Replace with the path to your directory
    output_file = "output.csv"  # The output file to save matching rows

    # Initialize an empty DataFrame to store matching rows
    output_df = pd.DataFrame()

    # Iterate over each CSV file in the directory
    for filename in os.listdir(input_directory):
        print(filename)
        if filename.endswith(".csv"):
            file_path = os.path.join(input_directory, filename)
            # Read the CSV file, skip the header row
            df = pd.read_csv(file_path, delimiter=';', on_bad_lines='skip')
            
            # Check if the value in column 5 (index 4) is in the reference list
            matching_rows = df[df.iloc[:, 4].isin(reference_list)]
            
            # Append the matching rows to the output DataFrame
            output_df = pd.concat([output_df, matching_rows])

    # Save the output DataFrame to a CSV file
    output_df.to_csv(output_file, index=False)


def aus_reduzierter_liste_zu_gleichmaeßiger_liste():

    # Path to the input and output files
    input_file = r"C:\Code Python\automation-with-sam2\alle_schaeden_ueber_900_liste.csv"  # Replace with the path to your input CSV file
    output_file = r"C:\Code Python\automation-with-sam2\alle_schaeden_gleichmaessige_liste.csv"  # The output file to save the balanced data

    # Load the data from the CSV file
    df = pd.read_csv(input_file, delimiter=',', on_bad_lines='skip')

    # Count the occurrences of each unique value in column 5
    value_counts = df.iloc[:, 4].value_counts()

    # Find the minimum frequency across all unique values
    min_count = value_counts.min()

    # Initialize a list to store the sampled rows
    sampled_rows = []

    # For each unique value, sample rows to match the count of the least frequent value
    for value in value_counts.index:
        subset = df[df.iloc[:, 4] == value]
        if len(subset) > min_count:
            sampled_subset = subset.sample(n=min_count, random_state=1)  # Set random_state for reproducibility
        else:
            sampled_subset = subset  # If there are fewer rows than min_count, take all rows
        sampled_rows.append(sampled_subset)

    # Concatenate all sampled subsets
    balanced_df = pd.concat(sampled_rows)

    # Save the balanced DataFrame to a CSV file
    balanced_df.to_csv(output_file, index=False, sep=';')


def check_auf_gleiches_video():

    input_file = r"C:\Code Python\automation-with-sam2\alle_schaeden_ueber_900_liste.csv"  # Replace with the path to your input CSV file
    output_file = r"C:\Code Python\automation-with-sam2\alle_schaeden_sortierte_liste.csv"  # The output file to save the balanced data

    # CSV-Datei laden (ersetze 'deine_datei.csv' mit deinem tatsächlichen Dateinamen)
    df = pd.read_csv(input_file, delimiter=',', on_bad_lines='skip')

    # Spalte 'Videozeitpunkt' in ein zeitliches Format umwandeln
    df['Videozeitpunkt'] = pd.to_datetime(df['Videozeitpunkt (h:min:sec)'], format='%H:%M:%S')

    # Sortieren nach 'Videopfad' und 'Videozeitpunkt'
    df_sorted = df.sort_values(by=['Videopfad', 'Videozeitpunkt'])

    # Ergebnis in eine neue CSV-Datei speichern
    df_sorted.to_csv(output_file, index=False, sep=';')


def filter_meter_difference(input_file, output_file, threshold=0.2):
    # CSV-Datei laden (ersetze 'deine_datei.csv' mit deinem tatsächlichen Dateinamen)
    df = pd.read_csv(input_file, delimiter=',', on_bad_lines='skip')

    # Spalte 'Videozeitpunkt' in ein zeitliches Format umwandeln
    df['Videozeitpunkt'] = pd.to_datetime(df['Videozeitpunkt (h:min:sec)'], format='%H:%M:%S')

    # Sortieren nach 'Videopfad' und 'Meter ab Rohrbeginn'
    df_sorted = df.sort_values(by=['Videopfad', 'Meter ab Rohrbeginn'])

    # Funktion, um Einträge zu filtern, bei denen der Unterschied im "Meter ab Rohrbeginn" kleiner als threshold ist
    filtered_entries = []
    grouped = df_sorted.groupby('Videopfad')

    for _, group in grouped:
        # Sortieren nach 'Meter ab Rohrbeginn'
        group_sorted = group.sort_values(by='Meter ab Rohrbeginn')
        for i in range(1, len(group_sorted)):
            # Berechne den Unterschied zwischen aufeinanderfolgenden Einträgen
            diff = abs(group_sorted.iloc[i]['Meter ab Rohrbeginn'] - group_sorted.iloc[i-1]['Meter ab Rohrbeginn'])
            if diff < threshold:
                filtered_entries.append(group_sorted.iloc[i-1])
                filtered_entries.append(group_sorted.iloc[i])
    
    # Filtered entries DataFrame erstellen und speichern
    df_filtered = pd.DataFrame(filtered_entries).drop_duplicates()
    df_filtered.to_csv(output_file, index=False, sep=';')

    print(f"Gefilterte Einträge wurden in {output_file} gespeichert.")






def count_schaden_pairs(input_file, output_file):
    # CSV-Datei laden
    df = pd.read_csv(input_file, delimiter=',', on_bad_lines='skip')

    # Sortiere nach 'Videopfad' und 'Meter ab Rohrbeginn'
    df_sorted = df.sort_values(by=['Videopfad', 'Meter ab Rohrbeginn'])

    # Liste für Paare
    pairs = []

    # Gruppiere die Daten nach 'Videopfad'
    grouped = df_sorted.groupby('Videopfad')

    for _, group in grouped:
        # Sortiere nach 'Meter ab Rohrbeginn'
        group_sorted = group.sort_values(by='Meter ab Rohrbeginn')
        
        # Iteriere durch die Gruppe und finde aufeinanderfolgende Einträge
        for i in range(1, len(group_sorted)):
            # Nimm nur die ersten 3 Buchstaben der Schadenskürzel
            schaden_1 = group_sorted.iloc[i-1]['Schadenskürzel'][:3]
            schaden_2 = group_sorted.iloc[i]['Schadenskürzel'][:3]
            
            # Erstelle ein Tuple mit den Kürzeln, sortiert damit (A, B) und (B, A) gleich sind
            pair = tuple(sorted([schaden_1, schaden_2]))
            pairs.append(pair)

    # Zähle die Häufigkeit der Paare
    pair_counts = Counter(pairs)

    # Konvertiere die Paare und ihre Zählungen in ein DataFrame
    pair_df = pd.DataFrame(pair_counts.items(), columns=['Schaden Paar', 'Anzahl'])

    # Speichere das DataFrame in eine CSV-Datei
    pair_df.to_csv(output_file, index=False, sep=';')

    print(f"Die Paar-Häufigkeiten wurden in {output_file} gespeichert.")



# Funktion zum Erstellen einer Liste mit max. 20 Einträgen pro Schadenskürzel
def get_limited_damage_entries(df, num_entries=20):
    result = pd.DataFrame()
    
    # Gruppieren nach Schadenskürzel
    groups = df.groupby('Schadenskürzel')
    
    # Für jede Gruppe die ersten num_entries Zeilen nehmen
    for name, group in groups:
        subset = group.head(num_entries)
        result = pd.concat([result, subset], axis=0)
    
    return result


# Datei laden
df = pd.read_csv(r"C:\Code Python\automation-with-sam2\labeling_project\alle_schaeden_gleichmaessige_liste.csv", sep=';')

# Die Liste mit max. 20 Einträgen pro Schadenskürzel erstellen
limited_entries = get_limited_damage_entries(df)

# Liste speichern oder weiterverarbeiten
limited_entries.to_csv(r'C:\Code Python\automation-with-sam2\labeling_project\avg polygons\gesammelte_einträge.csv', index=False)