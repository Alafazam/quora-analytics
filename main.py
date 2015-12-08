import Tkinter
from ttk import *
from crawl import QuoraCrawler

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
    for i in range(2):
      f1.grid_columnconfigure(i, weight=1, pad=5)

    entry = Tkinter.Label(f1, anchor='e', text='Answers Count : ')
    entry.grid(column=0, row=0, sticky='EWNS')
    #entry.grid_configure(padx=5, pady=5)

    self.answer_count = Tkinter.StringVar(value=len(self.crawler.answer_list))
    entry = Tkinter.Label(f1, anchor='w', textvariable=self.answer_count)
    entry.grid(column=1, row=0, sticky='EWNS')
    #entry.grid_configure(padx=5, pady=5)

    #entry.bind("<Return>", self.OnPressEnter)
    button = Tkinter.Button(f1, text='Reset', command=self.OnButtonClick)
    button.grid(column=0, row=1, sticky='EWNS')
    button = Tkinter.Button(f1, text='Update', command=self.OnPressEnter)
    button.grid(column=1, row=1, sticky='EWNS')

    # Adding The list of all answers
    tree = Treeview(f1, columns=('sno', 'date', 'question'))
    tree.heading('sno', text='S. No')
    tree.heading('date', text='Date')
    tree.heading('question', text='Question')

    tree.column("#0", width=0, stretch=False)
    tree.column('sno', width=40, stretch=False, anchor='center')
    tree.column('date', width=120, stretch=False, anchor='center')
    tree.column('question', stretch=True, anchor='w')
    for idx, answer in enumerate(self.crawler.answer_list):
      tree.insert('', 'end', idx + 1, value=((idx + 1, answer[1], answer[2])))
    tree.grid(column=0, columnspan=2, row=2, sticky='EWNS')
    tree.bind("<Double-1>", self.tree_item_click)
    self.answer_tree = tree

    f2 = Frame(self)
    self.add(f1, text='Answer Backup', underline=7)
    self.add(f2, text='Analytics')

  def tree_item_click(self, event):
    idx_clicked = self.answer_tree.identify_row(event.y)
    if idx_clicked:
      print "Tree Item Clicked - ", idx_clicked

  def OnButtonClick(self):
    print "You clicked the button !"

  def OnPressEnter(self):
    print "You pressed enter !"

if __name__ == '__main__':

  # Initialize Application and Run Main Loop
  app = QuoraAnalyticsUI()
  app.mainloop()
  exit()
