import xml.etree.ElementTree as ET
import pandas as pd

def get_results_for_nt(xml_file_path):
    print("xml", xml_file_path)
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    result_data = []

    for hit in root.findall(".//Hit"):
        hit_info = {
            'Hit Number': hit.find('Hit_num').text,
            'Hit ID': hit.find('Hit_id').text,
            'Hit Definition': hit.find('Hit_def').text,
            'Hit Accession': hit.find('Hit_accession').text,
            'Hit Length': hit.find('Hit_len').text,
            'Hsp Number': hit.find('.//Hsp_num').text,
            'Hsp Bit Score': hit.find('.//Hsp_bit-score').text,
            'Hsp Score': hit.find('.//Hsp_score').text,
            'Hsp E-value': hit.find('.//Hsp_evalue').text,
            'Hsp Query From': hit.find('.//Hsp_query-from').text,
            'Hsp Query To': hit.find('.//Hsp_query-to').text,
            'Hsp Hit From': hit.find('.//Hsp_hit-from').text,
            'Hsp Hit To': hit.find('.//Hsp_hit-to').text,
            'Hsp Query Frame': hit.find('.//Hsp_query-frame').text,
            'Hsp Hit Frame': hit.find('.//Hsp_hit-frame').text,
            'Hsp Identity': hit.find('.//Hsp_identity').text,
            'Hsp Positive': hit.find('.//Hsp_positive').text,
            'Hsp Gaps': hit.find('.//Hsp_gaps').text,
            'Hsp Alignment Length': hit.find('.//Hsp_align-len').text,
        }
        result_data.append(hit_info)

    # Create a DataFrame with column names
    column_names = [
        'Hit Number', 'Hit ID', 'Hit Definition', 'Hit Accession', 'Hit Length',
        'Hsp Number', 'Hsp Bit Score', 'Hsp Score', 'Hsp E-value',
        'Hsp Query From', 'Hsp Query To', 'Hsp Hit From', 'Hsp Hit To',
        'Hsp Query Frame', 'Hsp Hit Frame', 'Hsp Identity', 'Hsp Positive',
        'Hsp Gaps', 'Hsp Alignment Length'
    ]
    
    result_df = pd.DataFrame(result_data, columns=column_names)
    # print(result_df)
    return result_df
