import PySimpleGUI as sg
import glob
from os.path import exists
import pyperclip
import requests

profiles_path = glob.glob("./profiles/**")
profiles_dict = {}

directory_path = ""
selected_profile = ""

def load_option():
    global directory_path, selected_profile
    path = "./options.txt"
    if exists(path):
        with open(path) as f:
            directory_path, selected_profile = f.read().split("\n")

def save_option():
    with open("./options.txt", "w") as f:
        f.write("\n".join([directory_path, selected_profile]))

def load_profiles():
    for path in profiles_path:
        with open(f"{path}/info.txt") as f:
            profile_id, profile_name, modpack_version, info_url = f.read().split("\n")
            profiles_dict[profile_id] = {"name" : profile_name, "version" : float(modpack_version), "url" : info_url}


def add_profile(url):
    data = requests.get(url).content.decode()
    print(str((data)).split("\n"))


def main():
    global directory_path, selected_profile
    load_option()
    load_profiles()

    sg.theme("SystemDefault1")

    update_profile_tab = [[sg.Text("hi")],
                            [sg.Combo([profiles_dict[i]["name"] for i in list(profiles_dict)], key="-profile_combo-", default_value=selected_profile, size=50)],
                            [sg.Text("hi")]]

    add_profile_tab = [[sg.Text("URL")],
                       [sg.InputText(key="-add_profile_url-", size=40), sg.Button("貼り付け", key="-add_profile_url_paste-")],
                       [sg.Button("追加", key="-add_profile_accept-", disabled=False)]]

    option_tab = [[sg.Text("起動構成用のディレクトリ")],
                  [sg.InputText(key='-option_directory_path-', size=40, default_text=directory_path), sg.Button("貼り付け", key='-option_directory_path_paste-')]]

    layout = [[sg.TabGroup([[sg.Tab("Update Profile", update_profile_tab), sg.Tab("Add Profile", add_profile_tab), sg.Tab("Option", option_tab)]], size=(400, 525))],
            [sg.Button("Accept", key="-accept-"), sg.Button("Exit", key="-exit-")]]

    window = sg.Window("AutoSyncMCMODs", layout, size=(400,600))

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "-exit-":
            break

        elif event == "-accept-":
            selected_profile = values["-profile_combo-"]
            directory_path = values["-option_directory_path-"]
        
        elif event == "-add_profile_url_paste-":
            window["-add_profile_url-"].update(pyperclip.paste())
        elif event == "-option_directory_path_paste-":
            window["-option_directory_path-"].update(pyperclip.paste())
        
        elif event =="-add_profile_accept-":
            window["-add_profile_accept-"].update(disabled=True)
            add_profile(values["-add_profile_url-"])
    
    save_option()
    window.close()

main()