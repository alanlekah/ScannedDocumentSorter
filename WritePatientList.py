import cdb
import sys
import os

PATIENT_SCAN_DIR = "E:\Patient Scans\Patient Scans"
PATIENT_DB_LIST = "patients.xdb"

def read_folder(folder_title):
    name_array = []
    comma_count = folder_title.find(',')
    name_array.append(folder_title[0:comma_count]) # Last Name
    space_count = folder_title.find(' ', comma_count+2)
    name_array.append(folder_title[comma_count+2:space_count]) # First Name
    underscore_count = folder_title.find('_', space_count)
    if folder_title[space_count+1:underscore_count-1] != ' ':
        name_array.append(folder_title[space_count+1:underscore_count-1]) # Middle Name
    else:
        name_array.append('')
    second_space_count = folder_title.find(' ', underscore_count)
    name_array.append(folder_title[second_space_count+1:]) # DOB
    print name_array
    return name_array
    
def write_patient(last_name, first_name, middle_name, dob):
    db.update_db({last_name:first_name}, PATIENT_DB_LIST)

if "__main__" == __name__:
    db = cdb
    db.check_db(PATIENT_DB_LIST)
    for directories in os.listdir(PATIENT_SCAN_DIR):
        for patients in os.listdir(PATIENT_SCAN_DIR + "/" + directories):
            name_arr = read_folder(patients)
            write_patient(name_arr[0], name_arr[1], name_arr[2], name_arr[3])
            print "Successfully added '%s, %s, %s, %s' to database!" % (name_arr[0], name_arr[1], name_arr[2], name_arr[3])
        
        

