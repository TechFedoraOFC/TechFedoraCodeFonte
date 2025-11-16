import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gio, Gdk, GLib

# =================================================================
# VARIAVEIS DE CONFIGURAÇÃO DO MATE (CHAVES DCONF/GSETTINGS)
# =================================================================
# Chave que controla se ícones de desktop (Lixeira, Home, etc.) devem ser exibidos
CHAVE_DESKTOP_ICONS = "show-desktop-icons"
SCHEMA_DESKTOP = "org.mate.background"

# Chave que controla se a Lixeira (Trash) aparece no desktop
CHAVE_LIXEIRA = "trash-icon-visible"
SCHEMA_CAJA_DESKTOP = "org.mate.caja.desktop"


class MeuTweakApp(Gtk.Window):
    """Classe principal do nosso aplicativo de ajustes."""
    def __init__(self):
        # 1. Configuração Básica da Janela
        Gtk.Window.__init__(self, title="Meu Configurador MATE (M-Tweak Personalizado)")
        self.set_border_width(10)
        self.set_default_size(500, 300)

        # 2. Inicializa os objetos GSettings (comunicação Dconf)
        self.settings_desktop = Gio.Settings.new(SCHEMA_DESKTOP)
        self.settings_caja = Gio.Settings.new(SCHEMA_CAJA_DESKTOP)

        # 3. Cria o Notebook (Abas) para organizar as configurações
        notebook = Gtk.Notebook()
        self.add(notebook)

        # 4. Adiciona a Aba 1: Área de Trabalho
        self.criar_aba_desktop(notebook)

        # 5. Adiciona a Aba 2: Aparência (apenas como placeholder)
        self.criar_aba_aparencia(notebook)


    def criar_aba_desktop(self, notebook):
        """Cria o conteúdo da aba 'Área de Trabalho'."""
        
        # Cria uma Box para agrupar as opções (vertical)
        vbox_desktop = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        vbox_desktop.set_border_width(10)

        # --- Opção 1: Mostrar Ícones do Desktop ---
        
        # Usa Gtk.Switch para um controle ON/OFF
        label_desktop = Gtk.Label(label="Mostrar Ícones na Área de Trabalho:", xalign=0)
        switch_desktop = Gtk.Switch()
        
        # Conecta o switch diretamente à chave GSettings. É a forma mais 'limpa'!
        # O estado do switch reflete automaticamente o valor do Dconf.
        self.settings_desktop.bind(
            CHAVE_DESKTOP_ICONS,
            switch_desktop,
            "active",
            Gio.SettingsBindFlags.DEFAULT
        )
        
        # Cria uma Box horizontal para o rótulo e o switch
        hbox_desktop = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        hbox_desktop.pack_start(label_desktop, True, True, 0)
        hbox_desktop.pack_end(switch_desktop, False, False, 0)
        vbox_desktop.pack_start(hbox_desktop, False, False, 0)
        
        # --- Opção 2: Mostrar Ícone da Lixeira ---

        label_lixeira = Gtk.Label(label="Mostrar Ícone da Lixeira (Requer ícones Ativos):", xalign=0)
        switch_lixeira = Gtk.Switch()
        
        # Conecta o switch da Lixeira à chave específica do Caja (Desktop)
        self.settings_caja.bind(
            CHAVE_LIXEIRA,
            switch_lixeira,
            "active",
            Gio.SettingsBindFlags.DEFAULT
        )
        
        hbox_lixeira = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        hbox_lixeira.pack_start(label_lixeira, True, True, 0)
        hbox_lixeira.pack_end(switch_lixeira, False, False, 0)
        vbox_desktop.pack_start(hbox_lixeira, False, False, 0)

        # Adiciona a aba ao Notebook
        notebook.append_page(vbox_desktop, Gtk.Label(label="Área de Trabalho"))


    def criar_aba_aparencia(self, notebook):
        """Cria um placeholder para a aba 'Aparência'."""
        
        vbox_aparencia = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        label = Gtk.Label(label="Aqui você poderia adicionar opções de Temas, Fontes, etc.")
        
        vbox_aparencia.pack_start(label, True, True, 0)
        notebook.append_page(vbox_aparencia, Gtk.Label(label="Aparência"))


# =================================================================
# EXECUÇÃO DO APLICATIVO
# =================================================================

if __name__ == '__main__':
    # Garante que o killall caja seja chamado ao fechar a janela
    # para forçar a atualização dos ícones (opcional, mas recomendado)
    def on_destroy(window):
        import subprocess
        try:
            subprocess.run(['killall', 'caja'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            # Caso o caja não esteja rodando (instalação minimalista extrema), ignoramos
            pass
        Gtk.main_quit()

    win = MeuTweakApp()
    win.connect("destroy", on_destroy)
    win.show_all()
    Gtk.main()