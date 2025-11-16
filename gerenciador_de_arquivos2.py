import gi
import os
import shutil
import pathlib
from datetime import datetime
import math # Novo: Importação necessária para math.floor

gi.require_version('Gtk', '3.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio

class AdvancedFileManager(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.techfiles.filemanager", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.current_path = os.path.expanduser("~")
        self.current_location = Gio.File.new_for_path(self.current_path)
        self.show_hidden = False
        self.window = None
        self.search_bar_visible = False
        self.path_history = [self.current_location]
        self.history_index = 0
        self.history_limit = 50

    def do_activate(self):
        if not self.window:
            self.window = Gtk.ApplicationWindow(application=self, title="TechFiles")
            self.window.set_default_size(1000, 700)
            self.window.connect("key-press-event", self.on_key_press)
            
            main_grid = Gtk.Grid()
            self.window.add(main_grid)

            header_bar = Gtk.HeaderBar(title="TechFiles")
            header_bar.set_show_close_button(True)
            self.window.set_titlebar(header_bar)

            # Botões de navegação e atualização
            self.back_button = self._create_nav_button("go-previous-symbolic", "Voltar para o diretório anterior", self.on_back_button_clicked)
            header_bar.pack_start(self.back_button)
            self.forward_button = self._create_nav_button("go-next-symbolic", "Avançar para o próximo diretório", self.on_forward_button_clicked)
            header_bar.pack_start(self.forward_button)
            refresh_button = self._create_nav_button("view-refresh-symbolic", "Atualizar", self.on_refresh_button_clicked)
            header_bar.pack_start(refresh_button)

            # Entry de pesquisa
            self.search_entry = Gtk.SearchEntry()
            self.search_entry.set_placeholder_text("Pesquisar arquivos...")
            self.search_entry.connect("search-changed", self.on_search_changed)
            header_bar.pack_end(self.search_entry)
            self.search_entry.set_visible(self.search_bar_visible)
            
            # Botão para mostrar/esconder a barra de pesquisa
            search_button = Gtk.ToggleButton()
            search_button.set_image(Gtk.Image.new_from_icon_name("system-search-symbolic", Gtk.IconSize.BUTTON))
            search_button.connect("toggled", self.on_search_button_toggled)
            header_bar.pack_end(search_button)

            # Barra de caminho (breadcrumbs)
            self.path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            main_grid.attach(self.path_box, 1, 0, 1, 1)

            # Painel esquerdo (sidebar)
            self.sidebar = Gtk.ListBox()
            self.sidebar.set_selection_mode(Gtk.SelectionMode.SINGLE)
            self.sidebar.connect("row-activated", self.on_sidebar_row_activated)
            
            sidebar_scroll = Gtk.ScrolledWindow()
            sidebar_scroll.set_size_request(200, -1)
            sidebar_scroll.set_min_content_width(150)
            sidebar_scroll.add(self.sidebar)
            main_grid.attach(sidebar_scroll, 0, 0, 1, 2)
            
            self.add_sidebar_locations()

            # TreeView principal para exibir os arquivos
            # Colunas: Nome (str), Ícone (Pixbuf), Caminho/URI (str), É Diretório (bool), Tamanho Formatado (str), Data (str)
            self.store = Gtk.ListStore(str, GdkPixbuf.Pixbuf, str, bool, str, str) 
            self.tree_view = Gtk.TreeView(model=self.store)
            self.tree_view.set_headers_visible(True)
            self.tree_view.connect("row-activated", self.on_row_activated)
            self.tree_view.connect("button-press-event", self.on_tree_view_button_press)

            # Coluna Nome
            renderer_icon = Gtk.CellRendererPixbuf()
            renderer_text = Gtk.CellRendererText()
            column_name = Gtk.TreeViewColumn("Nome")
            column_name.pack_start(renderer_icon, False)
            column_name.pack_start(renderer_text, True)
            column_name.add_attribute(renderer_icon, "pixbuf", 1)
            column_name.add_attribute(renderer_text, "text", 0)
            self.tree_view.append_column(column_name)

            # Coluna Tamanho
            renderer_size = Gtk.CellRendererText()
            column_size = Gtk.TreeViewColumn("Tamanho", renderer_size, text=4)
            column_size.set_resizable(True)
            self.tree_view.append_column(column_size)

            # Coluna Data de Modificação
            renderer_date = Gtk.CellRendererText()
            column_date = Gtk.TreeViewColumn("Data de Modificação", renderer_date, text=5)
            column_date.set_resizable(True)
            self.tree_view.append_column(column_date)

            # Janela de rolagem para a TreeView
            scrolled_window = Gtk.ScrolledWindow()
            scrolled_window.set_vexpand(True)
            scrolled_window.add(self.tree_view)
            main_grid.attach(scrolled_window, 1, 1, 1, 1)
            
            self.window.show_all()
            self.update_view(self.current_location)
            
    def _create_nav_button(self, icon_name, tooltip_text, callback):
        """Função auxiliar para criar botões de navegação"""
        button = Gtk.Button()
        button.set_tooltip_text(tooltip_text)
        button.set_image(Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON))
        button.connect("clicked", callback)
        return button

    def _format_size(self, size_bytes):
        """Formata o tamanho em bytes para uma string legível (KB, MB, GB)"""
        if size_bytes is None:
            return ""
        if size_bytes == 0:
            return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        
        # CORREÇÃO: Usar math.floor e a função embutida pow()
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_h and event.state & Gdk.ModifierType.CONTROL_MASK:
            self.show_hidden = not self.show_hidden
            self.update_view(self.current_location, force_update=True)
            return True 
        return False

    def on_search_button_toggled(self, button):
        self.search_bar_visible = button.get_active()
        self.search_entry.set_visible(self.search_bar_visible)
        if not self.search_bar_visible:
            self.search_entry.set_text("")
            self.update_view(self.current_location, force_update=True)

    def on_search_changed(self, entry):
        self.update_view(self.current_location, force_update=True)

    def on_tree_view_button_press(self, tree_view, event):
        if event.button == 3:
            x, y = int(event.x), int(event.y)
            path = tree_view.get_path_at_pos(x, y)
            if path:
                model, iter = tree_view.get_selection().get_selected()
                if iter:
                    item_path_or_uri = model.get_value(iter, 2)
                    self.show_context_menu(event, item_path_or_uri, tree_view)
                    return True
            return True

        return False

    def show_context_menu(self, event, path_or_uri, tree_view):
        menu = Gtk.Menu()
        
        open_item = Gtk.MenuItem(label="Abrir")
        open_item.connect("activate", self.on_open_clicked, path_or_uri)
        menu.append(open_item)

        rename_item = Gtk.MenuItem(label="Renomear")
        rename_item.connect("activate", self.on_rename_clicked, path_or_uri)
        menu.append(rename_item)

        delete_item = Gtk.MenuItem(label="Excluir")
        delete_item.connect("activate", self.on_delete_clicked, path_or_uri)
        menu.append(delete_item)
        
        menu.show_all()
        menu.popup_at_pointer(event)


    def on_open_clicked(self, widget, path_or_uri):
        try:
            Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(path_or_uri).get_uri(), None)
        except Exception as e:
            if os.path.isdir(path_or_uri):
                 self.update_view(Gio.File.new_for_path(path_or_uri))
            else:
                print(f"Erro ao abrir: {e}")

    def on_rename_clicked(self, widget, file_path):
        print(f"Renomear: {file_path}")
        
    def on_delete_clicked(self, widget, file_path):
        print(f"Excluir: {file_path}")
        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
            self.update_view(self.current_location, force_update=True)
        except Exception as e:
            print(f"Erro ao excluir: {e}")

    def add_sidebar_locations(self):
        # Funções para obter caminhos de usuário (simplificado para caminhos padrão)
        home_path = os.path.expanduser("~")
        
        self.add_sidebar_row("Home", "user-home-symbolic", Gio.File.new_for_path(home_path))
        self.add_sidebar_row("Lixeira", "user-trash-full-symbolic", Gio.File.new_for_uri("trash://")) # URI Virtual
        self.add_sidebar_row("Área de Trabalho", "user-desktop-symbolic", Gio.File.new_for_path(os.path.join(home_path, "Área de trabalho")))
        self.add_sidebar_row("Downloads", "folder-download-symbolic", Gio.File.new_for_path(os.path.join(home_path, "Downloads")))
        self.add_sidebar_row("Documentos", "folder-documents-symbolic", Gio.File.new_for_path(os.path.join(home_path, "Documentos")))
        
        self.sidebar.show_all()

    def add_sidebar_row(self, name, icon_name, file_obj):
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        label = Gtk.Label(label=name) 
        row_box.pack_start(icon, False, False, 0)
        row_box.pack_start(label, False, False, 0)
        row = Gtk.ListBoxRow()
        row.add(row_box)
        row.file = file_obj
        self.sidebar.add(row)

    def update_path_box(self):
        for widget in self.path_box.get_children():
            self.path_box.remove(widget)

        file_path = self.current_location.get_path()
        
        if not file_path:
            uri_scheme = self.current_location.get_uri_scheme()
            display_name = "Lixeira" if uri_scheme == "trash" else uri_scheme.upper()
            button = Gtk.Button(label=display_name)
            button.set_relief(Gtk.ReliefStyle.NONE)
            self.path_box.pack_start(button, False, False, 0)
        else:
            path_parts = file_path.split(os.sep)
            if not path_parts[0]:
                path_parts[0] = os.sep
            
            current_path_so_far = ""
            for part in path_parts:
                if not part:
                    continue
                
                if part == os.sep:
                    current_path_so_far = os.sep
                else:
                    current_path_so_far = os.path.join(current_path_so_far, part)
                
                button = Gtk.Button(label=part)
                button.set_relief(Gtk.ReliefStyle.NONE)
                button.connect("clicked", self.on_path_button_clicked, Gio.File.new_for_path(current_path_so_far))
                
                self.path_box.pack_start(button, False, False, 0)
                
                if part != path_parts[-1]:
                    separator = Gtk.Label(label=" > ")
                    self.path_box.pack_start(separator, False, False, 0)
        
        self.path_box.show_all()

    def update_view(self, file_obj, force_update=False):
        if not force_update and self.current_location.equal(file_obj) and self.history_index >= 0:
            return

        self.store.clear()
        
        search_text = self.search_entry.get_text().lower()
        enumerator = None # CORREÇÃO: Inicializa enumerator como None
        
        try:
            query_attributes = 'standard::name,standard::icon,standard::type,standard::size,time::modified'
            enumerator = file_obj.enumerate_children(query_attributes, Gio.FileQueryInfoFlags.NONE, None)
            
            entries = []
            file_info = enumerator.next_file()
            while file_info is not None:
                entries.append(file_info)
                file_info = enumerator.next_file()

            sorted_entries = sorted(entries, key=lambda e: (e.get_file_type() == Gio.FileType.REGULAR, e.get_name().lower()))
            
            for entry in sorted_entries:
                name = entry.get_name()
                
                if (self.show_hidden or not name.startswith('.')) and \
                   (not search_text or search_text in name.lower()):
                    
                    icon = entry.get_icon()
                    try:
                        pixbuf = Gtk.IconTheme.get_default().load_icon(icon.get_names()[0], 24, 0)
                    except Exception:
                        pixbuf = Gio.content_type_get_icon(entry.get_content_type()).load_icon(24, 0)
                    
                    file_type = entry.get_file_type()
                    is_dir = file_type == Gio.FileType.DIRECTORY
                    
                    size = entry.get_size()
                    size_text = ""
                    if not is_dir:
                        size_text = self._format_size(size)
                    
                    modified_time_info = entry.get_attribute_uint64("time::modified")
                    modified_date_text = datetime.fromtimestamp(modified_time_info).strftime('%d/%m/%Y %H:%M') if modified_time_info else ""
                    
                    full_path_or_uri = file_obj.get_child(name).get_path() or file_obj.get_child(name).get_uri()

                    self.store.append([name, pixbuf, full_path_or_uri, is_dir, size_text, modified_date_text])
        
            self.current_location = file_obj
            self.update_path_box()
            
            if not force_update:
                if self.history_index < len(self.path_history) - 1:
                    self.path_history = self.path_history[:self.history_index + 1]
                self.path_history.append(file_obj)
                if len(self.path_history) > self.history_limit:
                    self.path_history.pop(0)
                self.history_index = len(self.path_history) - 1
            
            self.back_button.set_sensitive(self.history_index > 0)
            self.forward_button.set_sensitive(self.history_index < len(self.path_history) - 1)
            
        except Exception as e:
            # Note: O erro de diretório inexistente deve ser capturado aqui
            print(f"Erro ao listar diretório: {e}")
        finally:
            if enumerator: # Acessível porque foi inicializado fora do try
                enumerator.close(None)
    
    def on_row_activated(self, tree_view, path, column):
        model = tree_view.get_model()
        iter = model.get_iter(path)
        is_dir = model.get_value(iter, 3)
        item_path_or_uri = model.get_value(iter, 2)
        
        if is_dir:
            self.update_view(Gio.File.new_for_path(item_path_or_uri))
        else:
            try:
                Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(item_path_or_uri).get_uri(), None)
            except Exception as e:
                print(f"Erro ao abrir o arquivo: {e}")

    def on_sidebar_row_activated(self, listbox, row):
        self.update_view(row.file)

    def on_path_button_clicked(self, button, file_obj):
        self.update_view(file_obj)

    def on_back_button_clicked(self, button):
        if self.history_index > 0:
            self.history_index -= 1
            self.update_view(self.path_history[self.history_index], force_update=True) 

    def on_forward_button_clicked(self, button):
        if self.history_index < len(self.path_history) - 1:
            self.history_index += 1
            self.update_view(self.path_history[self.history_index], force_update=True) 

    def on_refresh_button_clicked(self, button):
        self.update_view(self.current_location, force_update=True)

if __name__ == "__main__":
    app = AdvancedFileManager()
    app.run(None)