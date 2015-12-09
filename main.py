import Tkinter, tkMessageBox
from ttk import *
from crawl import QuoraCrawler
from selenium.common.exceptions import TimeoutException as STException

RESET_MSG = 'Are you sure you want to reset answer list ? This is not usually \
not required unless there is a critical error or you want to reuse the \
application for a different Quora Account. Please Confirm.'
TIMEOUT_MSG = 'Operation Timed Out. Please check your internet connection!'
LOGIN_REQ_MSG = 'No User Logged In. Please Log In before Continuing !'
ALREADY_LOGIN_MSG = 'User Already Logged In'

class PasswordPopUp(Tkinter.Toplevel):
  def __init__(self, parent):
    Tkinter.Toplevel.__init__(self, parent)
    #top.overrideredirect(1)
    self.resizable(False, False)
    self.ulabel = Label(self, anchor='e', text="Enter Email Id :")
    self.ulabel.grid(row=0, column=0, sticky='EWNS')
    self.email = Entry(self)
    self.email.grid(row=0, column=1, columnspan=2, sticky='EWNS')
    self.plabel = Label(self, anchor='e', text="Enter Password :")
    self.plabel.grid(row=1, column=0, sticky='EWNS')
    self.password = Entry(self, show='*')
    self.password.grid(row=1, column=1, columnspan=2, sticky='EWNS')
    self.submit = Button(self, text='Submit', command=self.cleanup)
    self.submit.grid(row=2, column=1, sticky='EWN')
    self.cancel = Button(self, text='Cancel', command=self.cleanup)
    self.cancel.grid(row=2, column=2, sticky='WWN')
    self.grid_rowconfigure(0, weight=1, pad=5)
    self.grid_rowconfigure(1, weight=1, pad=5)
    self.grid_rowconfigure(2, weight=0, pad=5)
    self.grid_columnconfigure(0, weight=0, pad=5)
    self.grid_columnconfigure(1, weight=1, pad=5)
    self.grid_columnconfigure(2, weight=1, pad=5)
    self.configure(bg=self.ulabel['background'])

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
    self.crawler = QuoraCrawler()
    self.grid_rowconfigure(0, weight=1)
    self.grid_columnconfigure(0, weight=1)
    self._add_frames()

    self.pack(fill='both', expand=True)

  def _add_frames(self):
    # Adding Answer Backup Frame
    f1 = Frame(self, padding="3 3 12 12")
    f1.grid(column=0, row=0, sticky="NWES")
    for i in range(2):
      f1.grid_rowconfigure(i, weight=0, pad=5)
    f1.grid_rowconfigure(2, weight=1, pad=5)
    for i in range(4):
      f1.grid_columnconfigure(i, weight=1, pad=5)

    entry = Tkinter.Label(f1, anchor='e', text='Answers Count : ')
    entry.grid(column=0, row=0, sticky='EWNS')
    self.answer_count = Tkinter.StringVar(value=len(self.crawler.answer_list))
    entry = Tkinter.Label(f1, anchor='w', textvariable=self.answer_count)
    entry.grid(column=1, row=0, sticky='EWNS')
    entry = Tkinter.Label(f1, anchor='e', text='User Name : ')
    entry.grid(column=2, row=0, sticky='EWNS')
    self.user = Tkinter.StringVar(value='Unknown')
    entry = Tkinter.Label(f1, anchor='w', textvariable=self.user)
    entry.grid(column=3, row=0, sticky='EWNS')

    button = Tkinter.Button(f1, text='Login', command=self.login_crawler)
    button.grid(column=0, row=1, sticky='EWNS')
    button = Tkinter.Button(f1, text='Logout', command=self.logout_crawler)
    button.grid(column=1, row=1, sticky='EWNS')
    button = Tkinter.Button(f1, text='Reset', command=self.reset_answer_list)
    button.grid(column=2, row=1, sticky='EWNS')
    button = Tkinter.Button(f1, text='Update', command=self.update_answer_list)
    button.grid(column=3, row=1, sticky='EWNS')

    # Adding The list of all answers
    tree = Treeview(f1, columns=('sno', 'date', 'question'))
    tree.heading('sno', text='S. No')
    tree.heading('date', text='Date')
    tree.heading('question', text='Question')

    tree.column("#0", width=0, stretch=False)
    tree.column('sno', width=40, stretch=False, anchor='center')
    tree.column('date', width=120, stretch=False, anchor='center')
    tree.column('question', stretch=True, anchor='w')
    tree.grid(column=0, columnspan=4, row=2, sticky='EWNS')
    tree.bind("<Double-1>", self.tree_item_click)
    self.answer_tree = tree

    f2 = Frame(self)
    self.add(f1, text='Answer Backup', underline=7)
    self.add(f2, text='Analytics')

  def tree_item_click(self, event):
    idx_clicked = self.answer_tree.identify_row(event.y)
    if idx_clicked:
      print "Tree Item Clicked - ", idx_clicked

  def reset_answer_list(self):
    confirm = tkMessageBox.askquestion(
      title='Confirm Reset',
      message=RESET_MSG,
      icon='warning'
    )
    if confirm == 'yes':
      self.crawler.reset_answer_list()
      self.answer_count.set(len(self.crawler.answer_list))

  def update_answer_list(self):
    try:
      if not self.crawler.check_login():
        tkMessageBox.showerror(
          title='Login Required',
          message=LOGIN_REQ_MSG,
          icon=tkMessageBox.INFO
        )
      else:
        self.crawler.update_answer_list()
        self.answer_count.set(len(self.crawler.answer_list))
        self.populate_tree()
    except STException:
      tkMessageBox.showerror(
        title='Operation Aborted',
        message=TIMEOUT_MSG,
        icon=tkMessageBox.ERROR
      )

  def login_crawler(self):
    try:
      if False and self.crawler.check_login():
        tkMessageBox.showinfo(
          title='Login Successful',
          message=ALREADY_LOGIN_MSG,
          icon=tkMessageBox.INFO
        )
        self.user.set(self.crawler.get_user_name())
      else:
        # Opening Pop Up
        self.loginpop = PasswordPopUp(self)
        self.loginpop.grab_set()
        self.parent.wait_window(self.loginpop)
        self.loginpop.grab_release()
        print "Email = %s Password = %s" % (self.loginpop.uname, self.loginpop.passw)

    except STException:
      tkMessageBox.showerror(
        title='Operation Aborted',
        message=TIMEOUT_MSG,
        icon=tkMessageBox.ERROR
      )

  def logout_crawler(self):
    try:
      self.crawler.logout()
      self.user.set('Logged Out')
    except STException:
      tkMessageBox.showerror(
        title='Operation Aborted',
        message=TIMEOUT_MSG,
        icon=tkMessageBox.ERROR
      )

  def populate_tree(self):
    for i in self.answer_tree.get_children():
        self.answer_tree.delete(i)
    for idx, answer in enumerate(self.crawler.answer_list):
      self.asnwer_tree.insert('', 'end', idx + 1,
                              value=((idx + 1, answer[1], answer[2])))

  def destroy(self):
    self.crawler.quit()
    Notebook.destroy(self)

if __name__ == '__main__':
  # Initialize Application and Run Main Loop
  app = QuoraAnalyticsUI()
  app.mainloop()
  exit()
