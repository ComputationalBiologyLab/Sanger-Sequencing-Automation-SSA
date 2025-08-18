from post_proc.analyze_nt import get_results_for_nt
import pandas as pd
import os
from utils.results_utils import *
def summarize_folders(folder_path, file_type):
    folder_names = find_folders_gen(folder_path)
    print("SUM ", folder_names)
    # Create an empty DataFrame with the same columns
    summarized_df = pd.DataFrame()

    for folder in folder_names:
        try:
            print("SUM ", os.path.join(folder_path, folder, f"blast_results_{file_type}.xml"), os.path.exists(os.path.join(folder_path, folder, f"blast_results_{file_type}.xml")))
            df = get_results_for_nt(os.path.join(folder_path, folder, f"blast_results_{file_type}.xml"))
            #print("SUM", df)
            if not df.empty:
                print("SUM ", df.head())
                # Find the row with the greatest 'Hsp Score' in the current DataFrame
                max_row = df.loc[df['Hsp Score'].idxmax()]

                # Add a new column with the folder name ('Sample Name')
                max_row['Sample Name'] = folder

                # Move the 'Sample Name' column to the first position
                max_row = pd.concat([max_row[-1:], max_row[:-1]], axis=0)

                # Append the row to the summarized DataFrame
                summarized_df = pd.concat([summarized_df, max_row.to_frame().T], ignore_index=True)
        except Exception as e:
            print(f"Error processing file {folder}: {e}")

    # Check if the DataFrame is empty before sorting
    if summarized_df.empty:
        return summarized_df

    # Sort the DataFrame by 'Sample Name'
    summarized_df = summarized_df.sort_values(by='Sample Name')

    return summarized_df