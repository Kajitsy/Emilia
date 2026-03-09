import ctypes
import platform
import sys, datetime, sounddevice

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QFrame, QSizePolicy, QStackedWidget, QProgressBar)
from PyQt6.QtGui import QMouseEvent, QAction, QGuiApplication
from PyQt6.QtCore import (QEvent, QSettings, QRect, QDateTime, QPropertyAnimation,
                          QEasingCurve, QTimer, QParallelAnimationGroup,
                          QPoint, Qt, QLocale, pyqtSignal)
from PyQt6.QtMultimedia import QMediaDevices
from packaging import version

from modules import (ImageLoader, Svg,
                     UpdaterThread, UpdateThread, ChatThread)
from modules.ui.Elements import (PushButton, HorizontalScrollArea, ClickableFrame,
                                 LeftSidebar, CheckBox, Menu,
                                 VerticalScrollPage, HorizontalScrollPage, TabButton, SearchLineEdit)
from modules.Utils import color_avatar
from modules.logic.QThreads import DiscordRPCThread
from modules.ui.cards import CharacterCards, SceneCards, VoiceCards
from modules.ui.pages import UserPages, ScenePages, CharacterPages
from modules.ui.mainwindow import SettingsPage, SearchPage, ChatInterface
from modules.ui import TM

class MainPage(QMainWindow):
    mw_show_signal = pyqtSignal()
    mw_hide_signal = pyqtSignal()
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
        self.settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "Emilia", "settings")
        self.current_language = self.settings.value("emilia_language", QLocale.system().name())
        self.theme = self.settings.value("app_theme", "Dark", type=str)
        TM.set_theme(self.theme)
        self._is_updating = False
        self.drpc_enable = self.settings.value("discord_rpc/enable", True, type=bool)
        self.drpc_show_chat_name = self.settings.value("discord_rpc/show_chat_name", False, type=bool)
        self.drpc_show_username = self.settings.value("discord_rpc/show_username", False, type=bool)
        self.drpc_show_current_page = self.settings.value("discord_rpc/show_current_page", True, type=bool)
        self.svg_icons = Svg()
        self.version = "3.3.0"
        self.beta = version.parse(self.version).is_prerelease

        geometry = self.settings.value("main_window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.setGeometry(100, 100, 1360, 800)
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
        self.discord_thread = DiscordRPCThread(self)
        self.threads.append(self.discord_thread)
        self.updater_thread = UpdaterThread(self.settings.value("update_server", "https://germany.emiupd.ateez.ru/", type=str))
        self.updater_thread.has_update_signal.connect(self.checkForUpdates)
        self.updater_thread.error_signal.connect(self.checkForUpdatesError)
        self.threads.append(self.updater_thread)

        self.image_loader = ImageLoader()

        self.setOutputDevice(self.settings.value('output_device', 0, type=int))
        if getattr(sys, 'frozen', False):
            self.updater_thread.start()

        self.initUI()
        self.loadUI()

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(f"""
            background-color: {TM.c("mw_back")};
            color: {TM.c("mw_color")};
        """)
        self.main_content_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {TM.c('primary_bg')};
                border: none;
                border-radius: 4px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {TM.c('primary_bg')};
                width: 8px;
                margin: 0px 0 0px 0;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px; 
            }}
            QScrollBar::sub-control:vertical {{
                background: {TM.c('scroll_sub')};
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {TM.c('scroll_handle')};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical {{
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }}
            QScrollBar::sub-line:vertical {{
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {TM.c('scroll_hover')};
            }}
        """)
        self.overlay_content.setStyleSheet(f"""
            background-color: {TM.c("mw_back")};
            border-radius: 4px;
            border: none;
        """)
        self.notification_message_label.setStyleSheet(f"""
            background-color: {TM.c("text")};
            color: {TM.c("primary_bg")};
            border-radius: 4px;
            padding: 10px;
        """)
        self.top_bar_collapse_button.setIcon(self.svg_icons.ellipsis(TM.c("disabled_text")))

    def initUI(self):
        self.layout = QHBoxLayout()

        self.left_sidebar = self.createLeftSidebar()
        self.layout.addWidget(self.left_sidebar)

        self.main_layout = QVBoxLayout()
        self.layout.addLayout(self.main_layout, 1)

        self.top_widget, self.top_bar_stacked_widget, self.t_bar = self.createTopBar()
        self.top_bar_stacked_widget.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.t_bar)

        self.main_content_area = QStackedWidget()
        self.main_page = self.createMainContentPage()
        self.search_results_page = QWidget()
        self.search_results_layout = QVBoxLayout(self.search_results_page)
        self.settings_page = SettingsPage.SettingsPage(self)
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

                self.chat_thread.get_me()
                self.chat_thread.get_user_settings()

                self.chat_thread.get_recent_chats()
                self.chat_thread.get_main_page_chats()
                self.chat_thread.get_recommended_chars()
                self.chat_thread.get_scenes_curated()
                self.chat_thread.get_trythis_chats()
                self.chat_thread.get_featured_voices()
                self.chat_thread.get_available_models()
                self.chat_thread.get_available_models_git()

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
        self.profile_button = left_sidebar.profile_button
        self.recent_chat_scroll_layout = left_sidebar.recent_chat_scroll_layout

        self.left_sidebar_animation = QPropertyAnimation(left_sidebar, b"geometry")
        self.left_sidebar_animation.setDuration(500)
        self.left_sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.left_sidebar_animation.finished.connect(lambda: self.leftSidebarAnim())

        return left_sidebar

    def addRecentChatCard(self, character_id, character_name, chat_id, character_avatar_url, scene_id=None, scene_name=""):
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

        def updateTheme(card):
            card.name_label.setStyleSheet(f"background-color: transparent; border: none; color: {TM.c('text')};")
            card.menu_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    margin-right: 10px;
                }}
                QPushButton:hover {{
                    background-color: {TM.c("hover_bg")};
                    border-radius: 4px;
                }}
                QPushButton:pressed {{
                    background-color: {TM.c('pressed_bg')};
                    border-radius: 4px;
                }}
            """)
            menu_button.setIcon(self.svg_icons.ellipsis(TM.c("disabled_text")))

        chat_layout = QHBoxLayout()
        chat_layout.setContentsMargins(0, 0, 0, 0)

        avatar_label = QLabel()
        avatar_label.setFixedSize(50, 50)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_layout.addWidget(avatar_label)
        setattr(card, 'avatar_label', avatar_label)

        if character_avatar_url:
            self.image_loader.load(f"https://characterai.io/i/80/static/avatars/{character_avatar_url}?webp=true&anim=0",
                                   45, 45, 100, label=avatar_label,
                                   error_cb=lambda _: color_avatar(avatar_label, 45, 45, character_name))
        else:
            color_avatar(avatar_label, 45, 45, character_name)

        avatar_label_2 = QLabel()
        avatar_label_2.setFixedSize(60, 60)
        avatar_label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_layout.addWidget(avatar_label_2)
        setattr(card, 'avatar_label_2', avatar_label_2)

        if character_avatar_url:
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{character_avatar_url}?webp=true&anim=0", 55, 55, 100,
                label=avatar_label_2, error_cb=lambda _: color_avatar(avatar_label_2, 55, 55, character_name))
        else:
            color_avatar(avatar_label_2, 55, 55, character_name)
        avatar_label_2.setVisible(False)

        text_layout = QVBoxLayout()
        chat_layout.addLayout(text_layout)

        name_label = QLabel(character_name)
        text_layout.addWidget(name_label, 1)
        setattr(card, 'name_label', name_label)

        scene_label = QLabel(scene_name)
        scene_label.setStyleSheet("background-color: transparent; border: none; color: gray;")
        if scene_name:
            text_layout.addWidget(scene_label, 1)
            setattr(card, 'scene_label', scene_label)

        menu_button = QPushButton()
        menu_button.visibility = True
        menu_button.setVisible(False)
        menu_button.clicked.connect(lambda: showContextMenu(menu_button.pos(), card))
        chat_layout.addWidget(menu_button, 1, Qt.AlignmentFlag.AlignRight)
        setattr(card, 'menu_button', menu_button)

        chat_layout.addStretch()
        card.setLayout(chat_layout)

        self.recent_chat_scroll_layout.addWidget(card)
        self.left_sidebar.resizeCard(card)
        TM.theme_changed.connect(lambda: updateTheme(card))
        updateTheme(card)
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

    def checkForUpdates(self, has_update):
        def update():
            def update_overlay(x, y):
                self.download_overlay_progress.setValue(x)
                self.download_overlay_progress.setMaximum(y)
                self.download_overlay_progress_label.setText(f"{x}/{y}")

            overlay = self.createDownloadOverlay()
            thread = UpdateThread(self, self.updater_thread.remote_url, self.updater_thread.files_to_download, self.updater_thread.files_to_removed)
            thread.progress_signal.connect(update_overlay)
            thread.error_signal.connect(self.checkForUpdatesError)
            self.threads.append(thread)

            self.hide_overlay = False
            self.showOverlay(overlay)
            thread.start()

        if has_update:
            self.showNotification(self.tr("An update is available"))
            self.update_button.setVisible(True)
            self.update_button.clicked.connect(lambda: update())

    def checkForUpdatesError(self, error):
        self.showNotification(error)
        if not self.hide_overlay:
            self.hide_overlay = True
            self.hideOverlay()

    def createDownloadOverlay(self):
        self.download_overlay_frame = QFrame()
        self.download_overlay_frame.setFixedSize(150, 90)
        layout = QVBoxLayout()

        self.download_overlay_label = QLabel(self.tr("Downloading..."))
        self.download_overlay_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.download_overlay_label)

        self.download_overlay_progress_label = QLabel()
        self.download_overlay_progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.download_overlay_progress_label)

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
        scenes_section.setFixedHeight(375)
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
        self.top_bar_collapse_button.setIcon(self.svg_icons.ellipsis(TM.c("disabled_text")))
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

        self.search_bar = SearchLineEdit(self)
        self.search_bar.returnPressed.connect(self.showSearchResultsV2)
        self.search_bar.setFixedWidth(200)
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
        cards_viewport.setStyleSheet("background-color: transparent; border: none;")
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
        cards_viewport.setStyleSheet("background-color: transparent; border: none;")

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
        scroll_viewport = scroll_page.viewport
        scroll_viewport.setStyleSheet("background-color: transparent; border: none;")
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
        button_scroll_viewport.setStyleSheet("background-color: transparent; border: none;")
        button_scroll_layout = QHBoxLayout()
        button_scroll_layout.setContentsMargins(0, 0, 0, 0)
        button_scroll_viewport.setLayout(button_scroll_layout)
        button_scroll_area.setWidget(button_scroll_viewport)

        self.category_buttons = []

        for key, value in categories.items():
            btn = TabButton(value)
            btn.setObjectName(key)
            btn.clicked.connect(lambda checked, b=btn, cat=key: self.onCategoryClicked(b, cat))
            self.category_buttons.append(btn)
            button_scroll_layout.addWidget(btn)
            if key == "Assistants":
                btn.setChecked(True)
                self.onCategoryClicked(btn, key)
        section_layout.addWidget(button_scroll_area, alignment=Qt.AlignmentFlag.AlignTop)

        scroll_page = HorizontalScrollPage()
        scroll_viewport = scroll_page.viewport
        scroll_viewport.setStyleSheet("background-color: transparent; border: none;")
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
        self.overlay_content_layout = QVBoxLayout(self.overlay_content)

        self.overlay_layout.addWidget(self.overlay_content)

        self.overlay.setGeometry(self.rect())
        self.overlay.hide()

        self.notification_message_label = QLabel(self)
        self.notification_message_label.setWordWrap(True)
        self.notification_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

        self.chat_thread.character_search_signal.connect(search_page.characterPopulate)
        self.chat_thread.character_search(search_query)
        self.search_bar.setText("")

    def showMainPage(self, widget: QWidget | None):
        if widget: widget.setVisible(False)
        self.main_content_area.setCurrentWidget(self.main_page)
        self.current_chat_interface = None
        self.top_widget.setVisible(True)

    def openCharacter(self, path=None, character_id=None):
        widget = CharacterPages.MainPage(self, path, character_id)
        self.main_content_area.addWidget(widget)
        self.main_content_area.setCurrentWidget(widget)

    def openScene(self, data={}, scene_id=None):
        widget = ScenePages.MainPage(self, data, scene_id)
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
        self.create_char_page = CharacterPages.EditPage(self, character_id)
        self.main_content_area.addWidget(self.create_char_page)
        self.main_content_area.setCurrentWidget(self.create_char_page)
        if self.current_chat_interface:
            self.current_chat_interface.setVisible(False)
            self.search_bar.setText("")

    def openCreateScenePage(self, scene_id=None):
        if scene_id:
            self.chat_thread.get_scene_by_id(scene_id)
            self.chat_thread.get_scene_by_id_signal.connect(self._openEditScenePage)
        else:
            self.create_scene_page = ScenePages.CreatePages.ChoiceStep(self)
            self.main_content_area.addWidget(self.create_scene_page)
            self.main_content_area.setCurrentWidget(self.create_scene_page)
        if self.current_chat_interface:
            self.current_chat_interface.setVisible(False)
            self.search_bar.setText("")

    def _openEditScenePage(self, data):
        self.chat_thread.get_scene_by_id_signal.disconnect(self._openEditScenePage)
        if data.get("character_id"):
            self.edit_scene_page = ScenePages.CreatePages.MainCharCreatePage(self, data, False, data['scene_id'])
        else:
            self.edit_scene_page = ScenePages.CreatePages.AnyCharCreatePage(self, data, False, data['scene_id'])
        self.main_content_area.addWidget(self.edit_scene_page)
        self.main_content_area.setCurrentWidget(self.edit_scene_page)

    def openUserPage(self, username):
        self.user_page = UserPages.MainPage(self, username)
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
            card = self.addRecentChatCard(chat.get('character_id'), chat.get('character_name'), chat.get('chat_id'), chat.get('character_avatar_uri'), chat.get('scene_id'), chat.get('name', ''))
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
            card = VoiceCards.HorizontalMiniCard(self, voice)
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
            card = SceneCards.MainCard(self, scene)
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

    def event(self, event):
        if event.type() == 210:
            if self._is_updating:
                return super().event(event)

            self._is_updating = True
            try:
                settings = QGuiApplication.styleHints()

                if settings.colorScheme() == Qt.ColorScheme.Dark:
                    new_theme = "Dark"
                else:
                    new_theme = "Light"

                if TM.current != new_theme:
                    self.theme = new_theme
                    TM.set_theme(self.theme)
                    self.update_theme()
            finally:
                self._is_updating = False

        return super().event(event)

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
        self.settings.setValue("main_window/geometry", self.saveGeometry())

    def changeEvent(self, a0):
        super().changeEvent(a0)
        if a0.type() == QEvent.Type.WindowStateChange:
            self.settings.setValue("main_window/maximized", self.isMaximized())

    def moveEvent(self, a0):
        super().moveEvent(a0)
        self.settings.setValue("main_window/geometry", self.saveGeometry())

    def showEvent(self, a0):
        super().showEvent(a0)
        self.mw_show_signal.emit()
        self.discord_thread.update_wlrpc()
        if platform.system() == 'Windows':
            from modules.logic.WinDarkTheme import ChangeDWMAttrib, detect
            if TM.get_theme(self.theme).get('titlebar', 'dark') == 'dark':
                ChangeDWMAttrib(detect(self), 19, ctypes.c_int(1))
                ChangeDWMAttrib(detect(self), 20, ctypes.c_int(1))
            elif TM.get_theme(self.theme).get('titlebar', 'dark') == 'light':
                ChangeDWMAttrib(detect(self), 19, ctypes.c_int(0))
                ChangeDWMAttrib(detect(self), 20, ctypes.c_int(0))

    def hideEvent(self, a0):
        super().hideEvent(a0)
        self.mw_hide_signal.emit()
        self.discord_thread.clear()

    def closeEvent(self, a0):
        super().closeEvent(a0)
        if self.settings.value("backwork", False, type=bool):
            a0.ignore()
            self.hide()
        self.settings.setValue("main_window/geometry", self.saveGeometry())
