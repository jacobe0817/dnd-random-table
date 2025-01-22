import random
from datetime import datetime
from pathlib import Path
import openpyxl
import pyinputplus

excel_file_path = Path('Desktop', 'random_fantasy_table', 'random_fantasy_table.xlsx')
text_file_path = Path('Desktop', 'random_fantasy_table', 'random_fantasy_table.txt')
#source_excel_sheet_name = 'source'
escape_string = 'quit'

# generate a random seed based on date time value
dt = datetime.now()
epoch = datetime(1970, 1, 1)
delta = (dt - epoch).total_seconds()

random.seed(delta)

# connect to excel file
wb = openpyxl.open(excel_file_path)
ws = wb.active

# load a dictionary where key is column number and value is tuple (column header, list of cell values below header) from excel file
non_blank_cells_on_row_one = [cell for cell in ws[1] if cell.value is not None]
master_dict = { str(cell.column) : (cell.value, [_cell.value for _cell in ws[cell.column_letter] if _cell.value is not None and _cell.row != 1]) for cell in non_blank_cells_on_row_one}

# close excel file connection
wb.close()

# create text file connection and log date
text_file_log = open(text_file_path, 'a')
text_file_log.write('==================== ' + dt.strftime('%m/%d/%Y %H:%M:%S') + ' ====================\n')

# create prompt string
valid_inputs = list(master_dict.keys())
valid_inputs.append(escape_string)
prompt = '\nselect one of the following:'
for key in list(master_dict.keys()):
    prompt += '\n\t- ' + key + '. ' + master_dict[key][0]
prompt += '\n\t- ' + escape_string + '\n> '

# main program loop
while True:
    # prompt user to choose a category
    category_select_input = pyinputplus.inputChoice(choices=valid_inputs, prompt=prompt)
    if category_select_input == 'quit':
        break
    selected_list = master_dict[category_select_input][1]

    # if length of list is 0 report flawed excel file
    if len(selected_list) == 0:
        print('\nFLAWED EXCEL FILE: COLUMN PROVIDED WITH HEADER BUT 0 ROWS\nPLEASE SELECT A DIFFERENT COLUMN OR FIX THE EXCEL FILE\n')
        continue

    # catch error in interpretting one row columns as a 'min-max' int range
    if len(selected_list) == 1:
        try:
            min_max = selected_list[0].split('-')
            min_max = [int(value) for value in min_max]
            random.randint(min_max[0], min_max[1])
            
        except:
            print('\nFLAWED EXCEL FILE: COLUMN PROVIDED WITH HEADER AND EXACTLY 1 ROW BUT IT DOES NOT CONFORM TO THE REQUIRED "INT-INT" FORMAT\nPLEASE SELECT A DIFFERENT COLUMN OR FIX THE EXCEL FILE\n')
            continue

    while True:
        # print randomly selected value from int range or column of strings, depending on column type
        random_value = random.randint(min_max[0], min_max[1]) if len(selected_list) == 1 else random.choice(selected_list)
        equal_sign_border = '=' * len(random_value)
        print('\n' + equal_sign_border + '\n' + random_value + '\n' + equal_sign_border + '\n')

        # prompt for reroll or accept
        reroll_accept_input = pyinputplus.inputChoice(choices=['reroll', 'accept', 'r', 'a'], prompt='(r)eroll or (a)ccept random value:\n> ')
        if reroll_accept_input == 'accept' or reroll_accept_input == 'a':
            # write accepted value to a text file for record keeping
            text_file_log.write('\n' + master_dict[category_select_input][0] + ':\n' + str(random_value) + '\n\n')
            break

# close text file connection
text_file_log.close()