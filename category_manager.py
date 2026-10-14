import os

def get_category(location, folder_name):
    file_folder_path = os.path.join(location, folder_name)

    if not os.path.exists(file_folder_path):
        os.makedirs(file_folder_path)

    categories = {}

    category_files = os.listdir(file_folder_path)

    for filename in category_files:
        if filename.endswith(".txt"):
            name = filename.removesuffix(".txt")    
            file_path = os.path.join(file_folder_path, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                categories[name] = [line.strip() for line in f if line.strip()]
    return categories

def retrieval_unknown_apps(running_apps, cat):
    known_apps = {exe.lower() for exe in sum(cat.values(), [])}
    not_known_apps =  list(running_apps - known_apps)

    if not not_known_apps:
        print("lack applications to add")
        return [], None

    for index, app in enumerate(not_known_apps, start=1):
        print(f"[{index}] {app}")
    print("choose app to add")
    return not_known_apps, "selection_app_to_add"

def choose_from(number, items):
    if 0 <= number < len(items):
        return items[number]
    
    print(f"invalid number. choose number between 1 to {len(items)}")
    return None

def check_category_name(CATEGORIES, text):
    category_name = text[4:]

    if category_name in CATEGORIES:
        return category_name
        
    print("invalid category name")
    return None

def add_to_file_list_txt(file_name, location, item):
    file_path = os.path.join(location, (f"{file_name}.txt"))
    needs_newline = False

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

            if content and not content.endswith("\n"):
                needs_newline = True

    with open(file_path, "a", encoding="utf-8") as file:
        if needs_newline:
            file.write("\n")

        file.write(f"{item}\n")
        print(f"{item} been added to {file_name}.txt")
    
