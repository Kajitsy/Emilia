import sys, ctypes, platform, webbrowser, subprocess, datetime, os, json, logging

os.makedirs("logs", exist_ok=True)

timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_filename = os.path.join("logs", f"{timestamp}.log")
latest_log_filename = os.path.join("logs", "latest.log")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")

file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

latest_file_handler = logging.FileHandler(latest_log_filename, encoding="utf-8", mode="w")
latest_file_handler.setFormatter(formatter)
logger.addHandler(latest_file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logging.getLogger("qasync").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class LoggerWriter:
    def __init__(self, level, stream):
        self.level = level
        self.stream = stream

    def write(self, message):
        if message.strip():
            self.level(message.strip())

    def flush(self):
        self.stream.flush()

logging.info(f"""
OS:           {platform.system()} {platform.release()} {platform.version()} ({platform.architecture()[0]})
Script Path:  {os.path.abspath(sys.argv[0])}
Started at:   {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Python:       {sys.version.split()[0]} ({platform.architecture()[0]})
Frozen EXE:   {getattr(sys, 'frozen', False)}
Python Path:  {sys.executable}
Process ID:   {os.getpid()}""")

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QStackedWidget,
    QSystemTrayIcon, QProgressBar)
from PyQt6.QtGui import (QMouseEvent, QAction, QIntValidator, QRegularExpressionValidator,
    QKeySequence, QIcon)
from PyQt6.QtCore import (QEvent, QSettings, QRect, QDateTime, QPropertyAnimation,
    QEasingCurve, QTimer, QTranslator, QParallelAnimationGroup,
    QRegularExpression, QPoint)
from PyQt6.QtMultimedia import QMediaDevices
from qasync import QEventLoop
from packaging import version

from modules.ChatInterface import ChatInterface
from modules.GetCAICookies import GetCookies
from modules.QThreads import *
from modules.style.Elements import (PushButton, LineEdit, HorizontalScrollArea, ClickableFrame,
                                    LeftSidebar, CheckBox, KeySequenceEdit, Menu, ComboBox,
                                    VerticalScrollPage, HorizontalScrollPage, CardFrame)
from modules.style.Icons import Svg
from modules.style.Utils import format_text, color_avatar
from modules.cards import VoiceCards, CharacterCards, ScenesCards, UserCards

if platform.system() == 'Windows':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Emilia Next")
    logging.debug("ctypes SetCurrentProcessExplicitAppUserModelID")

app = QApplication(sys.argv)

translator = QTranslator()

translator.load(
    f"lang/{QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, 'Emilia', 'settings').value('emilia_language', QLocale.system().name())}.qm")
app.installTranslator(translator)

loop = QEventLoop(app)
asyncio.set_event_loop(loop)

class EmiliaNext(QMainWindow):
    def __init__(self):
        super().__init__()
        today = datetime.datetime.now().date()
        special_titles = {
            (1, 1): self.tr("Emilia | Happy New Year"),
            (4, 4): self.tr("Happy birthday Emilia!"),
            (7, 11): self.tr("Emilia | Happy birthday Kajitsy!"),
            (9, 16): self.tr("Emilia | Happy birthday CAI!"),
            (10, 31): "Spoooky | Trick or treat",
            (12, 31): self.tr("Emilia | Happy New Year")
        }
        date_key = (today.month, today.day)
        if date_key in special_titles:
            self.setWindowTitle(special_titles[date_key])
        else:
            self.setWindowTitle("Emilia")
        self.setStyleSheet("""
            background-color: #202124;
            color: #e8eaed;
        """)
        self.settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "Emilia", "settings")
        self.current_language = self.settings.value("emilia_language", QLocale.system().name())
        self.drpc_enable = self.settings.value("discord_rpc/enable", True, type=bool)
        self.drpc_show_chat_name = self.settings.value("discord_rpc/show_chat_name", False, type=bool)
        self.drpc_show_username = self.settings.value("discord_rpc/show_username", False, type=bool)
        self.drpc_show_current_page = self.settings.value("discord_rpc/show_current_page", True, type=bool)
        self.svg_icons = Svg()
        self.version = "3.2.1b"
        self.beta = version.parse(self.version).is_prerelease

        self.setGeometry(self.settings.value("main_window/x", 100, type=int), self.settings.value("main_window/y", 100, type=int),
                         self.settings.value("main_window/width", 1360, type=int), self.settings.value("main_window/height", 800, type=int))
        self.left_sidebar_visible = True
        self.left_sidebar_hide_user = False
        self.left_sidebar_hide_auto = False
        self.current_chat_interface = None
        self.hide_overlay = True
        self.me_has_avatar = False
        self.username = None
        self.muted = False

        self.threads = []
        self.overlays = []
        self.recent_chats = []
        self.try_this_chats = []
        self.featured_chats = []
        self.recommended_chats = []
        self.popular_chats = []
        self.trending_chats = []
        self.tray = tray_icon

        self.token = self.settings.value("cai_auth/token", "", type=str)
        self.cookie = self.settings.value("cai_auth/cookie", "", type=str)
        self.auto_collapse_sidebar = self.settings.value("auto_collapse_sidebar", False, type=bool)
        self.name = self.tr("User")
        self.input_devices = {}
        self.output_devices = {}

        for index, device in enumerate(QMediaDevices().audioInputs()):
            self.input_devices[str(index)] = device.description()

        for index, device in enumerate(sounddevice.query_devices()):
            if device['max_output_channels'] > 0:
                self.output_devices[str(index)] = device['name']

        self.chat_thread = ChatThread(self)
        self.threads.append(self.chat_thread)
        self.discord_thread = DiscordRPC(self)
        self.threads.append(self.discord_thread)

        self.setOutputDevice(self.settings.value('output_device', 0, type=int))
        if getattr(sys, 'frozen', False):
            self.checkForUpdates()

        self.initUI()
        self.loadUI()

    def initUI(self):
        self.layout = QHBoxLayout()

        self.left_sidebar = self.createLeftSidebar()
        self.layout.addWidget(self.left_sidebar)

        self.main_layout = QVBoxLayout()
        self.layout.addLayout(self.main_layout, 1)

        self.top_widget, self.top_bar_stacked_widget, self.t_bar = self.createTopBar()
        self.main_layout.addWidget(self.t_bar)

        self.main_content_area = QStackedWidget()
        self.main_content_area.setStyleSheet("""
            QScrollArea {
                background-color: #303134;
                border: none;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background: #303134;
                width: 8px;
                margin: 0px 0 0px 0;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px; 
            }
            QScrollBar::sub-control:vertical {
                background: #f0f0f0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical {
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
        """)
        self.main_page = self.createMainContentPage()
        self.search_results_page = QWidget()
        self.search_results_layout = QVBoxLayout(self.search_results_page)
        self.settings_page = SettingsPage(self)
        self.settings_page.save_button.clicked.connect(self.updateAutoCollapseSidebar)

        self.main_content_area_animation = QPropertyAnimation(self.main_content_area, b"geometry")
        self.main_content_area_animation.setDuration(500)
        self.main_content_area_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.main_content_area.addWidget(self.main_page)
        self.main_content_area.addWidget(self.search_results_page)
        self.main_content_area.addWidget(self.settings_page)

        self.main_layout.addWidget(self.main_content_area, 1)

        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)
        self.createOverlay()

        self.full_animation = QParallelAnimationGroup()
        self.full_animation.addAnimation(self.left_sidebar_animation)
        self.full_animation.addAnimation(self.main_content_area_animation)
        self.full_animation.addAnimation(self.top_bar_animation)

    def loadUI(self):
        self.chat_thread.recent_chats_signal.connect(self.addRecentChats)
        self.chat_thread.featured_voices_signal.connect(self.addFeaturedVoices)
        self.chat_thread.trythis_chats_signal.connect(self.addTryThisChats)
        self.chat_thread.get_main_page_chats_signal.connect(self.addMainPageChats)
        self.chat_thread.get_scenes_curated_signal.connect(self.addScenesMainPage)
        self.chat_thread.featured_chats_signal.connect(self.addForYouChats)
        self.chat_thread.category_characters_signal.connect(self.addCharacterByCategory)
        self.chat_thread.get_me_signal.connect(self.getMe)
        self.chat_thread.get_user_settings_signal.connect(self.getUserSettings)
        self.chat_thread.get_available_models_signal.connect(self.getAvailableModels)
        self.chat_thread.get_available_models_git_signal.connect(self.getAvailableModelsGit)

        self.chat_thread.start()
        self.discord_thread.start()
        if self.drpc_enable: self.discord_thread.connect()

        if QDateTime.fromString(self.settings.value("cai_auth/expiration_date")) < QDateTime.currentDateTime():
            if self.token:
                self.chat_thread.set_token(self.token)
                self.chat_thread.create_connect()

                self.chat_thread.get_recent_chats()
                self.chat_thread.get_scenes_curated()
                self.chat_thread.get_trythis_chats()
                self.chat_thread.get_featured_voices()
                self.chat_thread.get_me()
                self.chat_thread.get_main_page_chats()
                self.chat_thread.get_available_models()
                self.chat_thread.get_available_models_git()
                self.chat_thread.get_user_settings()

            if self.cookie:
                self.chat_thread.set_cookie(self.cookie)

            if not self.cookie or not self.token:
                self.openSettings()
                self.settings_page.getCookies()
        else:
            self.openSettings()
            self.settings_page.getCookies()
            self.showNotification(self.tr("Please re-enter (the login data has expired)"))

    def createLeftSidebar(self):
        left_sidebar = LeftSidebar(self)
        self.settings_button = left_sidebar.settings_button
        self.profile_button = left_sidebar.profile_button
        self.profile_button_2 = left_sidebar.profile_button_2
        self.recent_chat_scroll_layout = left_sidebar.recent_chat_scroll_layout

        self.left_sidebar_animation = QPropertyAnimation(left_sidebar, b"geometry")
        self.left_sidebar_animation.setDuration(500)
        self.left_sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.left_sidebar_animation.finished.connect(lambda: self.leftSidebarAnim())

        return left_sidebar

    def addRecentChatCard(self, character_id, character_name, chat_id, character_avatar_url, scene_id=None):
        def openChat(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.openChat(character_id, character_name, chat_id, card, scene_id)
            elif event.button() == Qt.MouseButton.RightButton:
                showContextMenu(QPoint(avatar_label.pos().x() + 45 , avatar_label.pos().y() + 22), card)

        card = ClickableFrame()
        card.setObjectName(chat_id)
        card.setFixedWidth(self.settings.value("left_sidebar_width", 255, type=int))
        card.mousePress = openChat
        card.enterEvent = lambda event: menu_button.setVisible(True) if menu_button.visibility else None
        card.leaveEvent = lambda event: menu_button.setVisible(False)
        card.setCursor(Qt.CursorShape.PointingHandCursor)


        def showContextMenu(pos, card):
            def deleteCard():
                self.showMainPage(self.current_chat_interface)
                self.chat_thread.hide_chat(character_id)
                card.setParent(None)
                card.deleteLater()

            context_menu = Menu(self)

            delete_action = QAction(self.tr("Remove from Recent Chats"), self)
            delete_action.triggered.connect(deleteCard)
            context_menu.addAction(delete_action)

            context_menu.exec(card.mapToGlobal(pos))

        chat_layout = QHBoxLayout()
        chat_layout.setContentsMargins(0, 0, 0, 0)

        avatar_label = QLabel()
        avatar_label.setFixedSize(50, 50)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_layout.addWidget(avatar_label)
        setattr(card, 'avatar_label', avatar_label)

        if character_avatar_url:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + character_avatar_url + '?webp=true&anim=0',
                45, 45)
            load_avatar_thread.image_loaded.connect(avatar_label.setPixmap)
            load_avatar_thread.error_loading.connect(lambda _: color_avatar(avatar_label, 45, 45, character_name))
            load_avatar_thread.start()
            self.threads.append(load_avatar_thread)
        else:
            color_avatar(avatar_label, 45, 45, character_name)

        avatar_label_2 = QLabel()
        avatar_label_2.setFixedSize(60, 60)
        avatar_label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_layout.addWidget(avatar_label_2)
        setattr(card, 'avatar_label_2', avatar_label_2)

        if character_avatar_url:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + character_avatar_url + '?webp=true&anim=0',
                55, 55)
            load_avatar_thread.image_loaded.connect(avatar_label_2.setPixmap)
            load_avatar_thread.error_loading.connect(lambda _: color_avatar(avatar_label_2, 55, 55, character_name))
            load_avatar_thread.start()
            self.threads.append(load_avatar_thread)
        else:
            color_avatar(avatar_label_2, 55, 55, character_name)
        avatar_label_2.setVisible(False)

        name_label = QLabel(character_name)
        name_label.setStyleSheet("background-color: transparent; border: none; color: white;")
        chat_layout.addWidget(name_label, 1)
        setattr(card, 'name_label', name_label)

        menu_button = QPushButton()
        menu_button.visibility = True
        menu_button.setIcon(self.svg_icons.ellipsis())
        menu_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #5a5c60;
                border-radius: 4px;
            }
            QPushButton:pressed {
                background-color: #3e4043;
                border-radius: 4px;
            }
        """)
        menu_button.setVisible(False)
        menu_button.clicked.connect(lambda: showContextMenu(menu_button.pos(), card))
        chat_layout.addWidget(menu_button, 0, Qt.AlignmentFlag.AlignRight)
        setattr(card, 'menu_button', menu_button)

        chat_layout.addStretch()
        card.setLayout(chat_layout)

        self.recent_chat_scroll_layout.addWidget(card)
        self.left_sidebar.resizeCard(card)
        return card

    def leftSidebarAnim(self):
        self.left_sidebar.setVisible(self.left_sidebar_visible)

    def toggleLeftSidebar(self):
        self.left_sidebar_hide_user = not self.left_sidebar_hide_user
        if self.left_sidebar_hide_user and self.left_sidebar_hide_auto:
            self.left_sidebar_visible = True
        else:
            self.left_sidebar_visible = not self.left_sidebar_visible

        left_current_rect = self.left_sidebar.geometry()
        main_current_rect = self.main_content_area.geometry()
        top_current_rect = self.t_bar.geometry()

        offset = left_current_rect.width() + 10

        if self.left_sidebar_visible:
            self.left_sidebar.setVisible(True)
            self.top_bar_collapse_button.setVisible(False)
            self.left_sidebar_animation.setStartValue(left_current_rect)
            self.left_sidebar_animation.setEndValue(QRect(left_current_rect.x() + offset,
                                                          left_current_rect.y(),
                                                          left_current_rect.width(),
                                                          left_current_rect.height()))

            self.main_content_area_animation.setStartValue(main_current_rect)
            self.main_content_area_animation.setEndValue(QRect(main_current_rect.x() + offset,
                                                               main_current_rect.y(),
                                                               main_current_rect.width() - offset,
                                                               main_current_rect.height()))

            self.top_bar_animation.setStartValue(top_current_rect)
            self.top_bar_animation.setEndValue(QRect(top_current_rect.x() + offset,
                                                     top_current_rect.y(),
                                                     top_current_rect.width() - offset,
                                                     top_current_rect.height()))

        else:
            self.left_sidebar_animation.setStartValue(left_current_rect)
            self.left_sidebar_animation.setEndValue(QRect(left_current_rect.x() - offset,
                                                          left_current_rect.y(),
                                                          left_current_rect.width(),
                                                          left_current_rect.height()))

            self.main_content_area_animation.setStartValue(main_current_rect)
            self.main_content_area_animation.setEndValue(QRect(main_current_rect.x() - offset,
                                                               main_current_rect.y(),
                                                               main_current_rect.width() + offset,
                                                               main_current_rect.height()))

            self.top_bar_animation.setStartValue(top_current_rect)
            self.top_bar_animation.setEndValue(QRect(top_current_rect.x() - offset,
                                                     top_current_rect.y(),
                                                     top_current_rect.width() + offset,
                                                     top_current_rect.height()))

        self.top_bar_collapse_button.setVisible(not self.left_sidebar_visible)
        self.full_animation.start()

    def checkForUpdates(self):
        try:
            headers = {"Accept": "application/vnd.github.v3+json"}
            response = requests.get(
                "https://api.github.com/repos/Kajitsy/Emilia/releases",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            releases = response.json()

            latest_release = next((r for r in releases if not r["prerelease"]), None)
            latest_prerelease = next((r for r in releases if r["prerelease"]), None)
            target_release = latest_prerelease if self.beta and latest_prerelease else latest_release

            if target_release:
                latest_version = target_release["tag_name"]
                asset = next((a for a in target_release["assets"] if a["name"] == "EmiliaSetup.exe"), None)

                if latest_version > self.version and asset:
                    self.showNotification(self.tr("A new version is available: ") + latest_version)
                    self.update_button.setVisible(True)
                    self.update_button.clicked.connect(lambda: self.downloadUpdate(asset["browser_download_url"]))
        except:
            pass

    def downloadUpdate(self, url):
        self.showOverlay(self.createDownloadOverlay())
        self.hide_overlay = False
        save_path = os.path.join(os.getcwd(), "update.exe")
        self.thread = FileLoaderThread(url, save_path=save_path)
        self.thread.progress.connect(lambda x: self.download_overlay_progress.setValue(x))
        self.thread.finished.connect(self.runInstaller)
        self.thread.start()

    def runInstaller(self, save_path):
        if save_path:
            self.download_overlay_label.setText(self.tr("Download complete. Running installer..."))
            self.closeEvent = lambda a0: None
            self.close()
            subprocess.Popen(save_path, shell=True)
        else:
            self.download_overlay_label.setText(self.tr("Download failed."))

    def createDownloadOverlay(self):
        self.download_overlay_frame = QFrame()
        self.download_overlay_frame.setFixedSize(150, 90)
        layout = QVBoxLayout()

        self.download_overlay_label = QLabel(self.tr("Downloading..."))
        self.download_overlay_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.download_overlay_label)

        self.download_overlay_progress = QProgressBar()
        self.download_overlay_progress.setTextVisible(False)
        self.download_overlay_progress.setValue(0)
        layout.addWidget(self.download_overlay_progress)

        self.download_overlay_frame.setLayout(layout)
        return self.download_overlay_frame

    def createMainContentPage(self):
        def show(event):
            self.top_bar_stacked_widget.addWidget(self.top_widget)
            self.top_bar_stacked_widget.setCurrentWidget(self.top_widget)
            if self.drpc_enable:
                if self.drpc_show_current_page:
                    self.discord_thread.update(details=self.tr("Looking at the main page"))
                else:
                    self.discord_thread.update()
        main_content_area = QWidget()
        main_content_area.showEvent = show
        self.main_content_layout = QVBoxLayout()

        scroll_area = VerticalScrollPage()
        scroll_area.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_area.layout

        for_you_section, self.for_you_layout = self.createSection(self.tr("For You"))
        scroll_layout.addWidget(for_you_section)

        scenes_section, self.scenes_layout = self.createSection(self.tr("Scenes"))
        scenes_section.setFixedHeight(350)
        scroll_layout.addWidget(scenes_section)

        recommended_section, self.recommended_layout = self.createSection(self.tr("Recommended"))
        scroll_layout.addWidget(recommended_section)

        popular_section, self.popular_layout = self.createSection(self.tr("Popular"))
        scroll_layout.addWidget(popular_section)

        trending_section, self.trending_layout = self.createSection(self.tr("Trending"))
        scroll_layout.addWidget(trending_section)

        try_this_section, self.try_this_odd_layout, self.try_this_even_layout = self.createTryThisSection(self.tr("Try This"))
        scroll_layout.addWidget(try_this_section)

        featured_voices_section, self.featured_voices_layout = self.createVoiceSection()
        scroll_layout.addWidget(featured_voices_section)

        category_section, self.category_layout, self.category_button_layout = self.createCategorySection()
        scroll_layout.addWidget(category_section)

        self.main_content_layout.addWidget(scroll_area)

        main_content_area.setLayout(self.main_content_layout)
        return main_content_area

    def createTopBar(self):
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        t_layout = QHBoxLayout()
        top_bar.setLayout(t_layout)

        def showEvent(event):
            top_bar_stacked_widget.setFixedHeight(50)
            top_bar.setStyleSheet(None)

        top_widget = QWidget()
        top_widget.showEvent = showEvent
        top_bar_layout = QHBoxLayout()
        top_widget.setLayout(top_bar_layout)

        top_bar_stacked_widget = QStackedWidget()
        top_bar_stacked_widget.setFixedHeight(50)
        top_bar_stacked_widget.addWidget(top_widget)
        top_widget.setStyleSheet("background-color: transparent;")

        self.top_bar_animation = QPropertyAnimation(top_bar, b"geometry")
        self.top_bar_animation.setDuration(500)
        self.top_bar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.top_bar_collapse_button = PushButton()
        self.top_bar_collapse_button.setIcon(self.svg_icons.ellipsis())
        self.top_bar_collapse_button.clicked.connect(self.toggleLeftSidebar)
        self.top_bar_collapse_button.setVisible(not self.left_sidebar_visible)

        self.welcome_label = QLabel(self.tr("Welcome back, User"))
        font = self.welcome_label.font()
        font.setPointSize(12)
        self.welcome_label.setFont(font)
        top_bar_layout.addWidget(self.welcome_label)

        top_bar_layout.addStretch(1)

        self.update_button = PushButton(self.tr("Update"))
        top_bar_layout.addWidget(self.update_button)
        self.update_button.setVisible(False)

        self.search_bar = LineEdit()
        self.search_bar.setPlaceholderText(self.tr("Character Search"))
        self.search_bar.returnPressed.connect(self.showSearchResultsV2)
        top_bar_layout.addWidget(self.search_bar)

        t_layout.addWidget(self.top_bar_collapse_button)
        t_layout.addWidget(top_bar_stacked_widget)

        return top_widget, top_bar_stacked_widget, top_bar

    def createSection(self, title):
        section_frame = QFrame()
        section_frame.setFixedHeight(204)
        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(0, 10, 0, 10)

        title_label = QLabel(title)
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        section_layout.addWidget(title_label)

        scroll_page = HorizontalScrollPage()
        cards_viewport = scroll_page.viewport
        cards_layout = scroll_page.layout


        section_layout.addWidget(scroll_page)
        section_frame.setLayout(section_layout)
        return section_frame, cards_layout

    def createTryThisSection(self, title):
        section_frame = QFrame()
        section_frame.setFixedHeight(216)
        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(0, 10, 0, 10)

        title_label = QLabel(title)
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        section_layout.addWidget(title_label)

        scroll_area = HorizontalScrollArea()

        cards_viewport = QWidget()
        cards_layout_main = QVBoxLayout()

        cards_layout_odd = QHBoxLayout()

        cards_layout_even = QHBoxLayout()

        cards_layout_main.addLayout(cards_layout_odd)
        cards_layout_main.addLayout(cards_layout_even)

        cards_viewport.setLayout(cards_layout_main)
        cards_viewport.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        scroll_area.setWidget(cards_viewport)

        section_layout.addWidget(scroll_area)
        section_frame.setLayout(section_layout)

        return section_frame, cards_layout_odd, cards_layout_even

    def createVoiceSection(self):
        section_frame = QFrame()
        section_frame.setFixedHeight(130)
        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(0, 10, 0, 10)

        title_label = QLabel(self.tr("Voices"))
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        section_layout.addWidget(title_label)

        scroll_page = HorizontalScrollPage()
        sctoll_viewport = scroll_page.viewport
        scroll_layout = scroll_page.layout

        section_layout.addWidget(scroll_page)
        section_frame.setLayout(section_layout)
        return section_frame, scroll_layout

    def createCategorySection(self):
        categories = {
            "Assistants": self.tr("Assistants"),
            "Anime": self.tr("Anime"),
            "Creativity & Writing": self.tr("Creativity and Writing"),
            "Entertainment & Gaming": self.tr("Entertainment and Gaming"),
            "History": self.tr("History"),
            "Humor": self.tr("Humor"),
            "Learning": self.tr("Learning"),
            "Lifestyle": self.tr("Lifestyle"),
            "Parody": self.tr("Parody"),
            "RPG & Puzzles": self.tr("RPG and Puzzles")
        }

        section_frame = QFrame()
        section_frame.setFixedHeight(234)
        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(0, 10, 0, 10)

        button_scroll_area = HorizontalScrollArea()
        button_scroll_area.setStyleSheet("")
        button_scroll_area.setWidgetResizable(True)
        button_scroll_area.horizontalScrollBar().setVisible(False)

        button_scroll_viewport = QWidget()
        button_scroll_layout = QHBoxLayout()
        button_scroll_viewport.setLayout(button_scroll_layout)
        button_scroll_area.setWidget(button_scroll_viewport)

        self.category_buttons = []

        for key, value in categories.items():
            btn = QPushButton(value)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #494a4d;
                    color: #e8eaed;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 15px;
                    text-align: center;
                }
                QPushButton:disabled {
                    background-color: #555;
                    color: #a2a2ac;
                }
                QPushButton:hover {
                    background-color: #5f6368;
                }
                QPushButton:pressed, QPushButton:checked {
                    background-color: #494a4d;
                    border-bottom: 5px solid #555;
                    padding-bottom: 3px;
                }
            """)
            btn.setObjectName(key)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, b=btn, cat=key: self.onCategoryClicked(b, cat))
            self.category_buttons.append(btn)
            button_scroll_layout.addWidget(btn)
            if key == "Assistants":
                btn.setChecked(True)
                self.onCategoryClicked(btn, key)
        section_layout.addWidget(button_scroll_area, alignment=Qt.AlignmentFlag.AlignTop)

        scroll_page = HorizontalScrollPage()
        scroll_viewport = scroll_page.viewport
        scroll_layout = scroll_page.layout

        section_layout.addWidget(scroll_page)

        section_frame.setLayout(section_layout)
        return section_frame, scroll_layout, button_scroll_layout

    def onCategoryClicked(self, clicked_button, category):
        for btn in self.category_buttons:
            if btn is not clicked_button:
                btn.setChecked(False)
        self.chat_thread.get_category_characters(category)

    def createOverlay(self):
        self.overlay = QFrame(self)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.overlay_layout = QVBoxLayout(self.overlay)
        self.overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.overlay_content = QWidget(self.overlay)
        self.overlay_content.setStyleSheet("""
            background-color: #202124;
            border-radius: 4px;
            border: none;""")
        self.overlay_content_layout = QVBoxLayout(self.overlay_content)

        self.overlay_layout.addWidget(self.overlay_content)

        self.overlay.setGeometry(self.rect())
        self.overlay.hide()

        self.notification_message_label = QLabel(self)
        self.notification_message_label.setWordWrap(True)
        self.notification_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.notification_message_label.setStyleSheet("""
                    background-color: white;
                    color: black;
                    border-radius: 4px;
                    padding: 10px;
                """)
        self.notification_message_label.setFixedSize(300, 50)
        self.notification_message_label.setGeometry(QRect(int((self.width() - self.notification_message_label.width()) / 2), -50, 300, 50))
        self.notification_message_label.hide()

        self.notification_message_animation = QPropertyAnimation(self.notification_message_label, b"geometry")
        self.notification_message_animation.setDuration(500)
        self.notification_message_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def showOverlay(self, widget):
        self.overlay_content_layout.addWidget(widget)
        widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        self.overlays.append(widget)

        self.overlay.setGeometry(self.rect())
        self.overlay.show()
        self.overlay.raise_()

    def showNotification(self, text = "notification_message_label"):
        self.notification_message_label.setText(text)
        self.notification_message_label.show()
        self.notification_message_label.raise_()
        start_rect = QRect(int((self.width() - self.notification_message_label.width()) / 2), -70, 300, 50)
        end_rect = QRect(int((self.width() - self.notification_message_label.width()) / 2), 10, 300, 50)
        self.notification_message_animation.setStartValue(start_rect)
        self.notification_message_animation.setEndValue(end_rect)
        self.notification_message_animation.start()
        QTimer.singleShot(3000, self.hideNotification)

    def hideNotification(self):
        start_rect = QRect(self.notification_message_label.x(), self.notification_message_label.y(), 300, 50)
        end_rect = QRect(self.notification_message_label.x(), -50, 300, 50)
        self.notification_message_animation.setStartValue(start_rect)
        self.notification_message_animation.setEndValue(end_rect)
        self.notification_message_animation.start()

    def hideOverlay(self):
        self.overlay.hide()
        for i in range(self.overlay_content_layout.count()):
            item = self.overlay_content_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

    def updateAutoCollapseSidebar(self):
        auto_collapse_sidebar_checkbox = self.settings_page.findChild(CheckBox, "auto_collapse_sidebar")
        self.auto_collapse_sidebar = auto_collapse_sidebar_checkbox.isChecked()
        self.settings.setValue("auto_collapse_sidebar", self.auto_collapse_sidebar)

    def showSearchResultsV2(self):
        search_query = self.search_bar.text().strip()
        if not search_query:
            return

        search_page = SearchPage(self)
        self.main_content_area.addWidget(search_page)
        self.main_content_area.setCurrentWidget(search_page)

        self.chat_thread.character_search_signal.connect(search_page.populate)
        self.chat_thread.character_search(search_query)
        self.search_bar.setText("")

    def showMainPage(self, widget: QWidget | None):
        if widget: widget.setVisible(False)
        self.main_content_area.setCurrentWidget(self.main_page)
        self.current_chat_interface = None
        self.top_widget.setVisible(True)

    def openCharacter(self, path=None, character_id=None):
        widget = CharacterCards.MainPage(self, path, character_id)
        self.main_content_area.addWidget(widget)
        self.main_content_area.setCurrentWidget(widget)

    def openScene(self, data={}, scene_id=None):
        widget = ScenesCards.MainPage(self, data, scene_id)
        self.main_content_area.addWidget(widget)
        self.main_content_area.setCurrentWidget(widget)

    def openChat(self, character_id, character_name, chat_id="", card=None, scene_id=""):
        if self.current_chat_interface:
            self.main_content_area.removeWidget(self.current_chat_interface)
            self.current_chat_interface.deleteLater()
            self.chat_thread.message_signal.disconnect()
            if self.current_chat_interface.voice_enabled:
                self.chat_thread.replay_signal.disconnect()
            self.current_chat_interface = None


        self.current_chat_interface = ChatInterface(self, character_name, character_id, chat_id, scene_id)
        if card:
            setattr(self.current_chat_interface, 'recent_card', card)
        self.main_content_area.addWidget(self.current_chat_interface)
        self.main_content_area.setCurrentWidget(self.current_chat_interface)

    def openSettings(self):
        self.main_content_area.setCurrentWidget(self.settings_page)
        if self.current_chat_interface:
            self.current_chat_interface.setVisible(False)
            self.search_bar.setText("")

    def openCreateCharacterPage(self, character_id=None):
        self.create_char_page = CharacterCards.EditPage(self, character_id)
        self.main_content_area.addWidget(self.create_char_page)
        self.main_content_area.setCurrentWidget(self.create_char_page)
        if self.current_chat_interface:
            self.current_chat_interface.setVisible(False)
            self.search_bar.setText("")

    def openUserPage(self, username):
        self.user_page = UserCards.UserProfile(self, username)
        self.main_content_area.addWidget(self.user_page)
        self.main_content_area.setCurrentWidget(self.user_page)
        if self.current_chat_interface:
            self.current_chat_interface.setVisible(False)
            self.search_bar.setText("")

    def addCharacterByCategory(self, characters):
        for i in reversed(range(self.category_layout.count())):
            item = self.category_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        for character in characters:
            card = CharacterCards.MainCard(self, character.get('participant__name', "Unknown"), character.get('avatar_file_name'),
                                           character.get('title'), character.get('user__username'),
                                           character.get('external_id'), character.get('participant__num_interactions'))
            card.setFixedSize(277, 134)
            self.category_layout.addWidget(card)

    def addRecentChats(self, chats):
        for i in reversed(range(self.recent_chat_scroll_layout.count())):
            item = self.recent_chat_scroll_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.recent_chats = chats
        for chat in self.recent_chats:
            card = self.addRecentChatCard(chat.get('character_id'), chat.get('name'), chat.get('id'), chat.get('avatar_file_name'), chat.get('scene_id'))
            if self.current_chat_interface is not None:
                if self.current_chat_interface.chat_id == chat.get('id'):
                    setattr(self.current_chat_interface, 'recent_card', card)
                    card.setStyleSheet(card.press_style)

    def addFeaturedVoices(self, voices):
        for i in reversed(range(self.featured_voices_layout.count())):
            item = self.featured_voices_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.featured_voices = voices
        for voice in self.featured_voices:
            card = VoiceCards.HorizontalMiniVoiceCard(self, voice)
            card.setFixedWidth(277)
            self.featured_voices_layout.addWidget(card)

    def addMainPageChats(self, results):
        for i in reversed(range(self.popular_layout.count())):
            item = self.popular_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        for i in reversed(range(self.trending_layout.count())):
            item = self.trending_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        for i in reversed(range(self.recommended_layout.count())):
            item = self.recommended_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()


        self.recommended_chats = results[0].get('result', {}).get('data', {}).get('json', {}).get('characters', [])
        self.popular_chats = results[1].get('result', {}).get('data', {}).get('json', {}).get('cold_start_popular_characters_l30d_v1', [])
        self.trending_chats = results[1].get('result', {}).get('data', {}).get('json', {}).get('cold_start_trending_characters_v1', [])

        for character in self.recommended_chats:
            card = CharacterCards.MainCard(self, character.get('name'), character.get('avatar_file_name'), character.get('title'), character.get('user__username'), character.get('external_id'), character.get('participant__num_interactions'))
            card.setFixedSize(277, 134)
            self.recommended_layout.addWidget(card)
        for character in self.popular_chats:
            card = CharacterCards.MainCard(self, character.get('name'), character.get('avatar_file_name'), character.get('title'), character.get('user__username'), character.get('external_id'), character.get('participant__num_interactions'))
            card.setFixedSize(277, 134)
            self.popular_layout.addWidget(card)
        for character in self.trending_chats:
            card = CharacterCards.MainCard(self, character.get('name'), character.get('avatar_file_name'), character.get('title'), character.get('user__username'), character.get('external_id'), character.get('participant__num_interactions'))
            card.setFixedSize(277, 134)
            self.trending_layout.addWidget(card)

    def addScenesMainPage(self, scenes):
        for i in reversed(range(self.scenes_layout.count())):
            item = self.popular_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.curated_scenes = scenes

        for scene in self.curated_scenes:
            card = ScenesCards.MainCard(self, scene)
            #card.setFixedSize(277, 134)
            self.scenes_layout.addWidget(card)

    def addForYouChats(self, chats):
        for i in reversed(range(self.for_you_layout.count())):
            item = self.popular_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.featured_chats = chats

        for character in self.featured_chats:
            character = character.get('character_item', {})
            card = CharacterCards.MainCard(self, character.get('name'), character.get('avatar_file_name'), character.get('title'), character.get('user__username'), character.get('external_id'), character.get('participant__num_interactions'))
            card.setFixedSize(277, 134)
            self.for_you_layout.addWidget(card)

    def addTryThisChats(self, chats):
        for layout in (self.try_this_odd_layout, self.try_this_even_layout):
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                if item and item.widget():
                    item.widget().deleteLater()

        self.try_this_chats = chats
        for index, character in enumerate(self.try_this_chats):
            card = CharacterCards.MiniCard(
                self,
                character.get('name'),
                character.get('external_id'),
                character.get('avatar_file_name')
            )
            card.setFixedSize(277, 70)
            if (index + 1) % 2 == 0:
                self.try_this_even_layout.addWidget(card)
            else:
                self.try_this_odd_layout.addWidget(card)

    def getMe(self, data):
        self.me_full = data
        self.me = self.me_full.get("user", {})
        self.author_id = self.me['id']
        self.name = self.me['account']['name']
        self.username = self.me['username']
        self.me_has_avatar = True if self.me.get('account', {}).get('avatar_file_name') else False
        self.me_avatar = self.me.get('account', {}).get('avatar_file_name')

        if self.me_has_avatar:
            self.left_sidebar.avatarUpdate()

        self.welcome_label.setText(self.tr("Welcome back, ") + self.name)
        self.profile_button.setText(self.name)

    def getUserSettings(self, data):
        self.chat_thread.get_user_settings_signal.disconnect()
        self.user_settings = data

    def getAvailableModels(self, data):
        self.available_models = data

    def getAvailableModelsGit(self, data):
        self.available_models_git = data

    def setOutputDevice(self, index):
        device_name = self.output_devices.get(index)
        devices = sounddevice.query_devices()
        for i, dev in enumerate(devices):
            if dev["name"] == device_name and dev["max_output_channels"] > 0:
                sounddevice.default.device = (sounddevice.default.device[0], i)
                break

    def mousePressEvent(self, event: QMouseEvent):
        if self.overlay.isVisible() and self.hide_overlay:
            global_click_pos = event.globalPosition().toPoint()
            sidebar_global_pos = self.overlay_content.mapToGlobal(self.overlay_content.rect().topLeft())
            sidebar_rect = QRect(sidebar_global_pos, self.overlay_content.size())
            if not sidebar_rect.contains(global_click_pos):
                self.hideOverlay()

        super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.auto_collapse_sidebar:
            if self.left_sidebar_visible and not self.left_sidebar_hide_user or self.left_sidebar_hide_auto:
                if self.width() < 1100:
                    self.left_sidebar_hide_auto = True
                else:
                    self.left_sidebar_hide_auto = False
                self.left_sidebar_visible = not self.left_sidebar_hide_auto
                self.left_sidebar.setVisible(self.left_sidebar_visible)
                self.top_bar_collapse_button.setVisible(not self.left_sidebar_visible)
        if hasattr(self, 'overlay'):
            self.overlay.setGeometry(self.rect())
        if hasattr(self, 'notification_message_label'):
            self.notification_message_label.setGeometry(QRect(int((self.width() - self.notification_message_label.width()) / 2), self.notification_message_label.y(), 300, 50))
        self.settings.setValue("main_window/height", self.geometry().height())
        self.settings.setValue("main_window/width", self.geometry().width())

    def changeEvent(self, a0):
        super().changeEvent(a0)
        if a0.type() == QEvent.Type.WindowStateChange:
            self.settings.setValue("main_window/maximized", self.isMaximized())

    def moveEvent(self, a0):
        super().moveEvent(a0)
        self.settings.setValue("main_window/x", self.geometry().x())
        self.settings.setValue("main_window/y", self.geometry().y())

    def showEvent(self, a0):
        super().showEvent(a0)
        hide_action.setVisible(True)
        show_action.setVisible(False)
        self.discord_thread.update_wlrpc()

    def hideEvent(self, a0):
        super().hideEvent(a0)
        hide_action.setVisible(False)
        show_action.setVisible(True)
        self.discord_thread.clear()

    def closeEvent(self, a0):
        super().closeEvent(a0)
        if self.settings.value("backwork", False, type=bool):
            a0.ignore()
            self.hide()

class SearchPage(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.chat_thread: ChatThread | None = self.mw.chat_thread
        self.discord_thread: DiscordRPC | None = self.mw.discord_thread
        self.svg_icons = Svg()
        self.setStyleSheet("background-color: transparent; border: none;")

        self.initUI()
        if self.mw.drpc_enable and self.mw.drpc_show_current_page:
            self.discord_thread.update(details=self.tr("Search characters..."))

    def initUI(self):
        self.layout = QVBoxLayout(self.mw)

        self.scroll_area, self.cards_viewport, self.cards_layout = self.createMainContentPage()
        self.top_bar, self.top_bar_layout = self.createTopBar()

        self.layout.addWidget(self.scroll_area, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(self.layout)

        self.mw.top_bar_stacked_widget.setFixedHeight(40)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def createMainContentPage(self):
        scroll_page = VerticalScrollPage()
        scroll_page.setFixedWidth(700)
        scroll_viewport = scroll_page.viewport
        scroll_viewport.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_page.layout

        return scroll_page, scroll_viewport, scroll_layout

    def showSearchResults(self):
        search_query = self.search_bar.text().strip()
        if not search_query:
            return

        self.mw.search_bar.setText(search_query)
        search_page = SearchPage(self.mw)
        self.mw.main_content_area.addWidget(search_page)
        self.mw.main_content_area.setCurrentWidget(search_page)

        self.chat_thread.character_search_signal.connect(search_page.populate)
        self.chat_thread.character_search(search_query)
        self.deleteLater()

    def populate(self, data):
        self.data = data[0].get("result", {}).get("data", {}).get("json", []).get('characters', [])
        if self.data:
            for character in self.data:
                card = CharacterCards.MainCard(self.mw, character.get('participant__name'), character.get('avatar_file_name'),
                                               character.get('title').replace('\n', ''), character.get('user__username'),
                                               character.get('external_id'), character.get('participant__num_interactions', 0),
                                               0, 70, 70)
                card.setFixedHeight(87)
                self.cards_layout.addWidget(card)
        else:
            no_results_label = QLabel(self.tr("Characters not found"))
            font = no_results_label.font()
            font.setBold(True)
            font.setPointSize(20)
            no_results_label.setFont(font)
            self.cards_layout.addWidget(no_results_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.chat_thread.character_search_signal.disconnect()

    def createTopBar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar_layout = QVBoxLayout()
        top_bar.setLayout(top_bar_layout)

        self.search_bar = LineEdit()
        self.search_bar.setIcon(QIcon(self.svg_icons.search()))
        self.search_bar.setText(self.mw.search_bar.text())
        self.search_bar.setPlaceholderText(self.tr("Character Search"))
        self.search_bar.returnPressed.connect(self.showSearchResults)
        top_bar_layout.addWidget(self.search_bar, alignment=Qt.AlignmentFlag.AlignTop)

        return top_bar, top_bar_layout

    def hideEvent(self, a0):
        super().hideEvent(a0)
        self.mw.search_bar.setText("")

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout()
        self.mw: EmiliaNext | None = parent
        self.chat_thread: ChatThread | None = self.mw.chat_thread
        self.discord_thread: DiscordRPC | None = self.mw.discord_thread
        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.languages = {
            "en_US": {"title": self.tr("English"), "lang_available": True, "google_code": "en"},
            "ru_RU": {"title": self.tr("Russian"), "lang_available": True, "google_code": "ru"},
            "fr_FR": {"title": self.tr("French"), "lang_available": False, "google_code": "fr"},
            "es_ES": {"title": self.tr("Spanish"), "lang_available": True, "google_code": "es"},
            "af_ZA": {"title": self.tr("Afrikaans"), "lang_available": False, "google_code": "af"},
            "sq_AL": {"title": self.tr("Albanian"), "lang_available": False, "google_code": "sq"},
            "am_ET": {"title": self.tr("Amharic"), "lang_available": False, "google_code": "am"},
            "ar_SA": {"title": self.tr("Arabic"), "lang_available": False, "google_code": "ar"},
            "hy_AM": {"title": self.tr("Armenian"), "lang_available": False, "google_code": "hy"},
            "az_AZ": {"title": self.tr("Azerbaijani"), "lang_available": False, "google_code": "az"},
            "eu_ES": {"title": self.tr("Basque"), "lang_available": False, "google_code": "eu"},
            "bn_BD": {"title": self.tr("Bengali"), "lang_available": False, "google_code": "bn"},
            "bg_BG": {"title": self.tr("Bulgarian"), "lang_available": False, "google_code": "bg"},
            "ca_ES": {"title": self.tr("Catalan"), "lang_available": False, "google_code": "ca"},
            "hr_HR": {"title": self.tr("Croatian"), "lang_available": False, "google_code": "hr"},
            "cs_CZ": {"title": self.tr("Czech"), "lang_available": False, "google_code": "cs"},
            "da_DK": {"title": self.tr("Danish"), "lang_available": False, "google_code": "da"},
            "nl_NL": {"title": self.tr("Dutch"), "lang_available": False, "google_code": "nl"},
            "et_EE": {"title": self.tr("Estonian"), "lang_available": False, "google_code": "et"},
            "tl_PH": {"title": self.tr("Filipino"), "lang_available": False, "google_code": "tl"},
            "fi_FI": {"title": self.tr("Finnish"), "lang_available": False, "google_code": "fi"},
            "ka_GE": {"title": self.tr("Georgian"), "lang_available": False, "google_code": "ka"},
            "de_DE": {"title": self.tr("German"), "lang_available": True, "google_code": "de"},
            "el_GR": {"title": self.tr("Greek"), "lang_available": False, "google_code": "el"},
            "gu_IN": {"title": self.tr("Gujarati"), "lang_available": False, "google_code": "gu"},
            "he_IL": {"title": self.tr("Hebrew"), "lang_available": False, "google_code": "he"},
            "hi_IN": {"title": self.tr("Hindi"), "lang_available": False, "google_code": "hi"},
            "hu_HU": {"title": self.tr("Hungarian"), "lang_available": False, "google_code": "hu"},
            "is_IS": {"title": self.tr("Icelandic"), "lang_available": False, "google_code": "is"},
            "id_ID": {"title": self.tr("Indonesian"), "lang_available": False, "google_code": "id"},
            "ga_IE": {"title": self.tr("Irish"), "lang_available": False, "google_code": "ga"},
            "it_IT": {"title": self.tr("Italian"), "lang_available": False, "google_code": "it"},
            "ja_JP": {"title": self.tr("Japanese"), "lang_available": False, "google_code": "ja"},
            "kn_IN": {"title": self.tr("Kannada"), "lang_available": False, "google_code": "kn"},
            "kk_KZ": {"title": self.tr("Kazakh"), "lang_available": False, "google_code": "kk"},
            "ko_KR": {"title": self.tr("Korean"), "lang_available": False, "google_code": "ko"},
            "lo_LA": {"title": self.tr("Lao"), "lang_available": False, "google_code": "lo"},
            "lv_LV": {"title": self.tr("Latvian"), "lang_available": False, "google_code": "lv"},
            "lt_LT": {"title": self.tr("Lithuanian"), "lang_available": False, "google_code": "lt"},
            "mk_MK": {"title": self.tr("Macedonian"), "lang_available": False, "google_code": "mk"},
            "ms_MY": {"title": self.tr("Malay"), "lang_available": False, "google_code": "ms"},
            "ml_IN": {"title": self.tr("Malayalam"), "lang_available": False, "google_code": "ml"},
            "mt_MT": {"title": self.tr("Maltese"), "lang_available": False, "google_code": "mt"},
            "mn_MN": {"title": self.tr("Mongolian"), "lang_available": False, "google_code": "mn"},
            "ne_NP": {"title": self.tr("Nepali"), "lang_available": False, "google_code": "ne"},
            "no_NO": {"title": self.tr("Norwegian"), "lang_available": False, "google_code": "no"},
            "fa_IR": {"title": self.tr("Persian"), "lang_available": False, "google_code": "fa"},
            "pl_PL": {"title": self.tr("Polish"), "lang_available": False, "google_code": "pl"},
            "pt_PT": {"title": self.tr("Portuguese"), "lang_available": True, "google_code": "pt"},
            "pa_IN": {"title": self.tr("Punjabi"), "lang_available": False, "google_code": "pa"},
            "ro_RO": {"title": self.tr("Romanian"), "lang_available": False, "google_code": "ro"},
            "sr_RS": {"title": self.tr("Serbian"), "lang_available": False, "google_code": "sr"},
            "sk_SK": {"title": self.tr("Slovak"), "lang_available": False, "google_code": "sk"},
            "sl_SI": {"title": self.tr("Slovenian"), "lang_available": False, "google_code": "sl"},
            "sw_KE": {"title": self.tr("Swahili"), "lang_available": False, "google_code": "sw"},
            "sv_SE": {"title": self.tr("Swedish"), "lang_available": False, "google_code": "sv"},
            "ta_IN": {"title": self.tr("Tamil"), "lang_available": False, "google_code": "ta"},
            "te_IN": {"title": self.tr("Telugu"), "lang_available": False, "google_code": "te"},
            "th_TH": {"title": self.tr("Thai"), "lang_available": False, "google_code": "th"},
            "tr_TR": {"title": self.tr("Turkish"), "lang_available": False, "google_code": "tr"},
            "uk_UA": {"title": self.tr("Ukrainian"), "lang_available": True, "google_code": "uk"},
            "ur_PK": {"title": self.tr("Urdu"), "lang_available": False, "google_code": "ur"},
            "vi_VN": {"title": self.tr("Vietnamese"), "lang_available": False, "google_code": "vi"},
            "cy_GB": {"title": self.tr("Welsh"), "lang_available": False, "google_code": "cy"},
            "xh_ZA": {"title": self.tr("Xhosa"), "lang_available": False, "google_code": "xh"}
        }
        self.settings_data = [
            {
                "label": self.tr("Character.AI Settings"),
                "settings": [
                    {"type": "pushbutton", "label": self.tr("Character.AI Login") + "\n" + self.tr("Valid until: ") + self.mw.settings.value('cai_auth/expiration_date') if self.mw.settings.value('cai_auth/expiration_date') else self.tr("Character.AI Login"),
                     "buttonlabel": self.tr("Re-Auth with Character.AI") if self.mw.token else self.tr("Auth with Character.AI") ,
                     "key": "auth_cookie_get", "click": self.getCookies},
                    {"type": "pushbutton", "label": self.tr("User Settings"), "buttonlabel": self.tr("Open"), "key": "cai_edit", "click": self.openUserSettings}
                ]
            }, {
                "label": self.tr("Emilia Settings"),
                "settings": [
                    {"type": "checkbox", "label": self.tr("Automatically hide the sidebar when the window is narrow"), "key": "auto_collapse_sidebar"},
                    {"type": "checkbox", "label": self.tr("Working in the background"), "key": "backwork", "def_value": True},
                    {"type": "checkbox", "label": self.tr("Display text formatting buttons"), "key": "show_format_buttons", "def_value": False},
                    {"type": "combobox", "label": self.tr("Input Device"), "items": self.mw.input_devices.values(), "key": "input_device"},
                    {"type": "combobox", "label": self.tr("Output Device"), "items": self.mw.output_devices.values(), "key": "output_device"},
                    {"type": "keybind", "label": self.tr("Microphone mute key"), "def_value": "Ctrl+M", "key": "microphone_mute_key_bind"},
                    {"type": "checkbox", "label": self.tr("Use the old implementation of voice chat"), "key": "use_old_voice_chat"},
                ]
            }, {
                "label": self.tr("VTube Studio Plugin"),
                "settings": [
                    {"type": "checkbox", "label": self.tr("Use VTube Studio"), "key": "vtube/use", "def_value": False},
                    {"type": "lineedit", "label": self.tr("VTube Studio Port"), "key": "vtube/port",
                     "validator": QIntValidator(0, 99999999), "def_value": 8001, "may_be_empty": False},
                    {"type": "pushbutton", "label": self.tr("VTube Emotes Editor"),
                     "buttonlabel": self.tr("Open"),
                     "key": "vtube/emotes_editor", "click": self.openEmotesEditor},
                    {"type": "pushbutton", "label": self.tr("Check the connection to VTube Studio"), "buttonlabel": self.tr("Check"),
                     "key": "vtube/check_connect", "click": self.vtubeCheck},
                ]
            }, {
                "label": self.tr("Discord Rich Presence"),
                "settings": [
                    {"type": "checkbox", "label": self.tr("Enable DiscordRPC"), "key": "discord_rpc/enable", "def_value": True},
                    {"type": "checkbox", "label": self.tr("Display the current page"), "key": "discord_rpc/show_current_page", "def_value": True},
                    {"type": "checkbox", "label": self.tr("Displaying the chat name"), "key": "discord_rpc/show_chat_name", "def_value": False},
                    {"type": "checkbox", "label": self.tr("Displaying the nickname of the profile being viewed"), "key": "discord_rpc/show_username", "def_value": False}
                ]
            }, {
                "label": self.tr("Languages of Emilia"),
                "settings": [
                    {"type": "combobox", "label": self.tr("Emilia Language"), "items": [lang["title"] for lang in self.languages.values() if lang.get("lang_available", False)], "key": "emilia_language"},
                    {"type": "checkbox", "label": self.tr("Translate user's messages"), "key": "tr_user_msg"},
                    {"type": "combobox", "label": self.tr("Translate user's messages to"), "items": [lang["title"] for lang in self.languages.values()], "key": "tr_user_msg_to"},
                    {"type": "checkbox", "label": self.tr("Translate character messages"), "key": "tr_char_msg"},
                    {"type": "combobox", "label": self.tr("Translate character messages to"), "items": [lang["title"] for lang in self.languages.values()], "key": "tr_char_msg_to"},
                ]
            }, {
                "label": self.tr("Other"),
                "settings": [
                    {"type": "pushbutton", "label": self.tr("Did you find a problem?"),
                     "buttonlabel": self.tr("Report a Problem"),
                     "key": "other/report_a_problem", "click": lambda: webbrowser.open("https://github.com/Kajitsy/Emilia/issues")},
                    {"type": "pushbutton", "label": self.tr("Settings Folder"),
                     "buttonlabel": self.tr("Open"),
                     "key": "other/settings_folder",
                     "click": lambda: os.startfile(os.path.dirname(self.mw.settings.fileName()))},
                    {"type": "pushbutton", "label": self.tr("Logs Folder"),
                     "buttonlabel": self.tr("Open"),
                     "key": "other/logs_folder",
                     "click": lambda: os.startfile(os.path.join(os.getcwd(), "logs"))},
                ]
            }, {
                "label": self.tr("About Emilia"),
                "settings": [
                    {
                        "label": self.tr("Emilia is a desktop version of Character.AI with several improvements and additional features.")+
                                 "\n"+self.tr("The program is distributed free of charge under the MIT License."),
                        "key": "about/title"},
                    {
                        "label": self.tr("By using Emilia, you accept the Terms of Use Character.AI and confirm that you have read the Privacy Policy Character.AI"),
                        "key": "about/tos"
                    }
                ]
            },
        ]

        self.setting_widgets = {}
        self.setting_data = {}

        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.scroll_area, self.settings_viewport, self.settings_layout = self.createMainContentPage()
        self.button_bar, self.button_layout = self.createButtonBar()

        main_layout.addWidget(self.scroll_area, alignment=Qt.AlignmentFlag.AlignHCenter)
        main_layout.addWidget(self.button_bar, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(main_layout)

    def openUserSettings(self):
        overlay = UserCards.EditOverlay(self.mw)
        self.mw.showOverlay(overlay)

    def openEmotesEditor(self):
        with open(f"./data/VTube_Emotes.json", "r") as f:
            emotes_data = json.load(f)

        def createEmoteSlot(emote, param_name="", random_value=False, value=0, value_1=0, value_2=100):
            def updateRandom():
                nonlocal random_value
                random_value = random_checkbox.isChecked()
                if random_value:
                    value_1_edit.setVisible(True)
                    value_2_edit.setVisible(True)
                    value_edit.setVisible(False)
                else:
                    value_1_edit.setVisible(False)
                    value_2_edit.setVisible(False)
                    value_edit.setVisible(True)
                updateParamName(param_name_edit.text(), param_name)

            def updateParamName(text, pn):
                if pn in emotes_data[emote]['params']:
                    del emotes_data[emote]['params'][pn]
                nonlocal param_name
                param_name = text
                if random_value:
                    emotes_data[emote]['params'][text] = f"rndm({value_1}, {value_2})"
                else:
                    emotes_data[emote]['params'][text] = value

            def updateParamValue(text):
                nonlocal value
                value = text
                emotes_data[emote]['params'][param_name] = value

            def updateParamValue1(text):
                nonlocal value_1
                value_1 = text
                if random_value:
                    emotes_data[emote]['params'][param_name] = f"rndm({value_1}, {value_2})"

            def updateParamValue2(text):
                nonlocal value_2
                value_2 = text
                if random_value:
                    emotes_data[emote]['params'][param_name] = f"rndm({value_1}, {value_2})"

            def removeParameter():
                if param_name in emotes_data[emote]['params']:
                    del emotes_data[emote]['params'][param_name]
                u_widget.hide()
                u_widget.deleteLater()

            validator = QRegularExpressionValidator(QRegularExpression(r"[^\s]+"))
            u_widget = CardFrame()
            u_widget.setCursor(Qt.CursorShape.LastCursor)
            u_layout = QHBoxLayout(u_widget)
            u_widget.setLayout(u_layout)

            param_name_edit = LineEdit()
            param_name_edit.setValidator(validator)
            param_name_edit.textChanged.connect(lambda t: updateParamName(t, param_name))
            param_name_edit.setPlaceholderText(self.tr("Parameter Name"))
            param_name_edit.setText(param_name)
            param_name_edit.setFixedWidth(150)
            u_layout.addWidget(param_name_edit)

            remove_button = PushButton()
            remove_button.clicked.connect(removeParameter)
            remove_button.setIcon(self.mw.svg_icons.close())
            u_layout.addWidget(remove_button)

            u_layout.addStretch()

            random_checkbox = CheckBox()
            random_checkbox.setChecked(random_value)
            random_checkbox.clicked.connect(updateRandom)
            u_layout.addWidget(random_checkbox)

            random_label = QLabel(self.tr("Use Random Value"))
            u_layout.addWidget(random_label)

            value_1_edit = LineEdit()
            value_1_edit.setValidator(validator)
            value_1_edit.textEdited.connect(updateParamValue1)
            value_1_edit.setPlaceholderText(self.tr("From"))
            value_1_edit.setText(str(value_1))
            value_1_edit.setFixedWidth(50)
            u_layout.addWidget(value_1_edit)
            value_1_edit.setVisible(random_value)

            value_2_edit = LineEdit()
            value_2_edit.setValidator(validator)
            value_2_edit.textEdited.connect(updateParamValue2)
            value_2_edit.setPlaceholderText(self.tr("To"))
            value_2_edit.setText(str(value_2))
            value_2_edit.setFixedWidth(50)
            u_layout.addWidget(value_2_edit)
            value_2_edit.setVisible(random_value)

            value_edit = LineEdit()
            value_edit.setValidator(validator)
            value_edit.textEdited.connect(updateParamValue)
            value_edit.setPlaceholderText(self.tr("Value"))
            value_edit.setText(str(value))
            value_edit.setFixedWidth(106)
            u_layout.addWidget(value_edit)
            value_edit.setVisible(not random_value)

            return u_widget

        def createParameter(button, layout, emote):
            layout.removeWidget(button)
            layout.addWidget(createEmoteSlot(emote))
            layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignHCenter)

        def save():
            with open("./data/VTube_Emotes.json", "w", encoding="utf-8") as f:
                json.dump(emotes_data, f, ensure_ascii=False, indent=4)
            self.mw.showNotification(self.tr("The values for emotions are saved"))
            self.mw.hideOverlay()

        scroll_page = VerticalScrollPage()
        scroll_viewport = scroll_page.viewport
        scroll_layout = scroll_page.layout
        scroll_viewport.setStyleSheet("background-color: transparent; border: none;")

        for emote_name in emotes_data.keys():
            e_widget = QWidget()
            e_layout = QVBoxLayout()
            e_widget.setLayout(e_layout)
            emote_data = emotes_data[emote_name]
            if emote_data.get("version", 1) == 1:
                break
            params = emote_data['params']

            head_layout = QHBoxLayout()
            head_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            group_label = QLabel(emote_data["label"])
            font = group_label.font()
            font.setBold(True)
            font.setPointSize(14)
            group_label.setFont(font)
            head_layout.addWidget(group_label)
            test_emote_button = QPushButton(self.tr(" | Test"))
            test_emote_button.setFont(font)
            test_emote_button.setCursor(Qt.CursorShape.PointingHandCursor)
            test_emote_button.clicked.connect(lambda _, e=emote_name: self.chat_thread.vtube_use_emote(e))
            head_layout.addWidget(test_emote_button)
            e_layout.addLayout(head_layout)

            for param in list(params.keys()):
                random_value = str(params[param]).startswith("rndm")
                if random_value:
                    param_widget = createEmoteSlot(emote_name, param, random_value, value_1=params[param].strip("rndm ()").split(", ")[0],
                                                   value_2=params[param].strip("rndm ()").split(", ")[1])
                else:
                    param_widget = createEmoteSlot(emote_name, param, random_value, params[param])
                e_layout.addWidget(param_widget)
            add_button = PushButton(self.tr("Add parameter"))
            add_button.clicked.connect(lambda _, b=add_button, l=e_layout, e=emote_name: createParameter(b, l, e))
            e_layout.addWidget(add_button, alignment=Qt.AlignmentFlag.AlignHCenter)
            scroll_layout.addWidget(e_widget)

        widget = QWidget()
        widget.setFixedSize(750, 750)
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)

        buttons_frame = QWidget(widget)
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        buttons_frame.setLayout(buttons_layout)

        save_button = PushButton(self.tr("Save"))
        save_button.clicked.connect(save)
        buttons_layout.addWidget(save_button)

        close_button = PushButton(self.tr("Close"))
        close_button.clicked.connect(self.mw.hideOverlay)
        buttons_layout.addWidget(close_button)

        layout.addWidget(scroll_page)
        layout.addWidget(buttons_frame)
        self.mw.showOverlay(widget)

    def _vtubeCheck(self, text):
        self.mw.showNotification(text)
        self.chat_thread.vtube_connect_signal.disconnect()

    def vtubeCheck(self):
        self.chat_thread.vtube_connect_signal.connect(self._vtubeCheck)
        self.chat_thread.check_vtube_connect()

    def createTopBar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(0)
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        return top_bar, top_bar_layout

    def createMainContentPage(self):
        scroll_area = VerticalScrollPage()
        scroll_area.setFixedWidth(800)

        settings_viewport = scroll_area.viewport
        # settings_viewport.setFixedWidth(780)
        settings_layout = scroll_area.layout
        scroll_area.setWidget(settings_viewport)

        for setting_group in self.settings_data:
            group_layout = QVBoxLayout()
            group_beta = setting_group.get('beta', False)
            group_label = QLabel(format_text(setting_group["label"]))
            if group_beta:
                group_label.setText(f'{format_text(setting_group["label"])} {self.tr("(Beta)")}')
            font = group_label.font()
            font.setBold(True)
            font.setPointSize(14)
            group_label.setFont(font)
            group_layout.addWidget(group_label, alignment=Qt.AlignmentFlag.AlignHCenter)

            for setting in setting_group["settings"]:
                layout = QHBoxLayout()
                if setting.get("label"):
                    label = QLabel()
                    label.setText(format_text(setting["label"]))
                    label.setWordWrap(True)
                    layout.addWidget(label, 1)

                key = setting["key"]

                if setting.get('type'):
                    if setting["type"] == "lineedit":
                        widget = LineEdit()
                        if setting.get("validator"):
                            widget.setValidator(setting["validator"])
                        widget.setObjectName(key)
                        widget.setEchoMode(setting.get("echo", LineEdit.EchoMode.Normal))
                    elif setting["type"] == "checkbox":
                        widget = CheckBox()
                        widget.setObjectName(key)
                    elif setting["type"] == "pushbutton":
                        widget = PushButton(setting["buttonlabel"])
                        widget.setObjectName(key)
                        widget.clicked.connect(setting["click"])
                    elif setting["type"] == "combobox":
                        widget = ComboBox()
                        widget.setObjectName(key)
                        widget.addItems(setting['items'])
                    elif setting["type"] == "keybind":
                        widget = KeySequenceEdit()
                        widget.setObjectName(key)
                        widget.keySequenceChanged.connect(lambda seq, edit=widget: edit.setKeySequence(QKeySequence(seq[0])) if seq.count() > 1 else None)

                    layout.addWidget(widget)

                if group_beta:
                    if self.mw.beta:
                        group_layout.addLayout(layout)
                        self.setting_widgets[setting["key"]] = widget
                        self.setting_data[setting["key"]] = setting
                else:
                    group_layout.addLayout(layout)
                    self.setting_widgets[setting["key"]] = widget
                    self.setting_data[setting["key"]] = setting

            if group_beta:
                if self.mw.beta:
                    settings_layout.addLayout(group_layout)
                    settings_layout.addWidget(QFrame())
            else:
                settings_layout.addLayout(group_layout)
                settings_layout.addWidget(QFrame())

        return scroll_area, settings_viewport, settings_layout

    def createButtonBar(self):
        button_bar = QWidget()
        button_layout = QHBoxLayout()
        button_bar.setLayout(button_layout)
        self.save_button = PushButton(self.tr("Save"))
        self.save_button.clicked.connect(self.saveSettings)
        self.cancel_button = PushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.loadSettings)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        return button_bar, button_layout

    def createTopBar(self):
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        return top_bar, top_bar_layout

    def getCookies(self):
        self.cookie_available = False
        self.token_available = False
        def cl():
            self.mw.hideOverlay()
            cookies.close()
            self.loadSettings()
            self.mw.showNotification(self.tr("The token is being updated..."))

            self.chat_thread.chat_histories = {}
            self.chat_thread.me = None
            for i in range(self.mw.recommended_layout.count()):
                item = self.mw.recommended_layout.itemAt(i)
                if item and item.widget():
                    item.widget().deleteLater()
            if self.mw.featured_chats:
                for i in range(self.mw.for_you_layout.count()):
                    item = self.mw.for_you_layout.itemAt(i)
                    if item and item.widget():
                        item.widget().deleteLater()
            if self.mw.recent_chats:
                for i in range(self.mw.recent_chat_scroll_layout.count()):
                    item = self.mw.recent_chat_scroll_layout.itemAt(i)
                    if item and item.widget():
                        item.widget().deleteLater()

            self.chat_thread.token = self.mw.token
            self.chat_thread.cookie = self.mw.cookie
            self.chat_thread.create_connect()

            self.chat_thread.get_recent_chats()
            self.chat_thread.get_main_page_chats()
            self.chat_thread.get_me()
        def get(auth_token, expiration_date: QDateTime):
            self.cookie_available = True
            self.mw.settings.setValue("cai_auth/cookie", auth_token)
            self.mw.settings.setValue("cai_auth/expiration_date", expiration_date.toString("yyyy.MM.dd HH:mm"))
            if self.token_available: cl(self)
        def token_get(token):
            self.token_available = True
            self.mw.settings.setValue("cai_auth/token", token)
            self.mw.token = token
            if self.cookie_available: cl()
        cookies = GetCookies()
        self.mw.showOverlay(cookies)
        cookies.auth_cookie_signal.connect(lambda token, date: get(token, date))
        cookies.authorization_signal.connect(lambda token: token_get(token))
        cookies.notification_signal.connect(self.mw.showNotification)

    def back(self):
        self.mw.main_content_area.setCurrentWidget(self.mw.main_page)
        self.mw.left_sidebar.setEnabled(True)

    def showEvent(self, event):
        super().showEvent(event)
        self.mw.top_bar_stacked_widget.setFixedHeight(0)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)
        self.loadSettings()
        if self.mw.drpc_enable and self.mw.drpc_show_current_page: self.discord_thread.update(details=self.tr("Looking at the settings..."))

    def hideEvent(self, a0):
        super().hideEvent(a0)
        self.mw.settings_button.setChecked(False)

    def loadSettings(self):
        for key, widget in self.setting_widgets.items():
            value = self.mw.settings.value(key, str(self.setting_data[key].get('def_value')))
            if isinstance(widget, LineEdit):
                widget.setText(value if value is not None else "")
            elif isinstance(widget, CheckBox):
                value = self.mw.settings.value(key, self.setting_data[key].get('def_value'), type=bool)
                widget.setChecked(value)
            elif isinstance(widget, ComboBox):
                if key == "emilia_language":
                    widget.setCurrentText(self.languages.get(self.mw.current_language, {}).get("title", self.tr("English")))
                elif key in {"tr_char_msg_to", "tr_user_msg_to"}:
                    widget.setCurrentText(self.languages.get(value, {}).get("title", self.tr("English")))
                elif key in {"input_device", "output_device"}:
                    if key == "input_device":
                        text = self.mw.input_devices.get(value)
                    elif key == "output_device":
                        text = self.mw.output_devices.get(value)
                    widget.setCurrentText(text)
                else:
                    widget.setCurrentText(value)
            elif isinstance(widget, KeySequenceEdit):
                widget.setKeySequence(QKeySequence(value))
        logging.debug(f"main.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Settings are loaded")

    def saveSettings(self):
        for key, widget in self.setting_widgets.items():
            if isinstance(widget, LineEdit):
                if not self.setting_data.get(key).get('may_be_empty', True) and not widget.text():
                    self.mw.showNotification(self.setting_data[key]['label'] + self.tr(" cannot be empty"))
                    return
                self.mw.settings.setValue(key, widget.text())
                if key == "vtube/port":
                    self.chat_thread.eec.create_vts_with_port(int(widget.text()))
            elif isinstance(widget, CheckBox):
                self.mw.settings.setValue(key, 'true' if widget.isChecked() else 'false')
                if key == "discord_rpc/enable":
                    self.mw.drpc_enable = widget.isChecked()
                    if self.mw.drpc_enable:
                        self.discord_thread.connect()
                    else:
                        self.discord_thread.clear()
                        self.discord_thread.close()
                if key == "discord_rpc/show_chat_name":
                    self.mw.drpc_show_chat_name = widget.isChecked()
                if key == "discord_rpc/show_username":
                    self.mw.drpc_show_username = widget.isChecked()
                if key == "discord_rpc/show_current_page":
                    self.mw.drpc_show_current_page = widget.isChecked()
                if self.mw.drpc_enable:
                    if self.mw.drpc_show_current_page:
                        self.discord_thread.update(state=self.tr("Looking at the settings..."))
                    else:
                        self.discord_thread.update()
            elif isinstance(widget, ComboBox):
                if key == "emilia_language":
                    lang = next((k for k, v in self.languages.items() if v["title"] == widget.currentText() and v.get("lang_available", False)), None)
                    if lang != self.mw.current_language:
                        self.mw.settings.setValue(key, lang)
                        self.mw.current_language = lang
                        translator.load(f"lang/{lang}.qm")
                        app.removeTranslator(translator)
                        if lang != "en_US":
                            app.installTranslator(translator)
                        self.mw.close()
                        global main_window
                        main_window = EmiliaNext()
                        main_window.show()
                elif key in {"tr_char_msg_to", "tr_user_msg_to"}:
                    lang = next(k for k, v in self.languages.items() if v["title"] == widget.currentText())
                    self.mw.settings.setValue(key, lang)
                elif key in {"input_device", "output_device"}:
                    if key == "input_device": index = next(k for k, v in self.mw.input_devices.items() if v == widget.currentText())
                    elif key == "output_device":
                        index = next(k for k, v in self.mw.output_devices.items() if v == widget.currentText())
                        self.mw.setOutputDevice(index)
                    self.mw.settings.setValue(key, index)
            elif isinstance(widget, KeySequenceEdit):
                self.mw.settings.setValue(key, widget.keySequence().toString())
        self.mw.showNotification(self.tr("Settings saved successfully"))
        logging.debug(f"main.py ({self.__class__.__name__}.{inspect.currentframe().f_code.co_name}): Settings saved successfully")

async def main():
    global main_window, tray_icon, show_action, hide_action, quit_action
    tray_icon = QSystemTrayIcon()
    tray_menu = Menu()
    main_window = EmiliaNext()

    tray_icon.activated.connect(
        lambda reason: main_window.show() or main_window.raise_() or main_window.activateWindow()
        if reason == QSystemTrayIcon.ActivationReason.Trigger else None
    )
    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("Emilia")
    app.setWindowIcon(QIcon("icon.ico"))
    tray_icon.setIcon(QIcon("icon.ico"))

    show_action = QAction(tray_icon.tr("Show"))
    show_action.triggered.connect(
        lambda: main_window.showMaximized() if main_window.isMaximized() else main_window.show())
    tray_menu.addAction(show_action)

    hide_action = QAction(tray_icon.tr("Hide"))
    hide_action.triggered.connect(lambda: main_window.hide())
    tray_menu.addAction(hide_action)

    quit_action = QAction(tray_icon.tr("Quit"))
    quit_action.triggered.connect(lambda: app.quit())
    tray_menu.addAction(quit_action)

    if main_window.settings.value("main_window/maximized", False, type=bool):
        main_window.showMaximized()
    else:
        main_window.show()

    tray_icon.show()

if __name__ == "__main__":
    with loop:
        loop.create_task(main())
        loop.run_forever()