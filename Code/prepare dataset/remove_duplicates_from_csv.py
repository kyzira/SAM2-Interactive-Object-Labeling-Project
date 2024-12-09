import pandas as pd

# Define file paths
file_path = r"C:\Code Python\SAM2-Interactive-Object-Labeling-Project\Infos and Tables\Max Info\max_liste.csv"
output_file = r"C:\Code Python\SAM2-Interactive-Object-Labeling-Project\Infos and Tables\Max Info\max_liste_gefiltert.csv"

# Read the CSV file with ";" as the delimiter
df = pd.read_csv(file_path, delimiter=';')

# Define columns to compare for duplicates
columns_to_check = ['Videozeitpunkt (h:min:sec)', 'Label', 'Videoname']

# Remove duplicate rows based on these columns
filtered_df = df.drop_duplicates(subset=columns_to_check)

# Save the filtered DataFrame to a new CSV file with ";" as the delimiter
filtered_df.to_csv(output_file, index=False, sep=';')

print(f"Filtered file saved as {output_file}.")
