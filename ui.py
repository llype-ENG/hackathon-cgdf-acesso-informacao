import tkinter as tk
from tkinter import filedialog, messagebox
from main import processar_planilha

def selecionar_planilha():
    arquivo = filedialog.askopenfilename(
        title="Selecione a planilha",
        filetypes=[("Planilhas Excel", "*.xlsx")]
    )

    if arquivo:
        processar_planilha(arquivo)
        messagebox.showinfo("Sucesso", "Planilha processada com sucesso!")

# 🔹 Criar janela principal
janela = tk.Tk()
janela.title("Classificação de Propostas - Hackathon")
janela.geometry("400x200")
janela.resizable(False, False)

# 🔹 Título
titulo = tk.Label(
    janela,
    text="Sistema de Classificação",
    font=("Arial", 14, "bold")
)
titulo.pack(pady=20)

# 🔹 Botão
botao = tk.Button(
    janela,
    text="Selecionar Planilha",
    command=selecionar_planilha,
    width=25
)
botao.pack(pady=20)

# 🔹 Loop da aplicação (ESSENCIAL)
janela.mainloop()
