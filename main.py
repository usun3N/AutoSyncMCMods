import PySimpleGUI as sg
import glob
from os.path import exists
from os.path import basename
from os import mkdir
from os import makedirs
from os import remove
import pyperclip
import requests
import threading
import shutil

directory_path = ""
selected_profile = ""
profiles_path = glob.glob("./profiles/**")
profiles_dict = {}
update_mods = []


def load_option():
    global directory_path, selected_profile
    path = "./options.txt"
    if exists(path):
        with open(path) as f:
            directory_path, selected_profile = f.read().split("\n")
    else:
        with open(path, "w") as f:
            f.write("")


def save_option():
    with open("./options.txt", "w") as f:
        f.write("\n".join([directory_path, selected_profile]))


def load_profiles():
    global profiles_dict, dict_for_combo
    for path in profiles_path:
        with open(f"{path}/info.txt") as f:
            profile_id, profile_name, info_url, modpack_version = f.read().split("\n")[0:4]
            profiles_dict[profile_id] = {"name" : profile_name, "url" : info_url, "version" : modpack_version}
    dict_for_combo = {profiles_dict[i]["name"] : i for i in list(profiles_dict)}


def download_file(url, path):
    data = requests.get(url).content
    with open(path, "wb") as f:
        f.write(data)


def unpack_file(path, out):
    shutil.unpack_archive(path, out)
    remove(path)


def add_profile_thread(url, r_id, key):
    try:
        window[key].update("Downloading...")
        download_file(url, f"./profiles/{r_id}/mods.zip")
        window[key].update("Making Directory...")
        makedirs(f"{directory_path}/{r_id}/mods")
        window[key].update("Unpacking...")
        unpack_file(f"./profiles/{r_id}/mods.zip", f"{directory_path}/{r_id}/mods")  
        window[key].update("Profiles Reloading...")
        load_profiles()
        window[key].update("Success!")
    except:
        window[key].update("Failed")
    finally:
        window[key].update(disabled=False)
    

def add_profile(url):
    try:
        data = requests.get(url).content.decode()
        r_id, r_name, r_url, r_version = str((data)).split("\n")[0:4]
        w_data = "\n".join([r_id, r_name, url, r_version])
        mkdir(f"./profiles/{r_id}")
        with open(f"./profiles/{r_id}/info.txt", "w") as f:
            f.write(w_data)
    except:
        window["-add_profile_state-"].update("Failed")
        window["-add_profile_accept-"].update(disabled=False)
        return
    dl = threading.Thread(target=add_profile_thread, args=(r_url, r_id, "-add_profile_state-"),daemon=True)
    dl.start()

def update_thread(url, r_id, key, old_mods_list, info_url, r_name, r_version):
    global update_mods
    update_mods = []
    if exists(f"./profiles/{r_id}/mods.zip"):
        remove(f"./profiles/{r_id}/mods.zip")
    window[key].update("Downloading...")
    download_file(url, f"./profiles/{r_id}/mods.zip")
    window[key].update("Making Directory...")
    mkdir(f"./profiles/{r_id}/temp")
    window[key].update("Unpacking...")
    unpack_file(f"./profiles/{r_id}/mods.zip", f"./profiles/{r_id}/temp")
    new_mods_list = set([basename(i) for i in glob.glob(f"./profiles/{r_id}/temp/*")])
    add_mods = new_mods_list - old_mods_list
    del_mods = old_mods_list - new_mods_list
    for i in add_mods:
        window["-update_mods_list-"].print(f"added {i}")
        shutil.move(f"./profiles/{r_id}/temp/{i}", f"{directory_path}/{r_id}/mods")
    for i in del_mods:
        window["-update_mods_list-"].print(f"removed {i}")
        remove(f"{directory_path}/{r_id}/mods/{i}")
    
    shutil.rmtree(f"./profiles/{r_id}/temp")

    window[key].update("Updating infomation...")
    w_data = "\n".join([r_id, r_name, info_url, r_version])
    with open(f"./profiles/{r_id}/info.txt", "w") as f:
            f.write(w_data)
    
    window[key].update("Profiles Reloading...")
    load_profiles()
    window["-profile_name-"].update(profiles_dict[combo_id]["name"])
    window["-profile_id-"].update(combo_id)
    window["-profile_version-"].update(profiles_dict[combo_id]["version"])
    window["-update_check-"].update(disabled = False)
    window[key].update("Success!")


def check_update(id):
    o_name, o_url, o_version = profiles_dict[id]["name"], profiles_dict[id]["url"], profiles_dict[id]["version"]

    try:
        data = requests.get(o_url).content.decode()
        r_id, r_name, r_url, r_version = str((data)).split("\n")[0:4]
        if float(o_version) < float(r_version):
            window["-update_state-"].update("更新があります")
            old_mods_list = set([basename(i) for i in glob.glob(f"{directory_path}/{r_id}/mods/*")])
            dl = threading.Thread(target=update_thread, args=(r_url, r_id, "-update_state-", old_mods_list, o_url, r_name, r_version))
            dl.start()
        else:
            window["-update_state-"].update("最新の状態です")
    except:
        window["-update_state-"].update("Failed")
    window["-update_check-"].update(disabled=False)

def main():
    global window, directory_path, selected_profile, combo_id
    combo_disable_flag = False
    load_option()
    load_profiles()
    try:
        pl_name = profiles_dict[dict_for_combo[selected_profile]]["name"]
        pl_id = dict_for_combo[selected_profile]
        pl_version = profiles_dict[dict_for_combo[selected_profile]]["version"]
        combo_id = dict_for_combo[selected_profile]
    except KeyError:
        selected_profile = ""
        pl_name = ""
        pl_id = ""
        pl_version = ""
        combo_disable_flag = True


    sg.theme("SystemDefault1")
    
    update_profile_tab = [[sg.Text("利用する起動構成を選択")],
                            [sg.Combo([profiles_dict[i]["name"] for i in list(profiles_dict)], key="-profile_combo-" ,enable_events=True, default_value=selected_profile, size=50)],
                            [sg.Text("Name:",size=6), sg.Text(pl_name, key="-profile_name-",)],
                            [sg.Text("ID:",size=6), sg.Text(pl_id, key="-profile_id-")],
                            [sg.Text("Version:",size=6), sg.Text(pl_version, key="-profile_version-")],
                            [sg.Button("更新をチェック", key="-update_check-", disabled=False), sg.Text("", key="-update_state-")],
                            [sg.Multiline("",size=(400, 300), key="-update_mods_list-")]]

    add_profile_tab = [[sg.Text("URL")],
                       [sg.InputText(key="-add_profile_url-", size=40), sg.Button("貼り付け", key="-add_profile_url_paste-")],
                       [sg.Button("追加", key="-add_profile_accept-", disabled=False)],
                       [sg.Text("", key="-add_profile_state-")]]

    option_tab = [[sg.Text("起動構成用のディレクトリ")],
                  [sg.InputText(key='-option_directory_path-', size=40, default_text=directory_path), sg.Button("貼り付け", key='-option_directory_path_paste-')],
                  [sg.Button("保存", key="-accept-")]]

    layout = [[sg.TabGroup([[sg.Tab("Update Profile", update_profile_tab), sg.Tab("Add Profile", add_profile_tab), sg.Tab("Option", option_tab)]], size=(400, 525))],
            [sg.Button("Exit", key="-exit-")]]

    window = sg.Window("AutoSyncMCMODs", layout, size=(400,600))
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == "-exit-":
            break

        elif event == "-accept-":
            directory_path = values["-option_directory_path-"]
        
        elif event =="-update_check-":
            if not combo_disable_flag:
                window["-update_check-"].update(disabled = True)
                check_update(combo_id)

        elif event == "-profile_combo-":
            selected_profile = values["-profile_combo-"]
            combo_id = dict_for_combo[selected_profile]
            window["-profile_name-"].update(profiles_dict[combo_id]["name"])
            window["-profile_id-"].update(combo_id)
            window["-profile_version-"].update(profiles_dict[combo_id]["version"])
            window["-update_check-"].update(disabled = False)


        elif event == "-add_profile_url_paste-":
            window["-add_profile_url-"].update(pyperclip.paste())

        elif event == "-option_directory_path_paste-":
            window["-option_directory_path-"].update(pyperclip.paste())
        
        elif event =="-add_profile_accept-":
            window["-add_profile_accept-"].update(disabled=True)
            window["-add_profile_state-"].update("Processing...")
            add_profile(values["-add_profile_url-"])

    save_option()
    window.close()

main()