import re
import csv

PATIENT_DEMOGRAPHIC_DATABASE = "backup.csv"

def csv_find(last_name= '', first_name= '', middle_name= '', dob= ''):
    dataset = []
    with open(PATIENT_DEMOGRAPHIC_DATABASE, 'rt') as f:
         reader = csv.reader(f, delimiter=',')
         for row in reader:
              if ((last_name != '' and last_name.lower() in row[5].lower()) or
              (first_name != '' and first_name.lower() in row[3].lower()) or
              (middle_name != '' and middle_name.lower() in row[4].lower()) or
              (dob != '' and dob.lower() in row[8].lower())):
                  dataset.append(csv_collect(row))
         return dataset

def csv_collect(row):
    return {"last_name": row[5], "first_name": row[3], "middle_name": row[4], "dob": row[8]}



            
            
              
