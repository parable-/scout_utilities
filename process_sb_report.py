#!/usr/bin/env python3

import os
import re
import sys
import argparse
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# TODO:
#   - Add merit badge information (?).
#   - Align requirement columns (e.g. some scouts have "6a"/"6b" and others only "6").

# In report builder:
#   - Select scouts.
#   - For each "Scout Rank" check "Rank Status" and the "<rank> Requirements" boxes.
#   - Under Settings:
#       - Check "Show Dates"
#       - Check "Show Requirement Descriptions"
#       - Check "Show Empty Requirements"
#       - Check "Show Current Rank"
#       - Check "Show DOB"
#       - Check "Show Age"

class PlotScoutAdvancement:

    # Most recently exported file.
    #data_file = 'ReportBuilder_Troop0318B_Rank_Requirements_20231119.csv'
    #data_file = 'ReportBuilder_Troop0318B_Rank_Requirements_20240429.csv'

    # Requiremts that have minimum durations.
    rank_progression = ('Scout', 'Tenderfoot', 'Second Class', 'First Class', 'Star Scout', 'Life Scout', 'Eagle Scout')
    req_min_durations = {
        'Scout':        dict(),
        'Tenderfoot':   {'1b':   2, '6c': 30},
        'Second Class': {'1a':   7, '7a': 30},
        'First Class':  {'1a':  13},
        'Star Scout':   {'1':  122},
        'Life Scout':   {'1':  183},
        'Eagle Scout':  {'1':  183},
        }
    do_req_where = {
        'do at meetings': {
            'Scout':        {'1a', '1b', '1c', '1d', '1e', '1f', '2a', '2b', '2c', '2d', '3a', '3b', '4a', '4b', '5', '6b'},
            'Tenderfoot':   {'2c', '3a', '3b', '3c', '4a', '4b', '4c', '5a', '5b', '5c', '5d', '6a', '6b', '6c', '8', '9'},
            'Second Class': {'2a', '2f', '2g', '3a', '3c', '5a','5d','6a', '6b', '6c', '6d', '6e', '7b', '8b', '9a', '9b'},
            'First Class':  {'2a', '2b', '2c', '3a', '3b', '3c', '5b', '5c', '5d', '6b', '7a', '7b', '7c', '7d', '7e', '7f', '8b'},
            'Star Scout':   {'1', '5'},
            'Life Scout':   {'1', '5', '6'},
            'Eagle Scout':  {'1', '4'},
            },
        'do as homework': {
            'Scout':        {'6', '6a', '6b'},
            'Tenderfoot':   {'1a', '4d', '7b'},
            'Second Class': {'1a', '7a', '7c', '8c', '8d', '8e', '10'},
            'First Class':  {'8a', '9a', '9b', '9d', '10', '11'},
            'Star Scout':   {'2', '3', '4', '6'},
            'Life Scout':   {'2', '3', '4'},
            'Eagle Scout':  {'2', '3', '5'},
            },
        'do on outings': {
            'Scout':        set(),
            'Tenderfoot':   {'1b', '1c', '2a', '2b', '3d', '7a'},
            'Second Class': {'1b', '1c', '2b', '2c', '2d', '2e', '3b', '3d' '4', '5b', '5c', '8a'},
            'First Class':  {'1a', '1b', '2d', '2e', '3d', '4a', '4b', '5a', '6a', '6c', '6d', '6e', '9c'},
            'Star Scout':   {},
            'Life Scout':   {},
            'Eagle Scout':  {},
            },
        }

    def __init__(self, csv_file, obscure_names):
        '''Constructor.'''

        # Check the file.
        self.csv_file = csv_file
        self.obscure_names = obscure_names
        assert os.path.isfile(csv_file), \
            f'[ERROR] Can\'t find file "{self.csv_file}".'

        # Get the report date.
        match = re.search('(?P<year>\d\d\d\d)(?P<month>\d\d)(?P<day>\d\d)', csv_file)
        assert match, \
            f'ERROR Couldn\'t get report date from "{csv_file}".'
        self.report_date = (match.group('year'), match.group('month'), match.group('day'))

    # Assumes the CSV file was created with these options in ScoutBook.
    def read_data(self):
        '''Read the advancement CSV file.'''

        def capitalize_name(scout_name):
            '''Capitalize the first letter of name and lower-case other letters if preceeded by a letter.'''
            capitalized_name = ''
            for name_letter in scout_name:
                if re.match('[a-zA-Z]', name_letter) and re.match('[a-zA-Z]', capitalized_name[-1:]):
                    capitalized_name += name_letter.lower()
                else:
                    capitalized_name += name_letter.upper()
            return capitalized_name

        # Read in the data.
        aged_out = set()
        scout_names = None
        current_rank = None
        self.data_dict = dict()
        self.req_check = dict()
        with open(self.csv_file, 'r') as dF:
            for index, line in enumerate(dF):
                line_tokens = re.sub('"', '', line.strip()).split(',')

                # Check for version line.
                match_version_line = re.search('(?P<rank>.*) (?P<version>v\d\d\d\d)', line_tokens[0])
                match_req_line = re.match('(?P<req>\d+[a-z]?)\.', line_tokens[0])

                # Names are in the first line.
                if index == 0:
                    scout_names = [capitalize_name(x) for x in line_tokens[1:]]
                    for scout_name in scout_names:
                        self.data_dict[scout_name] = dict()

                # Date of birth is in the second line.
                elif line_tokens[0] == 'DOB':
                    for index, scout_name in enumerate(scout_names):
                        self.data_dict[scout_name]['dob'] = line_tokens[index + 1]

                # Age is in the third line.
                elif line_tokens[0] == 'Age':
                    for index, scout_name in enumerate(scout_names):
                        self.data_dict[scout_name]['age'] = line_tokens[index + 1]
                        if int(self.data_dict[scout_name]['age']) >= 18: aged_out.add(scout_name)

                # Current rank is in the fourth line.
                elif line_tokens[0] == 'Current Rank':
                    for index, scout_name in enumerate(scout_names):
                        if   re.match('1st', line_tokens[index + 1]): line_tokens[index + 1] = 'First Class'
                        elif re.match('2nd', line_tokens[index + 1]): line_tokens[index + 1] = 'Second Class'
                        self.data_dict[scout_name]['rank'] = line_tokens[index + 1]
                        for scout_rank in type(self).rank_progression:
                            self.data_dict[scout_name][scout_rank] = dict()

                # Add the rank status.
                elif line_tokens[0] in type(self).rank_progression:
                    for index, scout_name in enumerate(scout_names):
                        self.data_dict[scout_name][line_tokens[0]]['award'] = line_tokens[index + 1]

                # Process rank version requirements.
                elif match_version_line:
                    scout_rank = match_version_line.group('rank')
                    req_version = match_version_line.group('version')
                    for index, scout_name in enumerate(scout_names):
                        if line_tokens[index + 1]:
                            self.data_dict[scout_name][scout_rank]['version'] = req_version
                            self.data_dict[scout_name][scout_rank]['reqs'] = list()

                # Add the requirement.
                elif match_req_line:

                    # To color unrecorded requirements.
                    rank_index = type(self).rank_progression.index(scout_rank)

                    # Add the requirement if the versions match.
                    for index, scout_name in enumerate(scout_names):
                        if 'version' in self.data_dict[scout_name][scout_rank] and \
                           self.data_dict[scout_name][scout_rank]['version'] == req_version:
                            req_status = [match_req_line.group('req'), line_tokens[index + 1]]

                            # Update requirement status if not recorded but rank awarded.
                            rank_index_cur = 0
                            if self.data_dict[scout_name]['rank']:
                                rank_name = self.data_dict[scout_name]['rank']
                                if rank_name in ('Star', 'Life', 'Eagle'): rank_name += ' Scout'
                                rank_index_cur = type(self).rank_progression.index(rank_name)
                            if rank_index < rank_index_cur and not req_status[1]:
                                req_status[1] = True
                            self.data_dict[scout_name][scout_rank]['reqs'].append(req_status)

                    # Build database to check for requirement renames or additions across versions.
                    if scout_rank not in self.req_check:
                        self.req_check[scout_rank] = dict()
                    if req_status[0] not in self.req_check[scout_rank]:
                        self.req_check[scout_rank][req_status[0]] = list()
                    self.req_check[scout_rank][req_status[0]].append(re.sub(req_status[0] + '\. ', '', line_tokens[0].strip()))

        # Remove scouts that have aged out.
        for scout_name in aged_out:
            del self.data_dict[scout_name]

        # Get maximum widths.
        self.max_name_len = max([len(x) for x in self.data_dict])
        self.max_rank_len = max([len(x) for x in type(self).rank_progression])

        # Check for missing data.

        # Get scout rank order from number of completed requirements.
        rank_req_complete = dict()
        for scout_name in sorted(self.data_dict):
            rank_req_complete[scout_name] = 0
            for scout_rank in type(self).rank_progression:
                for req_spec in self.data_dict[scout_name][scout_rank]['reqs']:
                    if req_spec[1]: rank_req_complete[scout_name] += 1
        self.scout_order = tuple(x for x in sorted(rank_req_complete, reverse=True, key=lambda x:rank_req_complete[x]))

    def dump_data(self):
        '''Dump the database.'''

        # Print requirements that differ between versions.
        #for scout_rank in self.req_check:
        #    print(scout_rank)
        #    for req in self.req_check[scout_rank]:
        #        if len(set(self.req_check[scout_rank][req])) > 1 or len(self.req_check[scout_rank][req]) in (0, 1):
        #            print(' ', req, self.req_check[scout_rank][req])

        # Print the data.
        for scout_name in sorted(self.data_dict):
            print(f'Scout: {scout_name}, {self.data_dict[scout_name]["age"]}, {self.data_dict[scout_name]["dob"]}:')
            print(f'  Current Rank: {self.data_dict[scout_name]["rank"]}')
            for scout_rank in type(self).rank_progression:
                rank_data = list()
                rank_data_str = ''
                rank_award = False

                # Create string for rank requirements version.
                if self.data_dict[scout_name][scout_rank]:
                    rank_data.append(f'{self.data_dict[scout_name][scout_rank]["version"]}')

                # Create string for when rank was awarded.
                if 'award' in self.data_dict[scout_name][scout_rank] and \
                   re.match('\d+/\d+/\d+', self.data_dict[scout_name][scout_rank]['award']):
                    rank_data.append(f'completed {self.data_dict[scout_name][scout_rank]["award"]}')
                    rank_award = True

                # Print the rank and requirements.
                if rank_data: rank_data_str = ' (' + ', '.join(rank_data) + ')'
                print(f'  {scout_rank} Requirements{rank_data_str}:')

                # Print the individual requirements.
                req_specs = (x for x in sorted(self.data_dict[scout_name][scout_rank]['reqs'], key=lambda x:int(re.sub('[a-z]*', '', x[0]))))
                reqs_done = list()
                reqs_remain = list()
                for req_spec in req_specs:
                    if rank_award or req_spec[1]: reqs_done.append(req_spec[0])
                    else:                         reqs_remain.append(req_spec[0])
                print(f'    ', ', '.join(reqs_done), ' | ', ', '.join(reqs_remain))

    # Plot characteristics.
    #   - Since everyone's 18th birthday is different, draw a timeline for each scout working back from Eagle.
    #   - Assume requirements take at least one day.
    #
    #                               Scout Tenderfoot ...   Scout Tenderfoot ...
    # <scout name>  <current rank>  <ranks completed>    # <ranks remaining>    #     #     #    #     #
    #                                                    ^                      ^     ^     ^    ^     ^
    #                                                    |                      |     |     |    |     |
    #                               current date --------'                      |     |     |    |     |
    #                       Tenderfoot for Eagle -------------------------------'     |     |    |     |
    #                     Second Class for Eagle -------------------------------------'     |    |     |
    #                      First Class for Eagle -------------------------------------------'    |     |
    #                       Star Scout for Eagle ------------------------------------------------'     |
    #                       Life Scout for Eagle ------------------------------------------------------'
    def plot_advancement(self):
        '''Plot the advancement data.'''


        # Get minimum number of days.
        min_rank_times = dict()
        rank_req_count = dict()
        for scout_name in sorted(self.scout_order):

            # Get the rank advancement information.
            for scout_rank in type(self).rank_progression:

                # Initialize time to zero.
                rank_time = 0

                # Add rank times.
                for req_spec in self.data_dict[scout_name][scout_rank]['reqs']:
                    if req_spec[0] in type(self).req_min_durations[scout_rank]:
                        rank_time += type(self).req_min_durations[scout_rank][req_spec[0]]
                    elif not re.search(' Scout', scout_rank):
                        rank_time += 1

                # Add the time. Notes that some versions have more requirements than others.
                if scout_rank not in min_rank_times or rank_time > min_rank_times[scout_rank]:
                    min_rank_times[scout_rank] = rank_time

                # Count the requirements.
                req_count = len(self.data_dict[scout_name][scout_rank]['reqs'])
                if scout_rank not in rank_req_count or req_count > rank_req_count[scout_rank]:
                    rank_req_count[scout_rank] = req_count

        # Start the plot.
        margin_pix = 60
        line_pix = 20
        req_pix = 15
        rank_width = self.max_rank_len * 12
        name_width = self.max_name_len * 12
        height = 4 * margin_pix + 3 * line_pix * len(self.scout_order)
        width = 2 * margin_pix + name_width + (rank_req_count['Second Class'] + rank_req_count['First Class']) * req_pix
        image_size = (width, height)

        # Set up fonts.
        title_font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Andale Mono.ttf', 24)
        line_font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Andale Mono.ttf', 16)
        rank_font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Courier New Bold.ttf', 14)
        req_font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Andale Mono.ttf', 10)

        def plot_rank_col(scout_rank, row_offset, col_offset):
            '''Plot the rank column with complete or incomplete requirements.'''

            # Print the rank.
            draw_image.text((col_offset, row_offset - 20), scout_rank, font=rank_font, fill='black')

            # Print the requirements.
            for index_scout, scout_name in enumerate(self.scout_order):

                # Sort the requirements by number first.
                req_specs = (x for x in sorted(self.data_dict[scout_name][scout_rank]['reqs'], key=lambda x:int(re.sub('[a-z]*', '', x[0]))))

                # Loop on requirements.
                for index_req, req_spec in enumerate(req_specs):
                    req_offset = (col_offset + index_req * req_pix, row_offset + index_scout * line_pix)

                    # Color the requirement if it is awarded or scout is past that rank or is time limiting.
                    fill_color = None
                    outline_color = None
                    if self.data_dict[scout_name][scout_rank]['reqs'][index_req][1]: fill_color = 'palegreen'
 
                    # If the requirement is not completed, add other colors or outlines.
                    else:

                        # Colorize requirements for where they can be done.
                        if   req_spec[0] in type(self).do_req_where['do at meetings'][scout_rank]: fill_color = 'azure'
                        elif req_spec[0] in type(self).do_req_where['do as homework'][scout_rank]: fill_color = 'cornsilk'
                        elif req_spec[0] in type(self).do_req_where['do on outings'][scout_rank]:  fill_color = 'lavenderblush'

                        # Outline requirements that have time durations.
                        if req_spec[0] in type(self).req_min_durations[scout_rank]: outline_color = 'red'

                    # Add fill and outline.
                    if fill_color is not None:
                        draw_image.rectangle((req_offset, (req_offset[0] + req_pix - 1, req_offset[1] + req_pix)), fill=fill_color, outline=outline_color)

                    # Add requirement reference.
                    draw_image.text((req_offset[0] + 1, req_offset[1] + 1), f'{req_spec[0]:>2s}', font=req_font, fill='black')

            # Calculate the column width.
            col_width = max(req_pix * rank_req_count[scout_rank], len(scout_rank) * 12) + 10
            return col_width

        # Create the image.
        image = Image.new('RGB', image_size, 'white')
        draw_image = ImageDraw.Draw(image)

        # Add the title.
        title_text = f'Scout Advancement and Eagle Timeline ({self.report_date[1]}/{self.report_date[2]}/{self.report_date[0]})'
        draw_image.text((2 * margin_pix, margin_pix // 3), title_text, font=title_font, fill='black')

        # Add the scout names and current rank.
        col_offset = margin_pix
        row_offset = 1.5 * margin_pix
        for index, scout_name in enumerate(self.scout_order):
            draw_image.text((col_offset + name_width, row_offset + index * line_pix), self.data_dict[scout_name]['rank'], font=line_font, fill='black')
            if self.obscure_names: scout_name = f'SCOUT NAME {index}'
            draw_image.text((col_offset, row_offset + index * line_pix), scout_name, font=line_font, fill='black')
        col_offset += name_width + rank_width

        # Add the ranks.
        for scout_rank in type(self).rank_progression:

            # Reset the row and add names agein.
            if scout_rank in ('Second Class', 'Star Scout'):

                # Reset the offsets.
                col_offset = margin_pix
                row_offset += margin_pix // 2 + len(self.scout_order) * line_pix

                # Add the names back.
                for index, scout_name in enumerate(self.scout_order):
                    if self.obscure_names: scout_name = f'SCOUT NAME {index}'
                    draw_image.text((col_offset, row_offset + index * line_pix), scout_name, font=line_font, fill='black')
                col_offset += name_width

            # Add the rank.
            col_offset += plot_rank_col(scout_rank, row_offset, col_offset)

        # Add the number of days until Eagle is impossible.
        draw_image.text((col_offset, row_offset - 20), 'Eagle is Impossible Unless', font=rank_font, fill='black')
        for index, scout_name in enumerate(self.scout_order):
            remain_rank_days = 0

            # Skip the rank they're currently working on.
            current_rank = self.data_dict[scout_name]['rank']
            if current_rank in ('Star', 'Life', 'Eagle'): current_rank += ' Scout'
            rank_index = 0
            if current_rank in type(self).rank_progression:
                rank_index = type(self).rank_progression.index(current_rank) + 1
            next_rank = type(self).rank_progression[rank_index]

            # Add days for requirements not completed.
            for scout_rank in type(self).rank_progression:
                if scout_rank == next_rank: continue
                for req_spec in self.data_dict[scout_name][scout_rank]['reqs']:
                    if not req_spec[1] and req_spec[0] in type(self).req_min_durations[scout_rank]:
                        remain_rank_days += type(self).req_min_durations[scout_rank][req_spec[0]]

            # Subtract from 18th birthday.
            dob_list = [int(x) for x in self.data_dict[scout_name]['dob'].split('/')]
            dob_list[2] += 2000 + 18
            age_out_date = datetime(dob_list[2], dob_list[0], dob_list[1])
            eagle_impossible = age_out_date - timedelta(days=remain_rank_days)

            # Add string to plot.
            if current_rank == 'Life Scout':
                eagle_str = 'Complete'
                remain_rank_days = (age_out_date - datetime.now()).days
            else:
                eagle_str = 'Advance'
            eagle_str += ' by {}, {} days remaining'.format(eagle_impossible.strftime('%Y_%m_%d'), remain_rank_days)
            draw_image.text((col_offset, row_offset + index * line_pix), eagle_str, font=req_font, fill='red')

        # Add color legend.
        legend_x, legend_y = image_size[0] - 5 * margin_pix, image_size[1] - 3 * margin_pix
        draw_image.rectangle((legend_x, legend_y, legend_x + 4 * margin_pix, legend_y + 2 * margin_pix), width=2, outline='black')
        x_off, y_off = legend_x + 15, legend_y + 15
        for row_off in range(4):
            fill_color, outline_color, row_text = {
                0: ('azure',         'black', 'Do at Meetings'),
                1: ('cornsilk',      'black', 'Do as Homework'),
                2: ('lavenderblush', 'black', 'Do on Outings'),
                3: (None,            'red',   'Has Time Requirement')
                }[row_off]
            draw_image.rectangle((x_off, y_off, x_off + 20, y_off + 20), fill=fill_color, outline=outline_color)
            draw_image.text((x_off + 30, y_off), row_text, font=rank_font, fill='black')
            y_off += 25

        # Save the image.
        image_name = f'scout_advancement.png'
        image.save(image_name, 'PNG')

    def plot_trip_template(self):
        '''Create trip checklist image.'''

        # Title text.
        title_text = 'Troop Checklist - EVENT ____________________________   START _________  END _________   EST COST $_____   ACT COST $_____'

        # Headings.
        heading_list = (
            ('', 'Scout Name'),
            ('Interest', '  Y/N'),
            ('Commit', ' Y/N'),
            ('Medical', 'A/B  C',),
            ('  Paid ',),
            ('Consent', ' Form',),
            (' Other', 'Form(s)',),
            ('', 'Age '),
            ('  Tent #', 'Assignment',),
            ('       Cleanup Assignment' + ' ' * 20, '     (tent #, bin, stove, etc.)',),
            ('Equipment', 'Returned',),
            )

        # Get the column widths based on the length of the string.
        max_col_widths = list()
        for heading_spec in heading_list:
            max_col_widths.append(max([len(x) for x in heading_spec]))
        max_col_widths[0] = max(max_col_widths[0], self.max_name_len)

        # Set the indices for which columns get boxes or lines.
        form_offsets = (
            (1, 'box'),
            (2, 'box'),
            (3, 'boxes'),
            (4, 'box'),
            (5, 'box'),
            (6, 'box'),
            (7, 'age'),
            (8, 'line'),
            (9, 'line'),
            (10, 'box'),
            )

        # Start the plot.
        margin_pix = 60
        line_pix = 50
        char_width = 13
        leader_count = 4

        # Note blank lines added for leaders.
        height = 4 * margin_pix + line_pix * (len(self.scout_order) + leader_count)
        width = 2 * margin_pix + max(sum([x * char_width for x in max_col_widths]), len(title_text) * (char_width + 3))
        image_size = (width, height)

        # Create the image.
        image = Image.new('RGB', image_size, 'white')
        draw_image = ImageDraw.Draw(image)

        # Set up fonts.
        title_font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Andale Mono.ttf', 24)
        header_font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Andale Mono.ttf', 16)
        line_font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Andale Mono.ttf', 20)

        # Add the title.
        draw_image.text((margin_pix, margin_pix // 2), title_text, font=title_font, fill='black')

        # Add the header information.
        col_offset = margin_pix
        row_offset = 1.5 * margin_pix
        for index, header_spec in enumerate(heading_list):
            draw_image.text((col_offset, row_offset), header_spec[0], font=header_font, fill='black')
            if len(header_spec) > 1:
                draw_image.text((col_offset, row_offset + line_pix // 2), header_spec[1], font=header_font, fill='black')
            col_offset += max_col_widths[index] * char_width

        # Add the scout names.
        col_offset = margin_pix
        row_offset = 2 * 1.5 * margin_pix
        for index, scout_name in enumerate(sorted(self.data_dict)):

            # Obscure data.
            if self.obscure_names:
                scout_name = f'SCOUT NAME {index}'
                scout_age = '##'

            # Add scout name.
            draw_image.text((col_offset, row_offset + index * line_pix), scout_name, font=line_font, fill='black')

            # Add scout age.
            scout_age = f'{self.data_dict[scout_name]["age"]}'
            draw_image.text((col_offset + sum(max_col_widths[:7]) * char_width, row_offset + index * line_pix), scout_age, font=line_font, fill='black')


        # Add some blank lines for leaders.
        for index in range(leader_count):
            draw_image.text((col_offset, row_offset + (index + len(self.scout_order)) * line_pix), '_' * max_col_widths[0], font=line_font, fill='black')
        col_offset += max_col_widths[0] * char_width

        # Add checkboxes and form lines
        row_offset = 2 * 1.5 * margin_pix
        for row_index in range(len(self.data_dict) + leader_count):
            col_offset = margin_pix + max_col_widths[0] * char_width
            for col_index, form_element in form_offsets:

                # One checkbox.
                if form_element == 'box':
                    box_coords = [(col_offset + 2 * char_width, row_offset + row_index * line_pix)]
                    box_coords.append((box_coords[0][0] + char_width, box_coords[0][1] + char_width))
                    draw_image.rectangle(box_coords, outline='black')

                # One checkbox.
                elif form_element == 'boxes':
                    for index in range(2):
                        box_coords = [(col_offset + char_width // 2 + 3 * index * char_width, row_offset + row_index * line_pix)]
                        box_coords.append((box_coords[0][0] + char_width, box_coords[0][1] + char_width))
                        draw_image.rectangle(box_coords, outline='black')

                # Underline.
                elif form_element == 'line':
                    box_coords = [(col_offset, row_offset + row_index * line_pix + 2 * char_width)]
                    box_coords.append((box_coords[0][0] + (max_col_widths[col_index] - 3) * char_width, box_coords[0][1]))
                    draw_image.line(box_coords, fill='black')

                # Go to the next column.
                col_offset += max_col_widths[col_index] * char_width

        # Save the image.
        image_name = f'event_checklist.png'
        image.save(image_name, 'PNG')

def main(sysargs):
    '''For command line running and testing.'''

    # Create the argument parser.
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    parser.add_argument('--dump', action='store_true')
    parser.add_argument('--plot', action='store_true')
    parser.add_argument('--obscure', action='store_true')
    args = parser.parse_args(sysargs)

    # Instance class and create plots.
    plot_scout_advancement = PlotScoutAdvancement(args.file, args.obscure)
    plot_scout_advancement.read_data()
    plot_scout_advancement.plot_advancement()
    plot_scout_advancement.plot_trip_template()
    if args.dump: plot_scout_advancement.dump_data()

if __name__ == '__main__':
    main(sys.argv[1:])
