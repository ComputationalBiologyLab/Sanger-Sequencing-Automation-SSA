from post_proc.analyze_nt import get_results_for_nt
import pandas as pd
import os
from utils.results_utils import *

def summarize_folders(folder_path):
    print("folder_path", folder_path)
    folder_names = find_folders_gen(folder_path)
    print("folder_path1", folder_names)

    # Create an empty DataFrame with the same columns
    summarized_df = pd.DataFrame()

    for folder in folder_names:
        df = get_results_for_nt(os.path.join(folder_path, folder, "blast_results_nt.xml"))
        if not df.empty:
            # Find the row with the greatest 'Hsp Score' in the current DataFrame
            max_row = df.loc[df['Hsp Score'].idxmax()]

            # Add a new column with the folder name ('Sample Name')
            max_row['Sample Name'] = folder

            # Move the 'Sample Name' column to the first position
            max_row = pd.concat([max_row[-1:], max_row[:-1]], axis=0)

            # Append the row to the summarized DataFrame
            summarized_df = pd.concat([summarized_df, max_row.to_frame().T], ignore_index=True)


    # Sort the DataFrame by 'Sample Name'
    summarized_df = summarized_df.sort_values(by='Sample Name')

    return summarized_df



