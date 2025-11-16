import gi
import subprocess
import os

gi.require_version("Gtk", "3.0")  # ou "4.0" se preferir GTK 4
from gi.repository import Gtk

class RPMInstaller(Gtk.Window):
    def __init__(self):
        super().__init__(title="Instalador de RPM")
        self.set_border_width(10)
        self.set_default_size(400, 100)

        # Layout
        box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        self.add(box)

        # Botão para selecionar arquivo
        self.file_button = Gtk.Button(label="Selecionar arquivo RPM")
        self.file_button.connect("clicked", self.on_file_clicked)
        box.pack_start(self.file_button, True, True, 0)

        # Botão para instalar
        self.install_button = Gtk.Button(label="Instalar")
        self.install_button.connect("clicked", self.on_install_clicked)
        self.install_button.set_sensitive(False)
        box.pack_start(self.install_button, True, True, 0)

        # Label de status
        self.status_label = Gtk.Label(label="")
        box.pack_start(self.status_label, True, True, 0)

        self.rpm_path = None

    def on_file_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Escolha um arquivo RPM", parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        filter_rpm = Gtk.FileFilter()
        filter_rpm.set_name("Arquivos RPM")
        filter_rpm.add_pattern("*.rpm")
        dialog.add_filter(filter_rpm)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.rpm_path = dialog.get_filename()
            self.status_label.set_text(f"Selecionado: {os.path.basename(self.rpm_path)}")
            self.install_button.set_sensitive(True)
        dialog.destroy()

    def on_install_clicked(self, widget):
        if self.rpm_path:
            self.status_label.set_text("Instalando...")
            try:
                subprocess.run(["pkexec", "dnf", "install", "-y", self.rpm_path], check=True)
                self.status_label.set_text("Instalação concluída com sucesso!")
            except subprocess.CalledProcessError:
                self.status_label.set_text("Erro na instalação.")

win = RPMInstaller()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()