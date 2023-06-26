import PySimpleGUI as sg
from JLFileHandler import FileHandler


file_handler = FileHandler()


def generate(jira_file: str, map_file: str, destination_folder: str, csv_file_name: str) -> None:
    if jira_file and map_file and destination_folder and csv_file_name:
        csv_file_path = f"{destination_folder}/{csv_file_name}"
        info = file_handler.generate_csv(jira_file, map_file, csv_file_path)
        sg.popup(info)
    else:
        sg.popup("You need to fill all the information above first!")


sg.theme('LightBrown3')  # Add a touch of color
layout = [[sg.Text('Wellcome to JiraLand!', size=(50, 1))],
          [sg.Input('Browse your Jira file here ...', disabled=True, disabled_readonly_background_color='#A7ECEE',
                    key='jira_file', size=(85, 1)), sg.FileBrowse()],
          [sg.Input('Browse your Map file here ...', disabled=True, disabled_readonly_background_color='#A7ECEE',
                    key='map_file', size=(85, 1)), sg.FileBrowse()],
          [sg.InputText('Choose a directory to save file.', disabled=True, disabled_readonly_background_color='#A7ECEE',
                    key='folder', size=(85, 1)), sg.FolderBrowse()],
          [sg.Input('Enter name of the csv file to be generated.', background_color='#A7ECEE', key='file_name')],
          [sg.Text('', size=(73, 1)), sg.Button('Generate')]]

# Create the Window
window = sg.Window('JiraLand', layout, size=(700, 200))
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:  # if user closes window
        break
    if event == 'Generate':
        if 'Choose a directory to save file.' in values.values():
            sg.Popup('You need to choose directory first!')
        else:
            generate(jira_file=values['jira_file'], map_file=values['map_file'], destination_folder=values['folder'],
                     csv_file_name=values['file_name'])
window.close()
