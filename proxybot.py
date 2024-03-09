import requests, base64, hashlib, random, threading, tkinter as tk, datetime
from tkinter import ttk, Label, font as tkFont, filedialog, scrolledtext
import tkinter.font as tkFont

class LikeBot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("800x600")

        try:
            self.accounts = Utilities.openContents("accounts.txt")
        except FileNotFoundError:
            self.accounts = []

        self.gui = GUI(self.root, self.accounts)
        self.root.bind("<Button-1>", self.on_root_click)

    def on_root_click(self, event):
        print("Root window clicked at coordinates ({}, {})".format(event.x, event.y))

    def run(self):
        self.root.mainloop()

class NetworkHandler:
    def __init__(self, gui):
        self.gui = gui

    def handleProfileComments(self, username, page, callback):
        try:
            special = NetworkOperations.getRequestedUserData(username, True)
            rawComments = NetworkOperations.getComments(0, special, 0, page) # for comment ID its [0] # CommentID
            callback(special, rawComments, 0)
        except Exception as e:
            self.gui.master.after(0, lambda: self.gui.update_log("Network Error, check your internet.", True))
            print(str(e))

    def handleLevelCommentsID(self, ID, page, filter, callback):
        try:
            rawComments = NetworkOperations.getComments(2, ID, filter, page) # for comment ID its [0] # CommentID
            callback(ID, rawComments, 1)
        except Exception as e:
            self.gui.master.after(0, lambda: self.gui.update_log("Network Error, check your internet.", True))

    def handleLevelCommentsAccount(self, username, page, filter, callback):
        try:
            rawComments = NetworkOperations.getComments(1, str(NetworkOperations.getRequestedUserData(username, False)), filter, page)
            callback(None, rawComments, 1)
        except Exception as e:
            self.gui.master.after(0, lambda: self.gui.update_log("Network Error, check your internet.", True))

    def handleRate(self, accounts, levelID, demonDifficulty):
        rateLoopInstance = ThreadManager(self.gui)
        rateLoopInstance.rateLoop(accounts, levelID, demonDifficulty)
        
class GUI:
    def __init__(self, master, accounts):
        self.master = master
        self.accounts = accounts
        self.page_number = 0
        self.current_username = ""
        self.last_username = ""
        self.comments = ""
        self.network_manager = NetworkHandler(self)
        self.bold_font = tkFont.Font(weight="bold")
        master.title("Geometry Dash Bot v0.0.7")
        self.progress = 0
        self.total_accounts = len(accounts)

        self.prepare_window()
        self.create_tabs()
        self.create_log_output()
        self.create_progress_bar()

        self.logMessage("Geometry Dash Bot v0.0.7\n----------------------------\nBy: 3lit3hax: https://www.tiktok.com/@3lit3hax\n", False)
        if self.accounts:
            self.logMessage("Auto loaded " + str(len(accounts)) + " accounts (accounts.txt).", True)
        else:
            self.logMessage("Could not auto load accounts. Press 'Load Accounts' to load.", True)

    def create_progress_bar(self):
        self.progress_frame = ttk.Frame(self.master)
        self.progress_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5)

        self.progress_bar = ttk.Progressbar(self.progress_frame, orient='horizontal', length=100, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.total_likes = self.total_accounts
        self.progress_bar['maximum'] = self.total_likes

        self.progress_label = Label(self.progress_frame, text="0/{}".format(self.total_accounts))
        self.progress_label.place(relx=0.5, rely=0.5, anchor="center")

        self.progress_frame.grid_columnconfigure(0, weight=1)

    def update_progress_bar(self, value):
        self.progress += value
        self.progress_bar['value'] = self.progress
        self.progress_label.config(text="{}/{}".format(self.progress, self.total_likes))

    def finished_liking(self, type):
        self.network_manager.thread_manager.is_running = False
        if type == 0:
            self.master.after(0, lambda: self.logMessage("Finished liking.", True))
        elif type == 0:
            self.master.after(0, lambda: self.logMessage("Finished rating.", True))

    def prepare_window(self):
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=0)
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1) 

    def create_tabs(self):
        notebook_size = (self.master.winfo_screenwidth() // 4, self.master.winfo_screenheight() // 2)
        self.tab_control = ttk.Notebook(self.master, width=notebook_size[0], height=notebook_size[1])
        self.info_tab = self.add_tab('Info')
        self.like_tab = self.add_tab('Likebot')
        self.rate_tab = self.add_tab('Ratebot')

        self.tab_control.select(self.like_tab)
        self.tab_control.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def add_tab(self, title):
        tab = ttk.Frame(self.tab_control)
        self.tab_control.add(tab, text=title)
        if title == 'Likebot':
            self.setup_like_tab(tab)
        elif title == 'Ratebot':
            self.setup_rate_tab(tab)
        elif title == "Info":
            self.setup_info_tab(tab)
        return tab
    
    def setup_info_tab(self, tab):
        info_label = tk.Label(tab, text="Information", font=self.bold_font)
        info_label.pack(side="top", fill="x", pady=5)

    def setup_like_tab(self, tab):
        self.load_accounts_button = tk.Button(tab, text="Load Accounts (.txt)", command=self.load_accounts)
        self.load_accounts_button.pack(side="top", fill="x", pady=5)

        self.like_type_combobox = ttk.Combobox(tab, textvariable=tk.StringVar(), state='readonly')
        self.like_type_combobox['values'] = ("--Select Like Type--", "Level", "Account Comment", "Level Comment")
        self.like_type_combobox.current(0)
        self.like_type_combobox.pack(side="top", fill="x", pady=5)
        self.like_type_combobox.bind('<<ComboboxSelected>>', self.update_like_gui)

        self.dynamic_frame = ttk.Frame(tab)
        self.dynamic_frame.pack(side="top", fill="both", expand=True)
        
        like_button_frame = tk.Frame(tab)
        like_button_frame.pack(side="bottom", fill="x", pady=5)

        self.like_button = tk.Button(like_button_frame, text="Start", command=self.like_action)
        self.like_button.pack(side="left", fill="x", expand=True, pady=5)

        self.stop_button = tk.Button(like_button_frame, text="Stop", command=self.stop_action)
        self.stop_button.pack(side="left", fill="x", expand=True, pady=5)


    def setup_rate_tab(self, tab):
        self.load_accounts_button = tk.Button(tab, text="Load Accounts (.txt)", command=self.load_accounts)
        self.load_accounts_button.pack(side="top", fill="x", pady=5)

        level_id_label = tk.Label(tab, text="Enter Level ID:", font=self.bold_font)
        level_id_label.pack(side="top", fill="x", pady=5)
    
        self.level_id_entry = tk.Entry(tab, borderwidth=0, highlightthickness=0)
        self.level_id_entry.pack(side="top", fill="x", pady=5)

        select_rating_label = tk.Label(tab, text="Select Level Rating:", font=self.bold_font)
        select_rating_label.pack(side="top", fill="x", pady=5)

        self.rating_var = tk.StringVar(value="none")

        demon_difficulties = {
            "Easy Demon": "1",
            "Medium Demon": "2",
            "Hard Demon": "3",
            "Insane Demon": "4",
            "Extreme Demon": "5"
        }

        for difficulty, value in demon_difficulties.items():
            rb = tk.Radiobutton(tab, text=difficulty, variable=self.rating_var, value=value, anchor='w')
            rb.pack(side="top", fill="x", pady=2)

        rate_button_frame = tk.Frame(tab)
        rate_button_frame.pack(side="bottom", fill="x", pady=5)

        self.rate_start_button = tk.Button(rate_button_frame, text="Start", command=self.rate_action)
        self.rate_start_button.pack(side="left", fill="x", expand=True, pady=5)

        self.rate_stop_button = tk.Button(rate_button_frame, text="Stop", command=self.stop_action)
        self.rate_stop_button.pack(side="left", fill="x", expand=True, pady=5)

    def stop_action(self):
        self.logMessage("This button does nothing yet LMAO", True)

    def rate_action(self):
        level_id = self.level_id_entry.get()
        selected_rating = self.rating_var.get()

        if level_id.isdigit():
            if selected_rating != "none":
                self.logMessage(f"Rating difficulty {selected_rating} on ID: {level_id}.", True)
                thread = threading.Thread(target=self.network_manager.handleRate, args=(self.accounts, level_id, selected_rating))
                thread.start()
            else:
                self.logMessage("Select a difficulty rating.", True)
        else:
            self.logMessage("Enter a valid ID.", True)

    def update_like_gui(self, event=None):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
        setup_methods = {
            "Level": self.setup_gui_like_level,
            "Account Comment": self.setup_gui_like_account_comment,
            "Level Comment": self.setup_gui_like_level_comment
        }
        setup_method = setup_methods.get(self.like_type_combobox.get())
        if setup_method:
            setup_method()

    def setup_gui_like_level(self):
        tk.Label(self.dynamic_frame, text="Enter Level ID:", font=self.bold_font).pack(side="top", fill="x", pady=5)

        self.level_id_entry = tk.Entry(self.dynamic_frame, borderwidth=0, highlightthickness=0)
        self.level_id_entry.pack(side="top", fill="x", pady=5)

        tk.Label(self.dynamic_frame, text="Select Like Type:", font=self.bold_font).pack(side="top", fill="x", pady=5)

        self.like_dislike_var = tk.StringVar(value="Like")
        tk.Radiobutton(self.dynamic_frame, text="Like", variable=self.like_dislike_var, value="Like", highlightthickness=0, anchor='w').pack(side="top", fill="x", pady=2)
        tk.Radiobutton(self.dynamic_frame, text="Dislike", variable=self.like_dislike_var, value="Dislike", highlightthickness=0, anchor='w').pack(side="top", fill="x", pady=2)

    def setup_gui_like_account_comment(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

        username_label = tk.Label(self.dynamic_frame, text="Enter Username:", font=self.bold_font)
        username_label.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        self.username_entry = tk.Entry(self.dynamic_frame, borderwidth=0, highlightthickness=0)
        self.username_entry.grid(row=1, column=0, sticky='ew', padx=(10, 5), pady=5)

        load_comments_button = tk.Button(self.dynamic_frame, text="Load Comments", command=lambda: self.load_account_comments(self.username_entry.get()))
        load_comments_button.grid(row=1, column=1, sticky='ew', padx=(5, 10), pady=5)

        comment_label = tk.Label(self.dynamic_frame, text="Input:", font=self.bold_font)
        comment_label.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        self.comment_entry = tk.Entry(self.dynamic_frame, borderwidth=0, highlightthickness=0)
        self.comment_entry.grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        self.dynamic_frame.grid_columnconfigure(0, weight=2)
        self.dynamic_frame.grid_columnconfigure(1, weight=1)

        like_dislike_label = tk.Label(self.dynamic_frame, text="Select Like Type:", font=self.bold_font)
        like_dislike_label.grid(row=4, column=0, sticky='ew', padx=10, pady=(10, 0))

        self.like_dislike_var = tk.StringVar(value="Like")

        like_radio = tk.Radiobutton(self.dynamic_frame, text="Like", variable=self.like_dislike_var, value="Like", highlightthickness=0)
        like_radio.grid(row=5, column=0, sticky='w', padx=20, pady=2)

        dislike_radio = tk.Radiobutton(self.dynamic_frame, text="Dislike", variable=self.like_dislike_var, value="Dislike", highlightthickness=0)
        dislike_radio.grid(row=6, column=0, sticky='w', padx=20, pady=2)

    def load_account_comments(self, username):
        if username and not(username.isdigit()):
            self.last_username = self.current_username
            self.current_username = username

            if self.last_username and self.current_username != self.last_username:
                self.page_number = 0
                self.comments == "" 
                self.canLike = False

            self.logMessage(f"Loading account comments for username: {username}.", True)
            thread = threading.Thread(target=self.network_manager.handleProfileComments, args=(username, self.page_number, self.on_comments_loaded))
            thread.start()
        else:
            self.logMessage("Invalid Username.", True)

    def on_comments_loaded(self, special, comments, commentType):
        commentStatus = ProcessComments.validateComments(self, comments, 0)
        if commentStatus == True:
            self.special = special # AccountID
            self.comments = ProcessComments.classifyComments(comments, commentType)

            self.logMessage("Enter the number of the comment in the 'Input' field: \n", False)
            for i in range(0, len(self.comments)):
                self.logMessage(str(i + 1) + ": " + self.comments[i][0], False)

            self.logMessage("\n'n': Next Page:\n'b': Previous Page\n", False)
        elif commentStatus == "1":
            self.page_number -= 1
            #self.load_account_comments(self.current_username)

    def setup_gui_like_level_comment(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

        filter_label = tk.Label(self.dynamic_frame, text="Filter Comments By:", font=self.bold_font)
        filter_label.grid(row=0, column=0, columnspan=2, sticky='w', pady=5)

        self.comment_type_var = tk.StringVar(value="level")
        level_comments_radio = tk.Radiobutton(self.dynamic_frame, text="Level", variable=self.comment_type_var, value="level_comments", anchor='w')
        user_profile_comments_radio = tk.Radiobutton(self.dynamic_frame, text="User Profile", variable=self.comment_type_var, value="user_profile_comments", anchor='w'
                                                     )
        level_comments_radio.grid(row=1, column=0, sticky='w', padx=5, pady=2)
        level_comments_radio.select()
        user_profile_comments_radio.grid(row=2, column=0, sticky='w', padx=5, pady=2)

        self.sort_filter_var = tk.StringVar(value="recent")
        recent_radio = tk.Radiobutton(self.dynamic_frame, text="Recent", variable=self.sort_filter_var, value="recent", anchor='w')
        most_liked_radio = tk.Radiobutton(self.dynamic_frame, text="Most Liked", variable=self.sort_filter_var, value="most_liked", anchor='w')

        recent_radio.grid(row=1, column=1, sticky='w', padx=5, pady=2)
        most_liked_radio.grid(row=2, column=1, sticky='w', padx=5, pady=2)

        self.dynamic_frame.grid_columnconfigure(0, weight=1)
        self.dynamic_frame.grid_columnconfigure(1, weight=1)

        last_row_index = 0
        for child in self.dynamic_frame.winfo_children():
            info = child.grid_info()
            last_row_index = max(last_row_index, info.get("row", 0) + 1)

        username_label = tk.Label(self.dynamic_frame, text="Enter Username/ID:", font=self.bold_font)
        username_label.grid(row=last_row_index + 1, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        self.username_entry = tk.Entry(self.dynamic_frame, borderwidth=0, highlightthickness=0)
        self.username_entry.grid(row=last_row_index + 2, column=0, sticky='ew', padx=(10, 5), pady=5)

        load_comments_button = tk.Button(self.dynamic_frame, text="Load Comments", command=lambda: self.load_level_comments(self.username_entry.get()))
        load_comments_button.grid(row=last_row_index + 2, column=1, sticky='ew', padx=(5, 10), pady=5)

        comment_label = tk.Label(self.dynamic_frame, text="Input:", font=self.bold_font)
        comment_label.grid(row=last_row_index + 3, column=0, columnspan=2, sticky='ew', padx=10)

        self.comment_entry = tk.Entry(self.dynamic_frame, borderwidth=0, highlightthickness=0)
        self.comment_entry.grid(row=last_row_index + 4, column=0, columnspan=2, sticky='ew', padx=10)

        like_dislike_label = tk.Label(self.dynamic_frame, text="Select Like Type:", font=self.bold_font)
        like_dislike_label.grid(row=last_row_index + 5, column=0, sticky='ew', padx=10, pady=(10, 0))

        self.like_dislike_var = tk.StringVar(value="Like")
        like_radio = tk.Radiobutton(self.dynamic_frame, text="Like", variable=self.like_dislike_var, value="Like", highlightthickness=0)
        like_radio.grid(row=last_row_index + 6, column=0, sticky='w', padx=20, pady=2)

        dislike_radio = tk.Radiobutton(self.dynamic_frame, text="Dislike", variable=self.like_dislike_var, value="Dislike", highlightthickness=0)
        dislike_radio.grid(row=last_row_index + 7, column=0, sticky='w', padx=20, pady=2)

        self.dynamic_frame.grid_columnconfigure(0, weight=2)
        self.dynamic_frame.grid_columnconfigure(1, weight=1)

        self.dynamic_frame.pack_propagate(False)

    def load_level_comments(self, username):

        selected_comment_type = self.comment_type_var.get()
        selected_sort_filter = self.sort_filter_var.get()

        filter = "0" if selected_sort_filter == "recent" else "1"
        type = 0 if selected_comment_type == "level_comments" else 1

        if type == 0:
            if username and username.isdigit():
                self.logMessage(f"Loading comments on level ID: {username}", True)
                thread = threading.Thread(target=self.network_manager.handleLevelCommentsID, args=(username, self.page_number, filter, self.on_comments_loaded))
                thread.start()
            else:
                self.logMessage("Invalid ID.", True)
        else:
            if username and not(username.isdigit()):
                self.logMessage(f"Loading comments on account: {username}.", True)
                thread = threading.Thread(target=self.network_manager.handleLevelCommentsAccount, args=(username, self.page_number, filter, self.on_comments_loaded))
                thread.start()
            else:
                self.logMessage("Invalid Username.", True)

    def create_log_output(self):
        self.logOutput = scrolledtext.ScrolledText(self.master, state='disabled', wrap=tk.WORD)
        self.logOutput.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

    def update_log(self, message, outputTime):
        if self.master.winfo_exists():
            self.master.after(0, lambda: self.logMessage(message, outputTime))

    def logMessage(self, message, outputTime):
        currentTime = datetime.datetime.now().strftime("%H:%M:%S")
        formattedMessage = f"[{currentTime}] {message}\n" if outputTime else f"{message}\n"
        self.logOutput.config(state='normal')
        self.logOutput.insert(tk.END, formattedMessage)
        self.logOutput.config(state='disabled')
        self.logOutput.yview(tk.END)

    def load_accounts(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if filepath:
            self.master.focus_set()
            self.accounts = Utilities.openContents(filepath)
            self.total_accounts = len(self.accounts)
            self.total_likes = self.total_accounts
            self.progress_bar['maximum'] = self.total_likes
            self.update_progress_bar(0)
            self.logMessage(f"Loaded {len(self.accounts)} accounts from: {filepath}.", True)

    def like_action(self):
        if self.progress > 0: # If the bot is already running
            self.total_likes += self.total_accounts
            self.progress_bar['maximum'] = self.total_likes

        self.likeType = ""
        comment_text = ""
        self.canLike = False

        if self.like_type_combobox.get() == "Level":
            self.likeType = "1"
            self.itemID = self.level_id_entry.get() # Get Level ID
            self.special = 0

            if self.itemID.isdigit() and self.itemID:
                self.canLike = True
            else:
                self.logMessage("Invalid ID.", True)
            
        elif self.like_type_combobox.get() == "Account Comment":
            self.likeType = "3"
            self.itemID = ""
            comment_text = self.comment_entry.get() # Get text from the comment entry

            if self.username_entry.get() != self.current_username:
                self.comments = ""

            if comment_text.isdigit() and self.comments:
                if int(comment_text) >= 1 and int(comment_text) <= 10:
                    self.itemID = str(self.comments[(int(comment_text)) - 1][1]) # Grab Comment ID
                    self.canLike = True
                else:
                    self.logMessage("Incorrect comment range, can only be 1-10.", True)
            elif not(comment_text.isdigit()) and self.comments:
                if comment_text == "n":
                    self.page_number += 1
                    self.load_account_comments(self.username_entry.get())
                elif comment_text == "b":
                    if self.page_number >= 1:
                        self.page_number -= 1
                        self.load_account_comments(self.username_entry.get())
                    else:
                        self.logMessage("Page number already at 0, cannot decrease.", True)
                elif comment_text:
                    self.logMessage("Incorrect string, it can only be 'n' or 'b'.", True)
                else:
                    self.logMessage("Some fields are left empty.", True)
                    
            elif not(self.comments):
                self.logMessage("Load a users comments before liking.", True)
            else:
                self.logMessage("Some other bug occured, you should not be seeing this.", True)

        elif self.like_type_combobox.get() == "Level Comment":
            self.likeType = "2"
            self.itemID = ""
            comment_text = self.comment_entry.get()
            username_value = self.username_entry.get()
            if comment_text.isdigit() and self.comments: 
                if int(comment_text) >= 1 and int(comment_text) <= 10:
                    self.itemID = str(self.comments[(int(comment_text)) - 1][1]) # Grab Comment ID
                    if not(username_value.isdigit()): # Meaning person entered a username not an level ID
                        self.special = str(self.comments[(int(comment_text)) - 1][2]) # Get Special
                    self.canLike = True
                else:
                    self.logMessage("Incorrect comment range, can only be 1-10.", True)

            elif not(comment_text.isdigit()) and self.comments:
                if comment_text == "n":
                    self.page_number += 1
                    self.load_level_comments(self.username_entry.get())
                elif comment_text == "b":
                    if self.page_number >= 1:
                        self.page_number -= 1
                        self.load_level_comments(self.username_entry.get())
                    else:
                        self.logMessage("Page number already at 1, cannot decrease.", True)
                elif comment_text:
                    self.logMessage("Incorrect string, it can only be 'n' or 'b'.", True)
                else:
                    self.logMessage("Some fields are left empty.", True)
            elif not(self.comments):
                self.logMessage("Load comments before liking.", True)
            else:
                self.logMessage("Some other bug occured, you should not be seeing this.", True)                

        if self.canLike == True:
            if self.accounts:
                like_or_dislike = self.like_dislike_var.get()
                self.liked = 1 if like_or_dislike == "Like" else 0

                self.logMessage("--Starting Bot--", True)
                self.logMessage("Scraping Proxies...", True)
                proxy_thread = threading.Thread(target=self.get_proxies_thread)
                proxy_thread.start()
            elif self.accounts == []:
                self.logMessage("Load accounts before liking.", True)

    def get_proxies_thread(self):
        likeLoopInstance = ThreadManager(self)
        #print(f"Liketype:{self.likeType}, itemID:{self.itemID}, special:{self.special}, liked:{self.liked}")
        likeLoopInstance.likeLoop(self.accounts, self.likeType, self.itemID, self.special, self.liked)


class NetworkOperations:
    baseURL = "http://www.boomlings.com/database/"
    playerURL = "getGJUsers20.php"
    likeURL = "likeGJItem211.php"
    commentURL = "getGJAccountComments20.php"
    userCommentURL = "getGJCommentHistory.php"
    levelCommentURL = "getGJComments21.php"
    rateURL = "rateGJDemon21.php"     

    @staticmethod
    def getProxies():
        proxyscrapev2url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all" # Good fast proxies
        proxyscrapev1url = "https://api.proxyscrape.com/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all" # Good fast proxies
        #alexaurl = "https://alexa.lr2b.com/proxylist.txt" # Slow inconsistent proxies
        #multiproxyurl = "https://multiproxy.org/txt_all/proxy.txt" # Slow inconsistent proxies
        remove = ':80'
        proxies = []

        proxies += requests.get(proxyscrapev2url).text.splitlines()
        proxies += requests.get(proxyscrapev1url).text.splitlines()
        #proxies += requests.get(alexaurl).text.splitlines()
        #proxies += requests.get(multiproxyurl).text.splitlines()
        proxies = list(set(proxies)) # Convert to set to remove duplicate proxies
        proxies = [proxy for proxy in proxies if not proxy.endswith(remove)]
        random.shuffle(proxies)
        return proxies
    
    @staticmethod
    def getComments(commentType, special, filter, page): # special: UserID or LevelID | filter: 0 - recent comments, 1 - most liked comments
        if commentType == 0: # Account Comment
            rawComments = NetworkOperations.post(NetworkOperations.baseURL+NetworkOperations.commentURL, {"userID": special, "accountID": special, "levelID": special, "page": page, "count": "10", "mode": '0', "secret": 'Wmfd2893gb7', "gameVersion": '21', "binaryVersion": '35'})
        elif commentType == 1: # Level Comment
            rawComments = NetworkOperations.post(NetworkOperations.baseURL+NetworkOperations.userCommentURL, {"userID": special, "accountID": special, "page": page, "count": "10", "mode": filter, "secret": "Wmfd2893gb7", "gameVersion": "21", "binaryVersion": "35"})
        else: # Profile Level Comment
            rawComments = NetworkOperations.post(NetworkOperations.baseURL+NetworkOperations.levelCommentURL, { "userID": special, "accountID": special, "levelID": special, "page": page, "count": "10", "mode": filter, "secret": 'Wmfd2893gb7', "gameVersion": '21', "binaryVersion": '35'})

        return rawComments
    
    @staticmethod
    def getRequestedUserData(accountName, getUserID):
        playerDataPost = { "str": accountName, "page": 0, "secret": "Wmfd2893gb7", "gameVersion": '21', "binaryVersion": '35'}
        try:
            response = requests.post(NetworkOperations.baseURL + NetworkOperations.playerURL, data=playerDataPost, headers={"User-Agent": ""})
            data = response.text.split(":")
            if getUserID == True:
                return int(data[21]) # AccountID
            else:
                return int(data[3]) # PlayerID
        except:
            return False
    
    @staticmethod
    def post(url, post):
        response = requests.post(url, data=post, headers={"User-Agent": ""})
        return response.text
    
class PostBuilder:
    @staticmethod
    def buildLikePost(itemID, special, liked, type, currentPassword, userID):
        chk = str(special) + str(itemID) + str(liked) + type + "8f0l0ClAN1" + str(userID) + "0" + "0" + "ysg6pUrtjn0J" #special + itemid + liked + type + rs + userid + udid + uuid + randomstring
        chkhash = hashlib.sha1(chk.encode('utf-8')).hexdigest()
        chk = Utilities.encrypt(chkhash, 58281)
        gjp = Utilities.encrypt(currentPassword, 37526)
        likePost = {
            "udid": "0", # Constant
            "uuid": "0", # Constant
            "rs": "8f0l0ClAN1", # Constant, random string
            "itemID": itemID, # ID of the comment
            "gjp": gjp, # "XOR" encrypted gd password
            "accountID": userID, # The online account ID of the player
            "like": liked, # Like / dislike level
            "special": special, # Player ID / Level you want to like (level ID, account ID, or '0' for levels)
            "type": type, # 1=level, 2=comment, 3=profile
            "chk": chk, # Check that makes sure all data being sent is correct
            "secret": "Wmfd2893gb7", # Constant, robtops super "secret" password stored in plain text
            "gameVersion": '21', # Constant, game version
            "binaryVersion": '35', # Constant, binary version
        }
        return likePost

    @staticmethod
    def buildRatePost(password, accountID, levelID, demonDifficulty):
        gjp = Utilities.encrypt(password, 37526)
        ratePost = {
            "gameVersion": "21",
            "binaryVersion": "35",
            "gdw": "0",
            "accountID": accountID,
            "gjp": gjp,
            "levelID": levelID,
            "rating": demonDifficulty,
            "secret": "Wmfp3879gc3"
        }
        return ratePost

class Utilities:
    @staticmethod
    def xor(string, key): # XOR encrypt given string
        key_str = str(key)
        encrypted = ""
        for i in range(0, len(string)):
            keyPosition = ord(key_str[i % len(key_str)])
            char_code = ord(string[i])
            encrypted += chr(keyPosition ^ char_code)
        return encrypted
    
    @staticmethod
    def encrypt(str, key):
        encrypted_str = Utilities.xor(str, key)
        str_bytes = encrypted_str.encode('ascii')
        base64_bytes = base64.b64encode(str_bytes)
        base64_message = base64_bytes.decode('ascii')
        message = base64_message.replace("/", "_").replace("+", "-")
        return message

    @staticmethod
    def decryptMessage(str):
        try:
            str = str.replace("_", "/").replace("-", "+")
            base64_bytes = str.encode('ascii')
            message_bytes = base64.b64decode(base64_bytes)
            return message_bytes.decode('ascii')
        except Exception as e:
            return "~Base64 Decoder Error~ :("

    @staticmethod
    def openContents(text):
        with open(text, "r") as file:
            textData = file.read()[:-1].split(":")
        return [textData[i:i+3] for i in range(0, len(textData), 3)]

class ProcessComments:
    @staticmethod
    def validateComments(gui, response, page):
        if response == "-1":
            if page > 0:
                gui.logMessage("You are at the end of the comment page.", True)
                return "1"
            else:
                gui.logMessage("This person has no comments.", True)
            return 0

        commentCount = [int(x) for x in response.rsplit("#", 1)[1].split(":")] # ['Number Of comments', 'Comments on display' 'Number of comments shownig']
        if commentCount[1] > commentCount[0]:
            gui.logMessage("You are at the end of the comment page, don't go so far.", True)
            return "1"
        if commentCount[0] == 0:
            gui.logMessage("This person has no comments.", True)
            return 0
        return True

    @staticmethod
    def classifyComments(response, commentType): # commentType values: 0-Account Comment, 1-Level Comment 2-Profile Level Comment
        data = response.split("|")
        combined = []
        for item in data:
            parts = item.split("~")
            decrypted_message = Utilities.decryptMessage(parts[1])

            if commentType == 0:
                message_id = parts[-1].split("#")[0]
                combined_item = (decrypted_message, message_id)
            else:
                level_id = parts[3]
                message_id = parts[13].split(":")[0]
                combined_item = (decrypted_message, message_id, level_id) if commentType != 2 else (decrypted_message, message_id)

            combined.append(combined_item)
        
        return combined

class ThreadManager:
    def __init__(self, gui):
        self.gui = gui
        self.threads = []
        self.proxies = NetworkOperations.getProxies()
        self.gui.master.after(1, lambda: self.gui.update_log(f"Scraped {len(self.proxies)} Proxies", True))
        self.lock = threading.Lock()
        self.outOfProxies = False

    def likeLoop(self, accounts, liketype, itemID, special, liked):
        for account in accounts:
            postData = PostBuilder.buildLikePost(itemID, special, liked, liketype, account[1], account[2])
            thread = threading.Thread(target=self.likeThread, args=(postData, self.proxies[-1], account))
            self.proxies.pop()
            self.threads.append(thread)
            thread.start()

        for thread in self.threads:
            thread.join()

        #self.gui.finished_liking(0)

    def rateLoop(self, accounts, levelID, demonDifficulty):
        for account in accounts:
            postData = PostBuilder.buildRatePost(account[1], str(account[2]), str(levelID), str(demonDifficulty))
            thread = threading.Thread(target=self.rateThread, args=(postData, self.proxies[-1], account))
            self.proxies.pop()
            self.threads.append(thread)
            thread.start()

        for thread in self.threads:
            thread.join()

    def rateThread(self, postData, proxy, account):
        try:
            #response = requests.post(NetworkOperations.baseURL+NetworkOperations.rateURL, proxies={"http": "http://" + proxy, "https" : "https://" + proxy}, data=postData, timeout=5, headers={"User-Agent": ""})
            response = requests.post(NetworkOperations.baseURL+NetworkOperations.rateURL, proxies={"http": "http://" + proxy}, data=postData, timeout=7, headers={"User-Agent": ""})

            if response.text == "1":
                self.gui.master.after(0, lambda: [self.gui.update_log("Sent on " + account[0] + ". P: " + proxy, True), self.gui.update_progress_bar(1)])
            else:
                #print("Rate Failed")
                self.retryLogin(postData, account, 2)
                
        except Exception as e:
            #print("failed to make post request for some other reason.")
            self.retryLogin(postData, account, 2)

    def likeThread(self, postData, proxy, account):
        try:
            #response = requests.post(NetworkOperations.baseURL+NetworkOperations.likeURL, proxies={"http": "http://" + proxy, "https" : "https://" + proxy}, data=postData, timeout=5, headers={"User-Agent": ""})
            response = requests.post(NetworkOperations.baseURL+NetworkOperations.likeURL, proxies={"http": "http://" + proxy}, data=postData, timeout=7, headers={"User-Agent": ""})
            if response.text == "1":
                self.gui.master.after(0, lambda: [self.gui.update_log("Sent on " + account[0] + ". P: " + proxy, True), self.gui.update_progress_bar(1)])
            else:
                #print("Like Failed")
                self.retryLogin(postData, account, 1)
                
        except Exception as e:
            #print("failed to make post request for some other reason. "  + str(e))
            self.retryLogin(postData, account, 1)

    def retryLogin(self, postData, account, likeOrRate):
        with self.lock:
            if not self.proxies and not self.outOfProxies:
                self.gui.master.after(0, lambda: self.gui.update_log("WARNING: Ran out of proxies, post consistency WILL drop!", True))
                self.proxies = NetworkOperations.getProxies()
                self.outOfProxies = True
            elif self.proxies:
                self.outOfProxies = False

        if self.proxies:
            proxy = self.proxies.pop()
            if likeOrRate == 1:
                thread = threading.Thread(target=self.likeThread, args=(postData, proxy, account))
            else:
                thread = threading.Thread(target=self.rateThread, args=(postData, proxy, account))
            thread.start()
        else:
            self.gui.master.after(0, lambda: self.gui.update_log("No proxies available.", True))

def downloadLevel(levelID):
    data = {
        "levelID": levelID, # bloodbath
        "secret": "Wmfd2893gb7"
    }
    req = requests.post("http://www.boomlings.com/database/downloadGJLevel22.php", data=data, headers={"User-Agent":""})
    print(req.text)

    #response = requests.post("http://boomlings.com/database/downloadGJLevel22.php", data={ "levelID": str(levelID), "secret": "Wmfd2893gb7" }, timeout=5, headers={"User-Agent": "", "Content-Type": "application/x-www-form-urlencoded"})
    #print(response.text)

#downloadLevel(91550945)

if __name__ == "__main__":
    instance1 = LikeBot()
    instance1.run()