import pandas as pd
import os

# Lade die CSV-Datei
csv_file_path = r"C:\Users\K3000\Documents\Max Vorbereitung\finale_image_liste.csv"
df = pd.read_csv(csv_file_path, delimiter=';', encoding='utf-8')

# Definiere die FPS (Frames Per Second) deines Videos
fps = 25  # Setze hier die richtige FPS ein

# Extrahiere Schadenskürzel aus dem basename der output_dir
df['Schadenskürzel'] = df['output_dir'].apply(lambda x: os.path.basename(x))

# Berechne den Videozeitpunkt
df['Videozeitpunkt (h:min:sec)'] = (df['frame'] / fps).apply(lambda x: pd.to_datetime(x, unit='s').strftime('%H:%M:%S'))

# Erstelle das neue DataFrame mit den gewünschten Spalten
new_df = df[['Schadenskürzel', 'Videozeitpunkt (h:min:sec)', 'video_name', 'video_path']]

# Speichere das neue DataFrame in eine neue CSV-Datei
new_csv_file_path = r"C:\Users\K3000\Documents\Max Vorbereitung\max_liste.csv"
new_df.to_csv(new_csv_file_path, index=False, sep=";", encoding="utf-8")
