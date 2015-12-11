import Tkinter, tkMessageBox
from ttk import Notebook, Treeview, Progressbar
from Tkinter import *
from crawl import QuoraCrawler
from selenium.common.exceptions import TimeoutException as STException
from threading import Thread

RESET_MSG = 'Are you sure you want to reset answer list ? This is not usually \
not required unless there is a critical error or you want to reuse the \
application for a different Quora Account. Please Confirm.'
TIMEOUT_MSG = 'Operation Timed Out. Please check your internet connection!'
LOGIN_REQ_MSG = 'No User Logged In. Please Log In before Continuing !'
ALREADY_LOGIN_MSG = 'User Already Logged In'
BUSY_MSG = 'A task is already being executed. Please wait for it to finish \
proceeding with another task.'

class PasswordPopUp(Tkinter.Toplevel):
  def __init__(self, parent):
    Tkinter.Toplevel.__init__(self, parent)
    #top.overrideredirect(1)
    col = '#e6e6e6'
    self.resizable(False, False)
    Label(self, anchor='e', text="Enter Email Id :", bg=col).grid(row=0, column=0, sticky='EWNS')
    self.email = Entry(self, highlightbackground=col)
    self.email.grid(row=0, column=1, columnspan=2, sticky='EWNS')
    Label(self, anchor='e', text="Enter Password :", bg=col).grid(row=1, column=0, sticky='EWNS')
    self.password = Entry(self, show='*', highlightbackground=col)
    self.password.grid(row=1, column=1, columnspan=2, sticky='EWNS')
    Button(self, text='Submit', command=self.cleanup, highlightbackground=col).grid(row=2, column=1, sticky='EWN')
    Button(self, text='Cancel', command=self.cleanup, highlightbackground=col).grid(row=2, column=2, sticky='EWN')
    self.grid_rowconfigure(0, weight=1, pad=5)
    self.grid_rowconfigure(1, weight=1, pad=5)
    self.grid_rowconfigure(2, weight=0, pad=5)
    self.grid_columnconfigure(0, weight=0, pad=5)
    self.grid_columnconfigure(1, weight=1, pad=5)
    self.grid_columnconfigure(2, weight=1, pad=5)
    self.configure(bg=col)

    # Default Values
    self.uname = ''
    self.passw = ''

  def cleanup(self):
    self.uname = self.email.get()
    self.passw = self.password.get()
    self.destroy()

class QuoraAnalyticsUI(Notebook):

  def __init__(self):
    self.parent = Tkinter.Tk()
    Notebook.__init__(self, self.parent)
    #self.parent.title('Quora Analytics')
    self.parent.title('Quora Backup and Analytics')
    self.parent.wm_title('Quora Backup and Analytics')
    self.parent.grid_rowconfigure(0, weight=1)
    self.parent.grid_columnconfigure(0, weight=1)
    self.parent.resizable(True, True)
    self.grid_rowconfigure(0, weight=1)
    self.grid_columnconfigure(0, weight=1)
    self.crawler = QuoraCrawler(driver=QuoraCrawler.CHROME_DRIVER)
    self._add_frames()
    self.pack(fill='both', expand=True)

  def _add_frames(self):
    # Adding Answer Backup Frame
    f1 = Frame(self)
    f1.grid(column=0, row=0, sticky="NWES")
    for i in range(4):
      f1.grid_rowconfigure(i, weight=0, pad=5)
    f1.grid_rowconfigure(4, weight=1, pad=5)
    for i in range(4):
      f1.grid_columnconfigure(i, weight=1, pad=5)

    Label(f1, anchor='e', text='Answers Count : ').grid(column=0, row=0, sticky='EWNS')
    self.answer_count = StringVar(value=len(self.crawler.answer_list))
    Label(f1, anchor='w', textvariable=self.answer_count).grid(column=1, row=0, sticky='EWNS')
    Label(f1, anchor='e', text='User Name : ').grid(column=2, row=0, sticky='EWNS')
    self.user = StringVar(value='Unknown')
    Label(f1, anchor='w', textvariable=self.user).grid(column=3, row=0, sticky='EWNS')

    tf_col = '#e6e6e6'
    tf = Tkinter.Frame(f1, relief=GROOVE, borderwidth='2p')
    tf.grid(row=1, columnspan=2, column=0, sticky='EWNS')
    Label(tf, text='Quora User Options', bg=tf_col, anchor='c').grid(column=0, row=0, columnspan=2, sticky='EWNS')
    Button(tf, text='Login', command=lambda : self.thread('login'),
      highlightbackground=tf_col).grid(column=0, row=1, sticky='EWNS')
    Button(tf, text='Logout', command=lambda : self.thread('logout'),
      highlightbackground=tf_col).grid(column=1, row=1, sticky='EWNS')
    tf.grid_rowconfigure(0, weight=1, pad=5)
    tf.grid_rowconfigure(1, weight=1, pad=5)
    tf.grid_columnconfigure(0, weight=1, pad=5)
    tf.grid_columnconfigure(1, weight=1, pad=5)

    tf = Frame(f1, relief=GROOVE, borderwidth='2p')
    tf.grid(row=1, columnspan=2, column=2, sticky='EWNS')
    Label(tf, text='Answer List Option', bg=tf_col, anchor='c').grid(column=0, columnspan=2, row=0, sticky='EWNS')
    Button(tf, text='Reset', command=lambda : self.thread('reset'),
      highlightbackground=tf_col).grid(column=0, row=1, sticky='EWNS')
    Button(tf, text='Update', command=lambda : self.thread('update'),
      highlightbackground=tf_col).grid(column=1, row=1, sticky='EWNS')
    tf.grid_rowconfigure(0, weight=1, pad=5)
    tf.grid_rowconfigure(1, weight=1, pad=5)
    tf.grid_columnconfigure(0, weight=1, pad=5)
    tf.grid_columnconfigure(1, weight=1, pad=5)

    # Add Progress Bar
    self.backup_progress = Progressbar(f1, orient="horizontal", length=100, mode="determinate")
    self.backup_progress.grid(row=2, columnspan=4, column=0, sticky='EWNS')

    # Adding Status Pane
    self.backup_status = StringVar(value='Ready')
    Label(f1, textvariable=self.backup_status, anchor='w').grid(row=3, column=0, columnspan=4, sticky='EWNS')

    # Adding The list of all answers
    tree = Treeview(f1, columns=('sno', 'date', 'question'))
    tree.heading('sno', text='S. No')
    tree.heading('date', text='Date')
    tree.heading('question', text='Question')

    tree.column("#0", width=0, stretch=False)
    tree.column('sno', width=40, stretch=False, anchor='center')
    tree.column('date', width=120, stretch=False, anchor='center')
    tree.column('question', stretch=True, anchor='w')
    tree.grid(column=0, columnspan=4, row=4, sticky='EWNS')
    tree.bind("<Double-1>", self.tree_item_click)
    self.answer_tree = tree
    self.populate_tree()

    f2 = Frame(self)
    self.add(f1, text='Answer Backup', underline=7)
    self.add(f2, text='Analytics')

  def tree_item_click(self, event):
    idx_clicked = self.answer_tree.identify_row(event.y)
    if idx_clicked:
      print "Tree Item Clicked - ", idx_clicked

  def show_busy_dialog(self):
    tkMessageBox.showerror(
      title='Task in Progress',
      message=BUSY_MSG,
      icon=tkMessageBox.INFO
    )

  def thread(self, task):
    print "Starting a new Thread for " + task
    if self.backup_status.get() != 'Ready': self.show_busy_dialog()
    else:
      self.backup_status.set('Starting a new Task...')
      task_ids = (
        ('login', self.login_crawler),
        ('logout', self.logout_crawler),
        ('update', self.update_answer_list),
        ('reset', self.reset_answer_list)
      )

      for task_relation in task_ids:
        if task == task_relation[0]: Thread(target=task_relation[1]).start()

  def reset_answer_list(self):
    confirm = tkMessageBox.askquestion(
      title='Confirm Reset',
      message=RESET_MSG,
      icon='warning'
    )
    if confirm == 'yes':
      self.backup_status.set('Reseting Answer List...')
      self.backup_progress.start(interval=500)
      self.crawler.reset_answer_list()
      self.answer_count.set(len(self.crawler.answer_list))
      self.populate_tree()

    self.backup_status.set('Ready')
    self.backup_progress.stop()
    self.backup_progress['value'] = 0

  def update_answer_list(self):
    try:
      self.backup_status.set('Checking Login Status...')
      self.backup_progress.start(interval=500)
      if not self.crawler.check_login(self.backup_progress, self.backup_status):
        self.backup_status.set('Logged Out !! Cannot continue')
        tkMessageBox.showerror(
          title='Login Required',
          message=LOGIN_REQ_MSG,
          icon=tkMessageBox.INFO
        )
      else:
        self.backup_progress['value'] = 10
        self.backup_status.set('Updating Answer List...It may take few minutes')
        self.crawler.update_answer_list(self.backup_progress, self.backup_status)
        self.answer_count.set(len(self.crawler.answer_list))
        self.populate_tree()
    except STException:
      tkMessageBox.showerror(
        title='Operation Aborted',
        message=TIMEOUT_MSG,
        icon=tkMessageBox.ERROR
      )

    self.backup_status.set('Ready')
    self.backup_progress.stop()
    self.backup_progress['value'] = 0

  def login_crawler(self):
    try:
      self.backup_status.set('Checking Login Status...')
      self.backup_progress.start(interval=500)
      self.backup_progress['value'] = 10
      if self.crawler.check_login(self.backup_progress, self.backup_status):
        self.backup_progress['value'] = 100
        self.backup_progress.stop()
        tkMessageBox.showinfo(
          title='Login Successful',
          message=ALREADY_LOGIN_MSG,
          icon=tkMessageBox.INFO
        )
        self.user.set(self.crawler.get_user_name())
      else:
        # Opening Pop Up
        self.backup_status.set('Waiting For Credentials...')
        self.backup_progress['value'] = 40
        self.loginpop = PasswordPopUp(self)
        self.loginpop.grab_set() # To lock parent window when child is shown
        self.parent.wait_window(self.loginpop)
        self.loginpop.grab_release() # Reactivate parent window
        email = self.loginpop.uname.strip()
        passw = self.loginpop.passw.strip()
        if len(email) > 0 and len(passw) > 0:
          try:
            self.backup_status.set('Trying to log in with ' + email + ' ...')
            self.backup_progress['value'] = 60
            self.crawler.login(email, passw, self.backup_progress, self.backup_status)
            self.user.set(self.crawler.get_user_name())
          except QuoraCrawler.InvalidCredentialException, e:
            self.backup_status.set('Login Unsuccessful')
            self.backup_progress['value'] = 100
            self.backup_progress.stop()
            tkMessageBox.showerror(
              title='Invalid Credentials',
              message=e.message,
              icon=tkMessageBox.ERROR
            )
    except STException:
      tkMessageBox.showerror(
        title='Operation Aborted',
        message=TIMEOUT_MSG,
        icon=tkMessageBox.ERROR
      )

    self.backup_status.set('Ready')
    self.backup_progress.stop()
    self.backup_progress['value'] = 0

  def logout_crawler(self):
    try:
      self.backup_progress.start(interval=500)
      self.backup_status.set('Trying to Logging Out')
      self.crawler.logout(self.backup_progress, self.backup_status)
      self.user.set('Logged Out')
    except STException:
      tkMessageBox.showerror(
        title='Operation Aborted',
        message=TIMEOUT_MSG,
        icon=tkMessageBox.ERROR
      )
    self.backup_status.set('Ready')
    self.backup_progress.stop()
    self.backup_progress['value'] = 0

  def populate_tree(self):
    for i in self.answer_tree.get_children():
        self.answer_tree.delete(i)
    for idx, answer in enumerate(self.crawler.answer_list):
      self.answer_tree.insert('', 'end', idx + 1,
                              value=((idx + 1, answer[1], answer[2])))

  def destroy(self):
    self.crawler.quit()
    Notebook.destroy(self)

if __name__ == '__main__':
  # Initialize Application and Run Main Loop
  app = QuoraAnalyticsUI()
  app.mainloop()
  exit()
