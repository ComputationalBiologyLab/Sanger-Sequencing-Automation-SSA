import xml.etree.ElementTree as ET
import pandas as pd

def get_results_for_nt(xml_file_path):
    try:
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
                'Hsp Identity': hit.find('.//Hsp_identity').text,
                'Hsp Positive': hit.find('.//Hsp_positive').text,
                'Hsp Gaps': hit.find('.//Hsp_gaps').text,
                'Hsp Align Len': hit.find('.//Hsp_align-len').text,
                'Hsp Qseq': hit.find('.//Hsp_qseq').text,
                'Hsp Hseq': hit.find('.//Hsp_hseq').text,
                'Hsp Midline': hit.find('.//Hsp_midline').text
            }
            result_data.append(hit_info)

        df = pd.DataFrame(result_data)
        return df

    except Exception as e:
        print(f"Error reading XML file {xml_file_path}: {e}")
        return pd.DataFrame()