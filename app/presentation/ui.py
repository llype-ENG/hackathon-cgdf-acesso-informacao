import tkinter as tk
from tkinter import filedialog, messagebox

from main import processar_planilha


def selecionar_planilha():
    arquivo = filedialog.askopenfilename(
        title="Selecione a planilha",
        filetypes=[("Planilhas Excel", "*.xlsx")],
    )
    if not arquivo:
        return

    try:
        processar_planilha(arquivo)
    except Exception as exc:
        messagebox.showerror("Erro", f"Não foi possível processar a planilha:\n{exc}")
        return

    messagebox.showinfo("Sucesso", "Planilha processada com sucesso!")


def build_ui():
    janela = tk.Tk()
    janela.title("Classificação de Propostas - Hackathon")
    janela.geometry("400x200")
    janela.resizable(False, False)

    titulo = tk.Label(janela, text="Sistema de Classificação", font=("Arial", 14, "bold"))
    titulo.pack(pady=20)

    botao = tk.Button(
        janela,
        text="Selecionar Planilha",
        command=selecionar_planilha,
        width=25,
    )
    botao.pack(pady=20)
    return janela


if __name__ == "__main__":
    build_ui().mainloop()
