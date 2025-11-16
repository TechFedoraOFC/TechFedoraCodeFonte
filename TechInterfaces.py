import gi
import subprocess
import threading
import sys

# Definindo a versão GTK
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

# --- Configuração dos Ambientes de Desktop ---
# Mapeamento do nome de exibição para o nome do META-PACOTE DNF
# SUBSTITUA AQUI PELOS NOMES REAIS DOS SEUS META-PACOTES (techfedora-*)
DESKTOP_ENVIRONMENTS = {
    "GNOME": "gnome-shell",
    "KDE Plasma": "plasma-desktop",
    "Cinnamon": "cinnamon",
    "MATE": "mate-desktop"
}

class TechFedoraBRApp(Gtk.Window):
    """
    Aplicação GUI para gerenciar a instalação e desinstalação de
    Ambientes de Desktop (DEs) usando DNF, via meta-pacotes RPM.
    """
    def __init__(self):
        super().__init__(title="TechFedoraBR: Gerenciador de Desktops")
        self.set_border_width(10)
        self.set_default_size(500, 300)

        # Container principal de grade
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(20)
        grid.set_margin_top(20)
        grid.set_margin_bottom(20)
        grid.set_margin_start(20)
        grid.set_margin_end(20)
        self.add(grid)

        # Adicionar cabeçalhos
        header_name = Gtk.Label("Ambiente de Desktop")
        header_name.set_markup("<b>Ambiente de Desktop</b>")
        grid.attach(header_name, 0, 0, 1, 1)
        
        header_status = Gtk.Label("Status")
        header_status.set_markup("<b>Status</b>")
        grid.attach(header_status, 1, 0, 1, 1)

        # Linha inicial para o conteúdo
        row = 1
        self.de_widgets = {}

        # Iteramos sobre o nome da interface e o nome do pacote RPM
        for name, package_name in DESKTOP_ENVIRONMENTS.items():
            # Nome do DE
            label = Gtk.Label(name)
            label.set_halign(Gtk.Align.START)
            grid.attach(label, 0, row, 1, 1)

            # Label de Status (para mostrar 'Verificando...' ou 'Instalado')
            status_label = Gtk.Label("Verificando...")
            grid.attach(status_label, 1, row, 1, 1)

            # Botão de Ação
            action_button = Gtk.Button(label="Carregando...")
            # Passamos o nome do pacote para a função de clique
            action_button.connect("clicked", self.on_button_clicked, package_name)
            action_button.set_sensitive(False) # Desativa até a verificação inicial
            grid.attach(action_button, 2, row, 1, 1)

            # Armazena referências para atualização
            self.de_widgets[package_name] = {
                'status': status_label,
                'button': action_button
            }

            # Inicia a verificação de status em uma thread separada
            threading.Thread(target=self.initial_status_check, args=(package_name,)).start()

            row += 1

    def check_installation_status(self, package_name):
        """
        Verifica se o META-PACOTE está instalado localmente usando 'rpm -q'. 
        Retorna True ou False.
        """
        try:
            # rpm -q retorna 0 (sucesso) se o pacote estiver instalado, e 1 se não.
            rpm_check = subprocess.run(
                ['rpm', '-q', package_name],
                capture_output=True,
                text=True
            )
            return rpm_check.returncode == 0
            
        except FileNotFoundError:
            print("Erro: O comando 'rpm' não foi encontrado. Verificação falhou.")
            return False


    def update_gui_status(self, package_name, is_installed, is_busy=False):
        """Atualiza a GUI (deve ser chamada via GLib.idle_add)."""
        if package_name not in self.de_widgets:
            return False

        widgets = self.de_widgets[package_name]
        button = widgets['button']
        status_label = widgets['status']
        
        if is_busy:
            status_label.set_text("Em progresso...")
            button.set_sensitive(False)
            return False

        button.set_sensitive(True)
        
        if is_installed:
            button.set_label("Desinstalar")
            button.get_style_context().add_class("destructive-action")
            status_label.set_text("Instalado")
        else:
            button.set_label("Instalar")
            button.get_style_context().remove_class("destructive-action")
            status_label.set_text("Não Instalado")
        
        return False # Retorna False para que a função não seja chamada novamente


    def initial_status_check(self, package_name):
        """Thread worker para a verificação de status inicial."""
        is_installed = self.check_installation_status(package_name)
        # Atualiza a GUI na thread principal
        GLib.idle_add(self.update_gui_status, package_name, is_installed, False)


    def on_button_clicked(self, button, package_name):
        """Trata o clique no botão para instalar ou desinstalar."""
        current_label = button.get_label()

        if current_label == "Instalar":
            action = "install"
            
        elif current_label == "Desinstalar":
            action = "remove"
        else:
            return

        # Define a GUI como 'ocupada'
        # Usamos o status atual (antes da ação) como base para a próxima verificação
        is_installed_before_action = self.check_installation_status(package_name)
        GLib.idle_add(self.update_gui_status, package_name, is_installed_before_action, True)

        # Executa a ação em uma thread
        threading.Thread(target=self.execute_dnf_action, args=(action, package_name)).start()


    def execute_dnf_action(self, action, package_name):
        """Executa a ação DNF usando pkexec em uma thread separada."""
        if action == "install":
            # Usa 'dnf install' para meta-pacotes
            command = ['pkexec', 'dnf', 'install', package_name, '-y']
        elif action == "remove":
            # Usa 'dnf remove'. Manter o '--noautoremove' é mais seguro para meta-pacotes.
            command = ['pkexec', 'dnf', 'remove', package_name, '--noautoremove', '-y']
        else:
            return

        try:
            print(f"Executando: {' '.join(command)}")
            # O Polkit (pkexec) lidará com a solicitação gráfica de senha
            process = subprocess.run(command, check=False, capture_output=True, text=True)
            
            success = process.returncode == 0
            
            if not success:
                 # Mostra o erro para debug
                 print(f"Falha na operação DNF/pkexec para {package_name}. Erro: {process.stderr}")

        except Exception as e:
            print(f"Erro inesperado durante a execução do comando DNF: {e}")

        # Verifica o status final na thread principal (GUI)
        is_installed_after_action = self.check_installation_status(package_name)
        GLib.idle_add(self.update_gui_status, package_name, is_installed_after_action, False)


if __name__ == "__main__":
    # Estilo básico para destacar o botão de desinstalação
    css = b"""
    .destructive-action {
        background: #CC0000;
        color: white;
    }
    .destructive-action:hover {
        background: #FF3333;
    }
    """
    style_provider = Gtk.CssProvider()
    style_provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        Gtk.Window().get_screen(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    win = TechFedoraBRApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
