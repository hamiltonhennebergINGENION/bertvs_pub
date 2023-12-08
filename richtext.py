##############################################################################
#							Rich Text for Tkinter			                 #
##############################################################################
# Author: 		Matthaeus Gebauer	                                 		 #
# References: 		  Bryan Oakly	                                         #
#   https://stackoverflow.com/questions/63099026/fomatted-text-in-tkinter	 #
##############################################################################


import tkinter as tk
from tkinter import font as tkFont

class RichText(tk.Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = self.cget("font").split()
        default_font = tkFont.Font(family=font[0], size=int(font[1]))
        
        em = default_font.measure("m")
        default_size = default_font.cget("size")
        bold_font = tkFont.Font(**default_font.configure())
        italic_font = tkFont.Font(**default_font.configure())
        h1_font = tkFont.Font(**default_font.configure())

        bold_font.configure(weight="bold")
        italic_font.configure(slant="italic")
        h1_font.configure(size=int(default_size*2), weight="bold")

        self.tag_configure("bold", font=bold_font)
        self.tag_configure("italic", font=italic_font)
        self.tag_configure("h1", font=h1_font, spacing3=default_size, justify='center')

        lmargin2 = em + default_font.measure("\u2022 ")
        self.tag_configure("bullet", lmargin1=em, lmargin2=lmargin2)

    def insert_bullet(self, index, text):
        self.insert(index, f"\u2022 {text}", "bullet")
        
        
if __name__ == "__main__":
    root = tk.Tk()
    text = RichText(root, width=40, height=15, font=('Arial', 10))
    text.pack(fill="both", expand=True)


    text.insert("end", "Rich Text Example\n", "h1")
    text.insert("end", "Hello, world\n\n")
    text.insert_bullet("end", "Item 1\n")
    text.insert_bullet("end", "Item 2\n")

    text.insert("end", "\n")
    text.insert("end", "This line is bold\n", "bold")
    text.insert("end", "This line is italicized\n", "italic")

    root.mainloop()