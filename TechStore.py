import gi
import os
import subprocess
import threading
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango, GLib

# Classe principal que define a janela e o comportamento da loja de aplicativos
class AppStore(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(900, 700)
        self.set_title("TechStore")
        
        # Define a janela como dark
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)
        self.get_style_context().add_class("techstore-main-window")

        # Cria a barra de cabeçalho
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.set_title("TechStore")
        self.set_titlebar(header_bar)

        # Adiciona a notebook com abas
        self.notebook = Gtk.Notebook()
        self.add(self.notebook)

        # Configura as abas
        self.setup_browse_tab()
        self.setup_updates_tab() # <-- Configuração da aba de Atualizações
        
        # Guarda a lista de IDs de aplicativos instalados para uma verificação mais eficiente
        self.installed_app_ids = set()

        # Inicia a checagem de apps instalados e atualizações em uma thread separada
        threading.Thread(target=self.initial_check).start()

    def initial_check(self):
        # A checagem inicial deve ser feita em uma thread para não travar a UI
        self.installed_app_ids = self.get_installed_flatpaks()
        GLib.idle_add(self.populate_browse_tab)
        # O check_for_updates já é chamado aqui no início
        self.check_for_updates() 
        return False # Retorna False para que o GLib não chame novamente

    def setup_browse_tab(self):
        """
        Configura a aba para navegar e instalar aplicativos com barra lateral.
        """
        main_browse_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        
        # Dados de exemplo para os aplicativos com seus IDs de Flatpak
        self.app_list = [
            {"name": "GIMP", "description": "Editor de imagens avançado.", "flatpak_id": "org.gimp.GIMP", "category": "Gráficos", "icon": "gimp"},
            {"name": "Inkscape", "description": "Editor de gráficos vetoriais de código aberto.", "flatpak_id": "org.inkscape.Inkscape", "category": "Gráficos", "icon": "inkscape"},
            {"name": "VLC", "description": "Reprodutor de mídia multiplataforma.", "flatpak_id": "org.videolan.VLC", "category": "Multimídia", "icon": "vlc"},
            {"name": "Blender", "description": "Software de criação 3D gratuito e de código aberto.", "flatpak_id": "org.blender.Blender", "category": "Multimídia", "icon": "blender"},
            {"name": "Audacity", "description": "Editor e gravador de áudio multifuncional.", "flatpak_id": "org.audacityteam.Audacity", "category": "Multimídia", "icon": "audacity"},
            {"name": "OBS Studio", "description": "Software de transmissão e gravação de vídeo.", "flatpak_id": "com.obsproject.Studio", "category": "Multimídia", "icon": "com.obsproject.Studio"},
            {"name": "Krita", "description": "Software de pintura digital profissional.", "flatpak_id": "org.kde.krita", "category": "Gráficos", "icon": "krita"},
            {"name": "Shotcut", "description": "Editor de vídeo gratuito e de código aberto.", "flatpak_id": "org.shotcut.Shotcut", "category": "Multimídia", "icon": "shotcut"},
            {"name": "Darktable", "description": "Aplicativo de fluxo de trabalho de fotografia.", "flatpak_id": "org.darktable.Darktable", "category": "Gráficos", "icon": "darktable"},
            {"name": "Google Chrome", "description": "O Google Chrome é um navegador de internet rápido, seguro e fácil de usar, desenvolvido pelo Google. Ele oferece uma experiência de navegação intuitiva em todos os seus dispositivos. O Chrome conta com uma barra de endereços inteligente (Omnibox) que preenche automaticamente as URLs, acelerando sua navegação. Para sua segurança, ele usa a Navegação Segura Aprimorada, que bloqueia automaticamente sites perigosos e avisa sobre ameaças. Você pode navegar sem deixar rastros com o modo de navegação anônima. Ao fazer login com sua Conta do Google, o navegador sincroniza seus favoritos, senhas e histórico em todos os seus dispositivos, mantendo a experiência contínua. Além disso, o Chrome tem recursos integrados como um tradutor de páginas e a opção de pesquisa por voz. Ele também oferece um modo de Economia de dados para reduzir o consumo de internet móvel. Com a vasta biblioteca da Chrome Web Store, você pode personalizar o navegador com extensões e temas, tornando sua experiência de navegação única.", "flatpak_id": "com.google.Chrome", "category": "Internet", "icon": "google-chrome"},
            {"name": "Mozilla Firefox", "description": "O Mozilla Firefox é um navegador rápido, seguro e privado. Desenvolvido pela Mozilla, uma organização sem fins lucrativos, ele coloca o controle da sua experiência online em suas mãos. Com uma navegação inteligente, o Firefox oferece uma interface intuitiva e fácil de usar. Sua principal característica é a proteção de privacidade aprimorada, com bloqueio de rastreadores e scripts que tentam coletar seus dados. Ele permite navegar sem ser seguido por anúncios intrusivos ou empresas de marketing. O Firefox também tem uma vasta biblioteca de complementos para personalização e funcionalidades extras, e sincroniza seus favoritos e histórico entre dispositivos. Baixe o Firefox para ter uma navegação mais livre e privada.", "flatpak_id": "org.mozilla.firefox", "category": "Internet", "icon": "firefox"},
            {"name": "VS Code", "description": "Poderoso editor de código para desenvolvimento.", "flatpak_id": "com.visualstudio.code", "category": "Desenvolvimento", "icon": "vscode"},
            {"name": "LibreOffice", "description": "Suite de escritório completa e gratuita.", "flatpak_id": "org.libreoffice.LibreOffice", "category": "Escritório", "icon": "libreoffice"},
            {"name": "Gnome Boxes", "description": "App de Virtualização simples do GNOME.", "flatpak_id": "org.gnome.Boxes", "category": "Virtualização", "icon": "gnome-boxes"},
            {"name": "Gedit", "description": "Um Editor de Texto Padrão do GNOME.", "flatpak_id": "org.gnome.gedit", "category": "Desenvolvimento", "icon": "gedit"},
            {"name": "Gnome Builder", "description": "Uma IDE Completa do GNOME pra Desenvolver apps GNOME.", "flatpak_id": "org.gnome.Builder", "category": "Desenvolvimento", "icon": "org.gnome.Builder"},
            {"name": "VS Codium", "description": "Uma versão do VS Code Sem telemetria.", "flatpak_id": "com.vscodium.codium", "category": "Desenvolvimento", "icon": "vscodium"},
            {"name": "GitKraken", "description": "Client Git com interface gráfica para facilitar o gerenciamento de repositórios.", "flatpak_id": "com.axosoft.GitKraken", "category": "Desenvolvimento", "icon": "gitkraken"},
            {"name": "Brave", "description": "O Brave é um navegador de internet rápido e focado em privacidade, que bloqueia anúncios e rastreadores por padrão. Ele foi construído com base no Chromium, mas com um forte foco em segurança e desempenho. Com o Brave, você não precisa de extensões adicionais para bloquear anúncios, o que acelera o carregamento das páginas. Ele tem um sistema de recompensas único, o Brave Rewards, que permite que você ganhe tokens (BAT) por assistir a anúncios que respeitam a sua privacidade, podendo usá-los para apoiar seus criadores de conteúdo favoritos. A interface é limpa e minimalista. O Brave se destaca por oferecer uma navegação muito mais rápida e segura, sem o incômodo dos anúncios.", "flatpak_id": "com.brave.Browser", "category": "Internet", "icon": "brave-browser"},
            {"name": "Chromium", "description": "O Chromium é um projeto de código aberto que serve como base para o Google Chrome. Ele é um navegador funcional e minimalista, mas diferente do Chrome, não inclui recursos proprietários do Google. O Chromium não possui o sistema de atualização automática do Google, o que significa que o usuário é responsável por mantê-lo atualizado manualmente. Ele também não vem com alguns codecs de mídia ou a integração com serviços do Google que o Chrome possui. Por ser um projeto de código aberto, o Chromium é uma opção popular para desenvolvedores e usuários que preferem um navegador sem as restrições e recursos fechados de softwares proprietários. Ele oferece a mesma velocidade e estabilidade do Chrome, mas em uma versão mais básica e controlada pela comunidade.", "flatpak_id": "org.chromium.Chromium", "category": "Internet", "icon": "org.chromium.Chromium"},
            {"name": "Discord", "description": "Um aplicativo de chat de voz, video e texto muito popular, especialmente entre comunidades de jogos. \n\nEle permite criar servidores para diferentes grupos e oferece uma forma fácil de se comunicar com amigos e colegas.", "flatpak_id": "com.discordapp.Discord", "category": "Internet", "icon": "com.discordapp.Discord"},
            {"name": "Podman Desktop", "description": "Podman desktop é o gerenciador de containers do Podman da Rad Hat", "flatpak_id": "io.podman_desktop.PodmanDesktop", "category": "Virtualização", "icon": "io.podman_desktop.PodmanDesktop"},
            {"name": "Olho do GNOME", "description": "O Olho do GNOME é visualizador de imagens oficial do GNOME", "flatpak_id": "org.gnome.eog", "category": "Gráficos", "icon": "org.gnome.eog"},
            {"name": "Celluloid", "description": "O Celluloid é um reprodutor de midía simples", "flatpak_id": "io.github.celluloid_player.Celluloid", "category": "Multimídia", "icon": "io.github.celluloid_player.Celluloid"},
            {"name": "KdenLive", "description": "O KdenLive é um editor de video grátis de codigo aberto com suporte á muito formatos de multimídia", "flatpak_id": "org.kde.kdenlive", "category": "Multimídia", "icon": "org.kde.kdenlive"},
            {"name": "OpenShot", "description": "O OpenShot é um editor de video Simples", "flatpak_id": "org.openshot.OpenShot", "category": "Multimídia", "icon": "org.openshot.OpenShot"},
            {"name": "WPS Office", "description": "O WPS Office é um office gratuito de codigo fechado e facil de usar", "flatpak_id": "com.wps.Office", "category": "Escritório", "icon": "com.wps.Office"}
        ]
        
        self.categories = ["Todas", "Multimídia", "Gráficos", "Internet", "Desenvolvimento", "Escritório", "Virtualização"]
        self.search_term = ""
        
        # Cria a barra lateral de categorias
        self.category_stack = Gtk.Stack()
        self.category_sidebar = Gtk.StackSidebar()
        self.category_sidebar.set_stack(self.category_stack)
        main_browse_box.pack_start(self.category_sidebar, False, False, 0)
        
        # Box para o conteúdo principal (pesquisa e aplicativos)
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_border_width(10)
        
        # Barra de busca
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        search_icon = Gtk.Image.new_from_icon_name("system-search-symbolic", Gtk.IconSize.MENU)
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar aplicativos...")
        self.search_entry.connect("search-changed", self.on_search_changed)
        search_box.pack_start(search_icon, False, False, 0)
        search_box.pack_start(self.search_entry, True, True, 0)
        content_box.pack_start(search_box, False, False, 0)

        # Adiciona a stack de categorias ao conteúdo
        content_box.pack_start(self.category_stack, True, True, 0)
        main_browse_box.pack_start(content_box, True, True, 0)
        
        # Barra de status para mensagens
        self.status_bar = Gtk.Statusbar()
        self.context_id = self.status_bar.get_context_id("app-store-context")
        content_box.pack_end(self.status_bar, False, False, 0)
        
        self.notebook.append_page(main_browse_box, Gtk.Label(label="Aplicativos"))

    def setup_updates_tab(self):
        """
        Configura a aba para verificar e aplicar atualizações.
        """
        updates_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        updates_box.set_border_width(10)

        # StackSwitcher para gerenciar diferentes visualizações (carregando, lista, sem atualizações)
        self.updates_stack = Gtk.Stack()
        self.updates_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        updates_box.pack_start(self.updates_stack, True, True, 0)
        
        # -- View de Carregamento --
        loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        loading_spinner = Gtk.Spinner()
        loading_spinner.start()
        loading_box.pack_start(loading_spinner, True, True, 0)
        loading_label = Gtk.Label(label="Verificando atualizações...")
        loading_box.pack_start(loading_label, True, True, 0)
        self.updates_stack.add_named(loading_box, "loading")
        
        # -- View da Lista de Atualizações --
        list_box_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.updates_list_box = Gtk.ListBox()
        self.updates_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.updates_list_box)
        list_box_container.pack_start(scrolled_window, True, True, 0)

        # Botão de Atualizar Tudo
        self.update_all_button = Gtk.Button(label="Atualizar Tudo")
        self.update_all_button.get_style_context().add_class("suggested-action")
        self.update_all_button.connect("clicked", self.on_update_all_clicked)
        list_box_container.pack_end(self.update_all_button, False, False, 0)
        self.updates_stack.add_named(list_box_container, "updates")

        # -- View de 'Nenhuma Atualização' --
        no_updates_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        no_updates_label = Gtk.Label(label="Nenhum App flatpak ta precisando ser atualizado")
        no_updates_box.pack_start(Gtk.Image.new_from_icon_name("software-update-available-symbolic", Gtk.IconSize.DIALOG), False, False, 0)
        no_updates_box.pack_start(no_updates_label, False, False, 0)
        self.updates_stack.add_named(no_updates_box, "no-updates")
        
        # Adiciona um botão de recarregar
        reload_button = Gtk.Button(label="Checar Atualizações")
        reload_button.connect("clicked", lambda x: threading.Thread(target=self.check_for_updates).start())
        updates_box.pack_end(reload_button, False, False, 0)


        # Adiciona a aba de atualizações
        self.notebook.append_page(updates_box, Gtk.Label(label="Atualizações"))
        self.updates_stack.set_visible_child_name("loading") # Começa na tela de carregamento


    def get_installed_flatpaks(self):
        """
        Obtém uma lista de todos os IDs de aplicativos Flatpak instalados.
        Retorna um conjunto para buscas rápidas.
        """
        try:
            result = subprocess.run(
                ["flatpak", "list", "--app", "--columns=application"],
                capture_output=True,
                text=True,
                check=True
            )
            # Filtra linhas vazias e retorna um set
            return set(filter(None, result.stdout.strip().split('\n')))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    def populate_browse_tab(self):
        """
        Popula a Gtk.FlowBox com os cards de aplicativos, aplicando filtros.
        Agora, popula uma FlowBox para cada categoria.
        """
        for child in self.category_stack.get_children():
            self.category_stack.remove(child)

        for category in self.categories:
            scrolled_window = Gtk.ScrolledWindow()
            scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            
            flow_box = Gtk.FlowBox()
            flow_box.set_valign(Gtk.Align.START)
            flow_box.set_homogeneous(True)
            flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
            flow_box.set_column_spacing(15)
            flow_box.set_row_spacing(15)
            flow_box.set_min_children_per_line(2)
            
            filtered_apps = [
                app_data for app_data in self.app_list 
                if (category == "Todas" or app_data["category"] == category) and 
                   (self.search_term.lower() in app_data["name"].lower())
            ]

            if not filtered_apps:
                no_results_label = Gtk.Label(label="Nenhum app foi encontrado")
                no_results_label.get_style_context().add_class("no-results-label")
                no_results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                no_results_box.pack_start(no_results_label, True, True, 0)
                flow_box.add(no_results_box)
            else:
                for app_data in filtered_apps:
                    app_card = self.create_app_card(app_data)
                    flow_box.add(app_card)
            
            scrolled_window.add(flow_box)
            self.category_stack.add_titled(scrolled_window, category, category)
        
        self.show_all()

    def create_app_card(self, app_data):
        """
        Cria um card para um único aplicativo e define o botão(ões) dinamicamente.
        """
        card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card_box.set_size_request(200, 250)
        card_box.get_style_context().add_class("app-card")
        
        # Ícone do aplicativo
        icon = Gtk.Image.new_from_icon_name(app_data.get("icon", "application-x-executable-symbolic"), Gtk.IconSize.DIALOG)
        icon.set_pixel_size(64)
        card_box.pack_start(icon, False, False, 0)
        
        # Adiciona o nome do aplicativo
        name_label = Gtk.Label(label=app_data["name"])
        name_label.set_halign(Gtk.Align.CENTER)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.set_markup(f"<b><big>{app_data['name']}</big></b>")
        card_box.pack_start(name_label, False, False, 0)

        # Adiciona a descrição truncada para o card
        description_text = app_data["description"]
        if len(description_text) > 80: # Limite de caracteres para o resumo
            description_text = description_text[:77] + "..."
        description_label = Gtk.Label(label=description_text)
        description_label.set_justify(Gtk.Justification.CENTER)
        description_label.set_line_wrap(True)
        description_label.set_max_width_chars(30)
        description_label.get_style_context().add_class("app-description")
        card_box.pack_start(description_label, True, True, 0)
        
        # Container para os botões
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.CENTER)
        card_box.pack_end(button_box, False, False, 0)
        
        # Botão "Ver Detalhes"
        details_button = Gtk.Button(label="Detalhes do App")
        details_button.connect("clicked", lambda _, data=app_data: self.on_details_button_clicked(data))
        button_box.pack_start(details_button, True, True, 0)

        is_installed = app_data["flatpak_id"] in self.installed_app_ids
        
        if is_installed:
            # Botão "Abrir"
            open_button = Gtk.Button(label="Abrir")
            open_button.get_style_context().add_class("suggested-action")
            open_button.connect("clicked", lambda _, app_id=app_data["flatpak_id"]: self.on_open_button_clicked(app_id))
            button_box.pack_start(open_button, True, True, 0)

            # Botão "Desinstalar"
            uninstall_button = Gtk.Button(label="Desinstalar")
            uninstall_button.connect("clicked", lambda _, app_id=app_data["flatpak_id"], button_box=button_box: self.on_uninstall_button_clicked(app_id, button_box))
            button_box.pack_start(uninstall_button, True, True, 0)

        else:
            # Botão "Instalar"
            install_button = Gtk.Button(label="Instalar")
            install_button.get_style_context().add_class("suggested-action")
            install_button.connect("clicked", lambda _, app_id=app_data["flatpak_id"], button_box=button_box: self.on_install_button_clicked(app_id, button_box))
            button_box.pack_start(install_button, True, True, 0)
        
        return card_box

    def on_details_button_clicked(self, app_data):
        # Implementação da tela de detalhes
        detail_window = Gtk.ApplicationWindow(application=self.get_application(), title=f"Detalhes de {app_data['name']}")
        detail_window.set_default_size(500, 600)
        detail_window.get_style_context().add_class("techstore-detail-window")
        
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.set_title(app_data["name"])
        header_bar.set_subtitle(app_data["category"])
        detail_window.set_titlebar(header_bar)

        detail_view = self.create_app_detail_view(app_data, detail_window)
        detail_window.add(detail_view)
        detail_window.show_all()

    def create_app_detail_view(self, app_data, parent_window):
        """
        Cria a interface da tela de detalhes de um aplicativo.
        """
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_border_width(20)

        # Box para o cabeçalho (ícone e nome)
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        header_box.set_halign(Gtk.Align.CENTER)
        
        icon = Gtk.Image.new_from_icon_name(app_data.get("icon", "application-x-executable-symbolic"), Gtk.IconSize.DIALOG)
        icon.set_pixel_size(128)
        header_box.pack_start(icon, False, False, 0)
        
        name_label = Gtk.Label(label=app_data["name"])
        name_label.set_markup(f"<big><b>{app_data['name']}</b></big>")
        header_box.pack_start(name_label, False, False, 0)
        
        main_box.pack_start(header_box, False, False, 0)

        # Janela de rolagem para a descrição
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        description_label = Gtk.Label(label=app_data["description"])
        description_label.set_justify(Gtk.Justification.LEFT)
        description_label.set_line_wrap(True)
        description_label.set_xalign(0)
        description_label.set_yalign(0)
        
        viewport = Gtk.Viewport()
        viewport.add(description_label)
        scrolled_window.add(viewport)
        main_box.pack_start(scrolled_window, True, True, 0)
        
        # Informações adicionais
        info_grid = Gtk.Grid()
        info_grid.set_column_spacing(10)
        info_grid.set_row_spacing(5)
        info_grid.set_halign(Gtk.Align.START)

        info_grid.attach(Gtk.Label(label="<b>Categoria:</b>", use_markup=True), 0, 0, 1, 1)
        info_grid.attach(Gtk.Label(label=app_data["category"]), 1, 0, 1, 1)
        
        info_grid.attach(Gtk.Label(label="<b>ID:</b>", use_markup=True), 0, 1, 1, 1)
        info_grid.attach(Gtk.Label(label=app_data["flatpak_id"]), 1, 1, 1, 1)
        
        main_box.pack_start(info_grid, False, False, 0)

        # Botões de ação na parte inferior
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.CENTER)
        
        is_installed = app_data["flatpak_id"] in self.installed_app_ids
        
        if is_installed:
            open_button = Gtk.Button(label="Abrir")
            open_button.get_style_context().add_class("suggested-action")
            open_button.connect("clicked", lambda _, app_id=app_data["flatpak_id"]: self.on_open_button_clicked(app_id))
            button_box.pack_start(open_button, True, True, 0)

            uninstall_button = Gtk.Button(label="Desinstalar")
            uninstall_button.connect("clicked", lambda _, app_id=app_data["flatpak_id"]: self.on_uninstall_button_clicked_detail(app_id, parent_window))
            button_box.pack_start(uninstall_button, True, True, 0)

        else:
            install_button = Gtk.Button(label="Instalar")
            install_button.get_style_context().add_class("suggested-action")
            install_button.connect("clicked", lambda _, app_id=app_data["flatpak_id"]: self.on_install_button_clicked_detail(app_id, parent_window))
            button_box.pack_start(install_button, True, True, 0)
        
        main_box.pack_end(button_box, False, False, 0)

        return main_box

    # Funções de instalação/desinstalação com tratamento de janela de detalhes
    def on_install_button_clicked_detail(self, app_id, window):
        self.status_bar.push(self.context_id, f"Instalando o app {app_id}...")
        window.destroy() # Fecha a janela de detalhes
        threading.Thread(target=self.run_flatpak_command, args=(["flatpak", "install", "-y", "flathub", app_id], app_id)).start()

    def on_uninstall_button_clicked_detail(self, app_id, window):
        self.status_bar.push(self.context_id, f"Desinstalando o app {app_id}...")
        window.destroy() # Fecha a janela de detalhes
        threading.Thread(target=self.run_flatpak_command, args=(["flatpak", "uninstall", "-y", app_id], app_id)).start()

    def on_search_changed(self, entry):
        self.search_term = entry.get_text()
        self.populate_browse_tab()
        
    def on_install_button_clicked(self, app_name, parent_button_box):
        self.status_bar.push(self.context_id, f"Instalando o app {app_name}...")
        for child in parent_button_box.get_children():
            child.set_sensitive(False)
        thread = threading.Thread(target=self.run_flatpak_command, args=(["flatpak", "install", "-y", "flathub", app_name], app_name, parent_button_box))
        thread.start()

    def on_uninstall_button_clicked(self, app_name, parent_button_box):
        self.status_bar.push(self.context_id, f"Desinstalando o app {app_name}...")
        for child in parent_button_box.get_children():
            child.set_sensitive(False)
        thread = threading.Thread(target=self.run_flatpak_command, args=(["flatpak", "uninstall", "-y", app_name], app_name, parent_button_box))
        thread.start()
        
    def on_open_button_clicked(self, app_name):
        self.status_bar.push(self.context_id, f"Iniciando {app_name}...")
        try:
            subprocess.Popen(["flatpak", "run", app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.status_bar.push(self.context_id, f"✅ Aplicativo {app_name} iniciado.")
        except FileNotFoundError:
            self.status_bar.push(self.context_id, "Erro: O comando 'flatpak' não foi encontrado.")
        except Exception as e:
            self.status_bar.push(self.context_id, f"Erro ao iniciar o aplicativo: {e}")

    def run_flatpak_command(self, command, app_name, parent_button_box=None):
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            if "uninstall" in command:
                status = "Desinstalação bem-sucedida"
            else:
                status = "Instalação bem-sucedida"
            GLib.idle_add(self.update_ui_after_command, status, app_name, parent_button_box)
        except subprocess.CalledProcessError as e:
            GLib.idle_add(self.update_ui_after_command, f"Erro: {e.stderr.strip() or e.stdout.strip() or 'Falha na execução.'}", app_name, parent_button_box)
        except FileNotFoundError:
            GLib.idle_add(self.update_ui_after_command, "Erro: 'flatpak' não encontrado.", app_name, parent_button_box)
        return False
        
    def update_ui_after_command(self, status, app_name, parent_button_box):
        self.status_bar.push(self.context_id, f"Status: {status} Operação do Flatpak foi concluida se for instalação do app é ideal reiniciar o computador {app_name}.")
        # Reatualiza a lista de apps instalados e a UI
        self.installed_app_ids = self.get_installed_flatpaks()
        self.populate_browse_tab()
        # Não é necessário chamar show_message se o status_bar já foi atualizado

        # Se o botão-pai foi fornecido (card na aba navegar), reativa os botões do card.
        # Mas como a populate_browse_tab recria todos os cards, isso não é estritamente necessário
        # a menos que o comando falhe e o card não seja reconstruído, o que é coberto pela
        # recriação total.
        
        return False

    # --- Implementação das Funções de Atualização ---
    
    def check_for_updates(self):
        """
        Checa por atualizações de Flatpak e DNF em threads separadas.
        É chamado dentro de uma thread separada (initial_check/reload_button).
        """
        GLib.idle_add(self.updates_stack.set_visible_child_name, "loading")
        
        # Roda os checks de forma síncrona dentro desta thread
        dnf_updates = self.check_dnf_updates()
        flatpak_updates = self.check_flatpak_updates()

        updates = []
        if dnf_updates:
            updates.append("--- Atualizações DNF/RPM (pkcon) ---")
            updates.extend(dnf_updates)
        if flatpak_updates and flatpak_updates[0] != "Nothing to do.":
            updates.append("\n--- Atualizações Flatpak ---")
            updates.extend(flatpak_updates)

        GLib.idle_add(self.populate_updates_list, updates)
        return False

    def check_dnf_updates(self):
        """
        Usa 'pkcon get-updates' para checar por atualizações de pacotes do sistema (DNF/RPM).
        """
        updates = []
        try:
            # Usando pkcon (PackageKit) pois geralmente é mais amigável em ambientes gráficos.
            process = subprocess.run(['pkcon', 'get-updates'], capture_output=True, text=True, check=False)
            output = process.stdout.strip()
            
            # Filtra apenas as linhas com o nome dos pacotes
            lines = output.splitlines()
            in_list = False
            for line in lines:
                if line.strip().startswith('Atualizações disponíveis:') or line.strip().startswith('Updates available:'):
                    in_list = True
                    continue
                if in_list and line.strip() and not line.startswith('Terminado'):
                    updates.append(line.strip())

        except FileNotFoundError:
            updates.append("Erro: O comando 'pkcon' não foi encontrado.")
        except Exception:
             # Captura erros gerais como permissão negada, etc.
             if not updates:
                 updates.append("Não foi possível verificar as atualizações DNF/RPM.")
        return updates

    def check_flatpak_updates(self):
        """
        Usa 'flatpak update --dry-run' para checar por atualizações Flatpak.
        """
        updates = []
        try:
            process = subprocess.run(['flatpak', 'update', '-y',], capture_output=True, text=True, check=False)
            output = process.stdout.strip()
            
            if "Nothing to do" in output:
                updates.append("Nothing to do.")
            else:
                # O dry-run lista as atualizações, vamos extrair as linhas que contêm o nome/versão.
                lines = output.splitlines()
                # Procuramos a tabela de atualizações
                start_parsing = False
                for line in lines:
                    if line.startswith('Application ID') or line.startswith('Runtime ID'):
                        start_parsing = True
                        updates.append(line) # Adiciona o cabeçalho
                    elif start_parsing and line.startswith('======') or line.startswith('-------'):
                         updates.append(line) # Adiciona a linha separadora
                    elif start_parsing and line.strip() and not line.startswith('Required runtime'):
                        updates.append(line)
        except FileNotFoundError:
            updates.append("Erro: O comando 'flatpak' não foi encontrado.")
        return updates

    def populate_updates_list(self, updates):
        """
        Preenche a Gtk.ListBox com os resultados da checagem de atualizações.
        """
        # Remove todas as linhas existentes
        for row in self.updates_list_box.get_children():
            self.updates_list_box.remove(row)
        
        # Filtra as linhas vazias que podem ter sobrado
        updates = [u for u in updates if u.strip()]

        if not updates or (len(updates) == 1 and updates[0].endswith("Nothing to do.")):
            self.updates_stack.set_visible_child_name("no-updates")
            self.update_all_button.set_sensitive(False)
            return
            
        for update_line in updates:
            row_label = Gtk.Label()
            row_label.set_markup(f"<code>{update_line}</code>" if not update_line.startswith("---") else f"<b>{update_line}</b>")
            row_label.set_justify(Gtk.Justification.LEFT)
            row_label.set_xalign(0)
            
            row = Gtk.ListBoxRow()
            row.add(row_label)
            self.updates_list_box.add(row)

        self.updates_stack.set_visible_child_name("updates")
        self.update_all_button.set_sensitive(True)
        self.updates_list_box.show_all()

    def on_update_all_clicked(self, button):
        """
        Inicia o processo de atualização completo em uma nova thread.
        """
        self.show_message("Atualizando...", "Iniciando a atualização de todos os pacotes. A interface pode ficar lenta. Uma notificação aparecerá ao final.")
        button.set_sensitive(False)
        button.set_label("Atualizando...")
        
        # Inicia a atualização em uma nova thread para não travar a UI
        threading.Thread(target=self.apply_updates, args=(button,)).start()

    def apply_updates(self, button):
        """
        Executa os comandos pkcon e flatpak para aplicar todas as atualizações.
        """
        try:
            # 1. Atualiza pacotes do sistema (DNF/RPM via pkcon)
            GLib.idle_add(self.status_bar.push, self.context_id, "Executando 'pkcon update -y'...")
            subprocess.run(['pkcon', 'update', '-y'], check=True, capture_output=True, text=True)
            
            # 2. Atualiza Flatpaks
            GLib.idle_add(self.status_bar.push, self.context_id, "Executando 'flatpak update -y'...")
            subprocess.run(['flatpak', 'update', '--noninteractive', '-y'], check=True, capture_output=True, text=True)
            
            # Notifica o usuário sobre o sucesso
            GLib.idle_add(self.show_message, "Sucesso", "Todas as atualizações foram aplicadas com sucesso!")
        except subprocess.CalledProcessError as e:
            GLib.idle_add(self.show_message, "Erro de Comando", f"Ocorreu um erro ao aplicar as atualizações. Verifique o console para detalhes: {e.stderr.strip() or e.stdout.strip()}")
        except FileNotFoundError:
            GLib.idle_add(self.show_message, "Erro", "pkcon ou flatpak não foram encontrados.")
        except Exception as e:
            GLib.idle_add(self.show_message, "Erro Desconhecido", f"Ocorreu um erro ao aplicar as atualizações: {e}")
        finally:
            # Reativa o botão e refaz a checagem
            GLib.idle_add(button.set_sensitive, False) # Desabilita o botão até a próxima checagem
            GLib.idle_add(button.set_label, "Atualizar Tudo")
            self.check_for_updates() # Refaz a checagem de updates

    def show_message(self, title, message):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, message)
        dialog.set_title(title)
        dialog.run()
        dialog.destroy()


class AppStoreApplication(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="com.techstore.app", **kwargs)

    def do_activate(self):
        win = AppStore(application=self)
        win.show_all()

if __name__ == '__main__':
    app = AppStoreApplication()
    app.run(None)
