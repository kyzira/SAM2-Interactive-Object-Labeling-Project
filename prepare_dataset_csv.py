import pandas as pd
import os


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


aus_reduzierter_liste_zu_gleichmaeßiger_liste()