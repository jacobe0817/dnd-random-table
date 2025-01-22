from pathlib import Path
import re
from datetime import datetime
import random
import pandas
import pyinputplus

excel_file_path = Path('random_fantasy_table.xlsx')
log_folder_path = Path('logs')
excel_sheet_name = 'source'
category_regex = re.compile(r'^category \d+$', re.IGNORECASE)
description_column_name = 'description'
skip_subcategory_string = 'NONE'

# returns a list of all values visible in the specified column, applying filters to any category columns {category column name : filtered value}
def get_visible_column_values(df, column_header, filters_by_category=dict()):
    list_of_filtered_sets = [set(df[column_header])]
    for category in filters_by_category.keys():
        new_set = set(df[df[category] == filters_by_category[category]][column_header])
        list_of_filtered_sets.append(new_set)
    return_list = list(set.intersection(*list_of_filtered_sets))
    return_list.sort()
    return return_list

# generates prompt based on dictionary of acceptable inputs : display values
def generate_prompt(acceptable_inputs_to_display_values_dict, line_break_index=None):
    prompt = '\n  select one of the following:\n'
    dict_keys = list(acceptable_inputs_to_display_values_dict.keys())
    for key, i in zip(dict_keys, list(range(len(dict_keys)))):
        number_of_spaces = 5 - len(key)
        if line_break_index is not None and i == line_break_index:
            prompt += '\n' + ' ' * number_of_spaces + key + ') ' + acceptable_inputs_to_display_values_dict[key] + '\n'
        else:
            prompt += ' ' * number_of_spaces + key + ') ' + acceptable_inputs_to_display_values_dict[key] + '\n'
    prompt += '\n  > '
    return prompt

# returns the user input and display value for a list of display values
def choose_value_from_category(display_values):
    acceptable_inputs_to_display_values_dict = {str(i + 1) : display_values[i] for i in range(len(display_values))}
    acceptable_inputs_to_display_values_dict['s'] = 'start over'
    acceptable_inputs_to_display_values_dict['q'] = 'quit'
    prompt = generate_prompt(acceptable_inputs_to_display_values_dict, len(display_values))
    user_input = pyinputplus.inputChoice(list(acceptable_inputs_to_display_values_dict.keys()), prompt)
    return user_input, acceptable_inputs_to_display_values_dict[user_input]

# returns the user input and display value for available choices
def choose_next_category_roll_start_over_or_quit(selected_category_display_value, valid_sub_categories=list()):
    acceptable_inputs_to_display_values_dict = {str(i + 1) : valid_sub_categories[i] for i in range(len(valid_sub_categories))}
    acceptable_inputs_to_display_values_dict['r'] = 'roll for ' + selected_category_display_value
    acceptable_inputs_to_display_values_dict['s'] = 'start over'
    acceptable_inputs_to_display_values_dict['q'] = 'quit'
    if len(valid_sub_categories) > 0:
        prompt = generate_prompt(acceptable_inputs_to_display_values_dict, len(valid_sub_categories))
    else:
        prompt = generate_prompt(acceptable_inputs_to_display_values_dict)
    user_input = pyinputplus.inputChoice(list(acceptable_inputs_to_display_values_dict.keys()), prompt)
    return user_input, acceptable_inputs_to_display_values_dict[user_input]

def choose_accept_roll_reroll_start_over_or_quit():
    acceptable_display_values = ['accept roll', 'reroll', 'start over', 'quit']
    acceptable_inputs_to_display_values_dict = {value[0] : value for value in acceptable_display_values}
    prompt = generate_prompt(acceptable_inputs_to_display_values_dict)
    user_input = pyinputplus.inputChoice(list(acceptable_inputs_to_display_values_dict.keys()), prompt)
    return user_input, acceptable_inputs_to_display_values_dict[user_input]

def roll(df, column_header, filters_by_category=dict()):
    visible_column_values = get_visible_column_values(df, column_header, filters_by_category)
    return random.choice(visible_column_values)

def print_rolled_value(rolled_value):
    print('\n  ' + '-' * len(rolled_value) + '\n  ' + rolled_value + '\n  ' + '-' * len(rolled_value))

# closes log file connection and ends program
def end_program(log_file):
    print()
    log_file.close()
    quit()


def main():
    # generate a random seed based on date time value
    now = datetime.now()
    epoch = datetime(1970, 1, 1)
    delta = (now - epoch).total_seconds()

    random.seed(delta)

    # load data from excel file
    df = pandas.read_excel(excel_file_path, sheet_name=excel_sheet_name)
    df = df.astype(str)

    # create list of category column headers
    categories = [list(category_regex.finditer(column_header))[0][0] for column_header in list(df.columns) if len(list(category_regex.finditer(column_header))) == 1]

    # create a log file for today's date if one does not already exist and establish txt file connection
    target_log_file_name = now.strftime('%Y_%m_%d') + '.txt'
    target_log_file_path = Path(log_folder_path, target_log_file_name)

    if not target_log_file_path.is_file():
        log_file = open(target_log_file_path, 'a')
        log_file.write('==================== ' + now.strftime('%m/%d/%Y %H:%M:%S') + ' ====================\n\n')
    else:
        log_file = open(target_log_file_path, 'a')

    # main program loop
    category_index = 0
    filters_by_category = dict()
    print('  ' + '-' * 100)

    while True:
        # if there is not a filter on the current category column, get one
        if categories[category_index] not in list(filters_by_category.keys()):
            visible_column_values = get_visible_column_values(df, categories[category_index], filters_by_category)
            user_input, display_value = choose_value_from_category(visible_column_values)

            if user_input == 's':
                category_index = 0
                filters_by_category = dict()
                print('\n  ' + '-' * 100)
                continue

            if user_input == 'q':
                end_program(log_file)
            
            filters_by_category[categories[category_index]] = display_value

        next_category_exists = len(categories) > category_index + 1
        if next_category_exists:
            subcategories = get_visible_column_values(df, categories[category_index + 1], filters_by_category)
            next_category_exists = next_category_exists and skip_subcategory_string not in subcategories

        if next_category_exists:
            user_input, display_value = choose_next_category_roll_start_over_or_quit(display_value, subcategories)

        if user_input == 'r' or not next_category_exists:
            while True:
                rolled_value = roll(df, description_column_name, filters_by_category)
                print_rolled_value(rolled_value)
                user_input, display_value = choose_accept_roll_reroll_start_over_or_quit()
                
                if user_input == 'a':
                    text_to_write_to_log = ' > '.join(list(filters_by_category.values())) + ' :\n' + rolled_value + '\n\n'
                    log_file.write(text_to_write_to_log)
                    break

                if user_input == 'r':
                    continue

                if user_input == 's':
                    break

                if user_input == 'q':
                    end_program(log_file)

        if user_input == 's' or user_input == 'a':
            category_index = 0
            filters_by_category = dict()
            print('\n  ' + '-' * 100)
            continue

        if user_input == 'q':
            end_program(log_file)

        else:
            category_index += 1
            filters_by_category[categories[category_index]] = display_value
            continue

main()