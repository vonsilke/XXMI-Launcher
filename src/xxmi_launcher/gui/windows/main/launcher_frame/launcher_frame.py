import core.event_manager as Events
import core.path_manager as Paths
import core.config_manager as Config
import gui.vars as Vars

from gui.events import Stage
from gui.classes.containers import UIFrame
from gui.classes.widgets import UIButton, UIText, UIProgressBar, UILabel, UIImageButton, UIImage
from gui.windows.main.launcher_frame.top_bar import TopBarFrame
from gui.windows.main.launcher_frame.bottom_bar import BottomBarFrame
from gui.windows.main.launcher_frame.tool_bar import ToolBarFrame


class LauncherFrame(UIFrame):
    def __init__(self, master):
        super().__init__(master, width=master.cfg.width, height=master.cfg.height, fg_color='transparent')

        self.current_stage = None
        self.staged_widgets = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Background
        self.canvas.grid(row=0, column=0)

        def upd_bg(event):
            self.set_background_image(f'background-image-{event.importer_id.lower()}.jpg', width=master.cfg.width, height=master.cfg.height)
        upd_bg(Events.Application.LoadImporter(importer_id=Config.Launcher.active_importer))
        self.subscribe(Events.Application.LoadImporter, upd_bg)

        self.put(ImporterVersionText(self))
        self.put(LauncherVersionText(self))

        # Top Panel
        self.put(TopBarFrame(self, self.canvas))

        # Bottom Panel
        self.put(BottomBarFrame(self, self.canvas, width=master.cfg.width, height=master.cfg.height)).grid(row=0, column=0, sticky='swe')

        # Game Tiles Panel
        self.put(SelectGameText(self))
        for index, importer_id in enumerate(Config.Importers.__dict__.keys()):
            self.put(GameTileButton(self, index, importer_id))

        # Action Panel
        self.put(UpdateButton(self))
        tools_button = self.put(ToolsButton(self))
        self.put(StartButton(self, tools_button))
        self.put(InstallButton(self, tools_button))
        self.put(ToolBarFrame(self, self.canvas))

        # Application Events
        self.subscribe(
            Events.Application.Ready,
            lambda event: Events.Fire(Events.GUI.LauncherFrame.StageUpdate(Stage.Ready)))
        self.subscribe(
            Events.PackageManager.InitializeDownload,
            lambda event: Events.Fire(Events.GUI.LauncherFrame.StageUpdate(Stage.Download)))
        self.subscribe(
            Events.Application.Busy,
            lambda event: Events.Fire(Events.GUI.LauncherFrame.StageUpdate(Stage.Busy)))


class ImporterVersionText(UIText):
    def __init__(self, master):
        super().__init__(x=20,
                         y=95,
                         text='',
                         font=('Roboto', 19),
                         fill='#cccccc',
                         activefill='white',
                         anchor='nw',
                         master=master)
        self.subscribe(Events.Application.LoadImporter, self.handle_load_importer)
        self.subscribe(Events.PackageManager.VersionNotification, self.handle_version_notification)
        self.set_tooltip(self.get_tooltip)
        # self.subscribe_show(
        #     Events.GUI.LauncherFrame.StageUpdate,
        #     lambda event: event.stage == Stage.Ready)

    def handle_load_importer(self, event):
        self.show(event.importer_id != 'XXMI')

    def handle_version_notification(self, event):
        package_state = event.package_states.get(Config.Launcher.active_importer, None)
        if package_state is None:
            return
        package_name = Config.Launcher.active_importer
        if package_state.installed_version:
            self.set(f'{package_name} {package_state.installed_version}')
        else:
            self.set(f'{package_name}: Not Installed')

    def get_tooltip(self):
        msg = 'Stable release build.\n'
        return msg.strip()


class SelectGameText(UIText):
    def __init__(self, master):
        super().__init__(x=30,
                         y=495,
                         text='Select Games To Mod:',
                         font=('Microsoft YaHei', 24, 'bold'),
                         fill='white',
                         activefill='white',
                         anchor='nw',
                         master=master)
        self.subscribe(Events.Application.LoadImporter, self.handle_load_importer)
        self.subscribe(Events.GUI.LauncherFrame.StageUpdate, self.handle_stage_update)
        # self.subscribe_show(
        #     Events.GUI.LauncherFrame.StageUpdate,
        #     lambda event: event.stage == Stage.Ready)

    def handle_load_importer(self, event):
        self.show(self.stage == Stage.Ready and event.importer_id == 'XXMI')

    def handle_stage_update(self, event):
        self.stage = event.stage
        self.show(self.stage == Stage.Ready and Config.Launcher.active_importer == 'XXMI')


class GameTileButton(UIImageButton):
    def __init__(self, master, pos_id, importer_id):
        super().__init__(
            x=130+pos_id*234,
            y=600,
            button_image_path='game-tile-background.png',
            width=206,
            height=116,
            button_normal_opacity=0.35,
            button_hover_opacity=0.65,
            button_selected_opacity=1,
            button_normal_brightness=1,
            button_selected_brightness=1,
            bg_image_path=f'game-tile-{importer_id.lower()}.png',
            bg_width=204,
            bg_height=113,
            bg_normal_opacity=0.75,
            bg_hover_opacity=0.75,
            bg_selected_opacity=1,
            bg_normal_brightness=0.6,
            bg_selected_brightness=1,
            command=lambda: Events.Fire(Events.Application.ToggleImporter(importer_id=importer_id)),
            master=master)

        self.eye_button_image = self.put(UIImageButton(
            x=self._x + 80, y=self._y - 42,
            button_image_path='eye-show.png',
            width=28,
            height=28,
            button_normal_opacity=0,
            button_hover_opacity=1,
            button_selected_opacity=0,
            bg_image_path=f'eye-hide.png',
            bg_width=28,
            bg_height=28,
            bg_normal_opacity=0,
            bg_hover_opacity=0,
            bg_selected_opacity=1,
            master=master))

        self.eye_button_image.bind("<ButtonPress-1>", self._handle_button_press)
        self.eye_button_image.bind("<ButtonRelease-1>", self._handle_button_release)
        self.eye_button_image.bind("<Enter>", self._handle_enter)
        self.eye_button_image.bind("<Leave>", self._handle_leave)

        self.importer_id = importer_id

        self.subscribe(Events.Application.LoadImporter, self.handle_load_importer)
        self.subscribe(Events.GUI.LauncherFrame.StageUpdate, self.handle_stage_update)
        self.subscribe(Events.GUI.LauncherFrame.ToggleImporter, self.handle_toggle_importer)

        try:
            idx = Config.Launcher.enabled_importers.index(importer_id)
            self.set_selected(True)
        except ValueError:
            self.set_selected(False)

    def handle_load_importer(self, event):
        self.show(self.stage == Stage.Ready and event.importer_id == 'XXMI')

    def handle_stage_update(self, event):
        self.stage = event.stage
        self.show(self.stage == Stage.Ready and Config.Launcher.active_importer == 'XXMI')

    def handle_toggle_importer(self, event):
        if event.importer_id != self.importer_id:
            return
        self.set_selected(event.show)

    def _handle_enter(self, event):
        super()._handle_enter(event)
        Events.Fire(Events.GUI.LauncherFrame.HoverImporter(importer_id=self.importer_id, hover=True))
        self.eye_button_image._handle_enter(event)
        if self.selected:
            self.eye_button_image.set_selected(self.selected)

    def _handle_leave(self, event):
        super()._handle_leave(event)
        Events.Fire(Events.GUI.LauncherFrame.HoverImporter(importer_id=self.importer_id, hover=False))
        self.eye_button_image._handle_leave(event)
        self.eye_button_image.set_selected(False)

    def set_selected(self, selected: bool = False):
        super().set_selected(selected)
        if self.hovered:
            self.eye_button_image.set_selected(selected)


class MainActionButton(UIImageButton):
    def __init__(self, **kwargs):
        self.command = kwargs['command']
        defaults = {}
        defaults.update(
            y=640,
            height=64,
            button_normal_opacity=0.95,
            button_hover_opacity=1,
            button_normal_brightness=0.95,
            button_hover_brightness=1,
            button_selected_brightness=0.8,
            bg_normal_opacity=0.95,
            bg_hover_opacity=1,
            bg_normal_brightness=0.95,
            bg_hover_brightness=1,
            bg_selected_brightness=0.8,
        )
        defaults.update(kwargs)
        super().__init__(**defaults)
        self.subscribe(Events.Application.LoadImporter, self.handle_load_importer)
        self.subscribe(Events.GUI.LauncherFrame.StageUpdate, self.handle_stage_update)

    def handle_load_importer(self, event):
        self.show(event.importer_id != 'XXMI')

    def handle_stage_update(self, event):
        self.stage = event.stage
        self.show(self.stage == Stage.Ready and Config.Launcher.active_importer != 'XXMI')


class UpdateButton(MainActionButton):
    def __init__(self, master):
        super().__init__(
            x=800,
            width=64,
            button_image_path='button-update.png',
            command=lambda: Events.Fire(Events.Application.Update(force=True)),
            master=master)
        self.stage = None
        self.set_tooltip('Update packages to latest versions', delay=0.01)
        self.subscribe(Events.PackageManager.VersionNotification, self.handle_version_notification)

    def handle_version_notification(self, event):
        pending_update_message = []
        for package_name, package in event.package_states.items():
            if package.latest_version != '' and (package.installed_version != package.latest_version):
                pending_update_message.append(
                    f'{package_name}: {package.installed_version or 'N/A'} -> {package.latest_version}')
        if len(pending_update_message) > 0:
            self.enabled = True
            self.set_tooltip('Update packages to latest versions:\n' + '\n'.join(pending_update_message))
            self.show(self.stage == Stage.Ready and Config.Launcher.active_importer != 'XXMI')
        else:
            self.enabled = False
            self.set_tooltip('No updates available!')
            self.hide()


class StartButton(MainActionButton):
    def __init__(self, master, tools_button):
        super().__init__(
            x=1023,
            width=32,
            height=32,
            button_image_path='button-start.png',
            button_x_offset=-14,
            bg_image_path='button-start-background.png',
            bg_width=340,
            bg_height=64,
            text='Start',
            text_x_offset=36,
            text_y_offset=-1,
            font=('Microsoft YaHei', 23, 'bold'),
            command=lambda: Events.Fire(Events.Application.Launch()),
            master=master)
        self.tools_button = tools_button
        self.stage = None
        self.subscribe(
            Events.PackageManager.VersionNotification,
            self.handle_version_notification)

    def handle_version_notification(self, event):
        package_state = event.package_states.get(Config.Launcher.active_importer, None)
        if package_state is None:
            return
        installed = package_state.installed_version != ''
        self.set_enabled(installed)
        self.show(self.stage == Stage.Ready and Config.Launcher.active_importer != 'XXMI')

    def _handle_enter(self, event):
        self.tools_button._handle_enter(None, True)
        super()._handle_enter(self)

    def _handle_leave(self, event):
        self.tools_button._handle_leave(None, True)
        super()._handle_leave(self)

    def _handle_button_press(self, event):
        self.tools_button.set_selected(True)
        super()._handle_button_press(self)

    def _handle_button_release(self, event):
        self.tools_button.selected = False
        self.tools_button._handle_leave(None, True)
        super()._handle_button_release(self)


class InstallButton(MainActionButton):
    def __init__(self, master, tools_button):
        super().__init__(
            x=1023,
            width=32,
            height=32,
            # button_image_path='button-start.png',
            # button_x_offset=-14,
            bg_image_path='button-start-background.png',
            bg_width=340,
            bg_height=64,
            text='Install',
            text_x_offset=18,
            text_y_offset=-1,
            font=('Microsoft YaHei', 23, 'bold'),
            command=lambda: Events.Fire(Events.ModelImporter.Install()),
            master=master)
        self.tools_button = tools_button
        self.subscribe(
            Events.PackageManager.VersionNotification,
            self.handle_version_notification)

    def handle_version_notification(self, event):
        package_state = event.package_states.get(Config.Launcher.active_importer, None)
        if package_state is None:
            return
        not_installed = package_state.installed_version == ''
        self.set_enabled(not_installed)
        self.show(self.stage == Stage.Ready and Config.Launcher.active_importer != 'XXMI')

    def _handle_enter(self, event):
        self.tools_button._handle_enter(None, True)
        super()._handle_enter(self)

    def _handle_leave(self, event):
        self.tools_button._handle_leave(None, True)
        super()._handle_leave(self)

    def _handle_button_press(self, event):
        self.tools_button.set_selected(True)
        super()._handle_button_press(self)

    def _handle_button_release(self, event):
        self.tools_button.selected = False
        self.tools_button._handle_leave(None, True)
        super()._handle_button_release(self)


class ToolsButton(MainActionButton):
    def __init__(self, master):
        super().__init__(
            x=1210,
            width=37,
            button_image_path='button-tools.png',
            command=lambda: True,
            master=master)

    def _handle_enter(self, event, suppress=False):
        if not suppress:
            Events.Fire(Events.GUI.LauncherFrame.ToggleToolbox(show=True))
        super()._handle_enter(self)

    def _handle_leave(self, event, suppress=False):
        if not suppress:
            Events.Fire(Events.GUI.LauncherFrame.ToggleToolbox(hide_on_leave=True))
        super()._handle_leave(self)


class LauncherVersionText(UIText):
    def __init__(self, master):
        super().__init__(x=20,
                         y=680,
                         text='',
                         font=('Roboto', 19),
                         fill='#bbbbbb',
                         activefill='#cccccc',
                         anchor='nw',
                         master=master)
        self.subscribe_set(
            Events.PackageManager.VersionNotification,
            lambda event: f'{event.package_states["Launcher"].installed_version}')
        self.subscribe_show(
            Events.GUI.LauncherFrame.StageUpdate,
            lambda event: event.stage == Stage.Ready)

