import sys, ctypes, platform, webbrowser, subprocess, datetime, os, json
import logging

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

if not getattr(sys, 'frozen', False):
    sys.stdout = LoggerWriter(logging.info, sys.__stdout__)
    sys.stderr = LoggerWriter(logging.error, sys.__stderr__)

logging.info(f"""
OS: {platform.system()} {platform.release()} {platform.version()} {platform.architecture()[0]}
EXE-version: {getattr(sys, 'frozen', False)}
Python: {sys.version.split()[0]} """)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow,
    QWidget, QHBoxLayout,
    QVBoxLayout,QLabel,
    QPushButton, QLineEdit,
    QScrollArea, QFrame,
    QSizePolicy, QStackedWidget,
    QComboBox, QSpacerItem,
    QMenu, QSystemTrayIcon,
    QProgressBar, QKeySequenceEdit,)
from PyQt6.QtGui import (
    QMouseEvent, QAction,
    QFontMetrics, QIntValidator,
    QRegularExpressionValidator,
    QKeySequence)
from PyQt6.QtCore import (
    QFile, QSettings,
    QRect, QDateTime,
    QPropertyAnimation,
    QEasingCurve, QTimer,
    QTranslator, QLocale,
    QParallelAnimationGroup,
    QRegularExpression, QPoint)
from PyQt6.QtMultimedia import QMediaDevices
from qasync import QEventLoop
from packaging import version

from modules.ChatInterface import ChatInterface
from modules.GetCAICookies import GetCookies
from modules.QCustom import HorizontalScrollArea, CheckablePushButton, ClickableFrame, LeftSidebar
from modules.QThreads import *
from modules.styles import *
from modules.Voice import HorizontalMiniVoiceCard

if platform.system() == 'Windows':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Emilia Next")
    logging.debug("ctypes SetCurrentProcessExplicitAppUserModelID")

class EmiliaNext(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emilia")
        self.setStyleSheet(main_window_style())
        self.settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "Emilia", "settings")
        self.current_language = self.settings.value("emilia_language", QLocale.system().name())
        self.svg_icons = SvgIcons()
        self.version = "3.0.1dev"
        self.beta = version.parse(self.version).is_prerelease

        self.setGeometry(self.settings.value("main_window/x", 100, type=int), self.settings.value("main_window/y", 100, type=int),
                         self.settings.value("main_window/width", 1360, type=int), self.settings.value("main_window/height", 800, type=int))
        self.left_sidebar_visible = True
        self.left_sidebar_hide_user = False
        self.left_sidebar_hide_auto = False
        self.current_chat_interface = None
        self.hide_overlay = True

        self.threads = []
        self.overlays = []
        self.recent_chats = []
        self.featured_chats = []
        self.recommended_chats = []
        self.tray = tray_icon

        self.token = self.settings.value("cai_auth/token", "", type=str)
        self.cookie = self.settings.value("cai_auth/cookie", "", type=str)
        self.auto_collapse_sidebar = self.settings.value("auto_collapse_sidebar", False, type=bool)
        self.name = self.tr("User")
        self.input_devices = {}
        self.output_devices = {}

        for index, device in enumerate(QMediaDevices().audioInputs()):
            self.input_devices[str(index)] = device.description()

        for index, device in enumerate(QMediaDevices().audioOutputs()):
            self.output_devices[str(index)] = device.description()

        self.chat_thread = ChatThread(self)
        self.chat_thread.start()
        self.threads.append(self.chat_thread)
        self.chat_thread.recent_chats_signal.connect(self.addRecentChats)
        self.chat_thread.featured_chats_signal.connect(self.addFeaturedChats)
        self.chat_thread.featured_voices_signal.connect(self.addFeaturedVoices)
        self.chat_thread.recommended_chats_signal.connect(self.addRecommendedChats)
        self.chat_thread.trythis_chats_signal.connect(self.addTryThisChats)
        self.chat_thread.category_characters_signal.connect(self.addCharacterByCategory)
        self.chat_thread.get_me_signal.connect(self.getMe)
        self.chat_thread.get_user_settings_signal.connect(self.getUserSettings)
        self.chat_thread.get_available_models_signal.connect(self.getAvailableModels)
        self.initUI()

        if QDateTime.fromString(self.settings.value("cai_auth/expiration_date")) < QDateTime.currentDateTime():
            if self.token:
                self.chat_thread.create_client(self.token)
                self.chat_thread.create_connect()

                self.chat_thread.get_recent_chats()
                self.chat_thread.get_recommend_chats()
                self.chat_thread.get_featured_chats()
                self.chat_thread.get_trythis_chats()
                self.chat_thread.get_featured_voices()
                self.chat_thread.get_me()
                # self.chat_thread.get_user_settings()
                self.chat_thread.get_available_models()

            if self.cookie:
                self.chat_thread.set_cookie(self.cookie)

            if not self.cookie or not self.token:
                self.openSettings()
                self.settings_page.getCookies()
        else:
            self.openSettings()
            self.settings_page.getCookies()
            self.showNotification(self.tr("Please re-enter (the login data has expired)"))

        self.setOutputDevice(self.settings.value('output_device', 0, type=int))
        if getattr(sys, 'frozen', False): self.checkForUpdates()

    def initUI(self):
        self.layout = QHBoxLayout()

        # Left Sidebar
        self.left_sidebar = self.createLeftSidebar()
        self.layout.addWidget(self.left_sidebar)

        self.main_layout = QVBoxLayout()
        self.layout.addLayout(self.main_layout, 1)

        self.top_widget, self.top_bar_stacked_widget, self.t_bar = self.createTopBar()
        self.main_layout.addWidget(self.t_bar)

        self.main_content_area = QStackedWidget()
        self.main_content_area.setStyleSheet(scroll_bar_style())
        self.main_page = self.createMainContentPage()
        self.search_results_page = QWidget()
        self.search_results_layout = QVBoxLayout(self.search_results_page)
        self.settings_page = SettingsPage(self)
        self.settings_page.save_button.clicked.connect(self.updateAutoCollapseSidebar)
        self.user_page = UserProfile(self)

        self.main_content_area_animation = QPropertyAnimation(self.main_content_area, b"geometry")
        self.main_content_area_animation.setDuration(500)
        self.main_content_area_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.main_content_area.addWidget(self.main_page)
        self.main_content_area.addWidget(self.search_results_page)
        self.main_content_area.addWidget(self.settings_page)
        self.main_content_area.addWidget(self.user_page)

        self.main_layout.addWidget(self.main_content_area, 1)

        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)
        self.createOverlay()

        self.full_animation = QParallelAnimationGroup()
        self.full_animation.addAnimation(self.left_sidebar_animation)
        self.full_animation.addAnimation(self.main_content_area_animation)
        self.full_animation.addAnimation(self.top_bar_animation)

    def createLeftSidebar(self):
        left_sidebar = LeftSidebar(self)
        self.settings_button = left_sidebar.settings_button
        self.profile_button = left_sidebar.profile_button
        self.profile_button_2 = left_sidebar.profile_button_2
        self.recent_chat_layout = left_sidebar.recent_chat_layout

        self.left_sidebar_animation = QPropertyAnimation(left_sidebar, b"geometry")
        self.left_sidebar_animation.setDuration(500)
        self.left_sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.left_sidebar_animation.finished.connect(lambda: self.leftSidebarAnim())

        return left_sidebar

    def addRecentChatCard(self, character_id, character_name, chat_id, character_avatar_url):
        def openChat(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.openChat(character_id, character_name, chat_id, card)
            elif event.button() == Qt.MouseButton.RightButton:
                showContextMenu(self, QPoint(avatar_label.pos().x() + 45 , avatar_label.pos().y() + 22), card)

        card = ClickableFrame()
        card.setObjectName(chat_id)
        card.setFixedWidth(self.settings.value("left_sidebar_width", 255, type=int))
        card.setStyleSheet(card_style())
        card.default_style = card_style()
        card.press_style = card_pressed_style()
        card.mousePress = openChat
        card.enterEvent = lambda event: menu_button.setVisible(True) if menu_button.visibility else None
        card.leaveEvent = lambda event: menu_button.setVisible(False)
        card.setCursor(Qt.CursorShape.PointingHandCursor)


        def showContextMenu(self, pos, card):
            def deleteCard():
                self.chat_thread.hide_chat(character_id)
                card.setParent(None)
                card.deleteLater()

            context_menu = QMenu(self)
            context_menu.setStyleSheet(menu_style())

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
        card.avatar_label = avatar_label

        if character_avatar_url:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + character_avatar_url + '?webp=true&anim=0',
                45, 45)
            load_avatar_thread.image_loaded.connect(avatar_label.setPixmap)
            load_avatar_thread.start()
            self.threads.append(load_avatar_thread)
        else:
            color_avatar(avatar_label, 45, 45, character_name)

        avatar_label_2 = QLabel()
        avatar_label_2.setFixedSize(60, 60)
        avatar_label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_layout.addWidget(avatar_label_2)
        card.avatar_label_2 = avatar_label_2

        if character_avatar_url:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + character_avatar_url + '?webp=true&anim=0',
                55, 55)
            load_avatar_thread.image_loaded.connect(avatar_label_2.setPixmap)
            load_avatar_thread.start()
            self.threads.append(load_avatar_thread)
        else:
            color_avatar(avatar_label_2, 55, 55, character_name)
        avatar_label_2.setVisible(False)

        name_label = QLabel(character_name)
        name_label.setStyleSheet("background-color: transparent; border: none; color: white;")
        chat_layout.addWidget(name_label, 1)
        card.name_label = name_label

        menu_button = QPushButton()
        menu_button.visibility = True
        menu_button.setIcon(self.svg_icons.ellipsis())
        menu_button.setStyleSheet(recent_delete_button_style())
        menu_button.setVisible(False)
        menu_button.clicked.connect(lambda: showContextMenu(self, menu_button.pos(), card))
        chat_layout.addWidget(menu_button, 0, Qt.AlignmentFlag.AlignRight)
        card.menu_button = menu_button

        chat_layout.addStretch()
        card.setLayout(chat_layout)

        self.recent_chat_layout.addWidget(card)

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
        self.thread = DownloadThread(url, save_path)
        self.thread.progress.connect(lambda x: self.download_overlay_progress.setValue(x))
        self.thread.finished.connect(self.runInstaller)
        self.thread.start()

    def runInstaller(self, save_path):
        if save_path:
            self.download_overlay_label.setText(self.tr("Download complete. Running installer..."))
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
        main_content_area = QWidget()
        main_content_area.showEvent = show
        self.main_content_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: transparent; border: none;")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("border-radius: 4px;")
        scroll_layout = QVBoxLayout()
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for_you_section, self.for_you_layout = self.createSection(self.tr("For You"))
        scroll_layout.addWidget(for_you_section)

        recommended_section, self.recommended_layout = self.createSection(self.tr("Recommended"))
        scroll_layout.addWidget(recommended_section)

        try_this_section, self.try_this_odd_layout, self.try_this_even_layout = self.createTryThisSection(self.tr("Try This"))
        scroll_layout.addWidget(try_this_section)

        featured_voices_section, self.featured_voices_layout = self.createVoiceSection()
        scroll_layout.addWidget(featured_voices_section)

        category_section, self.category_layout, self.category_button_layout = self.createCategorySection()
        scroll_layout.addWidget(category_section)

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
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

        self.top_bar_collapse_button = QPushButton()
        self.top_bar_collapse_button.setIcon(self.svg_icons.ellipsis())
        self.top_bar_collapse_button.setStyleSheet(icon_button_style())
        self.top_bar_collapse_button.clicked.connect(self.toggleLeftSidebar)
        self.top_bar_collapse_button.setVisible(not self.left_sidebar_visible)

        self.welcome_label = QLabel(self.tr("Welcome back, User"))
        self.welcome_label.setFont(QFont("Arial", 12))
        top_bar_layout.addWidget(self.welcome_label)

        top_bar_layout.addStretch(1)

        self.update_button = QPushButton(self.tr("Update"))
        self.update_button.setStyleSheet(button_style())
        top_bar_layout.addWidget(self.update_button)
        self.update_button.setVisible(False)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(self.tr("Character Search"))
        self.search_bar.setStyleSheet(lineedit_style())
        self.search_bar.returnPressed.connect(self.showSearchResultsV2)
        top_bar_layout.addWidget(self.search_bar)

        t_layout.addWidget(self.top_bar_collapse_button)
        t_layout.addWidget(top_bar_stacked_widget)

        return top_widget, top_bar_stacked_widget, top_bar

    def createWelcomeSection(self):
        welcome_frame = QFrame()
        welcome_frame.setStyleSheet("background-color: #3c3d3f; border-radius: 15px;")
        welcome_layout = QHBoxLayout()
        welcome_layout.setContentsMargins(15, 15, 15, 15)

        text_area = QWidget()
        text_layout = QVBoxLayout()
        welcome_text = QLabel("welcome_text")
        welcome_text.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_text = QLabel("main_text")
        main_text.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        text_layout.addWidget(welcome_text)
        text_layout.addWidget(main_text)
        text_area.setLayout(text_layout)
        welcome_layout.addWidget(text_area, 1)

        welcome_frame.setLayout(welcome_layout)
        return welcome_frame

    def createSection(self, title):
        section_frame = QFrame()
        section_frame.setFixedHeight(204)
        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(0, 10, 0, 10)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        section_layout.addWidget(title_label)

        scroll_area = HorizontalScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(scroll_style())

        cards_viewport = QWidget()
        cards_layout = QHBoxLayout()
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cards_viewport.setLayout(cards_layout)
        scroll_area.setWidget(cards_viewport)
        cards_layout.addStretch(1)

        section_layout.addWidget(scroll_area)
        section_frame.setLayout(section_layout)
        return section_frame, cards_layout

    def createTryThisSection(self, title):
        section_frame = QFrame()
        section_frame.setFixedHeight(216)
        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(0, 10, 0, 10)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        section_layout.addWidget(title_label)

        scroll_area = HorizontalScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(scroll_style())

        cards_viewport = QWidget()
        cards_layout_main = QVBoxLayout()

        cards_layout_odd = QHBoxLayout()
        cards_layout_odd.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cards_layout_even = QHBoxLayout()
        cards_layout_even.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        cards_layout_main.addLayout(cards_layout_odd)
        cards_layout_main.addLayout(cards_layout_even)

        cards_viewport.setLayout(cards_layout_main)
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
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        section_layout.addWidget(title_label)

        scroll_area = HorizontalScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(scroll_style())

        cards_viewport = QWidget()
        cards_layout = QHBoxLayout()
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cards_viewport.setLayout(cards_layout)
        scroll_area.setWidget(cards_viewport)
        cards_layout.addStretch(1)

        section_layout.addWidget(scroll_area)
        section_frame.setLayout(section_layout)
        return section_frame, cards_layout

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
        button_scroll_area.setWidgetResizable(True)
        button_scroll_area.horizontalScrollBar().setVisible(False)

        buttons_viewport = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_viewport.setLayout(buttons_layout)
        button_scroll_area.setWidget(buttons_viewport)

        self.category_buttons = []

        for key, value in categories.items():
            btn = QPushButton(value)
            btn.setStyleSheet(tab_button_style())
            btn.setObjectName(key)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, b=btn, cat=key: self.onCategoryClicked(b, cat))
            self.category_buttons.append(btn)
            buttons_layout.addWidget(btn)
            if key == "Assistants":
                btn.setChecked(True)
                self.onCategoryClicked(btn, key)
        section_layout.addWidget(button_scroll_area, alignment=Qt.AlignmentFlag.AlignTop)

        scroll_area = HorizontalScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(scroll_style())

        cards_viewport = QWidget()
        cards_layout = QHBoxLayout()
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cards_viewport.setLayout(cards_layout)
        scroll_area.setWidget(cards_viewport)
        cards_layout.addStretch(1)

        section_layout.addWidget(scroll_area)

        section_frame.setLayout(section_layout)
        return section_frame, cards_layout, buttons_layout

    def onCategoryClicked(self, clicked_button, category):
        for btn in self.category_buttons:
            if btn is not clicked_button:
                btn.setChecked(False)
        self.chat_thread.get_category_characters(category)

    def createCard(self, name="", avatar_url="", description="", author="", character_id="", chats=0, voted=0, avatar_label_w=90, avatar_label_h=114):
        card = QFrame()
        card.setStyleSheet(card_style())
        card.mousePressEvent = lambda event: self.openChat(character_id, name, None)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card_layout = QHBoxLayout()

        avatar_label = QLabel()
        avatar_label.setFixedSize(avatar_label_w, avatar_label_h)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(avatar_label)

        if avatar_url:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + avatar_url + '?webp=true&anim=0', avatar_label_w, avatar_label_h)
            load_avatar_thread.image_loaded.connect(avatar_label.setPixmap)
            load_avatar_thread.radius = 4
            load_avatar_thread.start()
            self.threads.append(load_avatar_thread)
        else:
            color_avatar(avatar_label, avatar_label_w, avatar_label_h, name, 4)

        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_layout.addLayout(text_layout, 1)

        title_label = QLabel(name)
        title_label.setWordWrap(True)
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        text_layout.addWidget(title_label)

        if author:
            author_label = QLabel(self.tr("Author: @") + author)
            author_label.setFont(QFont("Arial", 8))
            text_layout.addWidget(author_label)

        if description:
            description_label = QLabel(format_text(description, self.name))
            description_label.setFont(QFont("Arial", 9))
            description_label.setWordWrap(True)
            fm = QFontMetrics(description_label.font())
            description_label.setMaximumHeight(fm.lineSpacing() * 4)
            text_layout.addWidget(description_label)
            card.setToolTip(format_text(description))

        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        text_layout.addItem(spacer)

        add_info = QLabel()
        if chats:
            add_info.setText(add_info.text() + str(format_number(chats)) + self.tr(" chats"))
        if voted:
            add_info.setText(add_info.text() + " • " + str(format_number(voted)) + self.tr(" likes"))

        if add_info.text():
            add_info.setFont(QFont("Arial", 10))
            text_layout.addWidget(add_info)

        card.setLayout(card_layout)
        return card

    def createMiniCard(self, name="", avatar_url="", character_id=""):
        card = QFrame()
        card.setStyleSheet(card_style())
        card.mousePressEvent = lambda event: self.openChat(character_id, name, None)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card_layout = QHBoxLayout()

        avatar_label = QLabel()
        avatar_label.setFixedSize(54, 54)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(avatar_label)

        if avatar_url:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + avatar_url + '?webp=true&anim=0',54, 54)
            load_avatar_thread.image_loaded.connect(avatar_label.setPixmap)
            load_avatar_thread.radius = 4
            load_avatar_thread.start()
            self.threads.append(load_avatar_thread)
        else:
            color_avatar(avatar_label, 54, 54, name, 4)

        title_label = QLabel(name)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        card_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        card.setLayout(card_layout)
        return card

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
        auto_collapse_sidebar_checkbox = self.settings_page.findChild(CheckablePushButton, "auto_collapse_sidebar")
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
        # self.top_bar_stacked_widget.setCurrentWidget(self.top_widget)
        self.current_chat_interface = None
        self.top_widget.setVisible(True)

    def openChat(self, character_id, character_name, chat_id, card=None):
        if self.current_chat_interface:
            self.main_content_area.removeWidget(self.current_chat_interface)
            self.current_chat_interface.deleteLater()
            self.chat_thread.message_signal.disconnect()
            if self.current_chat_interface.voice_enabled:
                self.chat_thread.replay_signal.disconnect()
            self.current_chat_interface = None

        def hideEvent():
            if card:
                card.setCheckable(False)

        self.current_chat_interface = ChatInterface(main_window, character_name, character_id, chat_id)
        self.current_chat_interface.chat_id = chat_id
        self.current_chat_interface.hideEvent = lambda event: hideEvent()
        self.main_content_area.addWidget(self.current_chat_interface)
        self.main_content_area.setCurrentWidget(self.current_chat_interface)

    def openSettings(self):
        self.main_content_area.setCurrentWidget(self.settings_page)
        if self.current_chat_interface:
            self.current_chat_interface.setVisible(False)
            self.search_bar.setText("")

    def openUserPage(self, username):
        self.user_page.refresh(username)
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
            card = self.createCard(character.get('participant__name', "Unknown"), character.get('avatar_file_name'),
                                   character.get('title'), character.get('user__username'),
                                   character.get('external_id'), character.get('participant__num_interactions'))
            card.setFixedSize(252, 134)
            self.category_layout.addWidget(card)

    def addRecentChats(self, chats):
        for i in reversed(range(self.recent_chat_layout.count())):
            item = self.recent_chat_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.recent_chats = chats
        for chat in self.recent_chats:
            self.addRecentChatCard(chat.get('character_id'), chat.get('name'), chat.get('id'), chat.get('avatar_file_name'))
        self.left_sidebar.resizeCards()
    def addFeaturedVoices(self, voices):
        for i in reversed(range(self.featured_voices_layout.count())):
            item = self.featured_voices_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.featured_voices = voices
        for voice in self.featured_voices:
            card = HorizontalMiniVoiceCard(main_window, voice)
            card.setFixedWidth(200)
            self.featured_voices_layout.addWidget(card)

    def addFeaturedChats(self, chats):
        for i in reversed(range(self.for_you_layout.count())):
            item = self.for_you_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.featured_chats = chats
        for character in self.featured_chats:
            card = self.createCard(character.get('participant__name', "Unknown"), character.get('avatar_file_name'), character.get('title'), character.get('user__username'), character.get('external_id'), character.get('participant__num_interactions'))
            card.setFixedSize(244, 134)
            self.for_you_layout.addWidget(card)

    def addTryThisChats(self, chats):
        for layout in (self.try_this_odd_layout, self.try_this_even_layout):
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                if item and item.widget():
                    item.widget().deleteLater()

        self.featured_chats = chats
        for index, character in enumerate(self.featured_chats):
            card = self.createMiniCard(
                character.get('name', "Unknown"),
                character.get('avatar_file_name'),
                character.get('external_id')
            )
            card.setFixedSize(250, 70)
            if (index + 1) % 2 == 0:
                self.try_this_even_layout.addWidget(card)
            else:
                self.try_this_odd_layout.addWidget(card)

    def addRecommendedChats(self, chats):
        for i in reversed(range(self.recommended_layout.count())):
            item = self.recommended_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.recommended_chats = chats
        for character in self.recommended_chats:
            card = self.createCard(character.get('participant__name', "Unknown"), character.get('avatar_file_name'), character.get('title'), character.get('user__username'), character.get('external_id'), character.get('participant__num_interactions'))
            card.setFixedSize(244, 134)
            self.recommended_layout.addWidget(card)

    def getMe(self, data):
        self.me = data
        self.author_id = data['id']
        self.name = data['account']['name']
        self.username = data['username']

        self.welcome_label.setText(self.tr("Welcome back, ") + self.name)
        self.profile_button.setText(self.name)

    def getUserSettings(self, data):
        self.user_settings = data

    def getAvailableModels(self, data):
        self.available_models = data

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
        print(self.rect())
        self.settings.setValue("main_window/height", self.height())
        self.settings.setValue("main_window/width", self.width())

    def moveEvent(self, a0):
        super().moveEvent(a0)
        self.settings.setValue("main_window/x", self.x())
        self.settings.setValue("main_window/y", self.y())

    def showEvent(self, a0):
        super().showEvent(a0)
        hide_action.setVisible(True)
        show_action.setVisible(False)

    def hideEvent(self, a0):
        hide_action.setVisible(False)
        show_action.setVisible(True)
        super().hideEvent(a0)

class SearchPage(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.svg_icons = SvgIcons()
        self.setStyleSheet("background-color: transparent; border: none;")

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self.mw)

        self.scroll_area, self.cards_viewport, self.cards_layout = self.createMainContentPage()
        self.top_bar, self.top_bar_layout = self.createTopBar()


        self.layout.addWidget(self.scroll_area, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(self.layout)

        self.mw.top_bar_collapse_button.setStyleSheet("""
        QPushButton {
            background-color: #494a4d;
            color: #e8eaed;
            border: none;
            border-radius: 4px;
            padding: 12px 10px;
        }
        QPushButton:hover {
            background-color: #5f6368;
        }
        QPushButton:pressed {
            background-color: #3c3d3f;
        }
    """)
        self.mw.top_bar_stacked_widget.setFixedHeight(40)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def createMainContentPage(self):
        scroll_area = QScrollArea()
        scroll_area.setFixedWidth(700)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(scroll_style())

        cards_viewport = QWidget()
        cards_viewport.setStyleSheet("background-color: transparent; border: none;")
        cards_layout = QVBoxLayout()
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        cards_viewport.setLayout(cards_layout)
        scroll_area.setWidget(cards_viewport)

        return scroll_area, cards_viewport, cards_layout

    def showSearchResultsV2(self):
        search_query = self.search_bar.text().strip()
        if not search_query:
            return

        self.mw.search_bar.setText(search_query)
        search_page = SearchPage(self.mw)
        self.mw.main_content_area.addWidget(search_page)
        self.mw.main_content_area.setCurrentWidget(search_page)

        self.mw.chat_thread.character_search_signal.connect(search_page.populate)
        self.mw.chat_thread.character_search(search_query)
        self.deleteLater()

    def populate(self, data):
        self.data = data[0].get("result", {}).get("data", {}).get("json", []).get('characters', [])
        if self.data:
            for character in self.data:
                card = self.mw.createCard(character.get('participant__name'), character.get('avatar_file_name'),
                                          character.get('title').replace('\n', ''), character.get('user__username'),
                                          character.get('external_id'), character.get('participant__num_interactions', 0),
                                          0, 70, 70)
                card.setFixedHeight(87)
                self.cards_layout.addWidget(card)
        else:
            no_results_label = QLabel(self.tr("Characters not found"))
            no_results_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
            self.cards_layout.addWidget(no_results_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.mw.chat_thread.character_search_signal.disconnect()

    def createTopBar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(40)
        top_bar.setStyleSheet(lineedit_style2())
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        search_label = QLabel()
        search_label.setPixmap(self.svg_icons.search())
        search_label.setStyleSheet("background-color: transparent; color: #e8eaed; border: none; font-size: 8px;")
        top_bar_layout.addWidget(search_label)

        self.search_bar = QLineEdit()
        self.search_bar.setText(self.mw.search_bar.text())
        self.search_bar.setPlaceholderText(self.tr("Character Search"))
        self.search_bar.returnPressed.connect(self.showSearchResultsV2)
        top_bar_layout.addWidget(self.search_bar)

        return top_bar, top_bar_layout

    def hideEvent(self, a0):
        super().hideEvent(a0)
        self.mw.top_bar_collapse_button.setStyleSheet(icon_button_style())
        self.mw.search_bar.setText("")

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent; border: none;")
        main_layout = QVBoxLayout()
        self.mw: EmiliaNext | None = parent
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
                    {"type": "pushbutton", "label": self.tr("Character.AI Login") + " | " + self.tr("Valid until: ") + self.mw.settings.value('cai_auth/expiration_date') if self.mw.settings.value('cai_auth/expiration_date') else self.tr("Character.AI Login"),
                     "buttonlabel": self.tr("Re-Auth with Character.AI") if self.mw.token else self.tr("Auth with Character.AI") ,
                     "key": "auth_cookie_get", "click": self.getCookies}
                ]
            }, {
                "label": self.tr("Emilia Settings"),
                "settings": [
                    {"type": "checkbox", "label": self.tr("Automatically hide the sidebar when the window is narrow"), "key": "auto_collapse_sidebar"},
                    {"type": "checkbox", "label": self.tr("Working in the background"), "key": "backwork"},
                    {"type": "combobox", "label": self.tr("Input Device"), "items": self.mw.input_devices.values(), "key": "input_device"},
                    {"type": "combobox", "label": self.tr("Output Device"), "items": self.mw.output_devices.values(), "key": "output_device"},
                    {"type": "keybind", "label": self.tr("Microphone mute key"), "def_value": "Ctrl+M", "key": "microphone_mute_key_bind"},
                ]
            }, {
                "label": self.tr("VTube Studio Plugin"),
                "settings": [
                    {"type": "checkbox", "label": self.tr("Use VTube Studio"), "key": "vtube/use"},
                    {"type": "lineedit", "label": self.tr("VTube Studio Port"), "key": "vtube/port",
                     "validator": QIntValidator(0, 99999999), "def_value": 8001, "may_be_empty": False},
                    {"type": "pushbutton", "label": self.tr("VTube Emotes Editor"),
                     "buttonlabel": self.tr("Open"),
                     "key": "vtube/emotes_editor", "click": self.openEmotesEditor},
                    {"type": "pushbutton", "label": self.tr("Check the connection to VTube Studio"), "buttonlabel": self.tr("Check"),
                     "key": "vtube/check_connect", "click": self.vtubeCheck},
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
            u_widget = QFrame()
            u_widget.setStyleSheet(card_style())
            u_layout = QHBoxLayout(u_widget)
            u_widget.setLayout(u_layout)

            param_name_edit = QLineEdit()
            param_name_edit.setValidator(validator)
            param_name_edit.textChanged.connect(lambda t: updateParamName(t, param_name))
            param_name_edit.setStyleSheet(lineedit_style())
            param_name_edit.setPlaceholderText(self.tr("Parameter Name"))
            param_name_edit.setText(param_name)
            param_name_edit.setFixedWidth(150)
            u_layout.addWidget(param_name_edit)

            remove_button = QPushButton()
            remove_button.clicked.connect(removeParameter)
            remove_button.setStyleSheet(icon_button_style())
            remove_button.setIcon(self.mw.svg_icons.close())
            u_layout.addWidget(remove_button)

            u_layout.addStretch()

            random_checkbox = CheckablePushButton()
            random_checkbox.setChecked(random_value)
            random_checkbox.clicked.connect(updateRandom)
            u_layout.addWidget(random_checkbox)

            random_label = QLabel(self.tr("Use Random Value"))
            u_layout.addWidget(random_label)

            value_1_edit = QLineEdit()
            value_1_edit.setValidator(validator)
            value_1_edit.textEdited.connect(updateParamValue1)
            value_1_edit.setStyleSheet(lineedit_style())
            value_1_edit.setPlaceholderText(self.tr("From"))
            value_1_edit.setText(str(value_1))
            value_1_edit.setFixedWidth(50)
            u_layout.addWidget(value_1_edit)
            value_1_edit.setVisible(random_value)

            value_2_edit = QLineEdit()
            value_2_edit.setValidator(validator)
            value_2_edit.textEdited.connect(updateParamValue2)
            value_2_edit.setStyleSheet(lineedit_style())
            value_2_edit.setPlaceholderText(self.tr("To"))
            value_2_edit.setText(str(value_2))
            value_2_edit.setFixedWidth(50)
            u_layout.addWidget(value_2_edit)
            value_2_edit.setVisible(random_value)

            value_edit = QLineEdit()
            value_edit.setValidator(validator)
            value_edit.textEdited.connect(updateParamValue)
            value_edit.setStyleSheet(lineedit_style())
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

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(scroll_style())

        container = QWidget()
        container.setStyleSheet("background-color: transparent; border: none;")
        emotes_layout = QVBoxLayout()
        emotes_layout.setContentsMargins(10, 10, 10, 10)
        emotes_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        container.setLayout(emotes_layout)

        scroll_area.setWidget(container)

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
            group_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            head_layout.addWidget(group_label)
            test_emote_button = QPushButton(self.tr(" | Test"))
            test_emote_button.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            test_emote_button.clicked.connect(lambda _, e=emote_name: self.mw.chat_thread.vtube_use_emote(e))
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
            add_button = QPushButton(self.tr("Add parameter"))
            add_button.setStyleSheet(button_style())
            add_button.clicked.connect(lambda _, b=add_button, l=e_layout, e=emote_name: createParameter(b, l, e))
            e_layout.addWidget(add_button, alignment=Qt.AlignmentFlag.AlignHCenter)
            emotes_layout.addWidget(e_widget)

        widget = QWidget()
        widget.setFixedSize(750, 750)
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)

        buttons_frame = QWidget(widget)
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        buttons_frame.setLayout(buttons_layout)

        save_button = QPushButton(self.tr("Save"))
        save_button.clicked.connect(save)
        save_button.setStyleSheet(button_style())
        buttons_layout.addWidget(save_button)

        close_button = QPushButton(self.tr("Close"))
        close_button.clicked.connect(self.mw.hideOverlay)
        close_button.setStyleSheet(button_style())
        buttons_layout.addWidget(close_button)

        layout.addWidget(scroll_area)
        layout.addWidget(buttons_frame)
        self.mw.showOverlay(widget)

    def _vtubeCheck(self, text):
        self.mw.showNotification(text)
        self.mw.chat_thread.vtube_connect_signal.disconnect()

    def vtubeCheck(self):
        self.mw.chat_thread.vtube_connect_signal.connect(self._vtubeCheck)
        self.mw.chat_thread.check_vtube_connect()

    def createTopBar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(0)
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        return top_bar, top_bar_layout

    def createMainContentPage(self):
        scroll_area = QScrollArea()
        scroll_area.setFixedWidth(800)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(scroll_bar_style())

        settings_viewport = QWidget()
        settings_viewport.setStyleSheet("background-color: transparent; border: none;")
        settings_layout = QVBoxLayout()
        settings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        settings_viewport.setLayout(settings_layout)
        scroll_area.setWidget(settings_viewport)

        for setting_group in self.settings_data:
            group_layout = QVBoxLayout()
            group_label = QLabel(setting_group["label"])
            group_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            group_layout.addWidget(group_label, alignment=Qt.AlignmentFlag.AlignHCenter)

            for setting in setting_group["settings"]:
                layout = QHBoxLayout()
                if setting.get("label"):
                    label = QLabel(setting["label"])
                    layout.addWidget(label)
                    layout.addStretch(1)
                key = setting["key"]

                if setting["type"] == "lineedit":
                    widget = QLineEdit()
                    if setting.get("validator"):
                        widget.setValidator(setting["validator"])
                    widget.setObjectName(key)
                    widget.setEchoMode(setting.get("echo", QLineEdit.EchoMode.Normal))
                    widget.setStyleSheet(lineedit_style())
                elif setting["type"] == "checkbox":
                    widget = CheckablePushButton()
                    widget.setObjectName(key)
                elif setting["type"] == "pushbutton":
                    widget = QPushButton(setting["buttonlabel"])
                    widget.setObjectName(key)
                    widget.setStyleSheet(button_style())
                    widget.clicked.connect(setting["click"])
                elif setting["type"] == "combobox":
                    widget = QComboBox()
                    widget.setObjectName(key)
                    widget.setStyleSheet(combobox_style())
                    widget.addItems(setting['items'])
                elif setting["type"] == "keybind":
                    widget = QKeySequenceEdit()
                    widget.setObjectName(key)
                    widget.setStyleSheet(keysequenceedit_style())
                    widget.keySequenceChanged.connect(lambda seq, edit=widget: edit.setKeySequence(QKeySequence(seq[0])) if seq.count() > 1 else None)

                layout.addWidget(widget)
                group_layout.addLayout(layout)
                self.setting_widgets[setting["key"]] = widget
                self.setting_data[setting["key"]] = setting

            settings_layout.addLayout(group_layout)
            settings_layout.addWidget(QFrame())

        return scroll_area, settings_viewport, settings_layout

    def createButtonBar(self):
        button_bar = QWidget()
        button_layout = QHBoxLayout()
        button_bar.setLayout(button_layout)
        self.save_button = QPushButton(self.tr("Save"))
        self.save_button.clicked.connect(self.saveSettings)
        self.save_button.setStyleSheet(button_style())
        self.report_button = QPushButton(self.tr("Report a Problem"))
        self.report_button.clicked.connect(lambda: webbrowser.open("https://github.com/Kajitsy/Emilia/issues"))
        self.report_button.setStyleSheet(button_style())
        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.loadSettings)
        self.cancel_button.setStyleSheet(button_style())
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.report_button)

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

            self.mw.chat_thread.chat_histories = {}
            self.mw.chat_thread.me = None
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
                for i in range(self.mw.recent_chat_layout.count()):
                    item = self.mw.recent_chat_layout.itemAt(i)
                    if item and item.widget():
                        item.widget().deleteLater()

            self.mw.chat_thread.create_client(self.mw.token)
            self.mw.chat_thread.set_cookie(self.cookie)
            self.mw.chat_thread.create_connect()

            self.mw.chat_thread.get_recent_chats()
            self.mw.chat_thread.get_featured_chats()
            self.mw.chat_thread.get_recommend_chats()
            self.mw.chat_thread.get_me()
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

    def back(self):
        self.mw.main_content_area.setCurrentWidget(self.mw.main_page)
        self.mw.left_sidebar.setEnabled(True)

    def showEvent(self, event):
        super().showEvent(event)
        self.mw.top_bar_stacked_widget.setFixedHeight(0)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)
        self.loadSettings()

    def hideEvent(self, a0):
        super().hideEvent(a0)
        self.mw.settings_button.setChecked(False)

    def loadSettings(self):
        for key, widget in self.setting_widgets.items():
            value = self.mw.settings.value(key, str(self.setting_data[key].get('def_value')))
            if isinstance(widget, QLineEdit):
                widget.setText(value if value is not None else "")
            elif isinstance(widget, CheckablePushButton):
                widget.setChecked(value == 'true' if value is not None else False)
            elif isinstance(widget, QComboBox):
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
            elif isinstance(widget, QKeySequenceEdit):
                widget.setKeySequence(QKeySequence(value))
        logging.debug("main.py: Settings are loaded")

    def saveSettings(self):
        for key, widget in self.setting_widgets.items():
            if isinstance(widget, QLineEdit):
                if not self.setting_data.get(key).get('may_be_empty', True) and not widget.text():
                    self.mw.showNotification(self.setting_data[key]['label'] + self.tr(" cannot be empty"))
                    return
                self.mw.settings.setValue(key, widget.text())
                if key == "vtube/port":
                    self.mw.chat_thread.eec.create_vts_with_port(int(widget.text()))
            elif isinstance(widget, CheckablePushButton):
                self.mw.settings.setValue(key, 'true' if widget.isChecked() else 'false')
            elif isinstance(widget, QComboBox):
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
            elif isinstance(widget, QKeySequenceEdit):
                self.mw.settings.setValue(key, widget.keySequence().toString())
        self.mw.showNotification(self.tr("Settings saved successfully"))
        logging.debug("main.py: Settings saved successfully")

class UserProfile(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.profile_id = None
        self.is_me = False
        self.data = {}
        self.me_following = []
        self.mw = main_window
        self.svg_icons = SvgIcons()

        self.initUI()

    def initUI(self):
        self.top_bar, self.top_bar_layout = self.createTopBar()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        main_info_frame = QFrame(self)
        main_info_layout = QVBoxLayout()
        main_info_frame.setLayout(main_info_layout)
        layout.addWidget(main_info_frame)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(80, 80)
        main_info_layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.name_label = QLabel(self.tr("Name"))
        self.name_label.setStyleSheet("font-size: 18px;")
        main_info_layout.addWidget(self.name_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.username_label = QLabel("@username")
        self.username_label.setStyleSheet("color: #a2a2ac; font-size: 12px;")
        main_info_layout.addWidget(self.username_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        sub_frame = QFrame(self)
        sub_layout = QHBoxLayout()
        sub_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_frame.setLayout(sub_layout)
        layout.addWidget(sub_frame)

        self.followers_label = QLabel(self.tr("0 followers"))
        self.followers_label.mousePressEvent = lambda event: self.showFollowingFollowers("following")
        self.followers_label.setStyleSheet("color: #a2a2ac;")
        sub_layout.addWidget(self.followers_label)

        span_label = QLabel("•")
        span_label.setStyleSheet("color: #a2a2ac;")
        sub_layout.addWidget(span_label)

        self.following_label = QLabel(self.tr("0 following"))
        self.following_label.mousePressEvent = lambda event: self.showFollowingFollowers("followers")
        self.following_label.setStyleSheet("color: #a2a2ac;")
        sub_layout.addWidget(self.following_label)

        span2_label = QLabel("|")
        span2_label.setStyleSheet("color: #a2a2ac;")
        sub_layout.addWidget(span2_label)

        self.chats_label = QLabel(self.tr("0 chats"))
        self.chats_label.setStyleSheet("color: #a2a2ac;")
        sub_layout.addWidget(self.chats_label)

        but_frame = QFrame(self)
        but_layout = QHBoxLayout()
        but_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        but_frame.setLayout(but_layout)
        layout.addWidget(but_frame)

        self.follow_button = QPushButton(self.tr("Follow"))
        self.follow_button.setStyleSheet(button_style())
        self.follow_button.setVisible(False)
        but_layout.addWidget(self.follow_button)

        self.share_button = QPushButton()
        self.share_button.setStyleSheet(icon_button_style())
        self.share_button.setIcon(self.svg_icons.share())
        self.share_button.clicked.connect(self.share)
        but_layout.addWidget(self.share_button)

        content_layout = QVBoxLayout()

        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        buttons_frame.setLayout(buttons_layout)
        content_layout.addWidget(buttons_frame)

        self.characters_button = QPushButton(self.tr("Characters"))
        self.characters_button.setCheckable(True)
        self.characters_button.setChecked(True)
        self.characters_button.setStyleSheet(tab_button_style())
        self.characters_button.clicked.connect(lambda event: self.lists_widget.setCurrentWidget(self.character_list))
        self.characters_button.clicked.connect(lambda event: self.voices_button.setChecked(False))
        buttons_layout.addWidget(self.characters_button)

        self.voices_button = QPushButton(self.tr("Voices"))
        self.voices_button.setCheckable(True)
        self.voices_button.setStyleSheet(tab_button_style())
        self.voices_button.clicked.connect(lambda event: self.lists_widget.setCurrentWidget(self.voice_list))
        self.voices_button.clicked.connect(lambda event: self.characters_button.setChecked(False))
        buttons_layout.addWidget(self.voices_button)

        self.character_list, self.character_list_layout = self.scroll_page()
        self.voice_list, self.voice_list_layout = self.scroll_page()

        self.lists_widget = QStackedWidget()
        self.lists_widget.addWidget(self.character_list)
        self.lists_widget.addWidget(self.voice_list)
        self.lists_widget.setFixedWidth(600)
        self.lists_widget.setCurrentWidget(self.character_list)
        content_layout.addWidget(self.lists_widget, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addLayout(content_layout)

        self.setLayout(layout)

    def refresh(self, username):
        self.avatar_label.setPixmap(QPixmap())
        self.name_label.setText("")
        self.username_label.setText("")
        self.followers_label.setText("")
        self.following_label.setText("")
        self.chats_label.setText("")
        self.follow_button.setVisible(False)
        for i in range(self.character_list_layout.count()):
            item = self.character_list_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        for i in range(self.voice_list_layout.count()):
            item = self.voice_list_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self.profile_id = username
        self.is_me = self.profile_id == self.mw.username
        self.mw.chat_thread.get_user_signal.connect(self._getUser)
        self.mw.chat_thread.get_user(self.profile_id)
        self.mw.chat_thread.voices_search_username_signal.connect(self._getVoices)
        self.mw.chat_thread.voices_search_username(self.profile_id)

    def _getFollowing(self, data):
        self.mw.chat_thread.me_following_signal.disconnect()
        self.me_following = data.get('following', [])

        if self.username == self.mw.username:
            self.follow_button.setVisible(False)
        else:
            self.follow_button.setVisible(True)

        if self.username in self.me_following:
            self.follow_button.setText(self.tr("Unfollow"))
            self.follow_button.clicked.connect(self.unfollow)
        else:
            self.follow_button.clicked.connect(self.follow)

    def getFollowing(self):
        self.mw.chat_thread.me_following_signal.connect(self._getFollowing)
        self.mw.chat_thread.get_me_following()

    def _getVoices(self, data):
        self.mw.chat_thread.voices_search_username_signal.disconnect()
        self.voice_data = data

        if self.voice_data:
            for voice in self.voice_data:
                card = HorizontalMiniVoiceCard(main_window, voice)
                self.voice_list_layout.addWidget(card)
        else:
            empty_label = QLabel(self.tr("And it's empty here..."))
            self.voice_list_layout.addWidget(empty_label, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _getUser(self, data):
        self.mw.chat_thread.get_user_signal.disconnect()
        self.getFollowing()
        self.data = data
        self.username = self.data.get('username')

        if self.data.get('avatar_file_name'):
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.data.get('avatar_file_name') + '?webp=true&anim=0', 80, 80)
            load_avatar_thread.image_loaded.connect(self.avatar_label.setPixmap)
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            color_avatar(self.avatar_label, 80, 80, self.data.get('name'))

        chats_count = 0
        for character in self.data.get('characters', []):
            chats_count += character.get('participant__num_interactions', 0)
        chats_count = format_number(chats_count)

        self.name_label.setText(f"{self.data.get('name')}")
        self.username_label.setText(f"@{self.username}")
        self.followers_label.setText(str(self.data.get('num_followers')) + " " + self.tr("followers"))
        self.following_label.setText(str(self.data.get('num_following')) + " " + self.tr("following"))
        self.chats_label.setText(str(chats_count) + " " + self.tr("chats"))
        if self.data.get('characters', []):
            for character in self.data.get('characters', []):
                card = self.mw.createCard(character['participant__name'], character.get('avatar_file_name'), character.get('greeting'), "", character['external_id'], character["participant__num_interactions"], character["upvotes"], 70, 70)
                card.setFixedHeight(87)
                self.character_list_layout.addWidget(card)
        else:
            empty_label = QLabel(self.tr("And it's empty here..."))
            self.character_list_layout.addWidget(empty_label, alignment=Qt.AlignmentFlag.AlignHCenter)

    def share(self):
        QApplication.clipboard().setText(f'https://character.ai/profile/{self.username}')
        self.mw.showNotification(self.tr("Link copied to clipboard"))

    def scroll_page(self):
        f_page = QWidget()
        f_page_layout = QVBoxLayout(f_page)
        f_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        f_page.setLayout(f_page_layout)

        users_scroll_area = QScrollArea()
        users_scroll_area.setWidgetResizable(True)
        users_scroll_area.setStyleSheet(scroll_style())

        users_container = QWidget()
        users_container.setStyleSheet("background-color: transparent; border: none;")
        users_layout = QVBoxLayout()
        users_layout.setContentsMargins(10,10,10,10)
        users_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        users_container.setLayout(users_layout)

        users_scroll_area.setWidget(users_container)
        f_page_layout.addWidget(users_scroll_area)
        return f_page, users_layout

    def unfollow(self):
        def unfollow(self, data):
            self.follow_button.setText(self.tr("Follow"))
            self.follow_button.clicked.disconnect()
            self.follow_button.clicked.connect(self.follow)
        self.mw.chat_thread.user_unfollow_signal.connect(lambda data: unfollow(self, data))
        self.mw.chat_thread.user_unfollow(self.username)

    def follow(self):
        def follow(self, data):
            self.follow_button.setText(self.tr("Unfollow"))
            self.follow_button.clicked.disconnect()
            self.follow_button.clicked.connect(self.unfollow)
        self.mw.chat_thread.user_follow_signal.connect(lambda data: follow(self, data))
        self.mw.chat_thread.user_follow(self.username)

    def showFollowingFollowers(self, open_page="followers"):
        def openUser(username):
            self.mw.openUserPage(username)
            self.mw.hideOverlay()

        def follow(username, button: QPushButton):
            def follow(data):
                button.setText(self.tr("Unfollow"))
                button.clicked.disconnect()
                button.clicked.connect(lambda: unfollow(username, button))

            self.mw.chat_thread.user_follow_signal.connect(lambda data: follow(data))
            self.mw.chat_thread.user_follow(username)

        def unfollow(username, button: QPushButton):
            def unfollow(data):
                button.setText(self.tr("Follow"))
                button.clicked.disconnect()
                button.clicked.connect(lambda: follow(username, button))

            self.mw.chat_thread.user_unfollow_signal.connect(lambda data: unfollow(data))
            self.mw.chat_thread.user_unfollow(username)

        def _followers(data):
            self.mw.chat_thread.user_followers_signal.disconnect()
            for user in data.get('users', {}):
                card = createCard(self, user)
                card.setFixedWidth(435)
                followers_users_layout.addWidget(card)

        def _following(data):
            self.mw.chat_thread.user_following_signal.disconnect()
            for user in data.get('users', {}):
                card = createCard(self, user)
                card.setFixedWidth(435)
                following_users_layout.addWidget(card)

        def createCard(self: UserProfile, data):
            username = data.get("username")
            u_widget = QFrame()
            u_widget.setStyleSheet(card_style())
            u_widget.mousePressEvent = lambda event: openUser(username)
            u_widget.setCursor(Qt.CursorShape.PointingHandCursor)
            u_layout = QHBoxLayout(u_widget)
            u_widget.setLayout(u_layout)

            avatar_label = QLabel()
            avatar_label.setFixedSize(40, 40)
            if data.get('account__avatar_file_name'):
                load_avatar_thread = ImageLoaderThread(
                    "https://characterai.io/i/80/static/avatars/" + data.get('account__avatar_file_name') + '?webp=true&anim=0', 40, 40)
                load_avatar_thread.radius = 4
                load_avatar_thread.image_loaded.connect(avatar_label.setPixmap)
                load_avatar_thread.start()
                self.mw.threads.append(load_avatar_thread)
            else:
                color_avatar(avatar_label, 40, 40, username, 4)
            u_layout.addWidget(avatar_label)

            info_layout = QVBoxLayout()
            u_layout.addLayout(info_layout)
            name_label = QLabel(username)
            info_layout.addWidget(name_label, alignment=Qt.AlignmentFlag.AlignLeft)
            if data.get('account__bio'):
                bio = data.get('account__bio')
                if len(bio) > 45:
                    bio = data.get('account__bio')[:45] + "..."
                bio_label = QLabel(bio)
                bio_label.setStyleSheet("color: #a2a2ac;")
                info_layout.addWidget(bio_label, alignment=Qt.AlignmentFlag.AlignLeft)

            sub_button = QPushButton()
            sub_button.setStyleSheet(button_style())
            if username != self.mw.username:
                u_layout.addWidget(sub_button, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if username in self.me_following:
                    sub_button.setText(self.tr("Unfollow"))
                    sub_button.clicked.connect(lambda: unfollow(username, sub_button))
                else:
                    sub_button.setText(self.tr("Follow"))
                    sub_button.clicked.connect(lambda: follow(username, sub_button))
            return u_widget

        widget = QWidget()
        widget.setFixedSize(500, 750)
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)

        buttons_frame = QFrame(widget)
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        buttons_frame.setLayout(buttons_layout)

        followers_button = QPushButton(self.tr("Followers"))
        followers_button.setCheckable(True)
        followers_button.setStyleSheet(tab_button_style())
        followers_button.clicked.connect(lambda: pages_widget.setCurrentWidget(followers_page))
        followers_button.clicked.connect(lambda: following_button.setChecked(False))
        buttons_layout.addWidget(followers_button)

        following_button = QPushButton(self.tr("Following"))
        following_button.setCheckable(True)
        following_button.setStyleSheet(tab_button_style())
        following_button.clicked.connect(lambda: pages_widget.setCurrentWidget(following_page))
        following_button.clicked.connect(lambda: followers_button.setChecked(False))
        buttons_layout.addWidget(following_button)

        followers_page, followers_users_layout = self.scroll_page()
        following_page, following_users_layout = self.scroll_page()

        pages_widget = QStackedWidget()
        pages_widget.addWidget(followers_page)
        pages_widget.addWidget(following_page)
        if open_page == "followers":
            pages_widget.setCurrentWidget(following_page)
            following_button.setChecked(True)
        else:
            pages_widget.setCurrentWidget(followers_page)
            followers_button.setChecked(True)

        self.mw.chat_thread.user_followers_signal.connect(_followers)
        self.mw.chat_thread.user_following_signal.connect(_following)
        self.mw.chat_thread.get_user_followers(username=self.username)
        self.mw.chat_thread.get_user_following(username=self.username)

        layout.addWidget(buttons_frame)
        layout.addWidget(pages_widget, 1)
        self.mw.showOverlay(widget)

    def createTopBar(self):
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        return top_bar, top_bar_layout

    def showEvent(self, a0):
        super().showEvent(a0)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def hideEvent(self, a0):
        super().hideEvent(a0)
        self.mw.profile_button.setChecked(False)
        self.mw.profile_button_2.setChecked(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    translator = QTranslator() # pylupdate6 --verbose .\modules\ChatInterface.py .\modules\GetCAICookies.py .\modules\Voice.py .\modules\QThreads.py .\modules\QCustom.py .\main.py -ts lang/lang.ts
    translator.load(
        f"lang/{QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, 'Emilia', 'settings').value('emilia_language', QLocale.system().name())}.qm")
    app.installTranslator(translator)

    loop = asyncio.SelectorEventLoop()
    qloop = QEventLoop(app, set_running_loop=loop)
    asyncio.set_event_loop(qloop)

    tray_icon = QSystemTrayIcon()
    tray_menu = QMenu()
    main_window = EmiliaNext()

    tray_icon.activated.connect(
        lambda reason: main_window.show() or main_window.raise_() or main_window.activateWindow()
        if reason == QSystemTrayIcon.ActivationReason.Trigger else None
    )
    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("Emilia Next")
    app.setWindowIcon(QIcon("icon.ico"))
    tray_icon.setIcon(QIcon("icon.ico"))

    show_action = QAction(tray_icon.tr("Show"))
    show_action.triggered.connect(lambda: main_window.show())
    tray_menu.addAction(show_action)

    hide_action = QAction(tray_icon.tr("Hide"))
    hide_action.triggered.connect(lambda: main_window.hide())
    tray_menu.addAction(hide_action)

    quit_action = QAction(tray_icon.tr("Quit"))
    quit_action.triggered.connect(lambda event: sys.exit(app.exec()))
    tray_menu.addAction(quit_action)

    main_window.show()
    tray_icon.show()

    with qloop:
        qloop.run_forever()